from __future__ import annotations

from dataclasses import dataclass
import tempfile
from pathlib import Path

from convention_enricher.cache import FileCache
from convention_enricher.config import CrawlBounds
from convention_enricher.crawler import Crawler
from convention_enricher.models import DiscoveredUrl, FetchedPage
from convention_enricher.snapshot_store import SnapshotStore


def _scratch() -> Path:
    return Path(tempfile.mkdtemp(prefix="ce_test_", dir=Path.cwd()))


@dataclass
class FakeHttpClient:
    pages: dict[str, str]
    blocked: set[str] | None = None

    def is_allowed_by_robots(self, url: str) -> bool:
        return url not in (self.blocked or set())

    def fetch(self, url: str) -> FetchedPage:
        html = self.pages.get(url)
        if html is None:
            return FetchedPage(url, url, 404, False, "", "2026-01-01T00:00:00", "not found")
        return FetchedPage(url, url, 200, True, html, "2026-01-01T00:00:00")


def test_crawler_respects_bounds_and_deduplicates() -> None:
    base = _scratch()
    pages = {
        "https://alpha.example/": "<a href='/dates'>dates</a><a href='/about'>about</a>",
        "https://alpha.example/dates": "<p>Date: July 4, 2026</p>",
        "https://alpha.example/about": "<p>About page</p>",
    }
    crawler = Crawler(
        http_client=FakeHttpClient(pages),
        cache=FileCache(base / "cache"),
        snapshot_store=SnapshotStore(base / "snapshots"),
        bounds=CrawlBounds(max_depth=1, max_pages_per_domain=2, max_pages_per_convention=2, max_retries=1, max_runtime_seconds_per_convention=10, max_concurrency=2),
    )

    docs = crawler.crawl(
        "Alpha",
        [DiscoveredUrl("https://alpha.example/", "google", "q", "convention", 100, 1.0, 100.0)],
    )

    assert len(docs) <= 2


def test_crawler_respects_robots_block() -> None:
    base = _scratch()
    crawler = Crawler(
        http_client=FakeHttpClient({"https://alpha.example/": "<p>x</p>"}, blocked={"https://alpha.example/"}),
        cache=FileCache(base / "cache"),
        snapshot_store=SnapshotStore(base / "snapshots"),
        bounds=CrawlBounds(max_depth=0, max_pages_per_domain=1, max_pages_per_convention=1, max_retries=1, max_runtime_seconds_per_convention=10, max_concurrency=1),
    )

    docs = crawler.crawl(
        "Alpha",
        [DiscoveredUrl("https://alpha.example/", "google", "q", "convention", 100, 1.0, 100.0)],
    )
    assert docs == []
