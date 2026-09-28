from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUPPORTED_PLATFORMS = {"douyin", "wechat_channels"}
PLATFORM_ALIASES = {
    "douyin": "douyin",
    "抖音": "douyin",
    "wechat_channels": "wechat_channels",
    "channels": "wechat_channels",
    "video_channels": "wechat_channels",
    "tencent": "wechat_channels",
    "视频号": "wechat_channels",
}


@dataclass(frozen=True)
class PublishTask:
    video: Path
    title: str
    description: str
    platforms: list[str]
    tags: list[str]
    publish_now: bool = False

    @classmethod
    def from_file(cls, path: Path) -> "PublishTask":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data, base_dir=path.parent)

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_dir: Path) -> "PublishTask":
        missing = [key for key in ("video", "title", "platforms") if not data.get(key)]
        if missing:
            raise ValueError(f"任务文件缺少字段: {', '.join(missing)}")

        platforms = [normalize_platform(str(platform)) for platform in data["platforms"]]
        unsupported = sorted(set(platforms) - SUPPORTED_PLATFORMS)
        if unsupported:
            raise ValueError(f"暂不支持平台: {', '.join(unsupported)}")

        video = Path(data["video"])
        if not video.is_absolute():
            video = (base_dir / video).resolve()
        if not video.exists():
            raise FileNotFoundError(f"视频文件不存在: {video}")

        tags = data.get("tags", [])
        if isinstance(tags, str):
            tags = [item.strip() for item in tags.split(",") if item.strip()]

        return cls(
            video=video,
            title=str(data["title"]),
            description=str(data.get("description", "")),
            platforms=platforms,
            tags=list(tags),
            publish_now=bool(data.get("publish_now", False)),
        )


def normalize_platform(platform: str) -> str:
    key = platform.strip()
    try:
        return PLATFORM_ALIASES[key]
    except KeyError as exc:
        raise ValueError(f"未知平台: {platform}") from exc
