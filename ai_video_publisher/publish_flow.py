from __future__ import annotations

from pathlib import Path

from playwright.async_api import BrowserContext, async_playwright

from ai_video_publisher.browser import (
    close_context,
    launch_persistent,
    wait_for_user_confirm,
)
from ai_video_publisher.config import ensure_dirs, profile_path, state_path
from ai_video_publisher.task import PublishTask
from ai_video_publisher.uploaders import get_uploader


PLATFORM_NAMES = {
    "douyin": "抖音",
    "wechat_channels": "视频号",
}


def platform_display(platform: str) -> str:
    return PLATFORM_NAMES.get(platform, platform)


async def publish_task(task: PublishTask, account: str, headless: bool = False) -> bool:
    """按顺序上传并填写所有平台，全部完成后统一停在发布确认页。

    平台之间互相隔离：一个平台失败不影响其他平台（S2 修复）。
    返回是否全部成功；整体结果通过 [SUMMARY] 行输出，供网页轮询展示。
    """
    ensure_dirs()
    live: list[tuple[str, Path, BrowserContext]] = []
    results: list[tuple[str, str | None]] = []

    async with async_playwright() as playwright:
        for platform in task.platforms:
            name = platform_display(platform)
            print(f"[STEP 2] {name}: 启动 Chrome 并准备发布页")
            try:
                context = await launch_persistent(
                    playwright, profile_path(platform, account), headless
                )
            except Exception as exc:
                results.append((platform, f"浏览器启动失败: {exc}"))
                continue

            try:
                await get_uploader(platform).publish(context, task)
                results.append((platform, None))
                live.append((platform, state_path(platform, account), context))
            except Exception as exc:
                results.append((platform, str(exc)))
                await close_context(
                    context, state_file=state_path(platform, account), failed=True
                )

        ok = [platform for platform, error in results if error is None]
        failed = [(platform, error) for platform, error in results if error is not None]

        print(
            "[SUMMARY] "
            + ", ".join(
                f"{platform}={'ok' if error is None else 'fail'}"
                for platform, error in results
            )
        )

        if not ok:
            detail = "; ".join(
                f"{platform_display(platform)}: {error}" for platform, error in failed
            )
            raise RuntimeError(f"所有平台都失败了。{detail}")

        for platform, error in failed:
            print(f"[warn] {platform_display(platform)} 本次失败：{error}")

        message = (
            "[STEP 5] 已全部停在发布确认页（"
            + "、".join(platform_display(platform) for platform in ok)
            + "），请在浏览器中逐个检查并手动点击发布。"
        )
        await wait_for_user_confirm(
            message, [context for _, _, context in live]
        )

        for platform, state_file, context in live:
            await close_context(context, state_file=state_file)

    return not failed
