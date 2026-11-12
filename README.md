# Job Watcher

![tests](https://github.com/YOUR-USERNAME/job-watcher/actions/workflows/tests.yml/badge.svg)

A tool that watches the job market every day. It reads the open positions of 22 employers from their applicant tracking system boards (public JSON, no login), compares each day with the days before, records what is new and what is gone, and publishes the result to a website.

- Live site: https://YOUR-USERNAME.github.io/job-watcher/
- Role watched: **data and financial analyst** roles (the title rule is below). Every posting the boards return is kept, not only the ones in the role.

## Files

| File | What it does |
|---|---|
| `sources.json` | The employers watched: name, display name, applicant tracking system, board token |
| `watcher/convert.py` | Converts each system's JSON to the common columns; holds the title rule |
| `watcher/history.py` | Builds `data/history.csv` from the raw files alone |
| `watcher/status.py` | Builds the contents of `data/status.json` |
| `watcher/issue.py` | Builds the daily issue text and opens, updates and closes the GitHub Issues |
| `watcher/pipeline.py` | The daily run: fetch, save raw files, build history, write status |
| `tests/` | The pytest suite (converters, title rule, first-seen / last-seen / removed logic, pipeline) |
| `pytest.ini`, `requirements.txt` | Test settings and Python dependencies |
| `.github/workflows/daily.yml` | Runs the pipeline once a day, commits the data, opens the issue |
| `.github/workflows/tests.yml` | Runs the tests on every push |
| `data/raw/<date>/<source>.json.gz` | What each source returned that day (compressed). `_results.json` records the result of every source for that day |
| `data/history.csv` | One row per posting: first seen, last seen, status, removed date |
| `data/status.json` | Describes the latest run |
| `index.html` | Today page: last run, source status, four counts, new and removed postings |
| `browse.html` | Browse page: open postings with role switch, filters, search, sort, apply links, starred shortlist |
| `market.html` | Market page: six sections computed in the browser from the history file |
| `style.css`, `app.js`, `charts.js`, `today.js`, `browse.js`, `market.js` | Shared look, data loading, SVG charts, and page logic |
| `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png` | Make the site installable and usable offline |

## Sources

Every board returns JSON to a request with no login. No board in this list returns more than 5,000 postings, so none needs a search term (the pipeline prints a warning if one ever does).

| Employer | Source name | Applicant tracking system | Board token |
|---|---|---|---|
| Stripe | stripe | Greenhouse | `stripe` |
| Robinhood | robinhood | Greenhouse | `robinhood` |
| Coinbase | coinbase | Greenhouse | `coinbase` |
| Airbnb | airbnb | Greenhouse | `airbnb` |
| Affirm | affirm | Greenhouse | `affirm` |
| Chime | chime | Greenhouse | `chime` |
| Brex | brex | Greenhouse | `brex` |
| Marqeta | marqeta | Greenhouse | `marqeta` |
| Carta | carta | Greenhouse | `carta` |
| Betterment | betterment | Greenhouse | `betterment` |
| Gusto | gusto | Greenhouse | `gusto` |
| Upstart | upstart | Greenhouse | `upstart` |
| Dropbox | dropbox | Greenhouse | `dropbox` |
| Databricks | databricks | Greenhouse | `databricks` |
| Twilio | twilio | Greenhouse | `twilio` |
| Figma | figma | Greenhouse | `figma` |
| Plaid | plaid | Lever | `plaid` |
| Palantir | palantir | Lever | `palantir` |
| Spotify | spotify | Lever | `spotify` |
| Ramp | ramp | Ashby | `ramp` |
| Notion | notion | Ashby | `notion` |
| OpenAI | openai | Ashby | `openai` |

## Title rule

A posting is **in role** when its title contains the word *analyst* (or *analysts*) **and** at least one of: *data*, *financial*, *finance*, *FP&A*, *business intelligence*, *BI*. Matching ignores case and works on whole words, so "Metadata Analyst" does not match "data". The rule is `in_role()` in `watcher/convert.py`.

## Build the history file from the raw files

```
python -m watcher.history
```

This reads every `data/raw/<date>/<source>.json.gz` in date order and rewrites `data/history.csv` from scratch. Running it again gives the same file.

## Other commands

```
pip install -r requirements.txt
python -m pytest              # run the tests
python -m watcher.pipeline --check   # test every source, write nothing
python -m watcher.pipeline    # a full run for today (UTC)
```

## How a day is recorded

1. Each source is requested. A source that fails writes no raw file that day; its result (ok, count, error) is still recorded in `_results.json` and shown on the Today page.
2. The history is rebuilt from all raw files. A posting seen for the first time gets that day as first seen. A posting listed that day gets that day as last seen. An open posting is marked removed when its source has a raw file for that day and no longer lists it. A removed posting that is listed again is open again, with its removed date cleared and its first-seen date unchanged.
3. `data/status.json` is written, the data is committed, and an issue titled with the date lists the new and removed postings. The previous day's issue is closed.

A second run on the same day replaces that day's raw files, rebuilds the history, and updates that day's issue, so each day counts once.
