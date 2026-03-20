import json
from pathlib import Path
from typing import Optional

from data.schemas import PropertyCollection

CACHE_DIR = Path(".app_cache")
CACHE_FILE = CACHE_DIR / "properties.json"
PREV_CACHE_FILE = CACHE_DIR / "properties_prev.json"


def save_collection(collection: PropertyCollection) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if CACHE_FILE.exists():
        try:
            PREV_CACHE_FILE.write_text(CACHE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass
    data = collection.model_dump(mode="json")
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def load_collection() -> Optional[PropertyCollection]:
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return PropertyCollection.model_validate(data)
    except Exception:
        return None


def load_previous_collection() -> Optional[PropertyCollection]:
    if not PREV_CACHE_FILE.exists():
        return None
    try:
        data = json.loads(PREV_CACHE_FILE.read_text(encoding="utf-8"))
        return PropertyCollection.model_validate(data)
    except Exception:
        return None


def clear_cache() -> None:
    try:
        CACHE_FILE.unlink()
    except Exception:
        pass
    try:
        PREV_CACHE_FILE.unlink()
    except Exception:
        pass
