from __future__ import annotations

from pathlib import Path

from pythonCon.convention_enricher.parsers import extract_candidates_from_html


def test_json_ld_event_parsing_from_fixture() -> None:
    fixture = Path("tests/fixtures/jsonld_event.html").read_text(encoding="utf-8")
    extracted = extract_candidates_from_html(fixture, "https://fixture.example/event", "website")
    values = extracted.candidates

    assert values["conName"][0].value == "Fixture Comic Con"
    assert values["start_date"][0].value == "2026-11-03"
    assert values["end_date"][0].value == "2026-11-05"
    assert values["year"][0].value == "2026"
    assert values["event_location"][0].value == "Fixture Hall"
    assert values["city"][0].value == "Seattle"
    assert values["status"][0].value in {"EventScheduled", "eventscheduled"}


def test_extract_vague_date_generates_warning() -> None:
    html = Path("tests/fixtures/vague_date.html").read_text(encoding="utf-8")
    extracted = extract_candidates_from_html(html, "https://example.test", "website")
    warnings = extracted.warnings
    assert "start_date" in warnings
    assert "Vague/ambiguous date detected" in " ".join(warnings["start_date"])


def test_extract_supported_date_formats_from_visible_text() -> None:
    html = Path("tests/fixtures/visible_text_dates.html").read_text(encoding="utf-8")
    extracted = extract_candidates_from_html(html, "https://example.test", "website")
    starts = [c.value for c in extracted.candidates.get("start_date", [])]
    ends = [c.value for c in extracted.candidates.get("end_date", [])]
    years = [c.value for c in extracted.candidates.get("year", [])]
    assert "2026-01-10" in starts
    assert "2026-01-12" in ends
    assert "2026" in years
    assert "2026-03-28" in starts


def test_visible_text_location_and_notes_extraction() -> None:
    html = Path("tests/fixtures/visible_text_dates.html").read_text(encoding="utf-8")
    extracted = extract_candidates_from_html(html, "https://example.test", "website")
    values = extracted.candidates

    assert "Metro Expo Hall" in [item.value for item in values.get("event_location", [])]
    assert "Toronto" in [item.value for item in values.get("city", [])]
    assert "ON" in [item.value for item in values.get("state_abrev", [])]
    assert "Canada" in [item.value for item in values.get("country", [])]
    assert any("Badge pickup starts early." in item.value for item in values.get("notes", []))
