from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / ".publisher_data"
STATE_DIR = DATA_DIR / "states"
PROFILE_DIR = DATA_DIR / "profiles"
LOG_DIR = DATA_DIR / "logs"


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def state_path(platform: str, account: str) -> Path:
    safe_account = account.replace("/", "_").replace("\\", "_")
    return STATE_DIR / f"{platform}-{safe_account}.json"


def profile_path(platform: str, account: str) -> Path:
    safe_account = account.replace("/", "_").replace("\\", "_")
    return PROFILE_DIR / f"{platform}-{safe_account}"
