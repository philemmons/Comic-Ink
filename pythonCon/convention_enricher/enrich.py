from __future__ import annotations

import csv
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup, Tag

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

# This script lives in pythonCon/convention_enricher/, so pythonCon root is 1 level up.
PYTHONCON_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PYTHONCON_ROOT / "input.csv"
OUTPUT_CSV = PYTHONCON_ROOT / "output.csv"


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
    rows_processed: int = 0
    found_true: int = 0
    found_false: int = 0


def read_first_column_values(csv_path: Path) -> tuple[list[str], RunStats]:
    stats = RunStats()
    values: list[str] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row_index, row in enumerate(reader, start=1):
            stats.rows_seen += 1

            first_value = row[0] if row else ""
            if row_index == 1 and first_value.strip().lower() in {"convention", "query", "search_query"}:
                stats.header_rows_skipped += 1
                continue

            # We only skip truly empty/whitespace values in the first column.
            if first_value.strip() == "":
                stats.empty_rows_skipped += 1
                continue

            # Keep the first-column value exactly as parsed from CSV.
            values.append(first_value)

    return values, stats


def parse_redirect_href(href: str) -> str:
    if not href:
        return ""
    lowered = href.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        parsed = urlparse(href)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            encoded = parse_qs(parsed.query).get("uddg", [""])[0]
            if encoded:
                return unquote(encoded)
        return href

    if href.startswith("/l/"):
        parsed = urlparse(href)
        encoded = parse_qs(parsed.query).get("uddg", [""])[0]
        if encoded:
            return unquote(encoded)

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


def candidate_result_containers(soup: BeautifulSoup) -> list[Tag]:
    selectors = (
        "div#links div.result",
        "div.result",
        "article.result",
        "div.web-result",
        "div.results_links",
    )
    seen: set[int] = set()
    containers: list[Tag] = []
    for selector in selectors:
        for tag in soup.select(selector):
            tag_id = id(tag)
            if tag_id in seen:
                continue
            seen.add(tag_id)
            containers.append(tag)
    return containers


def is_ad_container(container: Tag) -> bool:
    classes = [cls.lower() for cls in container.get("class", [])]
    if any(cls.startswith("result--ad") for cls in classes):
        return True
    if any("sponsored" in cls for cls in classes):
        return True
    return any(cls in {"ad", "ads", "badge--ad"} for cls in classes)


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

    for container in candidate_result_containers(soup):
        if is_ad_container(container):
            continue

        # A meaningful organic result needs at least one plausible result link.
        for anchor in container.select("a.result__a, h2 a, a[href]"):
            href = anchor.get("href", "")
            resolved = parse_redirect_href(href)
            if resolved.startswith("http://") or resolved.startswith("https://"):
                return True

    return False


def query_duckduckgo(session: requests.Session, query: str) -> bool:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
            return False

        if response.status_code in {429, 500, 502, 503, 504}:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            return False

        if response.status_code != 200:
            return False

        # Redirect-only responses or non-DDG destinations are not meaningful SERP pages.
        if "duckduckgo.com" not in urlparse(response.url).netloc.lower():
            return False

        return has_meaningful_organic_result(response.text)

    return False


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
        found = query_duckduckgo(session, query)
        results.append(RowResult(original_value=query, search_query=query, found=found))

        state = "SUCCESS" if found else "FAILURE"
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
    print(
        "Loaded input rows: "
        f"seen={stats.rows_seen}, "
        f"header_skipped={stats.header_rows_skipped}, "
        f"empty_skipped={stats.empty_rows_skipped}, "
        f"queries={len(queries)}"
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
