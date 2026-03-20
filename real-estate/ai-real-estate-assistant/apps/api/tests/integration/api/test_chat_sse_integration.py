import types

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from api.dependencies import get_llm, get_vector_store
from api.main import app
from api.routers import chat as chat_router
from config.settings import settings as app_settings


class FakeAgent:
    def __init__(self):
        self.emitted = ['{"content":"Hello"}', '{"content":"World"}']

    async def astream_query(self, msg: str):
        for e in self.emitted:
            yield e

    def process_query(self, msg: str):
        return {"answer": "Hello World", "source_documents": []}

    def get_sources_for_query(self, query: str):
        return [Document(page_content="Doc", metadata={"id": "1"})]


@pytest.fixture(autouse=True)
def _patch_agent(monkeypatch):
    monkeypatch.setattr(
        chat_router, "create_hybrid_agent", lambda llm, retriever, memory=None: FakeAgent()
    )


def test_chat_sse_streams_events_and_sets_request_id_header():
    client = TestClient(app)
    app.dependency_overrides[get_llm] = lambda: object()
    app.dependency_overrides[get_vector_store] = lambda: types.SimpleNamespace(
        get_retriever=lambda: object()
    )
    payload = {"message": "Hi", "stream": True}
    headers = {"X-API-Key": "dev-secret-key"}
    old_max_items = app_settings.chat_sources_max_items
    old_max_chars = app_settings.chat_source_content_max_chars
    old_max_bytes = app_settings.chat_sources_max_total_bytes
    app_settings.chat_sources_max_items = 1
    app_settings.chat_source_content_max_chars = 2
    app_settings.chat_sources_max_total_bytes = 10_000

    try:
        with client.stream("POST", "/api/v1/chat", json=payload, headers=headers) as r:
            assert r.headers.get("content-type").startswith("text/event-stream")
            req_id = r.headers.get("X-Request-ID")
            assert req_id and isinstance(req_id, str)
            chunks = list(r.iter_lines())

        data_lines = [line for line in chunks if line]
        assert any(line.startswith("data: ") for line in data_lines)
        assert any(line.strip() == "event: meta" for line in data_lines)
        meta_line = next(
            line
            for line in data_lines
            if line.startswith("data: {") and '"sources"' in line and '"session_id"' in line
        )
        import json

        meta = json.loads(meta_line[len("data: ") :])
        assert meta["sources"] == [{"content": "Do", "metadata": {"id": "1"}}]
        assert meta["sources_truncated"] is True
        assert any(line.strip() == "data: [DONE]" for line in data_lines)
    finally:
        app_settings.chat_sources_max_items = old_max_items
        app_settings.chat_source_content_max_chars = old_max_chars
        app_settings.chat_sources_max_total_bytes = old_max_bytes
