from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import re
import time
from urllib.parse import urlparse

from .cache import FileCache
from .config import CrawlBounds
from .deduper import Deduper
from .http_client import HttpClient
from .models import DiscoveredUrl, SnapshotRecord, SourceRole
from .snapshot_store import SnapshotStore
from .utils import canonicalize_url, clean_source_text


TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", flags=re.IGNORECASE | re.DOTALL)


@dataclass(slots=True)
class CrawledDocument:
    url: str
    final_url: str
    source_role: SourceRole
    page_title: str
    html: str
    snapshot: SnapshotRecord


class Crawler:
    def __init__(
        self,
        http_client: HttpClient,
        cache: FileCache,
        snapshot_store: SnapshotStore,
        bounds: CrawlBounds,
    ) -> None:
        self.http_client = http_client
        self.cache = cache
        self.snapshot_store = snapshot_store
        self.bounds = bounds

    def crawl(self, convention_name: str, discovered_urls: list[DiscoveredUrl]) -> list[CrawledDocument]:
        start = time.monotonic()
        # Avoid stale per-domain robots state bleeding across conventions.
        self.http_client.reset_robots_cache()
        deduper = Deduper()
        documents: list[CrawledDocument] = []

        queue: list[tuple[str, SourceRole]] = []
        for item in discovered_urls:
            homepage_url = _to_homepage_url(item.url)
            if not homepage_url:
                continue
            if deduper.should_accept_url(homepage_url):
                queue.append((homepage_url, item.authority))

        pages_seen = 0

        while queue and pages_seen < self.bounds.max_pages_per_convention:
            if time.monotonic() - start > self.bounds.max_runtime_seconds_per_convention:
                break

            batch = queue[: self.bounds.max_concurrency]
            queue = queue[self.bounds.max_concurrency :]
            futures = {}
            with ThreadPoolExecutor(max_workers=self.bounds.max_concurrency) as pool:
                for url, role in batch:
                    futures[pool.submit(self._fetch_and_snapshot, url)] = (url, role)

                for future in as_completed(futures):
                    url, role = futures[future]
                    pages_seen += 1
                    page = future.result()
                    if not page["ok"]:
                        continue

                    final_url = str(page["final_url"])
                    content_hash = str(page["content_hash"])
                    if not deduper.should_accept_fetched(final_url, content_hash):
                        continue

                    snapshot = SnapshotRecord(
                        snapshot_id=str(page["snapshot_id"]),
                        fetched_url=str(page["fetched_url"]),
                        final_url=final_url,
                        timestamp_utc=str(page["timestamp_utc"]),
                        content_hash=content_hash,
                        html_path=str(page["html_path"]),
                    )
                    html = str(page["html"])
                    title = _extract_title(html)
                    documents.append(
                        CrawledDocument(
                            url=url,
                            final_url=final_url,
                            source_role=role,
                            page_title=title,
                            html=html,
                            snapshot=snapshot,
                        )
                    )

        return documents

    def _fetch_and_snapshot(self, url: str) -> dict[str, object]:
        canonical = canonicalize_url(url)
        if not canonical:
            return {"ok": False}

        cached = self.cache.get_json("fetched_pages", canonical)
        if isinstance(cached, dict):
            # Do not trust historical robots blocks forever; re-evaluate each run.
            if cached.get("error") == "robots_disallow":
                cached = None
            else:
                return cached

        if not self.http_client.is_allowed_by_robots(canonical):
            # Intentionally do not persist robots_disallow into cache, so temporary
            # robots retrieval/parsing issues do not become permanent denials.
            return {"ok": False, "error": "robots_disallow"}

        fetched = self.http_client.fetch(canonical)
        if not fetched.ok:
            payload = {"ok": False, "error": fetched.error}
            self.cache.set_json("fetched_pages", canonical, payload)
            return payload

        snapshot = self.snapshot_store.save(fetched)
        payload = {
            "ok": True,
            "fetched_url": fetched.requested_url,
            "final_url": fetched.final_url,
            "timestamp_utc": fetched.fetched_at_utc,
            "html": fetched.html,
            "content_hash": snapshot.content_hash,
            "snapshot_id": snapshot.snapshot_id,
            "html_path": snapshot.html_path,
        }
        self.cache.set_json("fetched_pages", canonical, payload)
        return payload


def _extract_title(html_text: str) -> str:
    match = TITLE_PATTERN.search(html_text)
    if not match:
        return ""
    return clean_source_text(re.sub(r"<[^>]+>", " ", match.group(1)))


def _to_homepage_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return canonicalize_url(f"{parsed.scheme}://{parsed.netloc}/") or ""
