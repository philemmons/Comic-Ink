from __future__ import annotations

from convention_enricher.crawler import CrawledDocument
from convention_enricher.extractor import extract_from_document
from convention_enricher.models import SnapshotRecord


def _doc(html: str) -> CrawledDocument:
    return CrawledDocument(
        url="https://alpha.example",
        final_url="https://alpha.example",
        source_role="convention",
        page_title="Alpha Con",
        html=html,
        snapshot=SnapshotRecord(
            snapshot_id="s1",
            fetched_url="https://alpha.example",
            final_url="https://alpha.example",
            timestamp_utc="2026-01-01T00:00:00",
            content_hash="x",
            html_path="/tmp/s1.html",
        ),
    )


def test_extractor_keeps_explicit_date_phrase_exact_wording() -> None:
    html = """
    <html><body>
    <h1>Alpha Comic Convention</h1>
    <p>Event Dates: November 14-16, 2026</p>
    </body></html>
    """
    result = extract_from_document(_doc(html), "Alpha Comic Convention")
    dates = [item.value for item in result.evidences if item.field_name == "event_date"]
    assert "November 14-16, 2026" in dates


def test_extractor_only_uses_explicit_location_labels() -> None:
    html = """
    <html><body>
    <p>Location: DeVos Place Convention Center</p>
    <p>City: Grand Rapids</p>
    <p>State: Michigan</p>
    <p>Country: USA</p>
    <p>123 Main St, Hidden City, ZZ 00000</p>
    </body></html>
    """
    result = extract_from_document(_doc(html), "Alpha")

    fields = {(item.field_name, item.value) for item in result.evidences}
    assert ("city", "Grand Rapids") in fields
    assert ("state", "Michigan") in fields
    assert ("country", "USA") in fields
    assert all(value != "Hidden City" for _, value in fields)


def test_extractor_handles_malformed_html() -> None:
    html = "<html><body><h1>Broken <p>Date: July 4, 2026"
    result = extract_from_document(_doc(html), "Broken")
    assert result.evidences
