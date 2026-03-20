import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class UserModelPreferences:
    user_email: str
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_email": self.user_email,
            "preferred_provider": self.preferred_provider,
            "preferred_model": self.preferred_model,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserModelPreferences":
        updated_at = data.get("updated_at")
        parsed_updated_at = datetime.now()
        if isinstance(updated_at, str):
            try:
                parsed_updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                parsed_updated_at = datetime.now()

        return cls(
            user_email=str(data.get("user_email") or "").strip(),
            preferred_provider=(
                str(data.get("preferred_provider")).strip()
                if data.get("preferred_provider")
                else None
            ),
            preferred_model=(
                str(data.get("preferred_model")).strip() if data.get("preferred_model") else None
            ),
            updated_at=parsed_updated_at,
        )


class UserModelPreferencesManager:
    def __init__(self, storage_path: str = ".preferences"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.preferences_file = self.storage_path / "model_preferences.json"
        self._preferences_cache: Dict[str, UserModelPreferences] = {}
        self._load_all_preferences()

    def get_preferences(self, user_email: str) -> UserModelPreferences:
        resolved = user_email.strip()
        if not resolved:
            raise ValueError("Missing user email")

        if resolved not in self._preferences_cache:
            prefs = UserModelPreferences(user_email=resolved)
            self._preferences_cache[resolved] = prefs
            self.save_preferences(prefs)

        return self._preferences_cache[resolved]

    def save_preferences(self, preferences: UserModelPreferences) -> None:
        preferences.updated_at = datetime.now()
        self._preferences_cache[preferences.user_email] = preferences
        self._save_all_preferences()

    def update_preferences(
        self,
        user_email: str,
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ) -> UserModelPreferences:
        prefs = self.get_preferences(user_email)
        if preferred_provider is not None:
            cleaned = preferred_provider.strip()
            prefs.preferred_provider = cleaned if cleaned else None
        if preferred_model is not None:
            cleaned = preferred_model.strip()
            prefs.preferred_model = cleaned if cleaned else None
        self.save_preferences(prefs)
        return prefs

    def _load_all_preferences(self) -> None:
        if not self.preferences_file.exists():
            return

        try:
            with open(self.preferences_file, "r") as f:
                data = json.load(f)
        except Exception as e:
            logger.warning("Error loading model preferences: %s", e)
            return

        if not isinstance(data, dict):
            return

        for email, prefs_data in data.items():
            if not isinstance(prefs_data, dict):
                continue
            prefs_data = dict(prefs_data)
            prefs_data.setdefault("user_email", email)
            prefs = UserModelPreferences.from_dict(prefs_data)
            if prefs.user_email:
                self._preferences_cache[prefs.user_email] = prefs

    def _save_all_preferences(self) -> None:
        data = {email: prefs.to_dict() for email, prefs in self._preferences_cache.items()}
        with open(self.preferences_file, "w") as f:
            json.dump(data, f, indent=2)


MODEL_PREFS_MANAGER = UserModelPreferencesManager()
