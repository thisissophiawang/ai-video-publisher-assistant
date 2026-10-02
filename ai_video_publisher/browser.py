from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import BrowserContext, async_playwright


# 网页触发（非交互）模式下，停在确认页后浏览器最多保留的时间（秒）。
HOLD_TIMEOUT_SECONDS = 30 * 60

CONTEXT_KWARGS = {
    "viewport": {"width": 1280, "height": 900},
    "locale": "zh-CN",
    "timezone_id": "Asia/Shanghai",
    "accept_downloads": True,
}


def launch_channel() -> str | None:
    if Path("/Applications/Google Chrome.app").exists():
        return "chrome"
    if Path("/Applications/Microsoft Edge.app").exists():
        return "msedge"
    return None


async def launch_persistent(
    playwright,
    profile_dir: Path,
    headless: bool = False,
) -> BrowserContext:
    profile_dir.mkdir(parents=True, exist_ok=True)
    channel = launch_channel()
    launch_kwargs = {"channel": channel} if channel else {}
    return await playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=headless,
        **launch_kwargs,
        **CONTEXT_KWARGS,
    )


async def close_context(
    context: BrowserContext,
    state_file: Path | None = None,
    failed: bool = False,
) -> None:
    try:
        if state_file:
            state_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                await context.storage_state(path=str(state_file))
            except Exception as exc:
                print(f"[warn] 保存登录态失败（不影响本次流程结果）: {exc}")
        if failed:
            print("该平台流程报错，浏览器将保持 60 秒方便你查看页面状态。")
            await keep_open_for_debug(context)
    finally:
        try:
            await context.close()
        except Exception:
            pass


@asynccontextmanager
async def browser_context(
    state_file: Path | None,
    headless: bool = False,
    profile_dir: Path | None = None,
):
    if profile_dir is None:
        raise RuntimeError("必须提供 profile_dir（浏览器 profile 用于复用登录态）。")

    async with async_playwright() as playwright:
        context = await launch_persistent(playwright, profile_dir, headless)
        failed = False
        try:
            yield context
        except Exception:
            failed = True
            raise
        finally:
            await close_context(context, state_file=state_file, failed=failed)


async def keep_open_for_debug(context: BrowserContext) -> None:
    pages = context.pages
    if pages:
        await pages[0].wait_for_timeout(60000)
    else:
        await asyncio.sleep(60)


async def pause_for_user(message: str) -> None:
    print(message)
    loop_message = "完成后回到这里按 Enter 继续..."
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, input, loop_message)


def _stdin_is_interactive() -> bool:
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except Exception:
        return False


async def wait_for_user_confirm(message: str, contexts: list[BrowserContext]) -> None:
    """停在发布确认页后的统一收尾。

    终端手动运行：等待用户按 Enter（原行为不变）。
    被 server/脚本拉起（stdin 不是终端）：不读 stdin，保持浏览器打开，
    直到用户关掉所有页面/窗口，或超时后自动收尾。
    """
    contexts = [context for context in contexts if context.pages]
    if not contexts:
        print(message)
        print("浏览器窗口已全部关闭，直接结束流程。")
        return

    if _stdin_is_interactive():
        await pause_for_user(message)
        return

    print(message)
    print(
        f"（自动模式：人工发布完成后直接关闭浏览器窗口即可；"
        f"{HOLD_TIMEOUT_SECONDS // 60} 分钟后也会自动收尾）"
    )
    loop = asyncio.get_running_loop()
    deadline = loop.time() + HOLD_TIMEOUT_SECONDS
    while any(context.pages for context in contexts):
        if loop.time() >= deadline:
            print("等待超时，自动收尾并关闭浏览器。")
            return
        await asyncio.sleep(1)
    print("检测到浏览器窗口已全部关闭，流程结束。")
