from types import SimpleNamespace

from langchain_core.documents import Document

from api.chat_sources import serialize_chat_sources, serialize_web_sources


def test_serialize_chat_sources_truncates_items():
    docs = [
        Document(page_content="a", metadata={"id": "1"}),
        Document(page_content="b", metadata={"id": "2"}),
        Document(page_content="c", metadata={"id": "3"}),
    ]
    sources, truncated = serialize_chat_sources(
        docs,
        max_items=2,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert len(sources) == 2
    assert sources[0]["metadata"]["id"] == "1"
    assert sources[1]["metadata"]["id"] == "2"
    assert truncated is True


def test_serialize_chat_sources_truncates_content_chars():
    docs = [Document(page_content="abcdef", metadata={"id": "1"})]
    sources, truncated = serialize_chat_sources(
        docs,
        max_items=10,
        max_content_chars=3,
        max_total_bytes=10_000,
    )
    assert sources[0]["content"] == "abc"
    assert truncated is True


def test_serialize_chat_sources_respects_total_bytes_budget():
    docs = [
        Document(page_content="x" * 50, metadata={"id": "1"}),
        Document(page_content="y" * 50, metadata={"id": "2"}),
    ]
    sources, truncated = serialize_chat_sources(
        docs,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=150,
    )
    assert len(sources) == 1
    assert sources[0]["metadata"]["id"] == "1"
    assert truncated is True


def test_serialize_chat_sources_sanitizes_non_dict_metadata():
    docs = [SimpleNamespace(page_content="a", metadata=["not", "a", "dict"])]
    sources, truncated = serialize_chat_sources(
        docs,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert sources == [{"content": "a", "metadata": {"value": "['not', 'a', 'dict']"}}]
    assert truncated is False


def test_serialize_chat_sources_converts_non_string_content():
    docs = [SimpleNamespace(page_content=123, metadata={"id": "1"})]
    sources, truncated = serialize_chat_sources(
        docs,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert sources[0]["content"] == "123"
    assert truncated is False


def test_serialize_chat_sources_handles_non_serializable_metadata():
    class CustomObj:
        def __str__(self):
            return "custom"

    docs = [Document(page_content="a", metadata={"obj": CustomObj()})]
    sources, truncated = serialize_chat_sources(
        docs,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert sources[0]["metadata"]["obj"] == "custom"
    assert truncated is False


def test_serialize_web_sources_basic():
    web_sources = [
        {"url": "https://example.com/1", "snippet": "Content 1", "title": "Title 1"},
        {"url": "https://example.com/2", "snippet": "Content 2", "title": "Title 2"},
    ]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert len(sources) == 2
    assert sources[0]["content"] == "Content 1"
    assert sources[0]["metadata"]["url"] == "https://example.com/1"
    assert sources[0]["metadata"]["title"] == "Title 1"
    assert truncated is False


def test_serialize_web_sources_truncates_items():
    web_sources = [
        {"url": "https://example.com/1", "snippet": "A"},
        {"url": "https://example.com/2", "snippet": "B"},
        {"url": "https://example.com/3", "snippet": "C"},
    ]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=2,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert len(sources) == 2
    assert truncated is True


def test_serialize_web_sources_truncates_content():
    web_sources = [{"url": "https://example.com", "snippet": "A" * 100}]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=10,
        max_content_chars=10,
        max_total_bytes=10_000,
    )
    assert len(sources[0]["content"]) == 10
    assert truncated is True


def test_serialize_web_sources_respects_total_bytes():
    web_sources = [
        {"url": "https://example.com/1", "snippet": "A" * 50},
        {"url": "https://example.com/2", "snippet": "B" * 50},
    ]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=150,
    )
    assert len(sources) == 1
    assert truncated is True


def test_serialize_web_sources_handles_non_dict_source():
    web_sources = ["not a dict", {"url": "https://example.com", "snippet": "A"}]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert len(sources) == 2
    assert sources[0]["metadata"]["value"] == "not a dict"
    assert sources[1]["content"] == "A"


def test_serialize_web_sources_handles_non_serializable_metadata():
    class CustomObj:
        pass

    web_sources = [{"url": "https://example.com", "snippet": "A", "custom": CustomObj()}]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert sources[0]["content"] == "A"
    assert "custom" in sources[0]["metadata"]


def test_serialize_web_sources_uses_content_when_snippet_missing():
    web_sources = [{"url": "https://example.com", "content": "From content field"}]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    assert sources[0]["content"] == "From content field"


def test_serialize_chat_sources_handles_none_in_docs():
    """Test that serialize_chat_sources stops when encountering None in docs."""
    docs = [
        Document(page_content="a", metadata={"id": "1"}),
        None,
        Document(page_content="b", metadata={"id": "2"}),
    ]
    sources, truncated = serialize_chat_sources(
        docs,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    # Should only get the first doc before hitting None
    assert len(sources) == 1
    assert sources[0]["metadata"]["id"] == "1"
    assert truncated is False


def test_serialize_chat_sources_max_items_sets_truncated_flag():
    """Test that hitting max_items limit sets truncated flag."""
    docs = [
        Document(page_content="a", metadata={"id": "1"}),
        Document(page_content="b", metadata={"id": "2"}),
        Document(page_content="c", metadata={"id": "3"}),
    ]
    sources, truncated = serialize_chat_sources(
        docs,
        max_items=2,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    # Should get first 2 docs, truncated flag should be True
    assert len(sources) == 2
    assert sources[0]["metadata"]["id"] == "1"
    assert sources[1]["metadata"]["id"] == "2"
    assert truncated is True


def test_serialize_web_sources_handles_none_in_sources():
    """Test that serialize_web_sources stops when encountering None in sources."""
    web_sources = [
        {"url": "https://example.com/1", "snippet": "A"},
        None,
        {"url": "https://example.com/2", "snippet": "B"},
    ]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=10,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    # Should only get the first source before hitting None
    assert len(sources) == 1
    assert sources[0]["content"] == "A"
    assert truncated is False


def test_serialize_web_sources_max_items_sets_truncated_flag():
    """Test that hitting max_items limit sets truncated flag for web sources."""
    web_sources = [
        {"url": "https://example.com/1", "snippet": "A"},
        {"url": "https://example.com/2", "snippet": "B"},
        {"url": "https://example.com/3", "snippet": "C"},
    ]
    sources, truncated = serialize_web_sources(
        web_sources,
        max_items=2,
        max_content_chars=100,
        max_total_bytes=10_000,
    )
    # Should get first 2 sources, truncated flag should be True
    assert len(sources) == 2
    assert sources[0]["content"] == "A"
    assert sources[1]["content"] == "B"
    assert truncated is True
