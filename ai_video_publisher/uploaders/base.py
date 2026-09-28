from __future__ import annotations

from abc import ABC, abstractmethod

from playwright.async_api import BrowserContext, Page, TimeoutError

from ai_video_publisher.task import PublishTask


class Uploader(ABC):
    platform: str
    login_url: str
    upload_url: str

    @abstractmethod
    async def login(self, context: BrowserContext) -> None:
        raise NotImplementedError

    @abstractmethod
    async def publish(self, context: BrowserContext, task: PublishTask) -> None:
        raise NotImplementedError

    async def check(self, context: BrowserContext) -> None:
        page = await context.new_page()
        await page.goto(self.login_url, wait_until="domcontentloaded")
        print(f"{self.platform} 页面已打开。如果页面显示账号头像/创作者后台，说明登录态可用。")

    async def wait_for_file_input(self, page: Page, platform_name: str):
        try:
            return await page.wait_for_selector("input[type=file]", state="attached", timeout=45000)
        except TimeoutError as exc:
            raise RuntimeError(
                f"没有找到{platform_name}上传控件。可能是未登录、页面改版、账号无权限，"
                "或需要先手动点击页面上的“上传视频/发表视频”按钮。"
            ) from exc

    async def set_video_file(self, page: Page, video_path: str, platform_name: str) -> None:
        last_error: Exception | None = None
        for attempt in range(1, 6):
            try:
                locator = page.locator("input[type=file]").last
                await locator.wait_for(state="attached", timeout=45000 if attempt == 1 else 8000)
                await locator.set_input_files(video_path, timeout=20000)
                return
            except Exception as exc:
                last_error = exc
                await page.wait_for_timeout(1000)

        raise RuntimeError(
            f"{platform_name}上传视频失败：页面上传控件被动态刷新或不可用。"
            "请保持页面打开，手动点击“上传视频/发表视频”后重试。"
        ) from last_error

    async def fill_first_available(self, page: Page, labels: list[str], text: str) -> bool:
        if not text:
            return True

        for label in labels:
            for getter in (
                lambda: page.get_by_placeholder(label).first,
                lambda: page.get_by_label(label).first,
                lambda: page.get_by_role("textbox", name=label).first,
            ):
                try:
                    target = getter()
                    await target.fill(text, timeout=2500)
                    return True
                except Exception:
                    pass

        for selector in (
            "textarea",
            "input[type=text]",
            "[contenteditable=true]",
            ".public-DraftEditor-content",
        ):
            try:
                targets = page.locator(selector)
                count = await targets.count()
                for index in range(count):
                    target = targets.nth(index)
                    if not await target.is_visible(timeout=1000):
                        continue
                    await target.fill(text, timeout=2500)
                    return True
            except Exception:
                pass

        print(f"未自动找到字段 {labels}，请在页面中手动填写：{text}")
        return False

    async def fill_tags(self, page: Page, tags: list[str]) -> None:
        if not tags:
            return
        tag_text = " ".join(f"#{tag.lstrip('#')}" for tag in tags)
        filled = await self.fill_first_available(page, ["标签", "话题", "添加话题"], tag_text)
        if not filled:
            print(f"请手动补充标签/话题：{tag_text}")
