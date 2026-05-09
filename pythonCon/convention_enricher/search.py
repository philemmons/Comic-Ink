from __future__ import annotations

from dataclasses import dataclass
import html
import re
from typing import Callable, Protocol
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

from .cache import FileCache
from .http_client import HttpClient
from .models import SearchResult
from .utils import canonicalize_url, clean_source_text


class SearchProvider(Protocol):
    name: str

    def search(self, query: str, max_results: int) -> list[SearchResult]:
        ...


@dataclass(slots=True)
class HtmlSearchProvider:
    name: str
    endpoint_builder: Callable[[str], str]
    blocked_hosts: set[str]
    http_client: HttpClient
    cache: FileCache | None = None

    def search(self, query: str, max_results: int) -> list[SearchResult]:
        if not query.strip():
            return []
        cache_key = f"{self.name}:{query}:{max_results}"
        if self.cache:
            raw = self.cache.get_json("search", cache_key)
            if isinstance(raw, list):
                parsed = [SearchResult(**item) for item in raw if isinstance(item, dict)]
                if parsed:
                    return parsed

        url = self.endpoint_builder(query)
        fetched = self.http_client.fetch(url)
        if not fetched.ok:
            return []

        urls = _extract_urls(fetched.html, self.blocked_hosts)
        results: list[SearchResult] = []
        for item in urls:
            results.append(
                SearchResult(
                    provider=self.name,
                    query=query,
                    url=item,
                    title="",
                    snippet="",
                )
            )
            if len(results) >= max_results:
                break

        if self.cache and results:
            self.cache.set_json("search", cache_key, [result.__dict__ for result in results])
        return results


def _is_bad_href(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("#", "javascript:", "mailto:", "tel:", "data:"))


def _extract_urls(markup: str, blocked_hosts: set[str]) -> list[str]:
    hrefs = re.findall(r"href\s*=\s*['\"]([^'\"]+)['\"]", markup, flags=re.IGNORECASE)
    out: list[str] = []
    seen: set[str] = set()
    for raw in hrefs:
        href = html.unescape(raw.strip())
        if not href or _is_bad_href(href):
            continue

        candidate = href
        if href.startswith("/url?"):
            parsed = urlparse(href)
            query = parse_qs(parsed.query)
            candidate = query.get("q", [""])[0] or query.get("url", [""])[0]
        elif "uddg=" in href:
            parsed = urlparse(href)
            decoded = parse_qs(parsed.query).get("uddg", [""])[0]
            candidate = unquote(decoded) if decoded else candidate
        elif href.startswith("//"):
            candidate = f"https:{href}"

        normalized = canonicalize_url(candidate)
        if not normalized:
            continue
        host = urlparse(normalized).netloc.lower()
        if any(marker in host for marker in blocked_hosts):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


class GoogleSearchAdapter(HtmlSearchProvider):
    def __init__(self, http_client: HttpClient, cache: FileCache | None = None) -> None:
        super().__init__(
            name="google",
            endpoint_builder=lambda q: f"https://www.google.com/search?q={quote_plus(q)}&hl=en&gl=us&pws=0",
            blocked_hosts={"google.", "gstatic.com", "googleusercontent.com"},
            http_client=http_client,
            cache=cache,
        )


class BingSearchAdapter(HtmlSearchProvider):
    def __init__(self, http_client: HttpClient, cache: FileCache | None = None) -> None:
        super().__init__(
            name="bing",
            endpoint_builder=lambda q: f"https://www.bing.com/search?q={quote_plus(q)}&setlang=en-us",
            blocked_hosts={"bing.com", "microsoft.com"},
            http_client=http_client,
            cache=cache,
        )


class DuckDuckGoSearchAdapter(HtmlSearchProvider):
    def __init__(self, http_client: HttpClient, cache: FileCache | None = None) -> None:
        super().__init__(
            name="duckduckgo",
            endpoint_builder=lambda q: f"https://html.duckduckgo.com/html/?q={quote_plus(q)}",
            blocked_hosts={"duckduckgo.com"},
            http_client=http_client,
            cache=cache,
        )


class CompositeSearch:
    def __init__(self, providers: list[SearchProvider]) -> None:
        self.providers = providers

    def search_all(self, convention_name: str, max_results_per_provider: int) -> list[SearchResult]:
        query = clean_source_text(convention_name)
        results: list[SearchResult] = []
        seen_urls: set[str] = set()
        for provider in self.providers:
            for result in provider.search(query, max_results_per_provider):
                if result.url in seen_urls:
                    continue
                seen_urls.add(result.url)
                results.append(result)
        return results
