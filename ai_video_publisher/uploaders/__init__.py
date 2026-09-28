from __future__ import annotations

from ai_video_publisher.uploaders.base import Uploader
from ai_video_publisher.uploaders.douyin import DouyinUploader
from ai_video_publisher.uploaders.wechat_channels import WechatChannelsUploader


UPLOADERS: dict[str, type[Uploader]] = {
    "douyin": DouyinUploader,
    "wechat_channels": WechatChannelsUploader,
}


def get_uploader(platform: str) -> Uploader:
    try:
        return UPLOADERS[platform]()
    except KeyError as exc:
        raise ValueError(f"未知平台: {platform}") from exc

