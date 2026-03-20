"""
Memory management for AI agents.
Handles session persistence using SQLite.
"""

import os

from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

# Define database path
DB_PATH = os.path.join(os.getcwd(), "data", "sessions.db")
CONNECTION_STRING = f"sqlite:///{DB_PATH}"


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Get chat message history for a session.

    Args:
        session_id: Unique session identifier

    Returns:
        BaseChatMessageHistory instance backed by SQLite
    """
    # SQLChatMessageHistory automatically creates the table 'message_store' if needed
    return SQLChatMessageHistory(session_id=session_id, connection_string=CONNECTION_STRING)
