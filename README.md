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

## Convention Enricher (Python)

The convention enricher lives in `pythonCon/convention_enricher` and runs a simple pipeline:

`INPUT (CSV) -> DUCKDUCKGO CHECK -> OUTPUT (CSV)`

## Behavior

- Uses only DuckDuckGo HTML endpoint: `https://html.duckduckgo.com/html/`
- Uses only first column from `pythonCon/input.csv`
- Ignores all other input columns
- Uses first-column value as the exact query string
- Preserves original formatting from CSV, including quotation marks
- Skips rows with empty first-column values
- Adds retry handling, timeout handling, random delays, and desktop User-Agent
- If all retries fail for a row, marks it as not found instead of crashing

## Input and Output

Input file:
- `pythonCon/input.csv`

Output file:
- `pythonCon/output.csv`

Output columns (exactly):
- `original_value`
- `search_query`
- `found`

`found` is written as:
- `TRUE`: at least one meaningful organic DuckDuckGo result container found
- `FALSE`: no meaningful organic result found (including error/block/empty cases)

## Dependencies

Install with:

```bash
python -m pip install -r pythonCon/convention_enricher/requirements.txt
```

Packages used:
- `requests`
- `beautifulsoup4`

## Run

From repo root:

```bash
python pythonCon/convention_enricher/enrich.py
```

The script prints per-row progress (`row/query/success-failure`) and summary totals when complete.
