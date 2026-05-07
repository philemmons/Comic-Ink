from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import logging
import time
from typing import Protocol

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
    user_agent: str
    _logger: logging.Logger = field(init=False, repr=False)
    _session: requests.Session = field(init=False, repr=False)
    _last_request_at: float = field(init=False, repr=False, default=0.0)

    def __post_init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._session = requests.Session()
        retry = Retry(
            total=self.retry_total,
            connect=self.retry_total,
            read=self.retry_total,
            status=self.retry_total,
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

        try:
            response = self._session.get(
                url,
                timeout=self.timeout_seconds,
                headers={"User-Agent": self.user_agent},
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

    def scrape_candidates(self, url: str, source_type: SourceType) -> ExtractionOutput:
        result = self.fetch(url)
        attempts = [
            FetchAttempt(
                url=normalize_url(url) or url,
                source_type=source_type,
                ok=result.ok,
                status_code=result.status_code,
                error=result.error or "",
            )
        ]
        if not result.ok:
            return ExtractionOutput(
                candidates={},
                warnings={"fetch": [f"Failed to fetch {url}: {result.error or 'unknown error'}"]},
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
