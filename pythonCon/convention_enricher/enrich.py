from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import time

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
from .models import ConventionOutputRow
from .resolver import resolve_output
from .search import BingSearchAdapter, CompositeSearch, DuckDuckGoSearchAdapter, GoogleSearchAdapter
from .snapshot_store import SnapshotStore
from .utils import get_domain


@dataclass(slots=True)
class RunResult:
    output_csv: Path
    rows_written: int


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
    return parser


def build_config(args: argparse.Namespace) -> RuntimeConfig:
    input_csv = Path(args.input)
    output_csv = Path(args.output) if args.output else input_csv.with_name("output.csv")
    work_dir = Path(args.work_dir)

    config = RuntimeConfig(input_csv=input_csv, output_csv=output_csv, work_dir=work_dir)
    config.requests_per_second = max(0.1, float(args.requests_per_second))
    config.search_results_per_provider = max(1, int(args.search_results_per_provider))
    config.discovery_top_n = max(1, int(args.discovery_top_n))
    config.offset = max(0, int(args.offset))
    config.limit = None if args.limit is None else max(0, int(args.limit))
    config.max_search_seconds_per_convention = max(0.1, float(args.max_search_seconds))
    config.network_failure_threshold = max(1, int(args.network_failure_threshold))
    config.progress_every = max(1, int(args.progress_every))

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

    output_rows: list[ConventionOutputRow] = []
    consecutive_network_misses = 0
    offline_short_circuit = False

    for idx, convention_name in enumerate(targets, start=1):
        if checkpoint.is_completed(convention_name):
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

        search_results = []
        search_started = time.monotonic()
        for query in _query_variants(convention_name):
            if (time.monotonic() - search_started) >= config.max_search_seconds_per_convention:
                break
            query_results = search.search_all(query, config.search_results_per_provider)
            search_results.extend(query_results)

        analyzer.stats.search_results_seen += len(search_results)

        discovered = ranker.rank(convention_name, search_results)[: config.discovery_top_n]
        analyzer.stats.discovered_urls += len(discovered)

        documents = crawler.crawl(convention_name, discovered)
        analyzer.stats.crawled_pages += len(documents)
        analyzer.stats.snapshots_written += len(documents)

        evidences = []
        for document in documents:
            extracted = extract_from_document(document=document, convention_name=convention_name)
            evidences.extend(extracted.evidences)

        output = resolve_output(convention_name, evidences)
        if output.website_url != config.unknown_value:
            memory.remember(convention_name, get_domain(output.website_url))

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
    analyzer.write(config.work_dir / "analysis" / "run_stats.json")
    return RunResult(output_csv=config.output_csv, rows_written=len(output_rows))


def _query_variants(convention_name: str) -> list[str]:
    return [
        convention_name,
        f"{convention_name} official website",
        f"{convention_name} registration",
        f"{convention_name} dates",
        f"{convention_name} venue",
    ]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = build_config(args)
    result = run(config)
    print(f"output_csv={result.output_csv}")
    print(f"rows_written={result.rows_written}")


if __name__ == "__main__":
    main()
