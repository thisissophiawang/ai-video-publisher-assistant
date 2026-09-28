from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from ai_video_publisher.config import ensure_dirs, profile_path, state_path
from ai_video_publisher.task import PublishTask, normalize_platform


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-video-publisher",
        description="自动发布本地视频到抖音和视频号。默认停在最终发布前，人工确认。",
    )
    parser.add_argument("--headless", action="store_true", help="使用无头浏览器。首次登录不建议开启。")

    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8765, type=int)

    for command in ("login", "check"):
        sub = subparsers.add_parser(command)
        sub.add_argument("platform", help="douyin / tencent / wechat_channels")
        sub.add_argument("--account", default="default", help="账号别名，用于隔离登录态。")

    upload = subparsers.add_parser("upload-video")
    upload.add_argument("platform", help="douyin / tencent / wechat_channels")
    upload.add_argument("--account", default="default")
    upload.add_argument("--file", required=True, type=Path)
    upload.add_argument("--title", required=True)
    upload.add_argument("--desc", default="")
    upload.add_argument("--tags", default="", help="逗号分隔，例如 AI,求职,留学生")
    upload.add_argument("--publish-now", action="store_true", help="仍会停下让你手动确认最终发布。")

    publish = subparsers.add_parser("publish")
    publish.add_argument("task", type=Path, help="任务 JSON 文件")
    publish.add_argument("--account", default="default")

    return parser


async def run_with_uploader(platform: str, account: str, headless: bool, action):
    from ai_video_publisher.browser import browser_context
    from ai_video_publisher.uploaders import get_uploader

    ensure_dirs()
    normalized = normalize_platform(platform)
    uploader = get_uploader(normalized)
    state = state_path(normalized, account)
    profile = profile_path(normalized, account)
    async with browser_context(state, headless=headless, profile_dir=profile) as context:
        await action(uploader, context)


async def main_async() -> None:
    args = build_parser().parse_args()

    if args.command == "serve":
        from ai_video_publisher.server import run

        run(host=args.host, port=args.port)
        return

    if args.command == "login":
        await run_with_uploader(args.platform, args.account, args.headless, lambda uploader, context: uploader.login(context))
        return

    if args.command == "check":
        await run_with_uploader(args.platform, args.account, args.headless, lambda uploader, context: uploader.check(context))
        return

    if args.command == "upload-video":
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        task = PublishTask.from_dict(
            {
                "video": str(args.file),
                "title": args.title,
                "description": args.desc,
                "platforms": [args.platform],
                "tags": tags,
                "publish_now": args.publish_now,
            },
            base_dir=Path.cwd(),
        )
        await run_with_uploader(
            args.platform,
            args.account,
            args.headless,
            lambda uploader, context: uploader.publish(context, task),
        )
        return

    if args.command == "publish":
        task = PublishTask.from_file(args.task)
        for platform in task.platforms:
            await run_with_uploader(
                platform,
                args.account,
                args.headless,
                lambda uploader, context, current_task=task: uploader.publish(context, current_task),
            )
        return


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
