from __future__ import annotations

from dataclasses import dataclass


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


@dataclass(slots=True)
class SearchResult:
    provider: str
    query: str
    url: str
    title: str
    snippet: str


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
class AnalyzerStats:
    conventions_total: int = 0
    conventions_completed: int = 0
    search_results_seen: int = 0
    discovered_urls: int = 0
