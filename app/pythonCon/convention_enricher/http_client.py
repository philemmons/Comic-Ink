from __future__ import annotations

from dataclasses import dataclass
import os
import threading
import time
from urllib import request as urllib_request
from urllib import error as urllib_error
from urllib import robotparser
from urllib.parse import urljoin, urlparse

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]
    HTTPAdapter = None  # type: ignore[assignment]
    Retry = None  # type: ignore[assignment]

from .models import FetchedPage
from .utils import now_utc_iso


@dataclass(slots=True)
class HttpClientConfig:
    timeout_seconds: float
    requests_per_second: float
    user_agent: str
    max_retries: int


class HttpClient:
    def __init__(self, config: HttpClientConfig) -> None:
        self.config = config
        self.session = None
        self._disable_env_proxy = self._should_disable_env_proxy()

        if requests is not None and Retry is not None and HTTPAdapter is not None:
            self.session = requests.Session()
            if self._disable_env_proxy:
                self.session.trust_env = False
            retry = Retry(
                total=max(0, config.max_retries),
                read=max(0, config.max_retries),
                connect=max(0, config.max_retries),
                status=max(0, config.max_retries),
                backoff_factor=0.4,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset({"GET", "HEAD"}),
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=retry, pool_connections=32, pool_maxsize=32)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

        self._lock = threading.Lock()
        self._last_request_monotonic = 0.0
        self._robots_cache: dict[str, robotparser.RobotFileParser | None] = {}

    def reset_robots_cache(self) -> None:
        self._robots_cache.clear()

    @staticmethod
    def _should_disable_env_proxy() -> bool:
        proxy_values = [
            os.getenv("HTTP_PROXY", ""),
            os.getenv("HTTPS_PROXY", ""),
            os.getenv("ALL_PROXY", ""),
            os.getenv("http_proxy", ""),
            os.getenv("https_proxy", ""),
            os.getenv("all_proxy", ""),
        ]
        blocked_markers = ("127.0.0.1:9", "localhost:9")
        return any(marker in value for value in proxy_values for marker in blocked_markers)

    def _pace(self) -> None:
        interval = 1.0 / max(self.config.requests_per_second, 0.1)
        with self._lock:
            now = time.monotonic()
            wait = interval - (now - self._last_request_monotonic)
            if wait > 0:
                time.sleep(wait)
            self._last_request_monotonic = time.monotonic()

    def _robot_parser_for(self, url: str) -> robotparser.RobotFileParser | None:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base in self._robots_cache:
            return self._robots_cache[base]

        robots_url = urljoin(base, "/robots.txt")
        parser = robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            req = urllib_request.Request(
                robots_url,
                headers={
                    "User-Agent": self.config.user_agent,
                    "Accept-Language": "en-US,en;q=0.9",
                },
                method="GET",
            )
            with urllib_request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                body = response.read().decode(charset, errors="replace")
            parser.parse(body.splitlines())
            self._robots_cache[base] = parser
            return parser
        except Exception:
            # Fail open when robots retrieval fails (network, SSL, DNS, etc).
            self._robots_cache[base] = None
            return None

    def is_allowed_by_robots(self, url: str) -> bool:
        parser = self._robot_parser_for(url)
        if parser is None:
            return True
        try:
            return parser.can_fetch(self.config.user_agent, url)
        except Exception:
            return True

    def fetch(self, url: str) -> FetchedPage:
        self._pace()
        if self.session is not None and requests is not None:
            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout_seconds,
                    allow_redirects=True,
                    headers={
                        "User-Agent": self.config.user_agent,
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                ok = 200 <= response.status_code < 400
                return FetchedPage(
                    requested_url=url,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    ok=ok,
                    html=response.text if ok else "",
                    fetched_at_utc=now_utc_iso(),
                    error="" if ok else f"HTTP {response.status_code}",
                )
            except requests.RequestException as exc:
                return FetchedPage(
                    requested_url=url,
                    final_url=url,
                    status_code=None,
                    ok=False,
                    html="",
                    fetched_at_utc=now_utc_iso(),
                    error=str(exc),
                )

        try:
            req = urllib_request.Request(
                url,
                headers={
                    "User-Agent": self.config.user_agent,
                    "Accept-Language": "en-US,en;q=0.9",
                },
                method="GET",
            )
            if self._disable_env_proxy:
                opener = urllib_request.build_opener(urllib_request.ProxyHandler({}))
                response_ctx = opener.open(req, timeout=self.config.timeout_seconds)
            else:
                response_ctx = urllib_request.urlopen(req, timeout=self.config.timeout_seconds)
            with response_ctx as response:
                status = int(getattr(response, "status", 200))
                final_url = str(getattr(response, "url", url))
                charset = response.headers.get_content_charset() or "utf-8"
                html = response.read().decode(charset, errors="replace")
            ok = 200 <= status < 400
            return FetchedPage(
                requested_url=url,
                final_url=final_url,
                status_code=status,
                ok=ok,
                html=html if ok else "",
                fetched_at_utc=now_utc_iso(),
                error="" if ok else f"HTTP {status}",
            )
        except urllib_error.URLError as exc:
            return FetchedPage(
                requested_url=url,
                final_url=url,
                status_code=None,
                ok=False,
                html="",
                fetched_at_utc=now_utc_iso(),
                error=str(exc),
            )
