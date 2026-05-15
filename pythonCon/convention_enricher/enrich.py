from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil

from .analyzer import Analyzer
from .cache import FileCache
from .config import RuntimeConfig
from .exporter import CsvExporter
from .http_client import HttpClient, HttpClientConfig
from .input_loader import InputLoader
from .models import AnalyzerStats, ConventionOutputRow, SearchResult
from .search import (
    CompositeSearch,
    GoogleSearchAdapter,
    HtmlSearchProvider,
)
from .utils import now_utc_iso, token_overlap, write_json


@dataclass(slots=True)
class RunResult:
    output_csv: Path
    rows_written: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convention discovery crawler")
    parser.add_argument("input", help="Path to input.csv")
    parser.add_argument("--output", help="Path to output.csv")
    parser.add_argument("--work-dir", default=".convention_crawler", help="Directory for cache and analysis outputs")
    parser.add_argument("--requests-per-second", type=float, default=1.5)
    parser.add_argument("--search-results-per-provider", type=int, default=8)
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
        help="After N consecutive no-search-result conventions, short-circuit to unknown output.",
    )
    parser.add_argument("--progress-every", type=int, default=10, help="Log progress every N conventions.")
    parser.add_argument(
        "--quiet-steps",
        action="store_true",
        help="Disable detailed per-convention step logs and investigation output.",
    )
    parser.add_argument(
        "--allow-zero-success",
        action="store_true",
        help="Allow run completion even when no non-unknown rows are produced.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="HTTP retry count for search provider requests.",
    )
    return parser


def build_config(args: argparse.Namespace) -> RuntimeConfig:
    input_csv = Path(args.input)
    output_csv = Path(args.output) if args.output else input_csv.with_name("output.csv")
    work_dir = Path(args.work_dir)

    config = RuntimeConfig(input_csv=input_csv, output_csv=output_csv, work_dir=work_dir)
    config.requests_per_second = max(0.1, float(args.requests_per_second))
    config.search_results_per_provider = max(1, int(args.search_results_per_provider))
    config.offset = max(0, int(args.offset))
    config.limit = None if args.limit is None else max(0, int(args.limit))
    config.max_search_seconds_per_convention = max(0.1, float(args.max_search_seconds))
    config.network_failure_threshold = max(1, int(args.network_failure_threshold))
    config.progress_every = max(1, int(args.progress_every))
    config.allow_zero_success = bool(args.allow_zero_success)
    config.show_steps = not bool(args.quiet_steps)
    config.max_retries = max(0, int(args.max_retries))
    return config


def run(config: RuntimeConfig) -> RunResult:
    _log_step(
        config.show_steps,
        f"step=run_config mode=baseline_search_only cache_policy=reset_each_run work_dir={config.work_dir}",
    )
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

    if config.cache_dir.exists():
        shutil.rmtree(config.cache_dir, ignore_errors=True)
    cache = FileCache(config.cache_dir)

    http_client = HttpClient(
        HttpClientConfig(
            timeout_seconds=config.request_timeout_seconds,
            requests_per_second=config.requests_per_second,
            user_agent=config.user_agent,
            max_retries=config.max_retries,
        )
    )
    preflight_ok, preflight_error = _preflight_network(http_client)

    search = CompositeSearch(
        providers=[
            GoogleSearchAdapter(http_client=http_client, cache=cache),
        ]
    )
    exporter = CsvExporter()

    output_rows: list[ConventionOutputRow] = []
    consecutive_network_misses = 0
    offline_short_circuit = False
    successful_rows = 0

    for idx, convention_name in enumerate(targets, start=1):
        _log_step(config.show_steps, f"step=convention_start idx={idx}/{len(targets)} name={convention_name}")
        if offline_short_circuit:
            _log_step(config.show_steps, "step=short_circuit_active action=write_unknown_row")
            output = ConventionOutputRow(convention_name=convention_name)
            output_rows.append(output)
            analyzer.stats.conventions_completed += 1
            continue

        _log_step(config.show_steps, "step=search_start")
        search_results = search.search_all(
            convention_name,
            config.search_results_per_provider,
            max_seconds=config.max_search_seconds_per_convention,
        )
        _log_step(config.show_steps, f"step=search_done results={len(search_results)}")
        analyzer.stats.search_results_seen += len(search_results)
        analyzer.stats.discovered_urls += len(search_results)

        output = _resolve_search_only_output(convention_name, search_results)
        _log_step(config.show_steps, f"step=search_only_resolve website={output.website_url}")
        if _row_has_success(output, config.unknown_value):
            successful_rows += 1
        _log_step(
            config.show_steps,
            f"step=resolve_done website={output.website_url} success={_row_has_success(output, config.unknown_value)}",
        )

        if not search_results:
            consecutive_network_misses += 1
            _log_step(
                config.show_steps,
                f"step=no_network_evidence miss_streak={consecutive_network_misses}/{config.network_failure_threshold}",
            )
            _investigate_convention_failure(config.show_steps, convention_name, search)
            if consecutive_network_misses >= config.network_failure_threshold:
                offline_short_circuit = True
                _log_step(config.show_steps, "step=short_circuit_enabled reason=network_miss_threshold")
        else:
            consecutive_network_misses = 0

        output_rows.append(output)
        analyzer.stats.conventions_completed += 1
        if idx % config.progress_every == 0:
            print(f"progress={idx}/{len(targets)} short_circuit={offline_short_circuit}")

    exporter.export(config.output_csv, output_rows)
    diagnostics = {
        "timestamp_utc": now_utc_iso(),
        "preflight_network_ok": preflight_ok,
        "preflight_network_error": preflight_error,
        "successful_rows": successful_rows,
        "total_rows": len(output_rows),
        "search_results_seen": analyzer.stats.search_results_seen,
        "discovered_urls": analyzer.stats.discovered_urls,
    }
    analysis_dir = config.work_dir / "analysis"
    analyzer.write(analysis_dir / "run_stats.json")
    write_json(analysis_dir / "run_diagnostics.json", diagnostics)

    if successful_rows == 0 and not config.allow_zero_success:
        _log_step(config.show_steps, "step=run_failure_investigation_start")
        _investigate_run_failure(config.show_steps, targets, search, analyzer.stats)
        raise RuntimeError(
            "Run produced zero successful rows in baseline search mode. "
            f"Preflight ok={preflight_ok}, error='{preflight_error}'. "
            "See run_diagnostics.json for details. "
            "Use --allow-zero-success to bypass this guard."
        )
    return RunResult(output_csv=config.output_csv, rows_written=len(output_rows))


def _log_step(enabled: bool, message: str) -> None:
    if enabled:
        print(message)


def _investigate_convention_failure(enabled: bool, convention_name: str, search: CompositeSearch) -> None:
    if not enabled:
        return
    print(f"investigate=convention_no_results name={convention_name}")
    query = convention_name.strip()
    if not query:
        print("investigate=skip reason=empty_query")
        return
    for provider in search.providers:
        if not isinstance(provider, HtmlSearchProvider):
            print(f"investigate=provider name={provider.name} status=unsupported_provider_type")
            continue
        probe = provider.debug_probe(query)
        print(
            "investigate=provider "
            f"name={provider.name} ok={probe.get('ok')} status={probe.get('status')} "
            f"html_len={probe.get('html_len')} extracted_urls={probe.get('extracted_urls')} "
            f"error={probe.get('error')}"
        )


def _investigate_run_failure(
    enabled: bool,
    targets: list[str],
    search: CompositeSearch,
    stats: AnalyzerStats,
) -> None:
    if not enabled:
        return
    print(
        "investigate=run_summary "
        f"search_results_seen={stats.search_results_seen} discovered_urls={stats.discovered_urls} "
        "mode=baseline_search_only"
    )
    if targets:
        _investigate_convention_failure(enabled, targets[0], search)


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


def _resolve_search_only_output(convention_name: str, search_results: list[SearchResult]) -> ConventionOutputRow:
    output = ConventionOutputRow(convention_name=convention_name)
    if not search_results:
        return output
    chosen = _choose_best_search_result(convention_name, search_results)
    output.website_url = chosen.url if chosen else output.website_url
    return output


def _choose_best_search_result(convention_name: str, search_results: list[SearchResult]) -> SearchResult | None:
    if not search_results:
        return None
    low_value_markers = (
        "merriam-webster.com",
        "dictionary.",
        "cambridge.org",
        "oxfordlearnersdictionaries.com",
        "wikipedia.org",
    )
    best: SearchResult | None = None
    best_score = float("-inf")
    for result in search_results:
        score = token_overlap(convention_name, result.url) * 100.0
        url_l = result.url.lower()
        if any(marker in url_l for marker in low_value_markers):
            score -= 25.0
        if any(marker in url_l for marker in ("comic", "con", "expo", "event", "tickets", "register")):
            score += 12.0
        if score > best_score:
            best_score = score
            best = result
    return best


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = build_config(args)
    result = run(config)
    print(f"output_csv={result.output_csv}")
    print(f"rows_written={result.rows_written}")


if __name__ == "__main__":
    main()
