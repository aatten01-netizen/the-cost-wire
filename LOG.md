# Build Log — The Cost Wire

Newest first.

## 2026-10-29 — Step 1: Project skeleton
**What I built**
- Folders: `src/costwire/` (code), `data/`, `site/`, `tests/`.
- `requirements.txt` (requests, pytest), `pyproject.toml` (test settings), `.gitignore` (keeps `.env` out of git), `.env.example` (lists the free keys later steps need).
- `src/costwire/records.py`: a `PriceRecord` — one price number. It refuses to exist without a source URL, source name and date, so a number with no source can never get into the brief ("never guess a number" rule, built in from day one).
- `src/costwire/paths.py`: one place that says where data and site files live.
- README now explains how to set up and run.

**How to try it**
`pip install -r requirements.txt` then `python -m pytest` — 12 tests pass.

**What Andy needs to do**
Nothing this week. Heads-up for later (free, no rush): an EIA API key (Step 4) and a NASS Quick Stats key (Step 9). Links are in `.env.example`.

**Next:** Step 2 — fertilizer + fuel puller from the USDA AMS Iowa Production Cost Report.

## 2026-10-29 — Setup
Created BRIEF.md, PLAN.md and CLAUDE.md. Next: Step 1 in PLAN.md.
