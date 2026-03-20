from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.chat_history import BaseChatMessageHistory

from api.auth import get_api_key
from api.dependencies import get_llm, get_vector_store
from api.main import app

client = TestClient(app)


@pytest.fixture
def mock_deps():
    mock_llm = MagicMock()
    mock_store = MagicMock()
    mock_retriever = MagicMock()
    mock_store.get_retriever.return_value = mock_retriever

    # Mock LLM to behave like a Chat Model
    mock_llm.bind_tools.return_value = mock_llm

    # We need to patch dependencies
    app.dependency_overrides[get_llm] = lambda: mock_llm
    app.dependency_overrides[get_vector_store] = lambda: mock_store
    app.dependency_overrides[get_api_key] = lambda: "test-key"

    yield mock_llm, mock_store

    app.dependency_overrides = {}


@patch("api.routers.chat.get_session_history")
@patch("api.routers.chat.create_hybrid_agent")
def test_chat_session_persistence(mock_create_agent, mock_get_history, mock_deps):
    mock_llm, mock_store = mock_deps

    # Setup Mock Agent
    mock_agent = MagicMock()
    mock_agent.process_query.return_value = {"answer": "Hello Alice", "source_documents": []}
    mock_create_agent.return_value = mock_agent

    # Setup Mock History
    # Must inherit from BaseChatMessageHistory to pass Pydantic validation in ConversationBufferMemory
    class MockHistory(BaseChatMessageHistory):
        messages = []

        def add_message(self, message):
            pass

        def clear(self):
            pass

    mock_history_obj = MockHistory()
    mock_get_history.return_value = mock_history_obj

    # 1. First request - No Session ID
    response1 = client.post("/api/v1/chat", json={"message": "Hello, my name is Alice."})
    assert response1.status_code == 200
    data1 = response1.json()
    session_id = data1["session_id"]
    assert session_id is not None

    # Verify history retrieved for new session
    mock_get_history.assert_called_with(session_id)

    # 2. Second request - With Session ID
    response2 = client.post(
        "/api/v1/chat", json={"message": "What is my name?", "session_id": session_id}
    )

    assert response2.status_code == 200
    # Verify history retrieved for existing session
    mock_get_history.assert_called_with(session_id)

    # Verify create_hybrid_agent was called with memory
    assert mock_create_agent.call_count == 2
    call_args = mock_create_agent.call_args
    assert "memory" in call_args.kwargs
    assert call_args.kwargs["memory"] is not None
    assert call_args.kwargs["memory"].chat_memory == mock_history_obj
