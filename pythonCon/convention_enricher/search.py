from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import html
import re
import time
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
            self.cache.set_json("search", cache_key, [asdict(result) for result in results])
        return results

    def debug_probe(self, query: str) -> dict[str, object]:
        url = self.endpoint_builder(query)
        fetched = self.http_client.fetch(url)
        if not fetched.ok:
            return {
                "provider": self.name,
                "ok": fetched.ok,
                "status": fetched.status_code,
                "error": fetched.error,
                "html_len": len(fetched.html),
                "extracted_urls": 0,
            }
        extracted = _extract_urls(fetched.html, self.blocked_hosts)
        return {
            "provider": self.name,
            "ok": fetched.ok,
            "status": fetched.status_code,
            "error": fetched.error,
            "html_len": len(fetched.html),
            "extracted_urls": len(extracted),
        }


def _is_bad_href(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith(("#", "javascript:", "mailto:", "tel:", "data:"))


def _extract_urls(markup: str, blocked_hosts: set[str]) -> list[str]:
    href_matches = re.findall(
        r"href\s*=\s*(?:['\"]([^'\"]+)['\"]|([^\s>]+))",
        markup,
        flags=re.IGNORECASE,
    )
    hrefs = [(quoted or bare).strip() for quoted, bare in href_matches]
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
        elif "bing.com/ck/a" in href:
            parsed = urlparse(href)
            query = parse_qs(parsed.query)
            encoded_target = query.get("u", [""])[0]
            decoded_target = _decode_bing_target(encoded_target)
            if decoded_target:
                candidate = decoded_target
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


def _decode_bing_target(raw_value: str) -> str:
    if not raw_value:
        return ""
    value = unquote(raw_value)
    if value.startswith(("http://", "https://")):
        return value

    # Bing commonly wraps result URLs in urlsafe base64 with an "a1" prefix.
    if value.startswith("a1") and len(value) > 2:
        payload = value[2:]
        padding = "=" * ((4 - (len(payload) % 4)) % 4)
        try:
            decoded = base64.urlsafe_b64decode((payload + padding).encode("ascii")).decode("utf-8", errors="ignore")
        except Exception:
            return ""
        if decoded.startswith(("http://", "https://")):
            return decoded
    return ""


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

    def search_all(
        self,
        convention_name: str,
        max_results_per_provider: int,
        max_seconds: float | None = None,
    ) -> list[SearchResult]:
        query = clean_source_text(convention_name)
        results: list[SearchResult] = []
        seen_urls: set[str] = set()
        start = time.monotonic()
        for provider in self.providers:
            if max_seconds is not None and (time.monotonic() - start) >= max_seconds:
                break
            for result in provider.search(query, max_results_per_provider):
                if result.url in seen_urls:
                    continue
                seen_urls.add(result.url)
                results.append(result)
        return results
