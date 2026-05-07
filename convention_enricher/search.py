from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import re
from typing import Protocol
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

from .cache import FileCache
from .normalize import normalize_for_compare, normalize_url
from .scraper import PageFetcher
from .utils import read_json_file


class SearchProvider(Protocol):
    def search(self, convention_name: str, max_results: int) -> list[str]:
        ...


@dataclass(slots=True)
class NoopSearchProvider:
    def search(self, convention_name: str, max_results: int) -> list[str]:
        return []


class DuckDuckGoHtmlSearchProvider:
    def __init__(self, fetcher: PageFetcher, cache: FileCache | None = None) -> None:
        self.fetcher = fetcher
        self.cache = cache
        self.logger = logging.getLogger(self.__class__.__name__)

    def search(self, convention_name: str, max_results: int) -> list[str]:
        query = convention_name.strip()
        if not query:
            return []

        cache_key = f"ddg::{query}::{max_results}"
        if self.cache:
            cached = self.cache.get_json("search", cache_key)
            if isinstance(cached, list):
                return [str(item) for item in cached]

        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        result = self.fetcher.fetch(url)
        if not result.ok:
            return []

        urls: list[str] = []
        seen: set[str] = set()
        for raw_href in re.findall(r'href="([^"]+)"', result.text, flags=re.IGNORECASE):
            parsed = urlparse(raw_href)
            candidate = raw_href
            if parsed.path.startswith("/l/"):
                uddg = parse_qs(parsed.query).get("uddg")
                if uddg:
                    candidate = unquote(uddg[0])

            normalized = normalize_url(candidate)
            if not normalized:
                continue
            host = urlparse(normalized).netloc.lower()
            if "duckduckgo.com" in host:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
            if len(urls) >= max_results:
                break

        if self.cache:
            self.cache.set_json("search", cache_key, urls)
        self.logger.info("Search query '%s' returned %s URL(s).", query, len(urls))
        return urls


class ManualSearchProvider:
    def __init__(self, mapping_path: str) -> None:
        path = Path(mapping_path)
        if not path.exists():
            raise FileNotFoundError(f"Manual search mapping file not found: {path}")
        raw = read_json_file(path)
        if not isinstance(raw, dict):
            raise ValueError("Manual search results must be a JSON object.")

        self.mapping: dict[str, list[str]] = {}
        for key, value in raw.items():
            query = normalize_for_compare(str(key))
            if isinstance(value, list):
                urls = [normalize_url(str(v)) for v in value]
                self.mapping[query] = [u for u in urls if u]
        self.logger = logging.getLogger(self.__class__.__name__)

    def search(self, convention_name: str, max_results: int) -> list[str]:
        key = normalize_for_compare(convention_name)
        urls = self.mapping.get(key, [])
        return urls[:max_results]


class ChainedSearchProvider:
    def __init__(self, providers: list[SearchProvider]) -> None:
        self.providers = providers

    def search(self, convention_name: str, max_results: int) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        for provider in self.providers:
            for url in provider.search(convention_name, max_results):
                if url in seen:
                    continue
                seen.add(url)
                urls.append(url)
                if len(urls) >= max_results:
                    return urls
        return urls
