from __future__ import annotations

import cgi
import json
import os
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ai_video_publisher.task import PublishTask


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "web"
TASK_PATH = PROJECT_ROOT / "task.web.json"
UPLOAD_DIR = PROJECT_ROOT / "uploads"


class PublishJob:
    """一次网页触发的 publish 子进程及其日志缓冲。"""

    def __init__(self, proc: subprocess.Popen):
        self.proc = proc
        self.lines: list[str] = []
        self.status = "running"  # running / success / error
        self.exit_code: int | None = None
        self.started_at = time.time()
        self.lock = threading.Lock()


_job_lock = threading.Lock()
_current_job: PublishJob | None = None


class PublisherRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"", "/"}:
            self.path = "/index.html"
        if parsed.path == "/api/publish/status":
            self.handle_publish_status()
            return
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/task":
            self.handle_create_task()
            return
        if parsed.path == "/api/upload":
            self.handle_upload()
            return
        if parsed.path == "/api/commands":
            self.handle_commands()
            return
        if parsed.path == "/api/publish":
            self.handle_publish()
            return
        self.send_json({"ok": False, "error": "未知接口"}, HTTPStatus.NOT_FOUND)

    def handle_create_task(self) -> None:
        try:
            payload = self.read_json()
            task_payload = normalize_payload(payload)
            task = PublishTask.from_dict(task_payload, base_dir=PROJECT_ROOT)
            TASK_PATH.write_text(
                json.dumps(task_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.send_json(
                {
                    "ok": True,
                    "task_path": str(TASK_PATH),
                    "task": {
                        "video": str(task.video),
                        "title": task.title,
                        "description": task.description,
                        "tags": task.tags,
                        "platforms": task.platforms,
                        "publish_now": task.publish_now,
                    },
                    "commands": build_commands(payload.get("account", "creator"), str(TASK_PATH)),
                }
            )
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def handle_commands(self) -> None:
        try:
            payload = self.read_json()
            account = str(payload.get("account") or "creator")
            self.send_json(
                {
                    "ok": True,
                    "task_path": str(TASK_PATH),
                    "commands": build_commands(account, str(TASK_PATH)),
                }
            )
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def handle_publish(self) -> None:
        global _current_job
        try:
            payload = self.read_json()
            task_payload = normalize_payload(payload)
            task = PublishTask.from_dict(task_payload, base_dir=PROJECT_ROOT)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return

        account = sanitize_account(str(payload.get("account") or "creator"))

        with _job_lock:
            if _current_job is not None and _current_job.status == "running":
                self.send_json(
                    {"ok": False, "error": "已有发布任务在运行，请等浏览器流程结束后再试。"},
                    HTTPStatus.CONFLICT,
                )
                return

            try:
                TASK_PATH.write_text(
                    json.dumps(task_payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception as exc:
                self.send_json(
                    {"ok": False, "error": f"写入任务文件失败: {exc}"},
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return

            cmd = [
                sys.executable,
                "-u",
                "-m",
                "ai_video_publisher",
                "publish",
                str(TASK_PATH),
                "--account",
                account,
            ]
            env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(PROJECT_ROOT),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )
            except Exception as exc:
                self.send_json(
                    {"ok": False, "error": f"启动发布进程失败: {exc}"},
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return

            job = PublishJob(proc)
            _current_job = job

        threading.Thread(target=drain_publish_job, args=(job,), daemon=True).start()
        self.send_json(
            {
                "ok": True,
                "task_path": str(TASK_PATH),
                "platforms": task.platforms,
                "account": account,
                "note": "后台已启动浏览器自动化；停在发布确认页，不会自动点击发布。",
            }
        )

    def handle_publish_status(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        try:
            offset = max(0, int(query.get("offset", ["0"])[0]))
        except ValueError:
            offset = 0

        job = _current_job
        if job is None:
            self.send_json({"ok": True, "started": False, "running": False, "lines": [], "offset": 0})
            return

        with job.lock:
            lines = job.lines[offset:]
            self.send_json(
                {
                    "ok": True,
                    "started": True,
                    "running": job.status == "running",
                    "status": job.status,
                    "exit_code": job.exit_code,
                    "elapsed": round(time.time() - job.started_at, 1),
                    "lines": lines,
                    "offset": offset + len(lines),
                }
            )

    def handle_upload(self) -> None:
        try:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                raise ValueError("上传接口需要 multipart/form-data")

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": content_type,
                    "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
                },
            )
            field = form["video"] if "video" in form else None
            if field is None or not getattr(field, "filename", ""):
                raise ValueError("没有收到视频文件")

            original_name = Path(field.filename).name
            if not original_name.lower().endswith((".mp4", ".mov", ".m4v")):
                raise ValueError("请上传 mp4 / mov / m4v 视频文件")

            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            target = unique_upload_path(original_name)
            with target.open("wb") as output:
                while True:
                    chunk = field.file.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)

            relative = target.relative_to(PROJECT_ROOT).as_posix()
            self.send_json(
                {
                    "ok": True,
                    "filename": target.name,
                    "path": relative,
                    "absolute_path": str(target),
                    "size": target.stat().st_size,
                }
            )
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        if not raw:
            return {}
        return json.loads(raw)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    platforms = payload.get("platforms") or []
    if not isinstance(platforms, list):
        raise ValueError("platforms 必须是数组")

    tags = payload.get("tags") or []
    if isinstance(tags, str):
        tags = [item.strip() for item in tags.split(",") if item.strip()]

    return {
        "video": payload.get("video", ""),
        "title": payload.get("title", ""),
        "description": payload.get("description", ""),
        "tags": tags,
        "platforms": platforms,
        "publish_now": bool(payload.get("publish_now", False)),
    }


def build_commands(account: str, task_path: str) -> dict[str, str]:
    return {
        "login_douyin": f"python -m ai_video_publisher login douyin --account {account}",
        "login_tencent": f"python -m ai_video_publisher login tencent --account {account}",
        "check_douyin": f"python -m ai_video_publisher check douyin --account {account}",
        "check_tencent": f"python -m ai_video_publisher check tencent --account {account}",
        "publish": f"python -m ai_video_publisher publish {task_path} --account {account}",
    }


def sanitize_account(value: str) -> str:
    cleaned = "".join(ch for ch in value if ch.isalnum() or ch in "-_")
    return cleaned or "creator"


def drain_publish_job(job: PublishJob) -> None:
    """在后台线程读取 publish 子进程输出，结束后落状态。"""
    proc = job.proc
    if proc.stdin:
        try:
            proc.stdin.close()
        except Exception:
            pass
    assert proc.stdout is not None
    for raw in proc.stdout:
        with job.lock:
            job.lines.append(raw.rstrip("\r\n"))
    code = proc.wait()
    with job.lock:
        job.exit_code = code
        job.status = "success" if code == 0 else "error"


def unique_upload_path(filename: str) -> Path:
    safe_name = filename.replace("/", "_").replace("\\", "_")
    target = UPLOAD_DIR / safe_name
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    index = 2
    while True:
        candidate = UPLOAD_DIR / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), PublisherRequestHandler)
    url = f"http://{host}:{port}"
    print(f"发发布ai小助手已启动: {url}")
    print("按 Ctrl+C 停止服务。")
    server.serve_forever()


if __name__ == "__main__":
    run()
