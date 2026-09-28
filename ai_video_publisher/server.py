from __future__ import annotations

import json
import cgi
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ai_video_publisher.task import PublishTask


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "web"
TASK_PATH = PROJECT_ROOT / "task.web.json"
UPLOAD_DIR = PROJECT_ROOT / "uploads"


class PublisherRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"", "/"}:
            self.path = "/index.html"
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
