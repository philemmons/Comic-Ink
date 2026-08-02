from __future__ import annotations

import csv
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

DDG_HTML_ENDPOINT = "https://html.duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_SECONDS = 12
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.2
REQUEST_DELAY_RANGE_SECONDS = (0.7, 1.5)
MAX_SEARCH_QUERIES = 10

# This script lives in pythonCon/convention_enricher/, so pythonCon root is 1 level up.
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


def contains_block_page(html: str) -> bool:
    lowered = html.lower()
    block_signals = (
        "captcha",
        "detected unusual traffic",
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


def build_snapshot_name(query: str, index: int) -> str:
    normalized = query.strip().strip("\"'").lower()
    safe = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    if not safe:
        safe = "query"
    return f"{index:04d}_{safe[:60]}"


def save_ddg_search_html(snapshot_base_name: str, html: str) -> str:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SNAPSHOTS_DIR / f"{snapshot_base_name}_ddg.html"
    output_path.write_text(html, encoding="utf-8", errors="replace")
    return str(output_path)


def query_duckduckgo(session: requests.Session, query: str, row_index: int) -> tuple[bool, str]:
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
            return False, ""

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
                return False, ""

        if response.status_code in {429, 500, 502, 503, 504}:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return False, ""

        snapshot_name = build_snapshot_name(query, row_index)
        saved_path = save_ddg_search_html(snapshot_name, response.text)

        if response.status_code != 200:
            return False, saved_path

        # Redirect-only responses or non-DDG destinations are not meaningful SERP pages.
        if "duckduckgo.com" not in urlparse(response.url).netloc.lower():
            return False, saved_path

        return has_meaningful_organic_result(response.text), saved_path

    return False, ""


def build_results(queries: Iterable[str]) -> tuple[list[RowResult], int]:
    session = requests.Session()
    # Ignore HTTP(S)_PROXY/ALL_PROXY env vars to prevent local proxy config
    # from causing false negatives in DuckDuckGo checks.
    session.trust_env = False
    results: list[RowResult] = []
    if not isinstance(queries, list):
        queries = list(queries)
    total = len(queries)
    failures = 0

    for index, query in enumerate(queries, start=1):
        found, saved_path = query_duckduckgo(session, query, index)
        results.append(RowResult(original_value=query, search_query=query, found=found))

        state = "SUCCESS" if found else "FAILURE"
        if saved_path:
            print(f"[{index}/{total}] query={query} state={state} html={saved_path}")
        else:
            print(f"[{index}/{total}] query={query} state={state}")

        if not found:
            failures += 1

        time.sleep(random.uniform(*REQUEST_DELAY_RANGE_SECONDS))

    return results, failures


def write_output_csv(output_path: Path, rows: list[RowResult]) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["original_value", "search_query", "found"])
        for row in rows:
            writer.writerow([row.original_value, row.search_query, "TRUE" if row.found else "FALSE"])


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: input.csv not found at project root: {INPUT_CSV}")
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
