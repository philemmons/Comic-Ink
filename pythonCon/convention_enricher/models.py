from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


SourceType = Literal["website", "search"]
AuditAction = Literal["kept", "updated", "set_unknown", "resumed", "skipped_dry_run"]
ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW", "NONE"]


@dataclass(slots=True)
class FetchResult:
    ok: bool
    url: str
    status_code: int | None
    text: str
    error: str | None = None


@dataclass(slots=True)
class FetchAttempt:
    url: str
    source_type: SourceType
    ok: bool
    status_code: int | None
    error: str


@dataclass(slots=True)
class FieldCandidate:
    field_name: str
    value: str
    source_url: str
    source_type: SourceType
    confidence: float
    verified: bool
    reason: str


@dataclass(slots=True)
class ExtractionOutput:
    candidates: dict[str, list[FieldCandidate]]
    warnings: dict[str, list[str]]
    fetch_attempts: list[FetchAttempt] = field(default_factory=list)


@dataclass(slots=True)
class AuditRecord:
    row_number: int
    row_id: str
    original_name: str
    original_website: str
    source_used: str
    fetch_status: str
    confidence: ConfidenceLevel
    fields_updated: str
    fields_left_unknown: str
    old_values: str
    new_values: str
    warnings: str
    notes: str
    timestamp_utc: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))

    def as_dict(self) -> dict[str, str]:
        return {
            "row_number": str(self.row_number),
            "row_id": self.row_id,
            "original_name": self.original_name,
            "original_website": self.original_website,
            "source_used": self.source_used,
            "fetch_status": self.fetch_status,
            "confidence": self.confidence,
            "fields_updated": self.fields_updated,
            "fields_left_unknown": self.fields_left_unknown,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "warnings": self.warnings,
            "notes": self.notes,
            "timestamp_utc": self.timestamp_utc,
        }


@dataclass(slots=True)
class RunStats:
    rows_total: int = 0
    rows_processed: int = 0
    rows_resumed: int = 0
    updated_cells: int = 0
    unknown_cells: int = 0
