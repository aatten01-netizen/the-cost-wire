# The Cost Wire

A weekly input-cost brief for Midwest farmers (fertilizer, fuel, feed, cash rent, land values).

- **BRIEF.md** — what we're building and why
- **PLAN.md** — build steps
- **LOG.md** — what's been done
- **CLAUDE.md** — instructions for Claude

## Folders
- `src/costwire/` — the Python code
- `data/` — clean CSV/JSON from the weekly data pulls
- `briefs/` — the weekly briefs (Markdown + HTML)
- `site/` — the static website
- `tests/` — automated checks

## How to run
Needs Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in keys when a step needs them
export PYTHONPATH=src            # so python can find the costwire code (Windows: set PYTHONPATH=src)
python -m pytest                 # run the tests
python -m costwire.pull_fertilizer   # pull Iowa + Illinois fertilizer/fuel (+ EIA Midwest fuel, + DDGS feed) into data/fertilizer.csv
python -m costwire.feed          # DDGS feed prices only (IA, IL, MN, WI); add --pdf FILE to read a saved report
EIA_API_KEY=yourkey python -m costwire.eia_fuel   # EIA Midwest diesel + propane only (skips if no key)
NASS_API_KEY=yourkey python -m costwire.nass_land   # yearly cash rents + land values -> data/land.csv (skips if no key)
python -m costwire.changes       # price vs 2 weeks ago and 1 year ago -> data/changes.csv
python -m costwire.brief         # weekly brief -> briefs/<date>.md and .html (add --date 2026-11-02 for a set date)
python -m costwire.site          # build the website into site/ (open site/index.html)
python -m costwire.weekly        # all of the above in one go (what the Monday GitHub job runs)
```

## Weekly automatic run
`.github/workflows/weekly.yml` runs every Monday at 6 AM Central: tests, pull, changes, brief, site, commit, then publish `site/` to GitHub Pages (once Pages is turned on; see LOG.md). Run it by hand from the Actions tab > Weekly brief > Run workflow.

Data credit: USDA AMS, USDA NASS, U.S. Energy Information Administration (EIA).
