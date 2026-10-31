# Build Log — The Cost Wire

Newest first.

## 2026-10-31 — Step 4: EIA Midwest diesel + propane
**What I built**
- `src/costwire/eia_fuel.py` pulls two weekly Midwest (PADD 2) prices from the free EIA API:
  - On-highway diesel, retail $/gal (weekly): https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EMD_EPD2D_PTE_R20_DPG&f=W
  - Residential propane, $/gal (weekly, Oct–Mar only): https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=W_EPLLPA_PRS_R20_DPG&f=W
- They go into `data/fertilizer.csv` with region `PADD2` and their own names (`onhwy_diesel`, `res_propane`), so they never get mixed up with USDA "farm diesel"/"propane" (on-highway diesel includes road taxes). Source credited as U.S. Energy Information Administration (EIA), with the public EIA page as the link.
- Key comes only from `EIA_API_KEY`. No key = prints a note and skips cleanly. The key is never saved or printed (even in error messages).
- Propane missing in summer is expected and noted, not guessed. Warns if EIA data is more than 2 weeks old. Running twice adds no duplicate rows.
- `python -m costwire.pull_fertilizer` now runs Iowa, Illinois and EIA together.
- 9 new tests with fake EIA replies (52 total, all pass).
- No EIA numbers are in the data file yet: my build sandbox can't reach api.eia.gov and there's no key here. They'll load the first time it runs with your key (your computer, or the Step 8 weekly job).

**How to try it**
`python -m pytest`. On your computer: `EIA_API_KEY=yourkey python -m costwire.eia_fuel`.

**What Andy needs to do** (same as noted in the last entry; needed before Step 8 can publish EIA prices)
1. Get a free EIA key: https://www.eia.gov/opendata/register.php (it's emailed to you).
2. Add it as a GitHub secret named `EIA_API_KEY`: https://github.com/aatten01-netizen/the-cost-wire/settings/secrets/actions > New repository secret. Never paste it into a file in the repo.

**Next:** Step 5 — change calculator (price vs 2 weeks ago and vs 1 year ago, $ and %).

## 2026-10-31 — Step 3b: Illinois parser checked on the real report
**What I built**
- Ran the Illinois parser on the real report you uploaded (`tests/samples/ams_3195.pdf`, week ending Oct 30, 2026). It read every row correctly with no code changes: the current Illinois report uses the newer USDA layout that Step 3a already handled.
- Added a test on the real PDF (checks all 8 prices, the date, region IL and the source link) and a test that "Biodiesel" is never read as farm diesel. 43 tests, all pass.
- Loaded the Illinois prices into `data/fertilizer.csv` (source: USDA AMS Illinois Production Cost Report, https://www.ams.usda.gov/mnreports/ams_3195.pdf): anhydrous $981.11/ton, DAP $932.14, UAN28 $467.86, UAN32 $540.00, MAP $948.00, red potash $517.73, urea $770.00, farm diesel $5.71/gal. This report has no propane row, so Illinois propane is left out.

**How to try it**
`python -m pytest`. `python -m costwire.illinois_cost --pdf tests/samples/ams_3195.pdf` (re-running adds no duplicate rows).

**What Andy needs to do**
Nothing new. Thanks for uploading the PDF. Step 4 will need a free EIA key (see below).

**Next:** Step 4 — EIA Midwest (PADD 2) diesel + propane. Needs a free key in `EIA_API_KEY` (sign up: https://www.eia.gov/opendata/register.php); it will be built to skip cleanly without one.

## 2026-10-30 — Step 3a: Illinois Production Cost Report puller
**What I built**
- `src/costwire/illinois_cost.py` reads the Illinois Production Cost Report (USDA AMS + Illinois Dept. of Ag, bi-weekly): https://www.ams.usda.gov/mnreports/ams_3195.pdf. It takes the "Average" price for anhydrous, urea, UAN28/32, DAP, MAP, potash, farm diesel and propane. "NA" = left out. An average outside its low–high range = skipped with a warning.
- I can't download the current Illinois PDF from my build sandbox (usda.gov is blocked here), so I don't know its exact layout yet. The parser reads both layouts I could confirm: the older Illinois table (2022) and the newer USDA layout that the current Iowa report uses.
- `data/fertilizer.csv` now has a `region` column (IA / IL) so Iowa and Illinois anhydrous don't get mixed up. Your existing Iowa rows were tagged IA.
- New `python -m costwire.pull_fertilizer` pulls Iowa and Illinois in one go. If one state's site is down, the other still runs.
- The "Fetch sample reports" Action now also grabs the Illinois PDF (still hand-run only).
- 13 new tests (41 total, all pass). No Illinois numbers were added to the data file yet: I won't publish numbers until the parser is checked on a real report.

**Split:** Step 3 is now 3a (done) and 3b (check against a real Illinois PDF).

**How to try it**
`python -m pytest`. On your computer: `python -m costwire.pull_fertilizer` (downloads both reports), or `python -m costwire.illinois_cost --pdf ams_3195.pdf` for a saved file.

**What Andy needs to do** (for Step 3b, same steps as the Iowa PDF)
1. Open https://www.ams.usda.gov/mnreports/ams_3195.pdf and save it.
2. Upload it on GitHub to `tests/samples/` named `ams_3195.pdf`: https://github.com/aatten01-netizen/the-cost-wire/tree/main/tests/samples > Add file > Upload files.

**Next:** Step 3b once the PDF is uploaded. Until then the bot can skip ahead to Step 4 (EIA diesel + propane), which doesn't depend on it. Step 4 needs a free EIA key (`EIA_API_KEY`, link in `.env.example`); it will be built to skip cleanly without one.

## 2026-10-30 — Step 2b: Iowa puller, PDF edition
**What I built**
- `src/costwire/iowa_cost.py` now reads the current Iowa Production Cost Report PDF (https://www.ams.usda.gov/mnreports/ams_2863.pdf) with pdfplumber (free). It takes the "Average" price on each row, the "week ending" date as the date, and the PDF link as the source. Missing prices ("NA") are left out. A row whose average isn't between its low and high is skipped with a warning (that would mean we read it wrong).
- `pull()` tries the old CSV first; if it's more than 3 weeks old or won't download, it uses the PDF. Same output file as before: `data/fertilizer.csv`.
- New: `python -m costwire.iowa_cost --pdf FILE` reads a report PDF you saved by hand.
- Loaded your uploaded report (week ending Oct 30, 2026) into `data/fertilizer.csv`: anhydrous $902.33/ton, UAN32 $510.00, MAP $976.00, red potash $499.80, farm diesel $5.65/gal, propane $1.69/gal. That week's report had no urea, UAN28 or DAP prices, so those are left out.
- 6 new tests (28 total, all pass), including the real PDF.

**How to try it**
`pip install -r requirements.txt` then `python -m pytest`. `python -m costwire.iowa_cost` downloads the latest report (works on your computer or GitHub; my build sandbox can't reach usda.gov).

**What Andy needs to do**
Nothing new. Thanks for uploading the PDF. (The GitHub billing block from the entry below still matters for Step 8's weekly auto-run.)

**Next:** Step 3 — add the Illinois Production Cost Report to the same puller.

## 2026-10-30 — Fix: "Fetch sample reports" Action failed
**What happened**
The Action never ran a single step. GitHub refused to start it: "recent account payments have failed or your spending limit needs to be increased." That is a GitHub account billing block, not a code bug. It hits every private repo on the account (market-sentry's GitHub jobs have been refused the same way since Oct 22). The live Commodity Wire 10:00 and 2:00 emails are NOT affected; they don't run on GitHub Actions.

**What I changed**
- `fetch-samples.yml` now runs by hand only, so it stops failing on every push.

**What Andy needs to do** (pick ONE)
1. Fastest: on your phone or computer, open https://www.ams.usda.gov/mnreports/ams_2863.pdf, save it, then upload it on GitHub to `tests/samples/` named `ams_2863.pdf` (repo page > tests/samples > Add file > Upload files). That unblocks Step 2b.
2. Or fix GitHub: go to https://github.com/settings/billing and check for a failed payment or Actions minutes used up. Then run the Action by hand from https://github.com/aatten01-netizen/the-cost-wire/actions.

**Note for the build bot:** until `tests/samples/ams_2863.pdf` exists, build Step 2b's PDF parser with pdfplumber and tests against a small text fixture shaped like the report table; don't check 2b off until it passes on the real PDF.

## 2026-10-29 — Step 2a: Iowa fertilizer + fuel puller (CSV edition)
**What I found**
USDA used to publish the Iowa Production Cost Report as a CSV on ESMIS, but that CSV stopped updating in April 2024. The current report (latest is dated Oct 16, 2026) is only a PDF. So I split Step 2 in PLAN.md: 2a = CSV parser (done today), 2b = PDF parser (next).

**What I built**
- `src/costwire/iowa_cost.py`: finds the newest Iowa CSV on ESMIS, reads anhydrous, urea, UAN 28%/32%, DAP, MAP, red potash, propane and farm diesel (the report's "Average" price), and saves them to `data/fertilizer.csv` with the report date and source link. If the report says "NA", that item is left out, never guessed. Running it twice doesn't duplicate rows. It prints a warning if the newest data is more than 3 weeks old.
- A real sample report (Apr 2, 2024) in `tests/samples/` and 10 new tests (22 total, all pass). No real network calls in tests.
- `.github/workflows/fetch-samples.yml`: a free GitHub Action that downloads the current report PDF into `tests/samples/ams_2863.pdf`. My build sandbox can't reach usda.gov, but GitHub can, so this gets us a real PDF to build Step 2b against. It should run on its own when this push lands.

**How to try it**
`python -m pytest` (22 pass). `python -m costwire.iowa_cost` downloads the latest CSV edition (will warn that it's old).

**What Andy needs to do**
Nothing required. If `tests/samples/ams_2863.pdf` doesn't show up in the repo, check the "Fetch sample reports" run in the repo's Actions tab: https://github.com/aatten01-netizen/the-cost-wire/actions

**Next:** Step 2b — parse the current Iowa report PDF.

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
