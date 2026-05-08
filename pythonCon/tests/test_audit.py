from __future__ import annotations

from pathlib import Path

from pythonCon.convention_enricher.audit import write_audit_csv
from pythonCon.convention_enricher.csv_io import read_csv_rows
from pythonCon.convention_enricher.models import AuditRecord


def test_write_audit_csv(tmp_path: Path) -> None:
    record = AuditRecord(
        row_number=1,
        row_id="1",
        original_name="Fixture Comic Con",
        original_website="https://fixture.example/event",
        source_used="website",
        fetch_status="ok",
        confidence="HIGH",
        fields_updated="city",
        fields_left_unknown="",
        old_values='{\"city\":\"\"}',
        new_values='{\"city\":\"Seattle\"}',
        warnings="",
        notes="",
    )

    output = tmp_path / "audit.csv"
    write_audit_csv(output, [record])

    headers, rows = read_csv_rows(output)
    assert "source_used" in headers
    assert rows[0]["fields_updated"] == "city"
    assert rows[0]["confidence"] == "HIGH"
    assert "warnings" in headers
