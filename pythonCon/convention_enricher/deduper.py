from __future__ import annotations

from dataclasses import dataclass

from .utils import canonicalize_url, get_domain


@dataclass(slots=True)
class SeenTracker:
    canonical_urls: set[str]
    final_urls: set[str]
    content_hashes: set[str]


class Deduper:
    def __init__(self) -> None:
        self.seen = SeenTracker(canonical_urls=set(), final_urls=set(), content_hashes=set())

    def should_accept_url(self, url: str) -> bool:
        canonical = canonicalize_url(url)
        if not canonical:
            return False
        if canonical in self.seen.canonical_urls:
            return False
        self.seen.canonical_urls.add(canonical)
        return True

    def should_accept_fetched(self, final_url: str, content_hash: str) -> bool:
        canonical_final = canonicalize_url(final_url)
        if canonical_final and canonical_final in self.seen.final_urls:
            return False
        if content_hash in self.seen.content_hashes:
            return False
        if canonical_final:
            self.seen.final_urls.add(canonical_final)
        self.seen.content_hashes.add(content_hash)
        return True

    @staticmethod
    def domain(url: str) -> str:
        return get_domain(url)
