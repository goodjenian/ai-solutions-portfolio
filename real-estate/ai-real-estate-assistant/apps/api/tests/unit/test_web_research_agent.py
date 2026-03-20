from types import SimpleNamespace

import tools.web_tools as web_tools
from agents.web_research_agent import WebResearchAgent, WebResearchConfig
from utils.web_fetch import WebSearchResult


class _LLMSequence:
    def __init__(self, contents):
        self._contents = list(contents)
        self._i = 0

    def invoke(self, _prompt):
        if self._i >= len(self._contents):
            return SimpleNamespace(content="")
        content = self._contents[self._i]
        self._i += 1
        return SimpleNamespace(content=content)


def test_web_research_agent_happy_path(monkeypatch):
    llm = _LLMSequence(["[1]", "Answer using source [1]."])
    cfg = WebResearchConfig(
        searxng_url="http://searx",
        web_search_max_results=5,
        web_fetch_timeout_seconds=1.0,
        web_fetch_max_bytes=1000,
        web_allowlist_domains=[],
        max_open_urls=2,
        max_page_chars_for_llm=100,
    )
    agent = WebResearchAgent(llm=llm, config=cfg)

    def fake_searxng_search(*, searxng_url, query, max_results, timeout_seconds):
        assert searxng_url == "http://searx"
        assert query == "q"
        return [
            WebSearchResult(title="t1", url="https://example.com/a", snippet="s1"),
            WebSearchResult(title="t2", url="https://example.com/b", snippet="s2"),
        ]

    monkeypatch.setattr(web_tools, "searxng_search", fake_searxng_search)
    monkeypatch.setattr(web_tools, "duckduckgo_html_search", lambda **_: [])
    monkeypatch.setattr(web_tools, "fetch_url_text", lambda *args, **kwargs: "page text")

    out = agent.research("q")
    assert "Answer" in out["answer"]
    assert len(out["sources"]) == 1
    assert out["sources"][0]["url"] == "https://example.com/a"
    assert out["intermediate_steps"][0]["tool"] == "web_search"
    assert any(s["tool"] == "open_url" for s in out["intermediate_steps"])


def test_web_research_agent_parses_json_array_from_wrapped_text(monkeypatch):
    llm = _LLMSequence(["Selected: [2, 1]", "Answer [1]."])
    cfg = WebResearchConfig(
        searxng_url=None,
        web_search_max_results=5,
        web_fetch_timeout_seconds=1.0,
        web_fetch_max_bytes=1000,
        web_allowlist_domains=[],
        max_open_urls=2,
        max_page_chars_for_llm=100,
    )
    agent = WebResearchAgent(llm=llm, config=cfg)

    monkeypatch.setattr(web_tools, "searxng_search", lambda **_: [])

    def fake_ddg(*, query, max_results, timeout_seconds):
        assert query == "q"
        return [
            WebSearchResult(title="t1", url="https://example.com/a", snippet="s1"),
            WebSearchResult(title="t2", url="https://example.com/b", snippet="s2"),
        ]

    monkeypatch.setattr(web_tools, "duckduckgo_html_search", fake_ddg)
    monkeypatch.setattr(web_tools, "fetch_url_text", lambda *args, **kwargs: "page")

    out = agent.research("q")
    urls = [s["url"] for s in out["sources"]]
    assert urls[0] == "https://example.com/b"
