import json

from utils.auth_storage import AuthStorage


def test_auth_storage_code_lifecycle_and_expiration(tmp_path):
    store = AuthStorage(storage_dir=str(tmp_path))

    store.set_code("u1@example.com", "123456", ttl_minutes=10)
    entry = store.get_code("u1@example.com")
    assert entry is not None
    assert entry["code"] == "123456"

    store.delete_code("u1@example.com")
    assert store.get_code("u1@example.com") is None

    store.set_code("u2@example.com", "999999", ttl_minutes=10)
    store._codes["u2@example.com"]["expires_at"] = "2000-01-01T00:00:00"
    store._save_all()
    assert store.get_code("u2@example.com") is None

    data = json.loads((tmp_path / "verification_codes.json").read_text(encoding="utf-8"))
    assert "u2@example.com" not in data


def test_auth_storage_session_lifecycle_and_expiration(tmp_path):
    store = AuthStorage(storage_dir=str(tmp_path))

    token = store.create_session("u1@example.com", ttl_days=10)
    session = store.get_session(token)
    assert session is not None
    assert session["email"] == "u1@example.com"

    store.delete_session(token)
    assert store.get_session(token) is None

    token2 = store.create_session("u2@example.com", ttl_days=10)
    store._sessions[token2]["expires_at"] = "2000-01-01T00:00:00"
    store._save_all()
    assert store.get_session(token2) is None

    data = json.loads((tmp_path / "sessions.json").read_text(encoding="utf-8"))
    assert token2 not in data


def test_auth_storage_load_ignores_invalid_json(tmp_path):
    (tmp_path / "verification_codes.json").write_text("{", encoding="utf-8")
    (tmp_path / "sessions.json").write_text("{", encoding="utf-8")

    store = AuthStorage(storage_dir=str(tmp_path))
    assert store.get_code("u1@example.com") is None
    assert store.get_session("nope") is None
