from __future__ import annotations

import csv
from pathlib import Path
import tempfile

from .models import OUTPUT_FIELDS
from .utils import clean_source_text


def load_search_targets(path: Path) -> list[str]:
    rows: list[list[str]] = []
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.reader(handle)
                rows = list(reader)
            last_error = None
            break
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    if not rows:
        return []
    data_rows = rows[1:]
    targets: list[str] = []
    for row in data_rows:
        if not row:
            continue
        raw_value = row[0] if len(row) > 0 else ""
        cleaned = clean_source_text(raw_value)
        if cleaned:
            targets.append(cleaned)
    return targets


def write_output_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in OUTPUT_FIELDS})
        tmp_path = Path(handle.name)
    tmp_path.replace(path)
