from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


OUTPUT_FIELDS = [
    "convention_name",
    "event_date",
    "event_location",
    "city",
    "state",
    "country",
    "website_url",
]

UNKNOWN_VALUE = "**"

ExtractionLayer = Literal["meta", "visible", "semantic", "structured"]
SourceRole = Literal["convention", "registration", "organizer", "venue", "listing", "unknown"]


@dataclass(slots=True)
class SearchResult:
    provider: str
    query: str
    url: str
    title: str
    snippet: str


@dataclass(slots=True)
class DiscoveredUrl:
    url: str
    provider: str
    query: str
    authority: SourceRole
    trust_score: int
    relevance_score: float
    rank_score: float


@dataclass(slots=True)
class FetchedPage:
    requested_url: str
    final_url: str
    status_code: int | None
    ok: bool
    html: str
    fetched_at_utc: str
    error: str = ""


@dataclass(slots=True)
class SnapshotRecord:
    snapshot_id: str
    fetched_url: str
    final_url: str
    timestamp_utc: str
    content_hash: str
    html_path: str


@dataclass(slots=True)
class FieldEvidence:
    field_name: str
    value: str
    source_url: str
    source_title: str
    extraction_layer: ExtractionLayer
    selector_hint: str
    authority: SourceRole
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    confidence_score: float = 0.0


@dataclass(slots=True)
class ExtractionResult:
    evidences: list[FieldEvidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CrawlPage:
    url: str
    depth: int
    source_role: SourceRole


@dataclass(slots=True)
class ConventionOutputRow:
    convention_name: str = UNKNOWN_VALUE
    event_date: str = UNKNOWN_VALUE
    event_location: str = UNKNOWN_VALUE
    city: str = UNKNOWN_VALUE
    state: str = UNKNOWN_VALUE
    country: str = UNKNOWN_VALUE
    website_url: str = UNKNOWN_VALUE

    def as_dict(self) -> dict[str, str]:
        return {
            "convention_name": self.convention_name,
            "event_date": self.event_date,
            "event_location": self.event_location,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "website_url": self.website_url,
        }


@dataclass(slots=True)
class ConventionRunRecord:
    convention_name: str
    output: ConventionOutputRow
    completed_at_utc: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))


@dataclass(slots=True)
class AnalyzerStats:
    conventions_total: int = 0
    conventions_completed: int = 0
    search_results_seen: int = 0
    discovered_urls: int = 0
    crawled_pages: int = 0
    snapshots_written: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
