from __future__ import annotations

from dataclasses import dataclass

from convention_enricher import enrich


@dataclass
class FakeResponse:
    status_code: int
    text: str
    url: str


class FakeSession:
    def __init__(self, *, post_responses: list[FakeResponse], get_responses: list[FakeResponse]) -> None:
        self.post_responses = list(post_responses)
        self.get_responses = list(get_responses)
        self.calls: list[tuple[str, str]] = []

    def post(self, url: str, **_: object) -> FakeResponse:
        self.calls.append(("post", url))
        return self.post_responses.pop(0)

    def get(self, url: str, **_: object) -> FakeResponse:
        self.calls.append(("get", url))
        return self.get_responses.pop(0)


def test_contains_block_page_detects_duckduckgo_anomaly() -> None:
    markup = """
    <div class="anomaly-modal__title">Unfortunately, bots use DuckDuckGo too.</div>
    <div>Please complete the following challenge to confirm this search was made by a human.</div>
    """

    assert enrich.contains_block_page(markup) is True


def test_query_search_falls_back_to_google_when_duckduckgo_is_blocked(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(enrich, "SNAPSHOTS_DIR", tmp_path)
    strategy = enrich.SearchRotationStrategy(
        provider_queries={
            "duckduckgo": enrich.query_duckduckgo,
            "google": enrich.query_google,
            "bing": enrich.query_bing,
        },
        provider_order=("duckduckgo", "google", "bing"),
    )
    session = FakeSession(
        post_responses=[
            FakeResponse(
                status_code=200,
                text="""
                <div class="anomaly-modal__title">Unfortunately, bots use DuckDuckGo too.</div>
                <div>Please complete the following challenge to confirm this search was made by a human.</div>
                """,
                url=enrich.DDG_HTML_ENDPOINT,
            )
        ],
        get_responses=[
            FakeResponse(
                status_code=200,
                text="""
                <html>
                    <body>
                        <a href="/url?q=https%3A%2F%2Fexample.com%2Fevent">Example Result</a>
                    </body>
                </html>
                """,
                url="https://www.google.com/search?q=Example+Con+2026",
            )
        ],
    )

    attempt = enrich.query_search(session, "Example Con 2026", 1, strategy)

    assert attempt.found is True
    assert attempt.provider == "google"
    assert attempt.saved_path.endswith("_google.html")
    assert attempt.attempted_providers == ("duckduckgo", "google")
    assert session.calls == [
        ("post", enrich.DDG_HTML_ENDPOINT),
        ("get", enrich.GOOGLE_SEARCH_ENDPOINT),
    ]


def test_query_search_keeps_duckduckgo_result_when_not_blocked(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(enrich, "SNAPSHOTS_DIR", tmp_path)
    strategy = enrich.SearchRotationStrategy(
        provider_queries={
            "duckduckgo": enrich.query_duckduckgo,
            "google": enrich.query_google,
            "bing": enrich.query_bing,
        },
        provider_order=("duckduckgo", "google", "bing"),
    )
    session = FakeSession(
        post_responses=[
            FakeResponse(
                status_code=200,
                text="<html><body>No results found for this search.</body></html>",
                url=enrich.DDG_HTML_ENDPOINT,
            )
        ],
        get_responses=[
            FakeResponse(
                status_code=200,
                text="<html><body>No results found for this search.</body></html>",
                url="https://www.google.com/search?q=Example+Con+2026",
            ),
            FakeResponse(
                status_code=200,
                text="<html><body>No results found for this search.</body></html>",
                url="https://www.bing.com/search?q=Example+Con+2026",
            ),
        ],
    )

    attempt = enrich.query_search(session, "Example Con 2026", 1, strategy)

    assert attempt.found is False
    assert attempt.provider == "bing"
    assert attempt.saved_path.endswith("_bing.html")
    assert attempt.attempted_providers == ("duckduckgo", "google", "bing")
    assert session.calls == [
        ("post", enrich.DDG_HTML_ENDPOINT),
        ("get", enrich.GOOGLE_SEARCH_ENDPOINT),
        ("get", enrich.BING_SEARCH_ENDPOINT),
    ]


def test_rotation_advances_after_two_successful_queries() -> None:
    strategy = enrich.SearchRotationStrategy(
        provider_queries={
            "google": enrich.query_google,
            "bing": enrich.query_bing,
            "duckduckgo": enrich.query_duckduckgo,
        }
    )

    assert strategy.providers_for_query()[0] == "google"

    success = enrich.SearchAttempt(found=True, saved_path="snapshot.html", provider="google")
    strategy.record_attempt("google", success)
    strategy.record_attempt("google", success)

    assert strategy.providers_for_query()[0] == "bing"
