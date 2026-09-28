from __future__ import annotations

from playwright.async_api import BrowserContext

from ai_video_publisher.browser import pause_for_user
from ai_video_publisher.task import PublishTask
from ai_video_publisher.uploaders.base import Uploader


class WechatChannelsUploader(Uploader):
    platform = "wechat_channels"
    login_url = "https://channels.weixin.qq.com/platform"
    upload_url = "https://channels.weixin.qq.com/platform/post/create"

    async def login(self, context: BrowserContext) -> None:
        page = await context.new_page()
        await page.goto(self.login_url, wait_until="domcontentloaded")
        await pause_for_user("视频号助手已打开。请用微信扫码或手动完成登录。")

    async def publish(self, context: BrowserContext, task: PublishTask) -> None:
        page = await context.new_page()
        await page.goto(self.upload_url, wait_until="domcontentloaded")

        await self.set_video_file(page, str(task.video), "视频号")

        await self.fill_first_available(page, ["标题", "请输入标题", "视频标题"], task.title)
        if task.description:
            await self.fill_first_available(page, ["描述", "简介", "说点什么", "请输入描述"], task.description)
        await self.fill_tags(page, task.tags)

        if task.publish_now:
            await pause_for_user("已填写视频号发布信息。请确认页面无误后手动点击发表/发布。")
        else:
            await pause_for_user("视频号已上传并填写信息，当前停在发布前确认页。")
