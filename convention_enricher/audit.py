from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .csv_io import write_csv_rows
from .models import AuditRecord


AUDIT_COLUMNS = [
    "row_number",
    "row_id",
    "original_name",
    "original_website",
    "source_used",
    "fetch_status",
    "confidence",
    "fields_updated",
    "fields_left_unknown",
    "old_values",
    "new_values",
    "warnings",
    "notes",
    "timestamp_utc",
]


def write_audit_csv(path: Path, records: Iterable[AuditRecord]) -> None:
    rows = [record.as_dict() for record in records]
    write_csv_rows(path, AUDIT_COLUMNS, rows)
