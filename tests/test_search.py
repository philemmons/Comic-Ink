from __future__ import annotations

import json
from pathlib import Path

from convention_enricher.enrich import SearchDatasetTraits, _build_search_queries_with_context, rank_official_url
from convention_enricher.models import FetchResult
from convention_enricher.search import GoogleComSearchProvider, ManualSearchProvider


class FakeFetcher:
    def __init__(self, html_text: str, status_code: int = 200) -> None:
        self.html_text = html_text
        self.status_code = status_code

    def fetch(self, url: str) -> FetchResult:
        return FetchResult(
            ok=200 <= self.status_code < 400,
            url=url,
            status_code=self.status_code,
            text=self.html_text,
            error=None if 200 <= self.status_code < 400 else f"HTTP {self.status_code}",
        )


def _empty_traits() -> SearchDatasetTraits:
    return SearchDatasetTraits(
        common_name_tokens=set(),
        known_hosts_by_name_key={},
        name_tokens_by_key={},
        frequent_hosts=set(),
    )


def test_build_search_queries_with_context_adds_site_and_location() -> None:
    queries = _build_search_queries_with_context(
        convention_name="TriCityComicCon Postponed",
        year=2026,
        city="Livingston",
        state="Texas",
        state_abrev="TX",
        country="USA",
        website="https://www.myticketing.pro/event/tricitycomiccon",
        traits=_empty_traits(),
    )

    assert any("TriCityComicCon 2026" in query for query in queries)
    assert any("Livingston Texas USA" in query for query in queries)
    assert any("site:myticketing.pro" in query for query in queries)
    assert all("Postponed" not in query for query in queries)


def test_manual_search_provider_fuzzy_matches_query_variant(tmp_path: Path) -> None:
    mapping_path = tmp_path / "manual.json"
    mapping_path.write_text(
        json.dumps({"Grand Rapids Comic-Con": ["https://www.grcomiccon.com"]}, ensure_ascii=False),
        encoding="utf-8",
    )

    provider = ManualSearchProvider(str(mapping_path))
    urls = provider.search("Grand Rapids Comic-Con official website 2026", 3)

    assert urls == ["https://www.grcomiccon.com"]


def test_google_search_provider_extracts_url_param_links() -> None:
    html_text = """
    <html>
      <body>
        <a href='/url?sa=t&url=https%3A%2F%2Fwww.grcomiccon.com%2F&ved=2ah'>Official</a>
        <a href='/url?sa=t&q=https%3A%2F%2Fwww.example.org%2Fevents'>Secondary</a>
      </body>
    </html>
    """
    provider = GoogleComSearchProvider(fetcher=FakeFetcher(html_text), cache=None)
    urls = provider.search("Grand Rapids Comic-Con 2026", 3)

    assert "https://www.grcomiccon.com/" in urls
    assert "https://www.example.org/events" in urls


def test_rank_official_url_prefers_hint_host_over_social() -> None:
    official_score = rank_official_url(
        "https://www.grcomiccon.com/",
        "Grand Rapids Comic-Con",
        2026,
        _empty_traits(),
        website_hint="https://www.grcomiccon.com",
        city="Grand Rapids",
        state="Michigan",
        country="USA",
    )
    social_score = rank_official_url(
        "https://www.facebook.com/grcomiccon/",
        "Grand Rapids Comic-Con",
        2026,
        _empty_traits(),
        website_hint="https://www.grcomiccon.com",
        city="Grand Rapids",
        state="Michigan",
        country="USA",
    )

    assert official_score > social_score
