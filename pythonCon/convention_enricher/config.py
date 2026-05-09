from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class CrawlBounds:
    max_depth: int = 1
    max_pages_per_domain: int = 6
    max_pages_per_convention: int = 24
    max_retries: int = 2
    max_runtime_seconds_per_convention: float = 45.0
    max_concurrency: int = 4


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
    discovery_top_n: int = 18
    offset: int = 0
    limit: int | None = None
    max_search_seconds_per_convention: float = 12.0
    network_failure_threshold: int = 25
    progress_every: int = 10
    crawl_bounds: CrawlBounds = field(default_factory=CrawlBounds)

    @property
    def checkpoint_path(self) -> Path:
        return self.work_dir / "checkpoints" / "checkpoint.json"

    @property
    def snapshots_dir(self) -> Path:
        return self.work_dir / "snapshots"

    @property
    def cache_dir(self) -> Path:
        return self.work_dir / "cache"

    @property
    def memory_path(self) -> Path:
        return self.work_dir / "memory" / "official_domains.json"
