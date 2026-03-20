from types import SimpleNamespace

import utils.web_fetch as web_fetch


def test_fetch_url_text_rejects_non_http_schemes():
    assert (
        web_fetch.fetch_url_text(
            "file:///etc/passwd",
            timeout_seconds=1,
            max_bytes=1000,
            allowlist_domains=[],
        )
        is None
    )


def test_fetch_url_text_rejects_localhost(monkeypatch):
    monkeypatch.setattr(
        web_fetch.socket, "getaddrinfo", lambda *_a, **_k: [("", "", "", "", ("127.0.0.1", 0))]
    )
    assert (
        web_fetch.fetch_url_text(
            "http://localhost:8000/",
            timeout_seconds=1,
            max_bytes=1000,
            allowlist_domains=[],
        )
        is None
    )


def test_searxng_search_parses_results(monkeypatch):
    html = """
    <article class="result result-default">
      <h3><a href="https://example.com/a">t1</a></h3>
      <p class="content">c1</p>
    </article>
    <article class="result result-default">
      <h3><a href="https://example.com/b">t2</a></h3>
      <p class="content">c2</p>
    </article>
    """

    def fake_get(_url, params=None, timeout=None, headers=None):
        assert params["q"] == "hello"
        assert timeout == 1
        assert headers and "X-Forwarded-For" in headers
        return SimpleNamespace(
            status_code=200,
            text=html,
        )

    monkeypatch.setattr(web_fetch.requests, "get", fake_get)
    results = web_fetch.searxng_search(
        searxng_url="http://searxng:8080", query="hello", max_results=1, timeout_seconds=1
    )
    assert len(results) == 1
    assert results[0].title == "t1"
    assert results[0].url == "https://example.com/a"
    assert results[0].snippet == "c1"


def test_duckduckgo_html_search_parses_results(monkeypatch):
    html = """
    <a class="result__a" href="https://example.com/1">Title 1</a>
    <a class="result__snippet">Snippet 1</a>
    <a class="result__a" href="https://example.com/2">Title 2</a>
    <a class="result__snippet">Snippet 2</a>
    """

    def fake_get(_url, params=None, headers=None, timeout=None):
        assert params["q"] == "hello"
        return SimpleNamespace(status_code=202, text=html)

    monkeypatch.setattr(web_fetch.requests, "get", fake_get)
    results = web_fetch.duckduckgo_html_search(query="hello", max_results=1, timeout_seconds=1)
    assert len(results) == 1
    assert results[0].url == "https://example.com/1"
    assert results[0].title == "Title 1"
    assert results[0].snippet == "Snippet 1"
