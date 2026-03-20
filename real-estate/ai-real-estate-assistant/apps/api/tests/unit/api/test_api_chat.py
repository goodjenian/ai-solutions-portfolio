from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from api.dependencies import get_llm, get_vector_store
from api.main import app

client = TestClient(app)


@pytest.fixture
def valid_headers():
    return {"X-API-Key": "dev-secret-key"}


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    return agent


def test_chat_success(mock_agent, valid_headers):
    # Mock agent response
    mock_agent.process_query.return_value = {
        "answer": "This is a test answer.",
        "source_documents": [Document(page_content="doc content", metadata={"id": "1"})],
    }

    mock_store = MagicMock()
    mock_store.get_retriever.return_value = MagicMock()
    app.dependency_overrides[get_vector_store] = lambda: mock_store
    app.dependency_overrides[get_llm] = lambda: MagicMock()

    with patch("api.routers.chat.create_hybrid_agent", return_value=mock_agent):
        response = client.post("/api/v1/chat", json={"message": "Hello"}, headers=valid_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "This is a test answer."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["content"] == "doc content"
    assert data["sources_truncated"] is False

    app.dependency_overrides = {}


def test_chat_agent_failure(mock_agent, valid_headers):
    mock_agent.process_query.side_effect = Exception("Agent Error")
    mock_store = MagicMock()
    mock_store.get_retriever.return_value = MagicMock()
    app.dependency_overrides[get_vector_store] = lambda: mock_store
    app.dependency_overrides[get_llm] = lambda: MagicMock()

    with patch("api.routers.chat.create_hybrid_agent", return_value=mock_agent):
        response = client.post("/api/v1/chat", json={"message": "Crash"}, headers=valid_headers)

    assert response.status_code == 500
    assert "Chat processing failed" in response.json()["detail"]

    app.dependency_overrides = {}


def test_chat_unauthorized():
    response = client.post("/api/v1/chat", json={"message": "Hello"})
    assert response.status_code == 401
