from notifications.uptime_monitor import make_http_checker


class DummyResp:
    def __init__(self, status_code: int):
        self.status_code = status_code


def test_http_checker_ok(monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return DummyResp(200)

    import requests

    monkeypatch.setattr(requests, "get", fake_get)
    check = make_http_checker("http://localhost:8000/health", timeout=1.0)
    assert check() is True
    assert calls and calls[0][0].startswith("http://localhost:8000")


def test_http_checker_handles_errors(monkeypatch):
    def fake_get(url, timeout):
        raise RuntimeError("network error")

    import requests

    monkeypatch.setattr(requests, "get", fake_get)
    check = make_http_checker("http://localhost:8000/health", timeout=1.0)
    assert check() is False
