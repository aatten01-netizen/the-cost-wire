# Build Plan — The Cost Wire

One step per weekly build session. Do the first unchecked step, then check it off and log it in LOG.md.

- [x] 1. Project skeleton: Python project (`src/`, `data/`, `site/`, `tests/`), `requirements.txt`, README with how to run.
- [x] 2a. Iowa puller, CSV edition: parse the ESMIS CSV (NW_GR910) for anhydrous, urea, UAN28/32, DAP, MAP, potash, diesel, propane into `data/fertilizer.csv` with date + source URL. Test with a saved sample. Warns when the newest CSV is stale (the CSV edition stopped in April 2024).
- [x] 2b. Iowa puller, PDF edition: parse the current report PDF (https://www.ams.usda.gov/mnreports/ams_2863.pdf) using the real sample in `tests/samples/ams_2863.pdf` (downloaded by the "Fetch sample reports" Action). Free library (e.g. pdfplumber). Same output as 2a; pull uses the PDF when the CSV is stale.
- [x] 3a. Illinois puller: parse the Illinois Production Cost Report (https://www.ams.usda.gov/mnreports/ams_3195.pdf) into the same `data/fertilizer.csv`, with a new `region` column (IA / IL). Reads both known table layouts. `python -m costwire.pull_fertilizer` runs every state; one failing doesn't stop the others.
- [x] 3b. Check the Illinois parser against a real current report PDF in `tests/samples/ams_3195.pdf` (needs Andy to upload it, see LOG.md). Fix the parser if the real layout differs, add a real-PDF test, then load it into `data/fertilizer.csv`.
- [x] 4. EIA puller: Midwest (PADD 2) on-highway diesel and propane via the EIA API (key from env var `EIA_API_KEY`; skip cleanly if missing).
- [x] 5. Change calculator: for each item, price vs 2 weeks ago and vs 1 year ago (dollars and %). Tests.
- [x] 6. Brief writer: build the weekly brief as Markdown + HTML from the data (template, no AI needed): headline = biggest move, table, one-line "what changed" per item, sources, disclaimer.
- [x] 7. Static site: `site/` with latest brief, archive list, signup form placeholder. Build script.
- [x] 8. GitHub Actions: weekly Monday 6 AM CT job that pulls data, builds the site, commits it; deploy to GitHub Pages.
- [x] 9. NASS Quick Stats puller: cash rents + land values for WI, IA, IL, MN (state + county where published), key from env var `NASS_API_KEY`. Cash rent page.
- [x] 10a. Feed line: puller for the USDA AMS National Weekly Grain Co-Products Report (https://www.ams.usda.gov/mnreports/ams_3618.pdf): dried distillers grains (10%) $/ton for IA, IL, MN, WI → `data/fertilizer.csv` as item `ddgs` → feed row in the brief. Part of the weekly pull. Tested against the report's layout.
- [ ] 10b. Check the feed parser against the real PDF in `tests/samples/ams_3618.pdf` (from the "Fetch sample reports" Action, or Andy uploads it). Fix the parser if the real text differs, add a real-PDF test, then load the real prices into `data/fertilizer.csv`.
- [x] 11. Email: send the weekly brief through Resend to a test address only (Andy). Key from env var `RESEND_API_KEY`. Do NOT email real subscribers until Andy says so.
- [x] 12. Signup form wired to a free list (Resend audience or Google Sheet). Andy approves before going live.
- [x] 13. Accuracy check script: every number in the brief has a source + date; flag anything missing. Runs before each build.
- [x] 14. Polish + launch checklist for Andy.
