from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import re

from .audit import write_audit_csv
from .cache import FileCache
from .confidence import resolve_field_value
from .config import ColumnConfig, RuntimeConfig, apply_env_overrides
from .csv_io import read_csv_rows, read_existing_rows_by_key, write_csv_rows
from .models import AuditRecord, ConfidenceLevel, ExtractionOutput, FieldCandidate, FetchAttempt, RunStats
from .normalize import is_missing, normalize_url, parse_year
from .scraper import Scraper, UrllibPageFetcher
from .search import (
    ChainedSearchProvider,
    DuckDuckGoHtmlSearchProvider,
    ManualSearchProvider,
    NoopSearchProvider,
    SearchProvider,
)
from .utils import clean_string, setup_logging


CANONICAL_FIELDS = [
    "conName",
    "start_date",
    "end_date",
    "year",
    "event_location",
    "city",
    "state",
    "state_abrev",
    "country",
    "website",
    "status",
    "notes",
]


@dataclass(slots=True)
class RunResult:
    output_csv: Path
    audit_csv: Path
    log_file: Path
    stats: RunStats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m convention_enricher.enrich",
        description="Enrich convention/event CSV values using website-first scraping with search fallback.",
    )
    parser.add_argument("input", help="Path to input CSV")
    parser.add_argument("--year", type=int, default=RuntimeConfig.default_year(), help="Target convention year.")
    parser.add_argument("--output", help="Path to enriched CSV output.")
    parser.add_argument("--audit", help="Path to audit CSV output.")
    parser.add_argument("--limit", type=int, help="Process at most N rows from input.")
    parser.add_argument("--dry-run", action="store_true", help="Run enrichment but do not write files.")
    parser.add_argument("--only-missing", action="store_true", help="Only fill missing values.")
    parser.add_argument("--resume", action="store_true", help="Reuse rows from existing output CSV by id.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs.")
    parser.add_argument("--cache-dir", default=".cache/convention_enricher", help="Directory for fetch/search cache.")
    parser.add_argument(
        "--search-provider",
        choices=["duckduckgo_html", "manual", "none"],
        default="duckduckgo_html",
        help="Search provider used when website field does not resolve enough fields.",
    )
    parser.add_argument(
        "--manual-search-results",
        help="Path to JSON map: convention name -> list of website URLs.",
    )
    return parser


def parse_runtime_config(args: argparse.Namespace) -> RuntimeConfig:
    input_csv = Path(args.input)
    output_csv = Path(args.output) if args.output else input_csv.with_name(f"{input_csv.stem}.enriched.csv")
    audit_csv = Path(args.audit) if args.audit else input_csv.with_name(f"{input_csv.stem}.audit.csv")

    config = RuntimeConfig(
        input_csv=input_csv,
        output_csv=output_csv,
        audit_csv=audit_csv,
        year=args.year,
        limit=args.limit,
        dry_run=args.dry_run,
        only_missing=args.only_missing,
        resume=args.resume,
        verbose=args.verbose,
        cache_dir=Path(args.cache_dir),
        search_provider=args.search_provider,
        manual_search_results=Path(args.manual_search_results) if args.manual_search_results else None,
    )
    return apply_env_overrides(config)


def build_column_map(columns: ColumnConfig) -> dict[str, str]:
    return {
        "conName": columns.name_column,
        "start_date": columns.start_date_column,
        "end_date": columns.end_date_column,
        "year": columns.year_column,
        "event_location": columns.venue_column,
        "city": columns.city_column,
        "state": columns.state_column,
        "state_abrev": columns.state_abbrev_column,
        "country": columns.country_column,
        "website": columns.website_column,
        "status": columns.status_column,
        "notes": columns.notes_column,
    }


def build_search_provider(config: RuntimeConfig, fetcher: UrllibPageFetcher, cache: FileCache) -> SearchProvider:
    providers: list[SearchProvider] = []

    if config.manual_search_results:
        providers.append(ManualSearchProvider(str(config.manual_search_results)))

    if config.search_provider == "duckduckgo_html":
        providers.append(DuckDuckGoHtmlSearchProvider(fetcher=fetcher, cache=cache))
    elif config.search_provider == "manual" and not providers:
        raise ValueError("--search-provider manual requires --manual-search-results.")
    elif config.search_provider == "none":
        providers.append(NoopSearchProvider())

    if not providers:
        providers.append(NoopSearchProvider())
    if len(providers) == 1:
        return providers[0]
    return ChainedSearchProvider(providers)


def should_update_field(
    field_name: str,
    row: dict[str, str],
    column_map: dict[str, str],
    year_target: int,
    only_missing: bool,
) -> bool:
    column = column_map[field_name]
    value = row.get(column, "")
    if is_missing(value):
        return True
    if only_missing:
        return False

    row_year = parse_year(row.get(column_map["year"], ""))
    if row_year is None or row_year >= year_target:
        return False

    stale_fields = {
        "start_date",
        "end_date",
        "year",
        "event_location",
        "city",
        "state",
        "state_abrev",
        "country",
        "website",
        "status",
        "notes",
    }
    return field_name in stale_fields


def merge_extraction(
    target_candidates: dict[str, list[FieldCandidate]],
    target_warnings: dict[str, list[str]],
    target_attempts: list[FetchAttempt],
    incoming: ExtractionOutput,
) -> None:
    for field_name, values in incoming.candidates.items():
        target_candidates.setdefault(field_name, []).extend(values)
    for field_name, messages in incoming.warnings.items():
        current = target_warnings.setdefault(field_name, [])
        for message in messages:
            if message not in current:
                current.append(message)
    target_attempts.extend(incoming.fetch_attempts)


def build_search_queries(convention_name: str, year: int) -> list[str]:
    base = clean_string(convention_name)
    if not base:
        return []
    return [
        f"{base} {year}",
        f"{base} official website",
        f"{base} convention dates venue",
    ]


def rank_official_url(url: str, convention_name: str) -> int:
    lowered = url.lower()
    score = 0
    if lowered.startswith("https://"):
        score += 1
    convention_tokens = [tok for tok in convention_name.lower().replace("-", " ").split() if len(tok) > 2]
    if any(tok in lowered for tok in convention_tokens):
        score += 2
    noisy_hosts = ["facebook.com", "instagram.com", "x.com", "twitter.com", "youtube.com", "eventbrite."]
    if any(host in lowered for host in noisy_hosts):
        score -= 2
    return score


def confidence_rank(level: ConfidenceLevel) -> int:
    return {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}[level]


def summarize_fetch_status(attempts: list[FetchAttempt]) -> str:
    if not attempts:
        return "no_fetch"
    ok_count = sum(1 for attempt in attempts if attempt.ok)
    fail_count = len(attempts) - ok_count
    if ok_count and not fail_count:
        return "ok"
    if ok_count and fail_count:
        return "partial"
    return "failed"


def normalize_date_output(raw_value: str, fallback_year: int | None, unknown_value: str) -> str:
    value = clean_string(raw_value)
    if not value or value == unknown_value:
        return unknown_value if value == unknown_value else value
    if re.match(r"^(19|20)\d{2}-\d{2}-\d{2}$", value):
        return value

    patterns = ["%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%m/%d/%Y"]
    parse_candidates = [value]
    if fallback_year and re.match(r"^[A-Za-z]{3,9}\s+\d{1,2}$", value):
        parse_candidates.append(f"{value}, {fallback_year}")

    for candidate in parse_candidates:
        for fmt in patterns:
            try:
                dt = datetime.strptime(candidate, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return value


def run_enrichment(config: RuntimeConfig) -> RunResult:
    if not config.input_csv.exists():
        raise FileNotFoundError(f"Input CSV does not exist: {config.input_csv}")
    if config.output_csv.resolve() == config.input_csv.resolve():
        raise ValueError("Output CSV cannot be the same file as input CSV.")
    if config.audit_csv.resolve() == config.input_csv.resolve():
        raise ValueError("Audit CSV cannot be the same file as input CSV.")

    log_path = setup_logging(config.verbose, config.cache_dir / "logs")
    logger = logging.getLogger("convention_enricher.enrich")

    try:
        headers, input_rows = read_csv_rows(config.input_csv)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to read input CSV '{config.input_csv}': {exc}") from exc

    if config.limit is not None:
        input_rows = input_rows[: max(config.limit, 0)]
    stats = RunStats(rows_total=len(input_rows))

    fetcher = UrllibPageFetcher(
        timeout_seconds=config.timeout_seconds,
        retry_total=config.retry_total,
        retry_backoff_seconds=config.retry_backoff_seconds,
        rate_limit_per_second=config.rate_limit_per_second,
        user_agent=config.user_agent,
    )
    cache = FileCache(config.cache_dir)
    scraper = Scraper(fetcher=fetcher, cache=cache)
    search_provider = build_search_provider(config, fetcher, cache)

    column_map = build_column_map(config.columns)
    if column_map["website"] not in headers:
        column_map["website"] = headers[-1]

    resumed_rows: dict[str, dict[str, str]] = {}
    id_column = config.columns.id_column
    if config.resume:
        resumed_rows = read_existing_rows_by_key(config.output_csv, id_column)
        logger.info("Resume mode enabled. Loaded %s previously enriched row(s).", len(resumed_rows))

    enriched_rows: list[dict[str, str]] = []
    audit_records: list[AuditRecord] = []

    for index, original_row in enumerate(input_rows, start=1):
        reference_row = dict(original_row)
        row = dict(original_row)
        row_id = clean_string(row.get(id_column, ""))
        original_name = clean_string(row.get(column_map["conName"], ""))
        original_website = clean_string(row.get(column_map["website"], ""))

        if config.resume and row_id and row_id in resumed_rows:
            resumed_row = resumed_rows[row_id]
            enriched_rows.append(resumed_row)
            stats.rows_resumed += 1
            audit_records.append(
                AuditRecord(
                    row_number=index,
                    row_id=row_id,
                    original_name=original_name,
                    original_website=original_website,
                    source_used="resume",
                    fetch_status="resumed",
                    confidence="HIGH",
                    fields_updated="",
                    fields_left_unknown="",
                    old_values="{}",
                    new_values="{}",
                    warnings="",
                    notes="Reused existing enriched row via --resume.",
                )
            )
            continue

        candidates_by_field: dict[str, list[FieldCandidate]] = defaultdict(list)
        warnings_by_field: dict[str, list[str]] = defaultdict(list)
        fetch_attempts: list[FetchAttempt] = []
        fetched_urls: set[str] = set()

        website = normalize_url(row.get(column_map["website"], ""))
        if website:
            merge_extraction(
                candidates_by_field,
                warnings_by_field,
                fetch_attempts,
                scraper.scrape_candidates(website, "website"),
            )
            fetched_urls.add(website)

        fields_needing_update = [
            field
            for field in CANONICAL_FIELDS
            if column_map[field] in headers and should_update_field(field, reference_row, column_map, config.year, config.only_missing)
        ]

        unresolved_fields = [field for field in fields_needing_update if not candidates_by_field.get(field)]

        if unresolved_fields and original_name:
            ranked_urls: list[tuple[int, str]] = []
            seen_urls: set[str] = set(fetched_urls)
            for query in build_search_queries(original_name, config.year):
                for url in search_provider.search(query, config.max_search_results):
                    normalized_url = normalize_url(url)
                    if not normalized_url or normalized_url in seen_urls:
                        continue
                    seen_urls.add(normalized_url)
                    ranked_urls.append((rank_official_url(normalized_url, original_name), normalized_url))

            ranked_urls.sort(key=lambda item: item[0], reverse=True)
            for _, normalized_url in ranked_urls[: config.max_search_results]:
                if normalized_url in fetched_urls:
                    continue
                fetched_urls.add(normalized_url)
                merge_extraction(
                    candidates_by_field,
                    warnings_by_field,
                    fetch_attempts,
                    scraper.scrape_candidates(normalized_url, "search"),
                )

        updated_fields: list[str] = []
        unknown_fields: list[str] = []
        old_values: dict[str, str] = {}
        new_values: dict[str, str] = {}
        row_warnings: list[str] = []
        best_row_confidence: ConfidenceLevel = "NONE"

        for field_name in CANONICAL_FIELDS:
            column_name = column_map[field_name]
            if column_name not in headers:
                continue

            old_value = clean_string(row.get(column_name, ""))
            needs_update = should_update_field(field_name, reference_row, column_map, config.year, config.only_missing)
            field_candidates = candidates_by_field.get(field_name, [])

            if not needs_update:
                continue

            resolved, reason, level = resolve_field_value(field_name, field_candidates, unknown_value=config.unknown_value)
            row[column_name] = resolved
            if confidence_rank(level) > confidence_rank(best_row_confidence):
                best_row_confidence = level

            if resolved == config.unknown_value:
                unknown_fields.append(field_name)
                stats.unknown_cells += 1
                explicit = warnings_by_field.get(field_name, [])
                generic_fetch = warnings_by_field.get("fetch", [])
                lowered = reason.lower()
                derived = []
                if "ambiguous" in lowered:
                    derived.append(f"{field_name}: ambiguous candidates")
                if "no candidates" in lowered:
                    derived.append(f"{field_name}: no verifiable candidates")
                row_warnings.extend(explicit + derived + generic_fetch)
            else:
                if resolved != old_value:
                    updated_fields.append(field_name)
                    stats.updated_cells += 1

            if resolved != old_value:
                old_values[field_name] = old_value
                new_values[field_name] = resolved

        row_year = parse_year(row.get(column_map["year"], ""))
        for date_field in ("start_date", "end_date"):
            column_name = column_map[date_field]
            if column_name not in headers:
                continue
            row[column_name] = normalize_date_output(row.get(column_name, ""), row_year, config.unknown_value)

        source_used_values = sorted({attempt.source_type for attempt in fetch_attempts if attempt.ok})
        source_used = ";".join(source_used_values) if source_used_values else "none"

        audit_records.append(
            AuditRecord(
                row_number=index,
                row_id=row_id,
                original_name=original_name,
                original_website=original_website,
                source_used=source_used,
                fetch_status=summarize_fetch_status(fetch_attempts),
                confidence=best_row_confidence,
                fields_updated=";".join(updated_fields),
                fields_left_unknown=";".join(unknown_fields),
                old_values=json.dumps(old_values, ensure_ascii=False, sort_keys=True),
                new_values=json.dumps(new_values, ensure_ascii=False, sort_keys=True),
                warnings=" | ".join(dict.fromkeys(row_warnings)),
                notes=clean_string(row.get(column_map["notes"], "")),
            )
        )

        enriched_rows.append(row)
        stats.rows_processed += 1

    logger.info(
        "Run complete: rows_total=%s rows_processed=%s rows_resumed=%s updated_cells=%s unknown_cells=%s",
        stats.rows_total,
        stats.rows_processed,
        stats.rows_resumed,
        stats.updated_cells,
        stats.unknown_cells,
    )

    if config.dry_run:
        logger.info("Dry-run enabled. No output files were written.")
    else:
        try:
            write_csv_rows(config.output_csv, headers, enriched_rows)
            write_audit_csv(config.audit_csv, audit_records)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to write output files: {exc}") from exc
        logger.info("Enriched CSV written: %s", config.output_csv)
        logger.info("Audit CSV written: %s", config.audit_csv)

    return RunResult(output_csv=config.output_csv, audit_csv=config.audit_csv, log_file=log_path, stats=stats)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = parse_runtime_config(args)
    result = run_enrichment(config)

    print(f"Rows total: {result.stats.rows_total}")
    print(f"Rows processed: {result.stats.rows_processed}")
    print(f"Rows resumed: {result.stats.rows_resumed}")
    print(f"Updated cells: {result.stats.updated_cells}")
    print(f"Unknown cells: {result.stats.unknown_cells}")
    print(f"Enriched CSV: {result.output_csv}")
    print(f"Audit CSV: {result.audit_csv}")
    print(f"Log file: {result.log_file}")


if __name__ == "__main__":
    main()
