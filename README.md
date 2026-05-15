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


### 05-08-26

## Convention Discovery Crawler (Python)

This repository includes a production-style convention discovery crawler under `pythonCon/convention_enricher`.

Pipeline:

`SEARCH -> DISCOVER -> CRAWL -> EXTRACT -> PRESERVE -> EXPORT`

Goal:
- gather convention/event data from authoritative sources
- preserve source wording as presented
- export only required fields

## Scope Rules

The crawler is a source gathering pipeline. It is **not** a normalization or transformation engine.

It does **not**:
- infer missing geography
- geocode
- parse or reformat dates for export
- synthesize merged values from conflicting sources

Allowed cleanup only:
- trim leading/trailing whitespace
- collapse accidental duplicated whitespace from scraping

Unknown values are exported as:
- `**`

## Input

Input file:
- `input.csv`

Input policy:
- use only column 1
- ignore all other columns
- one row = one search target
- search query is exactly the column 1 value (no appended query variants)

## Output

Output file:
- `output.csv`

Exported columns (exactly):
- `convention_name`
- `event_date`
- `event_location`
- `city`
- `state`
- `country`
- `website_url`

## Search Providers

Provider adapters are implemented for:
- Google
- Bing
- DuckDuckGo

Provider logic is swappable through the adapter layer.

## Authority and Conflict Resolution

When conflicting values exist, authority order is:
1. official convention source
2. official registration source
3. official organizer source
4. official venue source
5. trusted listing source

Higher authority wins. Values are not merged.

## Extraction Priority

Priority order:
1. Meta tags (`title`, `description`, canonical, Open Graph/social metadata)
2. Visible content (`h1/h2`, headings, schedule/registration/about/contact blocks)
3. Semantic HTML (`address`, `time`, `dl/dt/dd`, labeled blocks)
4. Structured data fallback (`JSON-LD`, microdata, schema.org Event)

Structured data is fallback/tie-breaker only.

## Crawler Boundaries and Reliability

Implemented:
- max depth
- max pages per domain
- max pages per convention
- max retries
- max runtime per convention
- max concurrency
- caching
- checkpointing/resume
- duplicate-request prevention
- robots-aware pacing
- connection/session reuse
- snapshot persistence

Crawl scope:
- capture only the site homepage/index HTML for each discovered domain
- do not follow internal links beyond the homepage

Snapshot data includes:
- raw HTML
- fetched URL
- final redirected URL
- timestamp
- content hash

## Architecture

Modules are split by responsibility:
- input loader
- search adapters
- discovery ranker
- crawler
- snapshot store
- extractor
- deduper
- exporter
- cache
- checkpoint manager
- analyzer
- learning memory (official domains)

## Setup

1. Install Python 3.11+.
2. Install dependencies:

```bash
python -m pip install -r pythonCon/requirements.txt
```

## Run

### From repo root

```bash
python -m pythonCon.convention_enricher.enrich "c:\Users\phile\Desktop\Comic-Ink\pythonCon\convention_enricher\input.csv" --output "c:\Users\phile\Desktop\Comic-Ink\pythonCon\convention_enricher\output.csv" --work-dir "c:\Users\phile\Desktop\Comic-Ink\pythonCon\.convention_crawler"
```

### Alternative (run inside `pythonCon`)

```bash
cd c:\Users\phile\Desktop\Comic-Ink\pythonCon
python -m convention_enricher.enrich "c:\Users\phile\Desktop\Comic-Ink\pythonCon\convention_enricher\input.csv" --output "c:\Users\phile\Desktop\Comic-Ink\pythonCon\convention_enricher\output.csv" --work-dir "c:\Users\phile\Desktop\Comic-Ink\pythonCon\.convention_crawler"
```

### Running from repo root, so use:

```bash
python -m pythonCon.convention_enricher.enrich "c:\Users\phile\Desktop\Comic-Ink\pythonCon\convention_enricher\input.csv" --output "c:\Users\phile\Desktop\Comic-Ink\pythonCon\convention_enricher\output.csv" --work-dir "c:\Users\phile\Desktop\Comic-Ink\pythonCon\.convention_crawler"
```

### Useful runtime controls

```bash
--max-depth
--max-pages-per-domain
--max-pages-per-convention
--max-runtime-seconds
--max-concurrency
--requests-per-second
--search-results-per-provider
--discovery-top-n
--max-search-seconds
--network-failure-threshold
--progress-every
--offset
--limit
```

## Reports

Recursive improvement artifacts are tracked in:
- `pythonCon/analysis_report.md`
- `pythonCon/CHANGELOG.md`

## Notes

- If input encoding is not UTF-8, loader fallback supports `cp1252` and `latin-1`.
- If column 1 is blank, the row is skipped as a search target.
