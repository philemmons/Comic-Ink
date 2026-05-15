from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from .analyzer import Analyzer
from .cache import FileCache
from .checkpoint import CheckpointManager
from .config import RuntimeConfig
from .crawler import Crawler
from .discovery import DiscoveryRanker
from .exporter import CsvExporter
from .extractor import extract_from_document
from .http_client import HttpClient, HttpClientConfig
from .input_loader import InputLoader
from .memory import DomainMemory
from .models import ConventionOutputRow, SearchResult
from .resolver import resolve_output
from .search import BingSearchAdapter, CompositeSearch, DuckDuckGoSearchAdapter, GoogleSearchAdapter
from .snapshot_store import SnapshotStore
from .utils import canonicalize_url, get_domain, normalize_for_ranking, now_utc_iso, token_overlap, write_json


@dataclass(slots=True)
class RunResult:
    output_csv: Path
    rows_written: int


@dataclass(slots=True)
class BootstrapWebsite:
    name: str
    website_url: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convention discovery crawler")
    parser.add_argument("input", help="Path to input.csv")
    parser.add_argument("--output", help="Path to output.csv")
    parser.add_argument("--work-dir", default=".convention_crawler", help="Directory for cache/checkpoints/snapshots")
    parser.add_argument("--max-depth", type=int, default=1)
    parser.add_argument("--max-pages-per-domain", type=int, default=6)
    parser.add_argument("--max-pages-per-convention", type=int, default=24)
    parser.add_argument("--max-runtime-seconds", type=float, default=45.0)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--requests-per-second", type=float, default=1.5)
    parser.add_argument("--search-results-per-provider", type=int, default=8)
    parser.add_argument("--discovery-top-n", type=int, default=18)
    parser.add_argument("--offset", type=int, default=0, help="Start processing at this zero-based input index.")
    parser.add_argument("--limit", type=int, help="Process at most this many conventions from input.")
    parser.add_argument(
        "--max-search-seconds",
        type=float,
        default=12.0,
        help="Per-convention time budget for search requests.",
    )
    parser.add_argument(
        "--network-failure-threshold",
        type=int,
        default=25,
        help="After N consecutive no-network-evidence conventions, short-circuit to unknown output.",
    )
    parser.add_argument("--progress-every", type=int, default=10, help="Log progress every N conventions.")
    parser.add_argument(
        "--allow-zero-success",
        action="store_true",
        help="Allow run completion even when no non-unknown rows are produced.",
    )
    parser.add_argument(
        "--resume-checkpoint",
        action="store_true",
        help="Reuse completed rows from an existing checkpoint in the work directory.",
    )
    parser.add_argument(
        "--bootstrap-csv",
        help="Optional CSV containing known convention->website mappings used when search providers return no candidates.",
    )
    return parser


def build_config(args: argparse.Namespace) -> RuntimeConfig:
    input_csv = Path(args.input)
    output_csv = Path(args.output) if args.output else input_csv.with_name("output.csv")
    work_dir = Path(args.work_dir)
    bootstrap_csv = Path(args.bootstrap_csv) if args.bootstrap_csv else None

    config = RuntimeConfig(input_csv=input_csv, output_csv=output_csv, work_dir=work_dir, bootstrap_csv=bootstrap_csv)
    config.requests_per_second = max(0.1, float(args.requests_per_second))
    config.search_results_per_provider = max(1, int(args.search_results_per_provider))
    config.discovery_top_n = max(1, int(args.discovery_top_n))
    config.offset = max(0, int(args.offset))
    config.limit = None if args.limit is None else max(0, int(args.limit))
    config.max_search_seconds_per_convention = max(0.1, float(args.max_search_seconds))
    config.network_failure_threshold = max(1, int(args.network_failure_threshold))
    config.progress_every = max(1, int(args.progress_every))
    config.allow_zero_success = bool(args.allow_zero_success)
    config.resume_checkpoint = bool(args.resume_checkpoint)

    config.crawl_bounds.max_depth = max(0, int(args.max_depth))
    config.crawl_bounds.max_pages_per_domain = max(1, int(args.max_pages_per_domain))
    config.crawl_bounds.max_pages_per_convention = max(1, int(args.max_pages_per_convention))
    config.crawl_bounds.max_runtime_seconds_per_convention = max(1.0, float(args.max_runtime_seconds))
    config.crawl_bounds.max_concurrency = max(1, int(args.max_concurrency))
    return config


def run(config: RuntimeConfig) -> RunResult:
    loader = InputLoader()
    all_targets = loader.load(config.input_csv)
    if config.offset >= len(all_targets):
        targets = []
    else:
        targets = all_targets[config.offset :]
    if config.limit is not None:
        targets = targets[: config.limit]

    analyzer = Analyzer()
    analyzer.stats.conventions_total = len(targets)

    cache = FileCache(config.cache_dir)
    memory = DomainMemory(config.memory_path)
    checkpoint = CheckpointManager(config.checkpoint_path)
    snapshot_store = SnapshotStore(config.snapshots_dir)

    http_client = HttpClient(
        HttpClientConfig(
            timeout_seconds=config.request_timeout_seconds,
            requests_per_second=config.requests_per_second,
            user_agent=config.user_agent,
            max_retries=config.crawl_bounds.max_retries,
        )
    )
    preflight_ok, preflight_error = _preflight_network(http_client)

    search = CompositeSearch(
        providers=[
            GoogleSearchAdapter(http_client=http_client, cache=cache),
            BingSearchAdapter(http_client=http_client, cache=cache),
            DuckDuckGoSearchAdapter(http_client=http_client, cache=cache),
        ]
    )
    ranker = DiscoveryRanker(domain_memory=memory)
    crawler = Crawler(http_client=http_client, cache=cache, snapshot_store=snapshot_store, bounds=config.crawl_bounds)
    exporter = CsvExporter()
    bootstrap_rows = _load_bootstrap_rows(config.bootstrap_csv)

    output_rows: list[ConventionOutputRow] = []
    consecutive_network_misses = 0
    offline_short_circuit = False
    successful_rows = 0

    for idx, convention_name in enumerate(targets, start=1):
        if config.resume_checkpoint and checkpoint.is_completed(convention_name):
            previous = checkpoint.get_output(convention_name)
            if previous is not None:
                output_rows.append(previous)
                analyzer.stats.conventions_completed += 1
                continue

        if offline_short_circuit:
            output = ConventionOutputRow(convention_name=convention_name)
            checkpoint.mark_completed(convention_name, output)
            output_rows.append(output)
            analyzer.stats.conventions_completed += 1
            continue

        search_results = search.search_all(convention_name, config.search_results_per_provider)

        analyzer.stats.search_results_seen += len(search_results)

        discovered = ranker.rank(convention_name, search_results)[: config.discovery_top_n]
        if not discovered and bootstrap_rows:
            bootstrap_urls = _bootstrap_urls_for_convention(convention_name, bootstrap_rows)
            bootstrap_results = [
                SearchResult(provider="bootstrap", query=convention_name, url=url, title="", snippet="")
                for url in bootstrap_urls
            ]
            discovered = ranker.rank(convention_name, bootstrap_results)[: config.discovery_top_n]
        analyzer.stats.discovered_urls += len(discovered)

        homepage_seed = discovered[:1]
        documents = crawler.crawl(convention_name, homepage_seed)
        analyzer.stats.crawled_pages += len(documents)
        analyzer.stats.snapshots_written += len(documents)

        evidences = []
        for document in documents:
            extracted = extract_from_document(document=document, convention_name=convention_name)
            evidences.extend(extracted.evidences)

        output = resolve_output(convention_name, evidences)
        if output.website_url != config.unknown_value:
            memory.remember(convention_name, get_domain(output.website_url))
        if _row_has_success(output, config.unknown_value):
            successful_rows += 1

        if not search_results and not documents:
            consecutive_network_misses += 1
            if consecutive_network_misses >= config.network_failure_threshold:
                offline_short_circuit = True
        else:
            consecutive_network_misses = 0

        checkpoint.mark_completed(convention_name, output)
        output_rows.append(output)
        analyzer.stats.conventions_completed += 1
        if idx % config.progress_every == 0:
            print(f"progress={idx}/{len(targets)} short_circuit={offline_short_circuit}")

    memory.save()
    exporter.export(config.output_csv, output_rows)
    diagnostics = {
        "timestamp_utc": now_utc_iso(),
        "preflight_network_ok": preflight_ok,
        "preflight_network_error": preflight_error,
        "successful_rows": successful_rows,
        "total_rows": len(output_rows),
        "search_results_seen": analyzer.stats.search_results_seen,
        "discovered_urls": analyzer.stats.discovered_urls,
        "crawled_pages": analyzer.stats.crawled_pages,
        "snapshots_written": analyzer.stats.snapshots_written,
    }
    analysis_dir = config.work_dir / "analysis"
    analyzer.write(analysis_dir / "run_stats.json")
    write_json(analysis_dir / "run_diagnostics.json", diagnostics)

    if successful_rows == 0 and not config.allow_zero_success:
        raise RuntimeError(
            "Run produced zero successful rows. Network/provider access appears unavailable. "
            f"Preflight ok={preflight_ok}, error='{preflight_error}'. "
            "See run_diagnostics.json for details. "
            "Use --allow-zero-success to bypass this guard."
        )
    return RunResult(output_csv=config.output_csv, rows_written=len(output_rows))


def _preflight_network(http_client: HttpClient) -> tuple[bool, str]:
    probe_urls = [
        "https://www.google.com/",
        "https://www.bing.com/",
        "https://html.duckduckgo.com/html/?q=test",
    ]
    errors: list[str] = []
    for url in probe_urls:
        fetched = http_client.fetch(url)
        if fetched.ok:
            return True, ""
        if fetched.error:
            errors.append(f"{url}: {fetched.error}")
    return False, " | ".join(errors[:3])


def _row_has_success(row: ConventionOutputRow, unknown: str) -> bool:
    return any(
        value != unknown
        for value in (
            row.event_date,
            row.event_location,
            row.city,
            row.state,
            row.country,
            row.website_url,
        )
    )


def _load_bootstrap_rows(path: Path | None) -> list[BootstrapWebsite]:
    if path is None or not path.exists():
        return []
    rows: list[BootstrapWebsite] = []
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    raw_name = (row.get("conName") or row.get("convention_name") or "").strip()
                    raw_site = (row.get("website") or row.get("website_url") or "").strip()
                    site = canonicalize_url(raw_site)
                    if raw_name and site:
                        rows.append(BootstrapWebsite(name=raw_name, website_url=site))
            if rows:
                return rows
        except UnicodeDecodeError:
            continue
    return rows


def _bootstrap_urls_for_convention(convention_name: str, rows: list[BootstrapWebsite]) -> list[str]:
    target = normalize_for_ranking(convention_name)
    if not target:
        return []
    scored: list[tuple[float, str]] = []
    for row in rows:
        candidate = normalize_for_ranking(row.name)
        score = token_overlap(target, candidate)
        if candidate == target:
            score = 1.0
        if score >= 0.60:
            scored.append((score, row.website_url))
    scored.sort(key=lambda item: item[0], reverse=True)
    out: list[str] = []
    seen: set[str] = set()
    for _, url in scored:
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
        if len(out) >= 4:
            break
    return out


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = build_config(args)
    result = run(config)
    print(f"output_csv={result.output_csv}")
    print(f"rows_written={result.rows_written}")


if __name__ == "__main__":
    main()
