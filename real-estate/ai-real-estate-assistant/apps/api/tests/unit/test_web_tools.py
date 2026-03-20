import json

from utils.web_fetch import WebSearchResult


def test_web_search_tool_uses_searxng_when_configured(monkeypatch):
    import tools.web_tools as web_tools

    def fake_searxng_search(*, searxng_url, query, max_results, timeout_seconds):
        assert searxng_url == "http://searx"
        assert query == "hello"
        assert max_results == 2
        assert timeout_seconds == 1.0
        return [
            WebSearchResult(title="t1", url="https://example.com/a", snippet="s1"),
            WebSearchResult(title="t2", url="https://example.com/b", snippet="s2"),
        ]

    monkeypatch.setattr(web_tools, "searxng_search", fake_searxng_search)
    monkeypatch.setattr(web_tools, "duckduckgo_html_search", lambda **_: [])

    tool = web_tools.WebSearchTool(searxng_url="http://searx", timeout_seconds=1.0)
    payload = json.loads(tool.run({"query": "hello", "max_results": 2}))
    assert payload["provider"] == "searxng"
    assert len(payload["results"]) == 2
    assert payload["results"][0]["url"] == "https://example.com/a"


def test_web_search_tool_falls_back_to_duckduckgo(monkeypatch):
    import tools.web_tools as web_tools

    monkeypatch.setattr(web_tools, "searxng_search", lambda **_: [])

    def fake_ddg(*, query, max_results, timeout_seconds):
        assert query == "hello"
        return [WebSearchResult(title="t1", url="https://example.com/a", snippet="s1")]

    monkeypatch.setattr(web_tools, "duckduckgo_html_search", fake_ddg)

    tool = web_tools.WebSearchTool(searxng_url="http://searx", timeout_seconds=1.0)
    payload = json.loads(tool.run({"query": "hello", "max_results": 5}))
    assert payload["provider"] == "duckduckgo"
    assert payload["results"][0]["title"] == "t1"


def test_open_url_tool_returns_truncated_text(monkeypatch):
    import tools.web_tools as web_tools

    monkeypatch.setattr(web_tools, "fetch_url_text", lambda *args, **kwargs: "x" * 50)

    tool = web_tools.OpenUrlTool(
        timeout_seconds=1.0,
        max_bytes=1000,
        allowlist_domains=[],
        max_text_chars=10,
    )
    payload = json.loads(tool.run("https://example.com/a"))
    assert payload["ok"] is True
    assert payload["text"] == "x" * 10
