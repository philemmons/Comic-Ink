from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path


@dataclass(slots=True)
class ColumnConfig:
    id_column: str = "id"
    name_column: str = "conName"
    start_date_column: str = "start_date"
    end_date_column: str = "end_date"
    year_column: str = "year"
    venue_column: str = "event_location"
    city_column: str = "city"
    state_column: str = "state"
    state_abbrev_column: str = "state_abrev"
    country_column: str = "country"
    website_column: str = "website"
    status_column: str = "status"
    notes_column: str = "notes"

    def target_fields(self) -> list[str]:
        return [
            self.name_column,
            self.start_date_column,
            self.end_date_column,
            self.year_column,
            self.venue_column,
            self.city_column,
            self.state_column,
            self.state_abbrev_column,
            self.country_column,
            self.website_column,
            self.status_column,
            self.notes_column,
        ]


@dataclass(slots=True)
class RuntimeConfig:
    input_csv: Path
    output_csv: Path
    audit_csv: Path
    year: int
    limit: int | None = None
    dry_run: bool = False
    only_missing: bool = False
    resume: bool = False
    verbose: bool = False
    cache_dir: Path = Path(".cache/convention_enricher")
    search_provider: str = "google.com"
    manual_search_results: Path | None = None
    unknown_value: str = "**"
    timeout_seconds: float = 12.0
    retry_total: int = 1
    retry_backoff_seconds: float = 0.6
    rate_limit_per_second: float = 2.0
    ssl_error_host_cooldown_seconds: float = 1800.0
    user_agent: str = "ConventionEnricher/2.0"
    max_search_results: int = 3
    search_time_limit_seconds: float = 8.0
    stop_after_first_empty_search_query: bool = True
    columns: ColumnConfig = field(default_factory=ColumnConfig)

    @staticmethod
    def default_year() -> int:
        return datetime.now().year


def apply_env_overrides(config: RuntimeConfig) -> RuntimeConfig:
    """
    Override selected runtime settings from environment variables.
    These are optional and designed for CI/automation use.
    """
    user_agent = os.getenv("CONVENTION_ENRICHER_USER_AGENT")
    if user_agent:
        config.user_agent = user_agent

    timeout = os.getenv("CONVENTION_ENRICHER_TIMEOUT_SECONDS")
    if timeout:
        try:
            config.timeout_seconds = float(timeout)
        except ValueError:
            pass

    retry_total = os.getenv("CONVENTION_ENRICHER_RETRY_TOTAL")
    if retry_total:
        try:
            config.retry_total = max(0, int(retry_total))
        except ValueError:
            pass

    retry_backoff = os.getenv("CONVENTION_ENRICHER_RETRY_BACKOFF_SECONDS")
    if retry_backoff:
        try:
            config.retry_backoff_seconds = max(0.0, float(retry_backoff))
        except ValueError:
            pass

    rate = os.getenv("CONVENTION_ENRICHER_RATE_LIMIT_PER_SECOND")
    if rate:
        try:
            config.rate_limit_per_second = max(0.1, float(rate))
        except ValueError:
            pass

    ssl_cooldown = os.getenv("CONVENTION_ENRICHER_SSL_ERROR_HOST_COOLDOWN_SECONDS")
    if ssl_cooldown:
        try:
            config.ssl_error_host_cooldown_seconds = max(0.0, float(ssl_cooldown))
        except ValueError:
            pass

    max_results = os.getenv("CONVENTION_ENRICHER_MAX_SEARCH_RESULTS")
    if max_results:
        try:
            config.max_search_results = max(1, int(max_results))
        except ValueError:
            pass

    search_time_limit = os.getenv("CONVENTION_ENRICHER_SEARCH_TIME_LIMIT_SECONDS")
    if search_time_limit:
        try:
            config.search_time_limit_seconds = max(0.0, float(search_time_limit))
        except ValueError:
            pass

    stop_after_empty = os.getenv("CONVENTION_ENRICHER_STOP_AFTER_FIRST_EMPTY_SEARCH_QUERY")
    if stop_after_empty:
        config.stop_after_first_empty_search_query = stop_after_empty.strip().lower() not in {"0", "false", "no"}

    return config
