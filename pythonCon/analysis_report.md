# Analysis Report

## Objective
Implement a production-grade convention discovery crawler pipeline:

SEARCH -> DISCOVER -> CRAWL -> EXTRACT -> PRESERVE -> EXPORT

with strict source-truth preservation and output constrained to:
- convention_name
- event_date
- event_location
- city
- state
- country
- website_url

Unknown value: `**`

## PASS 1 - Major Logic Flaws
- Replaced enrichment/normalization-first flow with source-gathering pipeline modules.
- Enforced input rule: use only column 1 from `input.csv`.
- Enforced output rule: export only the 7 required fields.
- Removed export-side date parsing/format conversion/inference behavior.
- Removed inference-heavy location synthesis behavior; kept explicit labeled/isolated extraction.
- Implemented source authority conflict resolution (single winning source, no merging).

## PASS 2 - Efficiency / Crawl Optimization
- Added pluggable provider adapters for Google, Bing, DuckDuckGo.
- Added broad discovery ranking with trust ordering and low-trust filtering.
- Added bounded crawl controls: depth/domain/pages/runtime/retries/concurrency.
- Added session reuse + connection pooling (when requests is present).
- Added robots-aware pacing checks before fetch.
- Added request/result caching and duplicate-request prevention.
- Added URL/final URL/content-fingerprint dedupe.
- Added snapshot persistence (raw HTML + fetched/final URL + timestamp + hash).
- Added checkpointing/resume and official-domain learning memory.
- Added anti-freeze operational controls:
  - offset/limit chunking
  - per-convention search time budget
  - network-failure circuit breaker
  - periodic progress logging

## PASS 3 - Cleanup / Maintainability
- Refactored into focused typed modules:
  - input_loader, search, discovery, crawler, snapshot_store, extractor, deduper,
    exporter, cache, checkpoint, analyzer, memory, resolver, config, models.
- Tightened extraction priority order:
  1. meta tags (incl canonical link + social metadata)
  2. visible content blocks
  3. semantic HTML blocks
  4. structured metadata fallback
- Improved date phrase selection with combined content blob scoring and confidence tie-breaks.
- Added encoding fallback for robust CSV loading (`utf-8-sig`, `cp1252`, `latin-1`).
- Kept provenance in internal evidence records (URL/title/layer/selector/authority/confidence).

## Validation Summary
- Module compile checks passed for updated pipeline files.
- CLI smoke execution passed with bounded-run configuration.
- Output schema verified as exact required 7 columns.
