from __future__ import annotations

from pathlib import Path

from convention_enricher.cache import FileCache
from convention_enricher.config import RuntimeConfig
from convention_enricher.csv_io import read_csv_rows, write_csv_rows
from convention_enricher.enrich import run_enrichment
from convention_enricher.models import FetchResult
from convention_enricher.scraper import Scraper


HEADERS = [
    "id",
    "conName",
    "start_date",
    "end_date",
    "year",
    "event_location",
    "city",
    "state",
    "state_abrev",
    "country",
    "website",
    "status",
    "notes",
]


class CountingFetcher:
    def __init__(self, html_by_url: dict[str, str] | None = None, **_: object) -> None:
        self.html_by_url = html_by_url or {}
        self.calls = 0

    def fetch(self, url: str) -> FetchResult:
        self.calls += 1
        html = self.html_by_url.get(url)
        if html is None:
            return FetchResult(ok=False, url=url, status_code=404, text="", error="Not found")
        return FetchResult(ok=True, url=url, status_code=200, text=html)


class CountingSearchProvider:
    def __init__(self, urls: list[str] | None = None) -> None:
        self.urls = urls or []
        self.calls = 0

    def search(self, convention_name: str, max_results: int) -> list[str]:
        self.calls += 1
        return self.urls[:max_results]


def test_cache_behavior_avoids_refetching_same_url(tmp_path: Path) -> None:
    html = Path("tests/fixtures/jsonld_event.html").read_text(encoding="utf-8")
    fetcher = CountingFetcher({"https://fixture.example/event": html})
    cache = FileCache(tmp_path / "cache")
    scraper = Scraper(fetcher=fetcher, cache=cache)

    first = scraper.scrape_candidates("https://fixture.example/event", "website")
    second = scraper.scrape_candidates("https://fixture.example/event", "website")

    assert "conName" in first.candidates
    assert "conName" in second.candidates
    assert fetcher.calls == 1


def test_overwrite_rules_only_missing_keeps_existing_values(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    audit_csv = tmp_path / "audit.csv"

    rows = [
        {
            "id": "1",
            "conName": "Keep City Con",
            "start_date": "",
            "end_date": "",
            "year": "2026",
            "event_location": "",
            "city": "Toronto",
            "state": "Ontario",
            "state_abrev": "ON",
            "country": "Canada",
            "website": "",
            "status": "",
            "notes": "",
        }
    ]
    write_csv_rows(input_csv, HEADERS, rows)

    class FakeFetcher(CountingFetcher):
        def __init__(self, **kwargs: object) -> None:
            super().__init__({}, **kwargs)

    monkeypatch.setattr("convention_enricher.enrich.UrllibPageFetcher", FakeFetcher)
    result = run_enrichment(
        RuntimeConfig(
            input_csv=input_csv,
            output_csv=output_csv,
            audit_csv=audit_csv,
            year=2026,
            only_missing=True,
            search_provider="none",
            cache_dir=tmp_path / ".cache",
        )
    )

    _, out_rows = read_csv_rows(result.output_csv)
    assert out_rows[0]["city"] == "Toronto"


def test_overwrite_rules_stale_values_preserve_existing_when_no_evidence(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    audit_csv = tmp_path / "audit.csv"

    rows = [
        {
            "id": "1",
            "conName": "Stale City Con",
            "start_date": "January 1",
            "end_date": "January 2",
            "year": "2020",
            "event_location": "Old Venue",
            "city": "Old City",
            "state": "Old State",
            "state_abrev": "OS",
            "country": "Old Country",
            "website": "",
            "status": "scheduled",
            "notes": "old",
        }
    ]
    write_csv_rows(input_csv, HEADERS, rows)

    class FakeFetcher(CountingFetcher):
        def __init__(self, **kwargs: object) -> None:
            super().__init__({}, **kwargs)

    monkeypatch.setattr("convention_enricher.enrich.UrllibPageFetcher", FakeFetcher)
    result = run_enrichment(
        RuntimeConfig(
            input_csv=input_csv,
            output_csv=output_csv,
            audit_csv=audit_csv,
            year=2026,
            only_missing=False,
            search_provider="none",
            cache_dir=tmp_path / ".cache",
        )
    )

    _, out_rows = read_csv_rows(result.output_csv)
    assert out_rows[0]["city"] == "Old City"


def test_overwrite_rules_stale_values_can_be_replaced_with_verified_candidates(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    audit_csv = tmp_path / "audit.csv"
    event_html = Path("tests/fixtures/jsonld_event.html").read_text(encoding="utf-8")

    rows = [
        {
            "id": "1",
            "conName": "Fixture Comic Con",
            "start_date": "January 1",
            "end_date": "January 2",
            "year": "2020",
            "event_location": "Old Venue",
            "city": "Old City",
            "state": "Old State",
            "state_abrev": "OS",
            "country": "Old Country",
            "website": "https://fixture.example/event",
            "status": "scheduled",
            "notes": "old",
        }
    ]
    write_csv_rows(input_csv, HEADERS, rows)

    class FakeFetcher(CountingFetcher):
        def __init__(self, **kwargs: object) -> None:
            super().__init__({"https://fixture.example/event": event_html}, **kwargs)

    monkeypatch.setattr("convention_enricher.enrich.UrllibPageFetcher", FakeFetcher)
    result = run_enrichment(
        RuntimeConfig(
            input_csv=input_csv,
            output_csv=output_csv,
            audit_csv=audit_csv,
            year=2026,
            only_missing=False,
            search_provider="none",
            cache_dir=tmp_path / ".cache",
        )
    )

    _, out_rows = read_csv_rows(result.output_csv)
    assert out_rows[0]["city"] == "Grand Rapids"


def test_audit_row_generation_includes_date_warning_for_vague_date(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    audit_csv = tmp_path / "audit.csv"
    vague_html = Path("tests/fixtures/vague_date.html").read_text(encoding="utf-8")

    rows = [
        {
            "id": "1",
            "conName": "Vague Date Con",
            "start_date": "",
            "end_date": "",
            "year": "",
            "event_location": "",
            "city": "",
            "state": "",
            "state_abrev": "",
            "country": "",
            "website": "https://fixture.example/vague",
            "status": "",
            "notes": "",
        }
    ]
    write_csv_rows(input_csv, HEADERS, rows)

    class FakeFetcher(CountingFetcher):
        def __init__(self, **kwargs: object) -> None:
            super().__init__({"https://fixture.example/vague": vague_html}, **kwargs)

    monkeypatch.setattr("convention_enricher.enrich.UrllibPageFetcher", FakeFetcher)
    run_enrichment(
        RuntimeConfig(
            input_csv=input_csv,
            output_csv=output_csv,
            audit_csv=audit_csv,
            year=2026,
            search_provider="none",
            cache_dir=tmp_path / ".cache",
        )
    )

    _, audit_rows = read_csv_rows(audit_csv)
    assert audit_rows
    assert "start_date" in audit_rows[0]["fields_left_unknown"]
    assert "Vague/ambiguous date detected" in audit_rows[0]["warnings"]


def test_resume_behavior_reuses_previous_output_row(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    audit_csv = tmp_path / "audit.csv"

    input_rows = [
        {
            "id": "1",
            "conName": "Input Name",
            "start_date": "",
            "end_date": "",
            "year": "",
            "event_location": "",
            "city": "",
            "state": "",
            "state_abrev": "",
            "country": "",
            "website": "",
            "status": "",
            "notes": "",
        }
    ]
    existing_rows = [
        {
            "id": "1",
            "conName": "Resumed Name",
            "start_date": "January 10",
            "end_date": "January 12",
            "year": "2026",
            "event_location": "Resumed Venue",
            "city": "Resumed City",
            "state": "Resumed State",
            "state_abrev": "RS",
            "country": "Resumed Country",
            "website": "https://resumed.example",
            "status": "scheduled",
            "notes": "resumed note",
        }
    ]
    write_csv_rows(input_csv, HEADERS, input_rows)
    write_csv_rows(output_csv, HEADERS, existing_rows)

    class FakeFetcher(CountingFetcher):
        def __init__(self, **kwargs: object) -> None:
            super().__init__({}, **kwargs)

    monkeypatch.setattr("convention_enricher.enrich.UrllibPageFetcher", FakeFetcher)
    result = run_enrichment(
        RuntimeConfig(
            input_csv=input_csv,
            output_csv=output_csv,
            audit_csv=audit_csv,
            year=2026,
            resume=True,
            search_provider="none",
            cache_dir=tmp_path / ".cache",
        )
    )

    _, out_rows = read_csv_rows(output_csv)
    _, audit_rows = read_csv_rows(audit_csv)

    assert result.stats.rows_resumed == 1
    assert out_rows[0]["conName"] == "Resumed Name"
    assert any(row["fetch_status"] == "resumed" for row in audit_rows)


def test_network_optimization_skips_search_if_website_already_has_candidates(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    audit_csv = tmp_path / "audit.csv"
    event_html = Path("tests/fixtures/jsonld_event.html").read_text(encoding="utf-8")

    write_csv_rows(
        input_csv,
        HEADERS,
        [
            {
                "id": "1",
                "conName": "Fixture Comic Con",
                "start_date": "",
                "end_date": "",
                "year": "",
                "event_location": "",
                "city": "",
                "state": "",
                "state_abrev": "",
                "country": "",
                "website": "https://fixture.example/event",
                "status": "",
                "notes": "",
            }
        ],
    )

    class FakeFetcher(CountingFetcher):
        def __init__(self, **kwargs: object) -> None:
            super().__init__({"https://fixture.example/event": event_html}, **kwargs)

    search_provider = CountingSearchProvider(["https://search.example/should-not-be-used"])

    monkeypatch.setattr("convention_enricher.enrich.UrllibPageFetcher", FakeFetcher)
    monkeypatch.setattr("convention_enricher.enrich.build_search_provider", lambda *args, **kwargs: search_provider)

    run_enrichment(
        RuntimeConfig(
            input_csv=input_csv,
            output_csv=output_csv,
            audit_csv=audit_csv,
            year=2026,
            search_provider="duckduckgo_html",
            cache_dir=tmp_path / ".cache",
        )
    )

    assert search_provider.calls == 0


def test_audit_includes_source_detail_columns(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    audit_csv = tmp_path / "audit.csv"
    event_html = Path("tests/fixtures/jsonld_event.html").read_text(encoding="utf-8")

    write_csv_rows(
        input_csv,
        HEADERS,
        [
            {
                "id": "1",
                "conName": "Fixture Comic Con",
                "start_date": "",
                "end_date": "",
                "year": "",
                "event_location": "",
                "city": "",
                "state": "",
                "state_abrev": "",
                "country": "",
                "website": "https://fixture.example/event",
                "status": "",
                "notes": "",
            }
        ],
    )

    class FakeFetcher(CountingFetcher):
        def __init__(self, **kwargs: object) -> None:
            super().__init__({"https://fixture.example/event": event_html}, **kwargs)

    monkeypatch.setattr("convention_enricher.enrich.UrllibPageFetcher", FakeFetcher)
    run_enrichment(
        RuntimeConfig(
            input_csv=input_csv,
            output_csv=output_csv,
            audit_csv=audit_csv,
            year=2026,
            search_provider="none",
            cache_dir=tmp_path / ".cache",
        )
    )

    headers, rows = read_csv_rows(audit_csv)
    assert "source_used" in headers
    assert "fetch_status" in headers
    assert "confidence" in headers
    assert rows[0]["source_used"] in {"website", "website;search", "none"}


def test_unsafe_overwrite_same_output_as_input_is_blocked(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    write_csv_rows(input_csv, HEADERS, [])
    try:
        run_enrichment(
            RuntimeConfig(
                input_csv=input_csv,
                output_csv=input_csv,
                audit_csv=tmp_path / "audit.csv",
                year=2026,
                search_provider="none",
                cache_dir=tmp_path / ".cache",
            )
        )
    except ValueError as exc:
        assert "Output CSV cannot be the same file as input CSV" in str(exc)
    else:
        raise AssertionError("Expected ValueError when output path equals input path.")
