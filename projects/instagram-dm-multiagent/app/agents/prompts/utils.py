from pathlib import Path
from typing import Any

import yaml

from app.core.config import get_settings


def load_brand_voice() -> dict[str, Any]:
    path = Path(get_settings().brand_voice_path)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}
