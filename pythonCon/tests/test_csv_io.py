from __future__ import annotations

import csv
from pathlib import Path

from pythonCon.convention_enricher.csv_io import read_csv_rows, write_csv_rows


def test_csv_round_trip_preserves_header_order(tmp_path: Path) -> None:
    headers = ["id", "conName", "year", "website"]
    rows = [
        {"id": "1", "conName": "A", "year": "2026", "website": "https://a.example"},
        {"id": "2", "conName": "B", "year": "2027", "website": "https://b.example"},
    ]
    csv_path = tmp_path / "out.csv"
    write_csv_rows(csv_path, headers, rows)

    loaded_headers, loaded_rows = read_csv_rows(csv_path)
    assert loaded_headers == headers
    assert loaded_rows == rows


def test_utf8_bom_handling(tmp_path: Path) -> None:
    csv_path = tmp_path / "bom.csv"
    content = '\ufeffid,conName,year\n1,"BOM Con",2026\n'
    csv_path.write_text(content, encoding="utf-8")

    headers, rows = read_csv_rows(csv_path)
    assert headers == ["id", "conName", "year"]
    assert rows[0]["conName"] == "BOM Con"


def test_malformed_rows_missing_and_extra_columns_are_handled(tmp_path: Path) -> None:
    # Row 1 has a missing column value; row 2 has an extra value.
    csv_path = tmp_path / "malformed.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("id,conName,year\n")
        handle.write("1,Short Row\n")
        handle.write("2,Extra Row,2026,EXTRA\n")

    headers, rows = read_csv_rows(csv_path)
    assert headers == ["id", "conName", "year"]
    assert rows[0]["year"] == ""
    assert rows[1]["year"] == "2026"
