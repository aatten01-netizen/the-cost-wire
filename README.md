# The Cost Wire

A weekly input-cost brief for Midwest farmers (fertilizer, fuel, feed, cash rent, land values).

- **BRIEF.md** — what we're building and why
- **PLAN.md** — build steps
- **LOG.md** — what's been done
- **CLAUDE.md** — instructions for Claude

## Folders
- `src/costwire/` — the Python code
- `data/` — clean CSV/JSON from the weekly data pulls
- `site/` — the static website
- `tests/` — automated checks

## How to run
Needs Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in keys when a step needs them
python -m pytest                 # run the tests
```

Data credit: USDA AMS, USDA NASS, U.S. Energy Information Administration (EIA).
