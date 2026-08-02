from __future__ import annotations

import tempfile
from pathlib import Path

from convention_enricher.csv_io import load_search_targets, write_output_rows


def _scratch() -> Path:
    return Path(tempfile.mkdtemp(prefix="ce_test_", dir=Path.cwd()))


def test_load_search_targets_uses_only_first_column() -> None:
    base = _scratch()
    csv_path = base / "input.csv"
    csv_path.write_text(
        "name,city,state\n"
        "Comic Alpha,Seattle,WA\n"
        "Comic Beta,Portland,OR\n",
        encoding="utf-8",
    )

    targets = load_search_targets(csv_path)
    assert targets == ["Comic Alpha", "Comic Beta"]


def test_load_search_targets_handles_short_and_empty_rows() -> None:
    base = _scratch()
    csv_path = base / "input.csv"
    csv_path.write_text("name\nCon A\n\n  \nCon B\n", encoding="utf-8")

    targets = load_search_targets(csv_path)
    assert targets == ["Con A", "Con B"]


def test_write_output_rows_exports_only_required_columns() -> None:
    base = _scratch()
    output_path = base / "output.csv"
    write_output_rows(
        output_path,
        [
            {
                "convention_name": "Con",
                "event_date": "July 1-2, 2026",
                "event_location": "Downtown Hall",
                "city": "Seattle",
                "state": "Washington",
                "country": "USA",
                "website_url": "https://example.com",
                "extra": "ignored",
            }
        ],
    )

    raw = output_path.read_text(encoding="utf-8")
    assert "extra" not in raw
    assert raw.splitlines()[0] == "convention_name,event_date,event_location,city,state,country,website_url"
