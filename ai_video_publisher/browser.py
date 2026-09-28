from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import BrowserContext, async_playwright


def launch_channel() -> str | None:
    if Path("/Applications/Google Chrome.app").exists():
        return "chrome"
    if Path("/Applications/Microsoft Edge.app").exists():
        return "msedge"
    return None


@asynccontextmanager
async def browser_context(
    state_file: Path | None,
    headless: bool = False,
    profile_dir: Path | None = None,
):
    async with async_playwright() as playwright:
        channel = launch_channel()
        context_kwargs = {
            "viewport": {"width": 1280, "height": 900},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "accept_downloads": True,
        }
        if profile_dir:
            profile_dir.mkdir(parents=True, exist_ok=True)
            launch_kwargs = {"channel": channel} if channel else {}
            context: BrowserContext = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=headless,
                **launch_kwargs,
                **context_kwargs,
            )
            failed = False
            try:
                yield context
            except Exception:
                failed = True
                raise
            finally:
                if state_file:
                    state_file.parent.mkdir(parents=True, exist_ok=True)
                    await context.storage_state(path=str(state_file))
                if failed:
                    print("流程报错，浏览器将保持 60 秒方便你查看页面状态。")
                    await keep_open_for_debug(context)
                await context.close()
        else:
            launch_kwargs = {"channel": channel} if channel else {}
            browser = await playwright.chromium.launch(headless=headless, **launch_kwargs)
            if state_file and state_file.exists():
                context_kwargs["storage_state"] = str(state_file)
            context = await browser.new_context(**context_kwargs)
            failed = False
            try:
                yield context
            except Exception:
                failed = True
                raise
            finally:
                if state_file:
                    state_file.parent.mkdir(parents=True, exist_ok=True)
                    await context.storage_state(path=str(state_file))
                if failed:
                    print("流程报错，浏览器将保持 60 秒方便你查看页面状态。")
                    await keep_open_for_debug(context)
                await context.close()
                await browser.close()


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
