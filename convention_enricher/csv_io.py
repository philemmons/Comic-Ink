from __future__ import annotations

import csv
from pathlib import Path
import tempfile
from typing import Iterable


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Input CSV is missing a header row: {path}")
        headers = list(reader.fieldnames)
        rows: list[dict[str, str]] = []
        for row in reader:
            normalized: dict[str, str] = {}
            for header in headers:
                value = row.get(header, "")
                normalized[header] = "" if value is None else value
            rows.append(normalized)
    return headers, rows


def write_csv_rows(path: Path, headers: list[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write atomically to reduce risk of partial/corrupt files if interrupted.
    with tempfile.NamedTemporaryFile(
        mode="w",
        newline="",
        encoding="utf-8",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})
        temp_path = Path(handle.name)
    temp_path.replace(path)


def read_existing_rows_by_key(path: Path, key_column: str) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    headers, rows = read_csv_rows(path)
    if key_column not in headers:
        return {}
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get(key_column, "").strip()
        if key:
            output[key] = row
    return output
