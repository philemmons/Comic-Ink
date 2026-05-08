from __future__ import annotations

from dataclasses import dataclass
import html
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


QUERY_NOISE_TOKENS = {
    "official",
    "website",
    "site",
    "convention",
    "comic",
    "con",
    "dates",
    "date",
    "venue",
    "location",
    "event",
}


def _normalize_query_key(text: str) -> str:
    lowered = normalize_for_compare(text)
    normalized = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", normalized).strip()


def _relaxed_query_key(text: str) -> str:
    normalized = _normalize_query_key(text)
    tokens = []
    for token in normalized.split():
        if re.fullmatch(r"(19|20)\d{2}", token):
            continue
        if token in QUERY_NOISE_TOKENS:
            continue
        tokens.append(token)
    return " ".join(tokens)


def _token_overlap_score(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))


def _is_unusable_href(href: str) -> bool:
    lowered = href.lower()
    prefixes = ("#", "javascript:", "mailto:", "tel:", "sms:", "data:")
    return lowered.startswith(prefixes)


def _host_matches_blocklist(host: str, blocked_hosts: set[str]) -> bool:
    return any(blocked_host in host for blocked_host in blocked_hosts)


def _extract_normalized_search_urls(
    html_text: str,
    max_results: int,
    blocked_hosts: set[str],
) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    # Parse generic href attributes to tolerate markup differences.
    raw_hrefs = re.findall(r"href\s*=\s*['\"]([^'\"]+)['\"]", html_text, flags=re.IGNORECASE)
    max_candidates = max(max_results * 8, 24)
    for raw_href in raw_hrefs:
        href = html.unescape(raw_href.strip())
        if _is_unusable_href(href):
            continue
        candidate = href

        # Google-style redirect links.
        if href.startswith("/url?"):
            parsed = urlparse(href)
            query = parse_qs(parsed.query)
            candidate = query.get("q", [""])[0] or query.get("url", [""])[0] or query.get("adurl", [""])[0]
        # DuckDuckGo-style redirect links.
        elif "/l/?" in href or "uddg=" in href:
            parsed = urlparse(href)
            uddg = parse_qs(parsed.query).get("uddg", [""])[0]
            if uddg:
                candidate = unquote(uddg)
        elif href.startswith("//"):
            candidate = f"https:{href}"

        normalized = normalize_url(candidate)
        if not normalized:
            continue
        host = urlparse(normalized).netloc.lower()
        if _host_matches_blocklist(host, blocked_hosts):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        urls.append(normalized)
        if len(urls) >= max_candidates:
            break
    return urls


def _looks_like_blocked_or_consent_page(html_text: str) -> bool:
    lowered = html_text.lower()
    markers = (
        "unusual traffic",
        "consent.google.com",
        "/sorry/",
        "captcha",
        "detected unusual traffic",
        "automated queries",
    )
    return any(marker in lowered for marker in markers)


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
            if isinstance(cached, list) and cached:
                return [str(item) for item in cached]

        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        result = self.fetcher.fetch(url)
        if not result.ok:
            return []
        if result.status_code == 202:
            self.logger.warning(
                "DuckDuckGo returned HTTP 202 for query '%s'; response may be challenge/placeholder content.",
                query,
            )

        urls = _extract_normalized_search_urls(
            result.text,
            max_results=max_results,
            blocked_hosts={"duckduckgo.com"},
        )

        if self.cache and urls:
            self.cache.set_json("search", cache_key, urls)
        self.logger.info("Search query '%s' returned %s URL(s).", query, len(urls))
        return urls


class GoogleComSearchProvider:
    def __init__(self, fetcher: PageFetcher, cache: FileCache | None = None) -> None:
        self.fetcher = fetcher
        self.cache = cache
        self.logger = logging.getLogger(self.__class__.__name__)

    def search(self, convention_name: str, max_results: int) -> list[str]:
        query = convention_name.strip()
        if not query:
            return []

        cache_key = f"google::{query}::{max_results}"
        if self.cache:
            cached = self.cache.get_json("search", cache_key)
            if isinstance(cached, list) and cached:
                return [str(item) for item in cached]

        url = f"https://www.google.com/search?q={quote_plus(query)}&udm=14&hl=en&gl=us&pws=0"
        result = self.fetcher.fetch(url)
        if not result.ok:
            return []

        urls = _extract_normalized_search_urls(
            result.text,
            max_results=max_results,
            blocked_hosts={"google.", "gstatic.com", "googleusercontent.com"},
        )

        if self.cache and urls:
            self.cache.set_json("search", cache_key, urls)
        if not urls:
            if _looks_like_blocked_or_consent_page(result.text):
                self.logger.warning(
                    "Search query '%s' appears blocked/consent-gated by Google.",
                    query,
                )
            self.logger.warning(
                "Search query '%s' returned 0 URL(s). Google may have returned throttled/consent markup.",
                query,
            )
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
        self.relaxed_mapping: dict[str, list[str]] = {}
        for key, value in raw.items():
            query = _normalize_query_key(str(key))
            if isinstance(value, list):
                urls = [normalize_url(str(v)) for v in value]
                clean_urls = [u for u in urls if u]
                if not clean_urls:
                    continue
                self.mapping[query] = clean_urls
                relaxed = _relaxed_query_key(query)
                if relaxed:
                    existing = self.relaxed_mapping.setdefault(relaxed, [])
                    for url in clean_urls:
                        if url not in existing:
                            existing.append(url)
        self.logger = logging.getLogger(self.__class__.__name__)

    def search(self, convention_name: str, max_results: int) -> list[str]:
        key = _normalize_query_key(convention_name)
        urls = self.mapping.get(key, [])
        if urls:
            return urls[:max_results]

        relaxed_key = _relaxed_query_key(convention_name)
        if relaxed_key:
            relaxed_urls = self.relaxed_mapping.get(relaxed_key, [])
            if relaxed_urls:
                return relaxed_urls[:max_results]

        best_score = 0.0
        best_urls: list[str] = []
        for candidate_key, candidate_urls in self.relaxed_mapping.items():
            score = _token_overlap_score(relaxed_key, candidate_key)
            if score < 0.6:
                continue
            if score > best_score:
                best_score = score
                best_urls = candidate_urls
        return best_urls[:max_results]


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
