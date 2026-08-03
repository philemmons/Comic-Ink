from __future__ import annotations

import base64
import csv
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

DDG_HTML_ENDPOINT = "https://html.duckduckgo.com/html/"
GOOGLE_SEARCH_ENDPOINT = "https://www.google.com/search"
BING_SEARCH_ENDPOINT = "https://www.bing.com/search"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_SECONDS = 12
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.2
QUERY_DELAY_RANGE_SECONDS = (2.0, 4.0)
PROVIDER_SWITCH_DELAY_RANGE_SECONDS = (0.8, 1.6)
PROVIDER_COOLDOWN_RANGE_SECONDS = (45.0, 90.0)
MAX_PROVIDER_FAILURES_BEFORE_COOLDOWN = 2
MAX_CONSECUTIVE_QUERIES_PER_PROVIDER = 2
MAX_SEARCH_QUERIES = 10

# This script lives in app/pythonCon/convention_enricher/, so pythonCon root is 1 level up.
PYTHONCON_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PYTHONCON_ROOT / "input.csv"
OUTPUT_CSV = PYTHONCON_ROOT / "output.csv"
SNAPSHOTS_DIR = Path(__file__).resolve().parent / "snapshots"


@dataclass(slots=True)
class RowResult:
    original_value: str
    search_query: str
    found: bool


@dataclass(slots=True)
class SearchAttempt:
    found: bool
    saved_path: str
    provider: str
    blocked: bool = False
    attempted_providers: tuple[str, ...] = ()


@dataclass(slots=True)
class ProviderState:
    name: str
    consecutive_queries: int = 0
    consecutive_failures: int = 0
    cooldown_until: float = 0.0
    total_attempts: int = 0


SearchFunction = Callable[[requests.Session, str, int], SearchAttempt]


@dataclass(slots=True)
class RunStats:
    rows_seen: int = 0
    header_rows_skipped: int = 0
    empty_rows_skipped: int = 0
    duplicate_rows_skipped: int = 0
    rows_processed: int = 0
    found_true: int = 0
    found_false: int = 0


def read_first_column_values(csv_path: Path) -> tuple[list[str], RunStats]:
    stats = RunStats()
    values: list[str] = []
    seen_values: set[str] = set()

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row_index, row in enumerate(reader, start=1):
            stats.rows_seen += 1

            # Use the raw first-column value exactly as read by csv.
            raw_value = row[0] if row else ""
            if row_index == 1 and raw_value.strip().lower() in {"convention", "query", "search_query"}:
                stats.header_rows_skipped += 1
                continue

            # Only skip truly empty values.
            if raw_value == "":
                stats.empty_rows_skipped += 1
                continue

            if raw_value in seen_values:
                stats.duplicate_rows_skipped += 1
                continue
            seen_values.add(raw_value)
            values.append(raw_value)

    return values, stats


def prefer_https(url: str) -> str:
    if url.startswith("http://"):
        return "https://" + url[len("http://") :]
    return url


def parse_redirect_href(href: str) -> str:
    if not href:
        return ""
    lowered = href.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        parsed = urlparse(href)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            encoded = parse_qs(parsed.query).get("uddg", [""])[0]
            if encoded:
                return prefer_https(unquote(encoded))
        return prefer_https(href)

    if href.startswith("/l/"):
        parsed = urlparse(href)
        encoded = parse_qs(parsed.query).get("uddg", [""])[0]
        if encoded:
            return prefer_https(unquote(encoded))

    return ""


def parse_google_redirect_href(href: str) -> str:
    if not href:
        return ""
    if href.startswith("/url?"):
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        return prefer_https(params.get("q", [""])[0] or params.get("url", [""])[0])
    if href.startswith(("http://", "https://")):
        return prefer_https(href)
    return ""


def decode_bing_target(raw_value: str) -> str:
    if not raw_value:
        return ""
    value = unquote(raw_value)
    if value.startswith(("http://", "https://")):
        return prefer_https(value)

    if value.startswith("a1") and len(value) > 2:
        payload = value[2:]
        padding = "=" * ((4 - (len(payload) % 4)) % 4)
        try:
            decoded = base64.urlsafe_b64decode((payload + padding).encode("ascii")).decode("utf-8", errors="ignore")
        except Exception:
            return ""
        if decoded.startswith(("http://", "https://")):
            return prefer_https(decoded)
    return ""


def parse_bing_redirect_href(href: str) -> str:
    if not href:
        return ""
    if href.startswith(("http://", "https://")) and "bing.com/ck/a" not in href:
        return prefer_https(href)
    if "bing.com/ck/a" in href:
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        return decode_bing_target(params.get("u", [""])[0])
    return ""


def contains_block_page(html: str) -> bool:
    lowered = html.lower()
    block_signals = (
        "anomaly-modal",
        "bots use duckduckgo too",
        "captcha",
        "confirm this search was made by a human",
        "detected unusual traffic",
        "please complete the following challenge",
        "verify you are human",
        "access denied",
        "forbidden",
        "robot check",
    )
    return any(signal in lowered for signal in block_signals)


def has_meaningful_organic_result(html: str) -> bool:
    if not html.strip() or contains_block_page(html):
        return False

    soup = BeautifulSoup(html, "html.parser")
    no_result_markers = (
        "no results.",
        "no results found",
        "did not match any documents",
    )
    page_text = soup.get_text(" ", strip=True).lower()
    if any(marker in page_text for marker in no_result_markers):
        return False

    # Keep parsing simple and defensive: find likely result links and
    # make sure they resolve to real external HTTP(S) URLs.
    anchors = soup.select("a.result__a, h2 a.result__a, h2 a, a[href]")
    for anchor in anchors:
        href = anchor.get("href", "")
        resolved = parse_redirect_href(href)
        if not resolved.startswith("https://"):
            continue
        host = urlparse(resolved).netloc.lower()
        if not host or host.endswith("duckduckgo.com"):
            continue
        classes = " ".join(anchor.get("class", [])).lower()
        if "ad" in classes or "sponsored" in classes:
            continue
        return True

    return False


def has_meaningful_google_result(html: str) -> bool:
    if not html.strip():
        return False

    soup = BeautifulSoup(html, "html.parser")
    no_result_markers = (
        "did not match any documents",
        "no results found",
    )
    page_text = soup.get_text(" ", strip=True).lower()
    if any(marker in page_text for marker in no_result_markers):
        return False

    anchors = soup.select("a[href]")
    for anchor in anchors:
        href = (anchor.get("href") or "").strip()
        if not href:
            continue

        resolved = ""
        if href.startswith("/url?"):
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            resolved = prefer_https(params.get("q", [""])[0] or params.get("url", [""])[0])
        elif href.startswith(("http://", "https://")):
            resolved = prefer_https(href)

        if not resolved.startswith("https://"):
            continue

        host = urlparse(resolved).netloc.lower()
        if not host or any(marker in host for marker in ("google.", "gstatic.com", "googleusercontent.com")):
            continue
        return True

    return False


def has_meaningful_bing_result(html: str) -> bool:
    if not html.strip() or contains_block_page(html):
        return False

    soup = BeautifulSoup(html, "html.parser")
    no_result_markers = (
        "there are no results for",
        "did not match any documents",
        "no results found",
    )
    page_text = soup.get_text(" ", strip=True).lower()
    if any(marker in page_text for marker in no_result_markers):
        return False

    anchors = soup.select("a[href]")
    for anchor in anchors:
        href = (anchor.get("href") or "").strip()
        resolved = parse_bing_redirect_href(href)
        if not resolved.startswith("https://"):
            continue

        host = urlparse(resolved).netloc.lower()
        if not host or any(marker in host for marker in ("bing.com", "microsoft.com")):
            continue
        return True

    return False


def build_snapshot_name(query: str, index: int) -> str:
    normalized = query.strip().strip("\"'").lower()
    safe = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    if not safe:
        safe = "query"
    return f"{index:04d}_{safe[:60]}"


def save_search_html(snapshot_base_name: str, provider: str, html: str) -> str:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SNAPSHOTS_DIR / f"{snapshot_base_name}_{provider}.html"
    output_path.write_text(html, encoding="utf-8", errors="replace")
    return str(output_path)


def save_ddg_search_html(snapshot_base_name: str, html: str) -> str:
    return save_search_html(snapshot_base_name, "ddg", html)


def save_google_search_html(snapshot_base_name: str, html: str) -> str:
    return save_search_html(snapshot_base_name, "google", html)


def save_bing_search_html(snapshot_base_name: str, html: str) -> str:
    return save_search_html(snapshot_base_name, "bing", html)


def query_duckduckgo(session: requests.Session, query: str, row_index: int) -> SearchAttempt:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.7,*/*;q=0.6",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://duckduckgo.com/",
    }
    payload = {"q": query}

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            response = session.post(
                DDG_HTML_ENDPOINT,
                headers=headers,
                data=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=True,
            )
        except requests.RequestException:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return SearchAttempt(found=False, saved_path="", provider="duckduckgo")

        # Some environments are blocked on POST. Try GET fallback before fail.
        if response.status_code == 403:
            try:
                response = session.get(
                    DDG_HTML_ENDPOINT,
                    headers=headers,
                    params=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    allow_redirects=True,
                )
            except requests.RequestException:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue
                return SearchAttempt(found=False, saved_path="", provider="duckduckgo", blocked=True)

        if response.status_code in {429, 500, 502, 503, 504}:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return SearchAttempt(
                found=False,
                saved_path="",
                provider="duckduckgo",
                blocked=response.status_code == 429,
            )

        snapshot_name = build_snapshot_name(query, row_index)
        saved_path = save_ddg_search_html(snapshot_name, response.text)

        blocked = contains_block_page(response.text)
        if blocked:
            return SearchAttempt(found=False, saved_path=saved_path, provider="duckduckgo", blocked=True)

        if response.status_code != 200:
            return SearchAttempt(
                found=False,
                saved_path=saved_path,
                provider="duckduckgo",
                blocked=response.status_code in {403, 429},
            )

        # Redirect-only responses or non-DDG destinations are not meaningful SERP pages.
        if "duckduckgo.com" not in urlparse(response.url).netloc.lower():
            return SearchAttempt(found=False, saved_path=saved_path, provider="duckduckgo")

        return SearchAttempt(
            found=has_meaningful_organic_result(response.text),
            saved_path=saved_path,
            provider="duckduckgo",
        )

    return SearchAttempt(found=False, saved_path="", provider="duckduckgo")


def query_google(session: requests.Session, query: str, row_index: int) -> SearchAttempt:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.7,*/*;q=0.6",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    params = {"q": query, "hl": "en", "gl": "us", "pws": "0"}

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            response = session.get(
                GOOGLE_SEARCH_ENDPOINT,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=True,
            )
        except requests.RequestException:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return SearchAttempt(found=False, saved_path="", provider="google")

        if response.status_code in {429, 500, 502, 503, 504}:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return SearchAttempt(found=False, saved_path="", provider="google")

        snapshot_name = build_snapshot_name(query, row_index)
        saved_path = save_google_search_html(snapshot_name, response.text)

        if response.status_code != 200:
            return SearchAttempt(found=False, saved_path=saved_path, provider="google")

        if "google." not in urlparse(response.url).netloc.lower():
            return SearchAttempt(found=False, saved_path=saved_path, provider="google")

        return SearchAttempt(
            found=has_meaningful_google_result(response.text),
            saved_path=saved_path,
            provider="google",
        )

    return SearchAttempt(found=False, saved_path="", provider="google")


def query_bing(session: requests.Session, query: str, row_index: int) -> SearchAttempt:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.7,*/*;q=0.6",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.bing.com/",
    }
    params = {"q": query, "setlang": "en-us"}

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            response = session.get(
                BING_SEARCH_ENDPOINT,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=True,
            )
        except requests.RequestException:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return SearchAttempt(found=False, saved_path="", provider="bing")

        if response.status_code in {429, 500, 502, 503, 504}:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return SearchAttempt(
                found=False,
                saved_path="",
                provider="bing",
                blocked=response.status_code == 429,
            )

        snapshot_name = build_snapshot_name(query, row_index)
        saved_path = save_bing_search_html(snapshot_name, response.text)

        blocked = contains_block_page(response.text)
        if blocked:
            return SearchAttempt(found=False, saved_path=saved_path, provider="bing", blocked=True)

        if response.status_code != 200:
            return SearchAttempt(
                found=False,
                saved_path=saved_path,
                provider="bing",
                blocked=response.status_code in {403, 429},
            )

        if "bing.com" not in urlparse(response.url).netloc.lower():
            return SearchAttempt(found=False, saved_path=saved_path, provider="bing")

        return SearchAttempt(
            found=has_meaningful_bing_result(response.text),
            saved_path=saved_path,
            provider="bing",
        )

    return SearchAttempt(found=False, saved_path="", provider="bing")


class SearchRotationStrategy:
    def __init__(
        self,
        provider_queries: dict[str, SearchFunction],
        provider_order: tuple[str, ...] = ("google", "bing", "duckduckgo"),
    ) -> None:
        self.provider_queries = provider_queries
        self.provider_order = provider_order
        self.provider_states = {name: ProviderState(name=name) for name in provider_order}
        self.primary_index = 0

    def _provider_names_from(self, start_index: int) -> list[str]:
        names = list(self.provider_order)
        return names[start_index:] + names[:start_index]

    def _active_names(self, now: float) -> list[str]:
        return [name for name in self.provider_order if self.provider_states[name].cooldown_until <= now]

    def _advance_primary(self, now: float) -> None:
        for offset in range(1, len(self.provider_order) + 1):
            candidate_index = (self.primary_index + offset) % len(self.provider_order)
            candidate_name = self.provider_order[candidate_index]
            if self.provider_states[candidate_name].cooldown_until <= now:
                self.primary_index = candidate_index
                return
        earliest_name = min(self.provider_order, key=lambda name: self.provider_states[name].cooldown_until)
        self.primary_index = self.provider_order.index(earliest_name)

    def providers_for_query(self) -> list[str]:
        now = time.monotonic()
        primary_name = self.provider_order[self.primary_index]
        primary_state = self.provider_states[primary_name]
        if (
            primary_state.cooldown_until > now
            or primary_state.consecutive_queries >= MAX_CONSECUTIVE_QUERIES_PER_PROVIDER
        ):
            self._advance_primary(now)
            primary_name = self.provider_order[self.primary_index]

        ordered = self._provider_names_from(self.primary_index)
        active = [name for name in ordered if self.provider_states[name].cooldown_until <= now]
        if active:
            return active

        earliest_name = min(ordered, key=lambda name: self.provider_states[name].cooldown_until)
        return [earliest_name]

    def record_attempt(self, provider_name: str, attempt: SearchAttempt) -> None:
        now = time.monotonic()
        state = self.provider_states[provider_name]
        state.total_attempts += 1

        if attempt.blocked:
            state.consecutive_failures += 1
            state.consecutive_queries = 0
            state.cooldown_until = now + random.uniform(*PROVIDER_COOLDOWN_RANGE_SECONDS)
            if provider_name == self.provider_order[self.primary_index]:
                self._advance_primary(now)
            return

        if attempt.found:
            state.consecutive_failures = 0
            state.cooldown_until = 0.0
            for other_name, other_state in self.provider_states.items():
                if other_name == provider_name:
                    other_state.consecutive_queries += 1
                else:
                    other_state.consecutive_queries = 0
            self.primary_index = self.provider_order.index(provider_name)
            return

        state.consecutive_failures += 1
        state.consecutive_queries = 0
        if state.consecutive_failures >= MAX_PROVIDER_FAILURES_BEFORE_COOLDOWN:
            state.cooldown_until = now + random.uniform(*PROVIDER_COOLDOWN_RANGE_SECONDS)
            if provider_name == self.provider_order[self.primary_index]:
                self._advance_primary(now)


def query_search(
    session: requests.Session,
    query: str,
    row_index: int,
    strategy: SearchRotationStrategy,
) -> SearchAttempt:
    attempted_providers: list[str] = []
    last_attempt: SearchAttempt | None = None
    provider_names = strategy.providers_for_query()

    for position, provider_name in enumerate(provider_names):
        attempt = strategy.provider_queries[provider_name](session, query, row_index)
        attempted_providers.append(provider_name)
        attempt = SearchAttempt(
            found=attempt.found,
            saved_path=attempt.saved_path,
            provider=attempt.provider,
            blocked=attempt.blocked,
            attempted_providers=tuple(attempted_providers),
        )
        strategy.record_attempt(provider_name, attempt)
        last_attempt = attempt
        if attempt.found:
            return attempt
        if position < len(provider_names) - 1:
            time.sleep(random.uniform(*PROVIDER_SWITCH_DELAY_RANGE_SECONDS))

    if last_attempt is not None:
        return last_attempt
    return SearchAttempt(found=False, saved_path="", provider="", attempted_providers=tuple())


def build_results(queries: Iterable[str]) -> tuple[list[RowResult], int]:
    session = requests.Session()
    # Ignore HTTP(S)_PROXY/ALL_PROXY env vars to prevent local proxy config
    # from causing false negatives in DuckDuckGo checks.
    session.trust_env = False
    strategy = SearchRotationStrategy(
        provider_queries={
            "google": query_google,
            "bing": query_bing,
            "duckduckgo": query_duckduckgo,
        }
    )
    results: list[RowResult] = []
    if not isinstance(queries, list):
        queries = list(queries)
    total = len(queries)
    failures = 0

    for index, query in enumerate(queries, start=1):
        attempt = query_search(session, query, index, strategy)
        results.append(RowResult(original_value=query, search_query=query, found=attempt.found))

        state = "SUCCESS" if attempt.found else "FAILURE"
        tried = "->".join(attempt.attempted_providers) if attempt.attempted_providers else attempt.provider
        if attempt.saved_path:
            print(
                f"[{index}/{total}] query={query} providers={tried} final_provider={attempt.provider} "
                f"state={state} html={attempt.saved_path}"
            )
        else:
            print(f"[{index}/{total}] query={query} providers={tried} final_provider={attempt.provider} state={state}")

        if not attempt.found:
            failures += 1

        time.sleep(random.uniform(*QUERY_DELAY_RANGE_SECONDS))

    return results, failures


def write_output_csv(output_path: Path, rows: list[RowResult]) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["original_value", "search_query", "found"])
        for row in rows:
            writer.writerow([row.original_value, row.search_query, "TRUE" if row.found else "FALSE"])


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: input.csv not found at pythonCon root: {INPUT_CSV}")
        return 1

    queries, stats = read_first_column_values(INPUT_CSV)
    queries = queries[:MAX_SEARCH_QUERIES]
    print(
        "Loaded input rows: "
        f"seen={stats.rows_seen}, "
        f"header_skipped={stats.header_rows_skipped}, "
        f"empty_skipped={stats.empty_rows_skipped}, "
        f"duplicate_skipped={stats.duplicate_rows_skipped}, "
        f"queries={len(queries)} "
        f"(limit={MAX_SEARCH_QUERIES})"
    )

    results, failures = build_results(queries)
    write_output_csv(OUTPUT_CSV, results)

    stats.rows_processed = len(results)
    stats.found_true = sum(1 for row in results if row.found)
    stats.found_false = sum(1 for row in results if not row.found)

    print("Run complete:")
    print(f"  output_file={OUTPUT_CSV}")
    print(f"  rows_processed={stats.rows_processed}")
    print(f"  found_true={stats.found_true}")
    print(f"  found_false={stats.found_false}")
    print(f"  request_failures={failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
