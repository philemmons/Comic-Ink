from __future__ import annotations

from dataclasses import dataclass
import tempfile
from pathlib import Path

from convention_enricher.cache import FileCache
from convention_enricher.models import FetchedPage
from convention_enricher.search import BingSearchAdapter, DuckDuckGoSearchAdapter, GoogleSearchAdapter


def _scratch() -> Path:
    return Path(tempfile.mkdtemp(prefix="ce_test_", dir=Path.cwd()))


@dataclass
class FakeHttpClient:
    html: str

    def fetch(self, url: str) -> FetchedPage:
        return FetchedPage(
            requested_url=url,
            final_url=url,
            status_code=200,
            ok=True,
            html=self.html,
            fetched_at_utc="2026-01-01T00:00:00",
        )


def test_google_adapter_extracts_redirect_urls() -> None:
    base = _scratch()
    markup = """
    <a href='/url?sa=t&url=https%3A%2F%2Falpha.example%2Fhome'>A</a>
    <a href='/url?sa=t&q=https%3A%2F%2Fbeta.example%2Fevent'>B</a>
    """
    provider = GoogleSearchAdapter(FakeHttpClient(markup), cache=FileCache(base / "cache"))
    results = provider.search("Alpha Con", 5)

    assert any(item.url == "https://alpha.example/home" for item in results)
    assert any(item.url == "https://beta.example/event" for item in results)


def test_bing_and_ddg_adapters_parse_urls() -> None:
    base = _scratch()
    markup = """
    <a href='https://gamma.example/convention'>Gamma</a>
    <a href='https://duckduckgo.com/l/?uddg=https%3A%2F%2Fdelta.example%2Fdates'>Delta</a>
    """
    bing = BingSearchAdapter(FakeHttpClient(markup), cache=FileCache(base / "cache_b"))
    ddg = DuckDuckGoSearchAdapter(FakeHttpClient(markup), cache=FileCache(base / "cache_d"))

    assert any(item.url == "https://gamma.example/convention" for item in bing.search("Gamma", 5))
    assert any(item.url == "https://delta.example/dates" for item in ddg.search("Delta", 5))
