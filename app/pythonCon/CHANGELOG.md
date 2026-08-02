# CHANGELOG

## 3.1.0 - Production Crawler Overhaul Finalization

### Added
- End-to-end crawler workflow: SEARCH -> DISCOVER -> CRAWL -> EXTRACT -> PRESERVE -> EXPORT.
- Swappable search adapters:
  - Google
  - Bing
  - DuckDuckGo
- Discovery ranker with domain trust ordering and filtering.
- Bounded crawler with depth/page/runtime/retry/concurrency limits.
- Snapshot store for raw HTML replay + metadata/hash records.
- Checkpoint resume support and persisted official-domain memory.
- Anti-freeze execution controls (`offset`, `limit`, search time budget, failure circuit breaker, progress heartbeats).

### Changed
- Input reads only column 1 from `input.csv`.
- Output exports only:
  - `convention_name`
  - `event_date`
  - `event_location`
  - `city`
  - `state`
  - `country`
  - `website_url`
- Unknown value standardized to `**`.
- Extraction now preserves source wording with only allowed whitespace cleanup.
- Canonical website extraction now supports `<link rel="canonical">` and social URL metadata.
- Date selection now uses combined content blob scoring and confidence-based tie-breaking.

### Removed / Disallowed Behavior
- Export-side normalization/transformation of source truth.
- Date parsing/format conversion/range computation for exported values.
- Inferred location synthesis/geocoding/heuristic splitting.
- Multi-source value merging for conflicts.

### Internal Quality
- Typed models and focused modules across pipeline stages.
- Internal provenance retained per evidence item (URL/title/layer/selector/authority/confidence).
- Updated behavior-focused tests and smoke validation path.
