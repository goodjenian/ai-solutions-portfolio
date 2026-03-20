import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional


class AuthStorage:
    def __init__(self, storage_dir: str = ".auth"):
        self.storage_path = Path(storage_dir)
        self.storage_path.mkdir(exist_ok=True)
        self.codes_file = self.storage_path / "verification_codes.json"
        self.sessions_file = self.storage_path / "sessions.json"
        self._codes: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        if self.codes_file.exists():
            try:
                with open(self.codes_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._codes = data
            except Exception:
                self._codes = {}
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._sessions = data
            except Exception:
                self._sessions = {}

    def _save_all(self) -> None:
        with open(self.codes_file, "w") as f:
            json.dump(self._codes, f, indent=2)
        with open(self.sessions_file, "w") as f:
            json.dump(self._sessions, f, indent=2)

    def set_code(self, email: str, code: str, ttl_minutes: int) -> None:
        expires_at = (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat()
        self._codes[email] = {"code": code, "expires_at": expires_at}
        self._save_all()

    def get_code(self, email: str) -> Optional[Dict[str, Any]]:
        entry = self._codes.get(email)
        if not entry:
            return None
        expires_at_str = entry.get("expires_at")
        try:
            expires_at = (
                datetime.fromisoformat(expires_at_str) if isinstance(expires_at_str, str) else None
            )
        except Exception:
            expires_at = None
        if expires_at and datetime.now() > expires_at:
            self._codes.pop(email, None)
            self._save_all()
            return None
        return entry

    def delete_code(self, email: str) -> None:
        if email in self._codes:
            self._codes.pop(email, None)
            self._save_all()

    def create_session(self, email: str, ttl_days: int) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(days=ttl_days)).isoformat()
        self._sessions[token] = {
            "email": email,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
        }
        self._save_all()
        return token

    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        entry = self._sessions.get(token)
        if not entry:
            return None
        expires_at_str = entry.get("expires_at")
        try:
            expires_at = (
                datetime.fromisoformat(expires_at_str) if isinstance(expires_at_str, str) else None
            )
        except Exception:
            expires_at = None
        if expires_at and datetime.now() > expires_at:
            self._sessions.pop(token, None)
            self._save_all()
            return None
        return entry

    def delete_session(self, token: str) -> None:
        if token in self._sessions:
            self._sessions.pop(token, None)
            self._save_all()
