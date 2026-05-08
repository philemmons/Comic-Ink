from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import logging
import time
from typing import Protocol
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .cache import FileCache
from .models import ExtractionOutput, FetchAttempt, FetchResult, FieldCandidate, SourceType
from .normalize import normalize_url
from .parsers import extract_candidates_from_html


class PageFetcher(Protocol):
    def fetch(self, url: str) -> FetchResult:
        ...


@dataclass(slots=True)
class UrllibPageFetcher:
    timeout_seconds: float
    retry_total: int
    retry_backoff_seconds: float
    rate_limit_per_second: float
    ssl_error_host_cooldown_seconds: float
    user_agent: str
    _logger: logging.Logger = field(init=False, repr=False)
    _session: requests.Session = field(init=False, repr=False)
    _last_request_at: float = field(init=False, repr=False, default=0.0)
    _ssl_blocked_hosts: dict[str, float] = field(init=False, repr=False, default_factory=dict)

    def __post_init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._session = requests.Session()
        retry = Retry(
            total=self.retry_total,
            connect=0,
            read=self.retry_total,
            status=self.retry_total,
            other=0,
            backoff_factor=self.retry_backoff_seconds,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "HEAD"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def fetch(self, url: str) -> FetchResult:
        interval = 1.0 / max(self.rate_limit_per_second, 0.1)
        now = time.monotonic()
        wait_seconds = interval - (now - self._last_request_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        host = urlparse(url).netloc.lower()
        blocked_until = self._ssl_blocked_hosts.get(host, 0.0)
        if host and blocked_until > now:
            remaining = blocked_until - now
            self._logger.info(
                "Skipping %s due to prior SSL handshake failure; %.1fs cooldown remaining.",
                host,
                remaining,
            )
            self._last_request_at = time.monotonic()
            return FetchResult(
                ok=False,
                url=url,
                status_code=None,
                text="",
                error=f"Host temporarily skipped after SSL handshake failure ({remaining:.1f}s remaining)",
            )

        try:
            response = self._session.get(
                url,
                timeout=self.timeout_seconds,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept-Language": "en-US,en;q=0.9",
                },
                allow_redirects=True,
            )
            self._last_request_at = time.monotonic()
            ok = 200 <= response.status_code < 400
            text = response.text if ok else ""
            error_text = "" if ok else f"HTTP {response.status_code}"
            return FetchResult(
                ok=ok,
                url=str(response.url),
                status_code=response.status_code,
                text=text,
                error=error_text or None,
            )
        except requests.exceptions.SSLError as exc:
            self._last_request_at = time.monotonic()
            if host and self.ssl_error_host_cooldown_seconds > 0:
                self._ssl_blocked_hosts[host] = self._last_request_at + self.ssl_error_host_cooldown_seconds
            self._logger.warning("Fetch failed for %s: %s", url, exc)
            return FetchResult(ok=False, url=url, status_code=None, text="", error=str(exc))
        except requests.RequestException as exc:
            self._last_request_at = time.monotonic()
            self._logger.warning("Fetch failed for %s: %s", url, exc)
            return FetchResult(ok=False, url=url, status_code=None, text="", error=str(exc))
        except Exception as exc:  # noqa: BLE001
            self._last_request_at = time.monotonic()
            self._logger.warning("Fetch failed for %s: %s", url, exc)
            return FetchResult(ok=False, url=url, status_code=None, text="", error=str(exc))


class Scraper:
    def __init__(self, fetcher: PageFetcher, cache: FileCache | None = None) -> None:
        self.fetcher = fetcher
        self.cache = cache
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch(self, url: str) -> FetchResult:
        normalized = normalize_url(url)
        if not normalized:
            return FetchResult(ok=False, url=url, status_code=None, text="", error="Invalid URL")

        if self.cache:
            cached = self.cache.get_text("html", normalized)
            if cached is not None:
                return FetchResult(ok=True, url=normalized, status_code=200, text=cached)

        result = self.fetcher.fetch(normalized)
        if result.ok and self.cache:
            self.cache.set_text("html", normalized, result.text)
        return result

    def _build_url_fallbacks(self, normalized_url: str) -> list[str]:
        parsed = urlparse(normalized_url)
        if not parsed.netloc:
            return [normalized_url]

        path = parsed.path or "/"
        query = f"?{parsed.query}" if parsed.query else ""
        fragment = f"#{parsed.fragment}" if parsed.fragment else ""
        suffix = f"{path}{query}{fragment}"

        hosts = [parsed.netloc]
        plain_host = parsed.netloc.split(":")[0]
        if "." in plain_host and plain_host != "localhost":
            if plain_host.startswith("www."):
                alt = parsed.netloc.replace("www.", "", 1)
            else:
                alt = parsed.netloc.replace(plain_host, f"www.{plain_host}", 1)
            if alt and alt not in hosts:
                hosts.append(alt)

        schemes = [parsed.scheme]
        if parsed.scheme == "https":
            schemes.append("http")
        elif parsed.scheme == "http":
            schemes.append("https")

        variants: list[str] = []
        for scheme in schemes:
            for host in hosts:
                candidate = f"{scheme}://{host}{suffix}"
                if candidate not in variants:
                    variants.append(candidate)
        return variants[:4]

    def _fetch_with_fallbacks(self, url: str, source_type: SourceType) -> tuple[FetchResult, list[FetchAttempt]]:
        normalized = normalize_url(url)
        if not normalized:
            return (
                FetchResult(ok=False, url=url, status_code=None, text="", error="Invalid URL"),
                [FetchAttempt(url=url, source_type=source_type, ok=False, status_code=None, error="Invalid URL")],
            )

        attempts: list[FetchAttempt] = []
        primary_result = self.fetch(normalized)
        attempts.append(
            FetchAttempt(
                url=normalized,
                source_type=source_type,
                ok=primary_result.ok,
                status_code=primary_result.status_code,
                error=primary_result.error or "",
            )
        )
        if primary_result.ok:
            return primary_result, attempts

        lowered_error = (primary_result.error or "").lower()
        should_try_fallback = any(
            token in lowered_error
            for token in (
                "ssl",
                "certificate",
                "hostname mismatch",
                "failed to establish a new connection",
                "connection refused",
                "max retries exceeded",
                "timed out",
            )
        )
        proxy_blocked = any(
            token in lowered_error
            for token in (
                "proxyerror",
                "unable to connect to proxy",
                "httpsconnection(host='127.0.0.1', port=9)",
                "httpconnection(host='127.0.0.1', port=9)",
            )
        )
        if proxy_blocked:
            should_try_fallback = False
        if not should_try_fallback:
            return primary_result, attempts

        for candidate in self._build_url_fallbacks(normalized):
            if candidate == normalized:
                continue
            result = self.fetch(candidate)
            attempts.append(
                FetchAttempt(
                    url=candidate,
                    source_type=source_type,
                    ok=result.ok,
                    status_code=result.status_code,
                    error=result.error or "",
                )
            )
            if result.ok:
                self.logger.info("Recovered fetch using URL fallback: %s -> %s", normalized, candidate)
                return result, attempts

        return primary_result, attempts

    def scrape_candidates(self, url: str, source_type: SourceType) -> ExtractionOutput:
        result, attempts = self._fetch_with_fallbacks(url, source_type)
        if not result.ok:
            attempted_urls = ", ".join(attempt.url for attempt in attempts)
            return ExtractionOutput(
                candidates={},
                warnings={
                    "fetch": [
                        f"Failed to fetch {url}: {result.error or 'unknown error'}",
                        f"Attempted URL variants: {attempted_urls}",
                    ]
                },
                fetch_attempts=attempts,
            )

        extracted = extract_candidates_from_html(result.text, result.url, source_type)
        candidates = defaultdict(list, extracted.candidates)
        candidates["website"].append(
            FieldCandidate(
                field_name="website",
                value=result.url,
                source_url=result.url,
                source_type=source_type,
                confidence=1.0,
                verified=True,
                reason="Fetched URL resolved successfully",
            )
        )
        return ExtractionOutput(candidates=dict(candidates), warnings=extracted.warnings, fetch_attempts=attempts)
