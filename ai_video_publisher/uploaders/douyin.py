from __future__ import annotations

from playwright.async_api import BrowserContext

from ai_video_publisher.browser import pause_for_user
from ai_video_publisher.task import PublishTask
from ai_video_publisher.uploaders.base import Uploader


class DouyinUploader(Uploader):
    platform = "douyin"
    login_url = "https://creator.douyin.com/"
    upload_url = "https://creator.douyin.com/creator-micro/content/upload"

    async def login(self, context: BrowserContext) -> None:
        page = await context.new_page()
        await page.goto(self.login_url, wait_until="domcontentloaded")
        await pause_for_user("抖音创作者中心已打开。请扫码或手动登录。")

    async def publish(self, context: BrowserContext, task: PublishTask) -> None:
        page = await context.new_page()
        await page.goto(self.upload_url, wait_until="domcontentloaded")

        await self.set_video_file(page, str(task.video), "抖音")

        await self.fill_first_available(page, ["标题", "作品标题", "填写作品标题"], task.title)
        if task.description:
            await self.fill_first_available(page, ["简介", "描述", "添加作品描述"], task.description)
        await self.fill_tags(page, task.tags)

        print("[STEP 4] 抖音: 标题/简介/标签已填写（未找到的字段看上方提示，需手动补）")
        print("抖音已上传并填写信息，停在发布前确认页（当前版本不会自动点击发布）。")
