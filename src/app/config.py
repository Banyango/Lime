import os
import json

from pathlib import Path
from pydantic import BaseModel
from wireup import injectable


class AppConfig(BaseModel):
    show_context: bool = True


def _default_settings_path() -> Path:
    # Windows roaming app data
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "lime" / "settings.json"

    # Fallback to a dotdir in the user's home (cross-platform)
    return Path.home() / ".lime" / "settings.json"


def _create_default_settings_file(path: Path) -> AppConfig:
    path.parent.mkdir(parents=True, exist_ok=True)
    default_config = AppConfig()
    with path.open("w", encoding="utf-8") as f:
        json.dump(default_config.model_dump(), f, indent=4)
    return default_config


@injectable
def get_app_config() -> AppConfig:
    path = Path(str(_default_settings_path()))
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return AppConfig.model_validate_json(f.read())
    else:
        return _create_default_settings_file(path)
