# Comic-Ink

## “Ka-Pow! Comic Books and Pop Culture Collide.”

###### by Phillip Emmons

05-08-2017  In development

### Our story

Users will encounter are friendly splash page as they arrived at the site with some scrolling comic book covers ranging from the early fifties and up. All are welcome to browse our comic collection or North American conventions. Users will be presented with a display of the comic books available. They are welcome to sort through the collection by title creator publisher or be able to do a combination, and present the list and several orders buyer sort by function.

### Bonus

A bonus feature to all comic collectors is the ability to see if the Comic Book Creator is being headlined at one of the North American conventions by clicking on the autograph hyperlink.

### Conventions

Users travel to the convention page, they will be presented with some of the North American comic conventions available. Users are also able to sort through the conventions based on name Creator state or sort them. They also are welcome to get more information from the convention website itself.

### Admin

Users who go to the administration portion will have had to registered with Comics Ink. to continue. Once registered, they are given privileges to be able to add new conventions, see some statistics about them, and update or delete the conventions. Admin's who remove a convention should be cautious because this information is not recoverable. All new convention information entered should he be complete as possible. The update portion is very user-friendly has the information is persistent and resettable. Administrators are provided with some statistical analysis of the convention that display total attendance, average attendance, number of conventions per state, the total number of conventions, and some specific details of the highest turnout of them all.

To use the admin functionality:

### Mock Up Design

[https://github.com/philemmons/Comic-Ink/blob/master/document/mockUpDesign.pdf](https://github.com/philemmons/Comic-Ink/blob/master/document/mockUpDesign.pdf)

### ER Diagram

[https://github.com/philemmons/Comic-Ink/blob/master/document/erDiagram.pdf](https://github.com/philemmons/Comic-Ink/blob/master/document/erDiagram.pdf)

### Future Functions

###### 09-23-19

- Logout button should appear only if there is an admin logged in.
- Scalability for various browsers and mobile devices.
- Admin function to change username and password.
- Encrypt password with php password_hash function as it wil secure the database. https://stackoverflow.com/questions/24862499/correct-way-of-creating-salted-hash-password.

### 05-06-26

# Convention Enricher for Updating Conventions Data

## Project purpose
Convention Enricher is a reusable Python 3.11+ pipeline that enriches convention/event CSV records from online sources while preserving your original column order and source file. It prioritizes structured website data first, then optionally falls back to search results.

The pipeline is built for rerunnable workflows:
- it never overwrites the input CSV
- it writes a separate enriched CSV
- it writes a detailed audit CSV
- it writes timestamped logs

## Installation steps
1. Install Python 3.11 or newer.
2. Open a terminal in this project folder.
3. (Recommended) Create and activate a virtual environment.
4. Install dependencies:

```bash
python -m pip install -r pythonCon/requirements.txt
```

## CLI examples
Basic run:

```bash
python -m pythonCon.convention_enricher.enrich input.csv --year 2026 --output output.csv --audit audit.csv
```

Only process first 100 rows:

```bash
python -m pythonCon.convention_enricher.enrich input.csv --year 2026 --limit 100 --output output.csv --audit audit.csv
```

Only fill missing fields (do not refresh existing values):

```bash
python -m pythonCon.convention_enricher.enrich input.csv --year 2026 --only-missing --output output.csv --audit audit.csv
```

Dry run (no file write):

```bash
python -m pythonCon.convention_enricher.enrich input.csv --year 2026 --dry-run
```

Resume from existing output rows by `id`:

```bash
python -m pythonCon.convention_enricher.enrich input.csv --year 2026 --resume --output output.csv --audit audit.csv
```

Manual search provider results:

```bash
python -m pythonCon.convention_enricher.enrich input.csv --year 2026 --search-provider manual --manual-search-results manual_search.json --output output.csv --audit audit.csv
```

## Required environment variables
No environment variables are strictly required.

Optional overrides:
- `CONVENTION_ENRICHER_USER_AGENT`
- `CONVENTION_ENRICHER_TIMEOUT_SECONDS`
- `CONVENTION_ENRICHER_MAX_SEARCH_RESULTS`
- `CONVENTION_ENRICHER_RETRY_TOTAL`
- `CONVENTION_ENRICHER_RETRY_BACKOFF_SECONDS`
- `CONVENTION_ENRICHER_RATE_LIMIT_PER_SECOND`
- `CONVENTION_ENRICHER_SSL_ERROR_HOST_COOLDOWN_SECONDS`
- `CONVENTION_ENRICHER_SEARCH_TIME_LIMIT_SECONDS`
- `CONVENTION_ENRICHER_STOP_AFTER_FIRST_EMPTY_SEARCH_QUERY`

## Search provider setup
Supported providers:
- `google.com` (default)
- `duckduckgo_html`
- `manual`
- `none`

Provider behavior:
- `google.com` automatically falls back to `duckduckgo_html` when Google returns no usable links.
- Search uses multiple contextual query variants (name/year, official-site phrasing, location, and optional `site:` host hints).
- Search queries stop early only after consecutive empty query results (default behavior) to avoid aborting on a single bad SERP response.
- Per-row search has a time limit (default: 8 seconds) to prevent long pauses on blocked or rate-limited providers.
- Hosts with SSL handshake failures are temporarily skipped in-run (default cooldown: 1800 seconds).
- Search query and ranking logic automatically profile the input dataset (common name tokens, known host/name mappings, and frequent reusable hosts) to improve official URL selection.
- When no verifiable replacement is found for a populated field, the existing value is preserved instead of being overwritten with `**`.
- Website fetch attempts include automatic URL fallbacks (`www`/non-`www`, `https`/`http`) before marking fetch failure.

Manual provider file format (`--manual-search-results`):

```json
{
  "Doxacon": ["https://www.doxacon.org"],
  "Grand Rapids Comic-Con": ["https://www.grcomiccon.com"]
}
```

Search/extraction priority:
1. Existing website URL in the row
2. Search provider URLs by convention name

Manual provider notes:
- `manual` does not perform live web searching.
- It only reads URLs you provide in `manual_search.json`.
- It supports query-variant matching (for example, `official website` / year-suffixed query text) against your mapping keys.
- It is usually the most stable option when automated search engines throttle or block requests.

## Output CSV explanation
The output CSV:
- preserves original column order
- preserves original columns
- updates only fields selected by update rules
- writes unknown/unverified fields as `**`
- normalizes enriched dates to `YYYY-MM-DD`

## Audit CSV explanation
The audit CSV contains one row per input row with:
- row identity (`row_number`, `row_id`, `original_name`, `original_website`)
- source details (`source_used`, `fetch_status`)
- confidence level (`HIGH`, `MEDIUM`, `LOW`, `NONE`)
- changed field summaries (`fields_updated`, `fields_left_unknown`)
- value diffs (`old_values`, `new_values`)
- warning and notes fields (`warnings`, `notes`)
- timestamp (`timestamp_utc`)

## Unknown value policy using `**`
When data is unknown, unavailable, ambiguous, conflicting, low-confidence, or unverified, the field is set to `**` by default.

For date fields, vague values such as `TBD`, `Coming soon`, or `Spring 2026` are treated as ambiguous and set to `**` with an audit warning.

## Confidence levels
Candidate values include numeric confidence scores and verification state.
Audit output reports confidence tiers:
- `HIGH`
- `MEDIUM`
- `LOW`
- `NONE`

Current behavior:
- high-confidence, verified, non-conflicting values are accepted
- conflicting candidate values become unknown (`**`)
- confidence below threshold becomes unknown (`**`)

## Limitations
- HTML parsing uses regex-based heuristics, not a full browser DOM.
- Some sites block scraping or return incomplete content.
- Non-English and heavily scripted pages may reduce extraction quality.
- Status normalization is heuristic-based.
- Search result markup can change over time.

## Ethical scraping notes
- Respect each site terms of service and robots policies.
- Use reasonable request volumes and caching.
- Identify your scraper with a clear User-Agent.
- Avoid scraping private, gated, or personal data.
- Verify critical data before operational use.

## Troubleshooting
`No module named pytest`:
- install test dependencies: `python -m pip install -r pythonCon/requirements.txt`

Output path error (same as input):
- choose a different `--output` file path than the input file.

No enrichment happening:
- check website URLs in input
- run with `--verbose`
- test with `--search-provider manual` and curated URLs

Too many unknown values:
- verify source pages contain event metadata
- provide better manual search mappings
- improve source CSV website/name quality

Search provider not finding results:
- use `--search-provider manual` with explicit URLs
- check network access and site availability

Resume behavior not applied:
- confirm `--resume` is set
- confirm output CSV exists and includes matching `id` values
