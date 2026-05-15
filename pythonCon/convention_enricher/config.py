from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RuntimeConfig:
    input_csv: Path
    output_csv: Path
    work_dir: Path
    unknown_value: str = "**"
    request_timeout_seconds: float = 12.0
    requests_per_second: float = 1.5
    user_agent: str = "ConventionDiscoveryCrawler/1.0"
    search_results_per_provider: int = 8
    offset: int = 0
    limit: int | None = None
    max_search_seconds_per_convention: float = 12.0
    network_failure_threshold: int = 25
    progress_every: int = 10
    allow_zero_success: bool = False
    show_steps: bool = True
    max_retries: int = 2

    @property
    def cache_dir(self) -> Path:
        return self.work_dir / "cache"
