import sys
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.health import (
    DependencyHealth,
    HealthCheckResponse,
    HealthStatus,
    check_llm_provider,
    check_redis,
    get_health_status,
    require_healthy,
)


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class FakeAsyncClient:
    def __init__(self, status_code: int):
        self._status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url):
        return FakeResponse(self._status_code)


class FakeRedisClient:
    def __init__(self, should_fail: bool):
        self._should_fail = should_fail

    def ping(self):
        if self._should_fail:
            raise RuntimeError("redis down")
        return "PONG"

    def close(self):
        return None


@pytest.mark.asyncio
async def test_check_redis_returns_none_when_not_configured(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    result = await check_redis()
    assert result is None


@pytest.mark.asyncio
async def test_check_redis_reports_healthy_when_ping_succeeds(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    fake_module = SimpleNamespace(from_url=lambda *_args, **_kwargs: FakeRedisClient(False))
    monkeypatch.setitem(sys.modules, "redis", fake_module)
    result = await check_redis()
    assert result is not None
    assert result.status == HealthStatus.HEALTHY
    assert result.message == "OK"


@pytest.mark.asyncio
async def test_check_redis_reports_unhealthy_on_error(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    fake_module = SimpleNamespace(from_url=lambda *_args, **_kwargs: FakeRedisClient(True))
    monkeypatch.setitem(sys.modules, "redis", fake_module)
    result = await check_redis()
    assert result is not None
    assert result.status == HealthStatus.UNHEALTHY
    assert result.message.startswith("Error:")


@pytest.mark.asyncio
async def test_check_llm_provider_degraded_without_providers(monkeypatch):
    settings = SimpleNamespace(
        openai_api_key=None,
        anthropic_api_key=None,
        google_api_key=None,
        grok_api_key=None,
        deepseek_api_key=None,
        default_provider="openai",
    )
    fake_httpx = SimpleNamespace(AsyncClient=lambda timeout=2.0: FakeAsyncClient(404))
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)
    monkeypatch.setattr("api.health.get_settings", lambda: settings)
    result = await check_llm_provider()
    assert result.status == HealthStatus.DEGRADED
    assert result.details == {"configured_providers": []}


@pytest.mark.asyncio
async def test_check_llm_provider_includes_ollama_when_available(monkeypatch):
    settings = SimpleNamespace(
        openai_api_key=None,
        anthropic_api_key=None,
        google_api_key=None,
        grok_api_key=None,
        deepseek_api_key=None,
        default_provider="openai",
    )
    fake_httpx = SimpleNamespace(AsyncClient=lambda timeout=2.0: FakeAsyncClient(200))
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)
    monkeypatch.setattr("api.health.get_settings", lambda: settings)
    result = await check_llm_provider()
    assert result.status == HealthStatus.HEALTHY
    assert result.details == {"configured_providers": ["ollama"], "default": "openai"}


@pytest.mark.asyncio
async def test_check_llm_provider_healthy_with_configured_key(monkeypatch):
    settings = SimpleNamespace(
        openai_api_key="sk-test",
        anthropic_api_key=None,
        google_api_key=None,
        grok_api_key=None,
        deepseek_api_key=None,
        default_provider="openai",
    )
    fake_httpx = SimpleNamespace(AsyncClient=lambda timeout=2.0: FakeAsyncClient(500))
    monkeypatch.setitem(sys.modules, "httpx", fake_httpx)
    monkeypatch.setattr("api.health.get_settings", lambda: settings)
    result = await check_llm_provider()
    assert result.status == HealthStatus.HEALTHY
    assert result.details == {"configured_providers": ["openai"], "default": "openai"}


@pytest.mark.asyncio
async def test_get_health_status_unhealthy_when_vector_store_unhealthy(monkeypatch):
    settings = SimpleNamespace(version="9.9.9")
    monkeypatch.setattr("api.health.get_settings", lambda: settings)

    async def _vector_store_unhealthy():
        return DependencyHealth(
            name="vector_store",
            status=HealthStatus.UNHEALTHY,
            message="down",
        )

    async def _redis_healthy():
        return DependencyHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="ok",
        )

    async def _llm_healthy():
        return DependencyHealth(
            name="llm_providers",
            status=HealthStatus.HEALTHY,
            message="ok",
        )

    monkeypatch.setattr("api.health.check_vector_store", _vector_store_unhealthy)
    monkeypatch.setattr("api.health.check_redis", _redis_healthy)
    monkeypatch.setattr("api.health.check_llm_provider", _llm_healthy)
    result = await get_health_status(include_dependencies=True)
    assert result.status == HealthStatus.UNHEALTHY
    assert result.dependencies["vector_store"].status == HealthStatus.UNHEALTHY
    assert result.version == "9.9.9"


@pytest.mark.asyncio
async def test_require_healthy_raises_on_unhealthy_dependencies(monkeypatch):
    response = HealthCheckResponse(
        status=HealthStatus.UNHEALTHY,
        version="1.0.0",
        timestamp="2026-01-01T00:00:00Z",
        dependencies={
            "vector_store": DependencyHealth(
                name="vector_store",
                status=HealthStatus.UNHEALTHY,
                message="down",
            ),
            "redis": DependencyHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="ok",
            ),
        },
        uptime_seconds=1.0,
    )

    async def _fake_get_health_status(*_args, **_kwargs):
        return response

    monkeypatch.setattr("api.health.get_health_status", _fake_get_health_status)
    with pytest.raises(HTTPException) as exc_info:
        await require_healthy()
    assert "vector_store" in str(exc_info.value.detail)
