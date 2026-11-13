# Build Log — The Cost Wire

Newest first.

## 2026-11-13 — Step 19: Real alert sender (Resend, test address only)
**Built:** `src/costwire/alerts.py` now has a `ResendSender`. It sends real email through Resend, but EVERY alert goes to Andy's one test address (`BRIEF_TEST_EMAIL`), never to a reader. The subject says which reader it was meant for (`[TEST for reader@farm.com] ...`) and the first line says the reader was NOT emailed. It's off unless `ALERTS_LIVE=yes` AND `RESEND_API_KEY` AND `BRIEF_TEST_EMAIL` are all set; otherwise the mock sender is used and nothing is sent. Safety extras: max 10 test emails per run; only alerts that really went out are remembered (a failed send gets retried next run); if live is asked for but the key is missing, the dry run writes to `alerts_sent_mock.csv` so it can't block the real test later. Errors print the error type only, never the key. Still not in the weekly job (no reader list yet). `.env.example` has `ALERTS_LIVE`. 10 new tests, Resend never called (228 total, all pass).
**Try it:** `PYTHONPATH=src python3 -m pytest -q tests/test_alert_sender.py`. Real test (on your computer): make `alerts.csv` OUTSIDE the repo with `email,item,region,threshold` + a row like `you@example.com,anhydrous,IA,1`, then `ALERTS_LIVE=yes RESEND_API_KEY=... BRIEF_TEST_EMAIL=you@example.com ALERTS_FILE=/path/alerts.csv PYTHONPATH=src python3 -m costwire.alerts`. It only emails if the two newest saved reports moved at least your amount.
**Andy:** optional now: (1) free Resend key at https://resend.com/api-keys (same one as Step 11, if made), (2) run the real test above and check your inbox. Biggest blocker to a first dollar is still the signup form go-live (docs/signup-google-sheet.md).
Marketing: Pro alerts founding-tester invite (marketing/pro-alerts-beta-invite.md) - Andy: reply SEND/POST in chat to have it sent
**Next:** market-scan step "Sample Pro alert page" (site/pro-sample.html), done before the cost-per-pound-of-N line because it helps sell Pro.

## 2026-11-13 — Step 18: Alert sign-up on the site (night shift)
**Built:** `src/costwire/alert_signup.py`. New page `site/alerts.html` ("Alerts" is in every page's nav, and the pricing page links to it): a reader picks an item + state (only ones we actually publish, from `data/fertilizer.csv`) and a dollar amount ($5-$100). It is a disabled "coming soon" preview unless `SIGNUP_FORM_URL` is set AND the new go-ahead `ALERTS_SIGNUP_LIVE=yes` (separate from the free signup, since alerts are Pro). It posts to the same Google Sheet. `docs/signup-google-sheet.md` now has a new Apps Script that saves `alert_item`, `alert_region`, `alert_threshold` columns, plus how to turn the Sheet into the alert list: `python -m costwire.alert_signup sheet.csv alerts.csv` writes the ALERTS_FILE format (newest choice wins, bad/unknown choices skipped, refuses to write inside the repo because it holds emails). Also fixed: the weekly Action never passed `PRO_CHECKOUT_URL`/`PRO_CHECKOUT_LIVE` to the site build, so Step 16's checkout switch could not have turned on; it does now (plus `ALERTS_SIGNUP_LIVE`). Nav wraps on phones. 8 new tests (217 total, all pass); accuracy check passes; alerts, home and pricing pages checked at 375px, no sideways scroll.
**Try it:** `PYTHONPATH=src python3 -m pytest -q tests/test_alert_signup.py`; `PYTHONPATH=src python3 -m costwire.site`, open `site/alerts.html`.
**Andy:** nothing required now. When you turn on the signup form, paste the NEW Apps Script from `docs/signup-google-sheet.md` (and add the 3 new header columns). Add repo variable `ALERTS_SIGNUP_LIVE=yes` only when you want to take alert sign-ups.
Marketing: alert sign-up launch posts (marketing/alerts-page-launch-posts.md) - Andy: reply SEND/POST in chat to have it sent
**Next:** Step 19, real alert sender through Resend (test address only, off unless ALERTS_LIVE=yes).

## 2026-11-12 — Step 17: Price-move alerts (mock sender) — extra run
**Why this step:** alerts are the one core Pro feature on the pricing page; nothing can be sold without them.
**Built:** `src/costwire/alerts.py`. A reader picks an item, a state and a dollar amount. After a pull, it compares the two newest published reports for that item and state (same USDA/EIA source and unit, at most 45 days apart; otherwise no alert, never a guess) and writes a short alert for every reader whose move hit their amount, up or down. Each alert has both prices, both dates, the source links, "Data, not advice" and "reply STOP". It remembers what it already alerted, so the same report never alerts twice. Sending is a MockSender only: no real email. Reader emails never go in this public repo: the list is a CSV outside it (`ALERTS_FILE`), and `alerts*.csv` is now git-ignored. 8 new tests (209 total, all pass). Dry run on real data: 0 alerts, correct (only one report date saved so far).
**Try it:** `PYTHONPATH=src python3 -m pytest -q tests/test_alerts.py`; make a CSV outside the repo with `email,item,region,threshold` (e.g. `you@example.com,anhydrous,IA,25`) and run `ALERTS_FILE=/path/alerts.csv PYTHONPATH=src python3 -m costwire.alerts` (prints what would go out, sends nothing).
**Andy:** nothing now. Not in the weekly job yet on purpose (no reader list exists).
Marketing: Pro alerts announcement (brief P.S. + sample alert) (marketing/pro-alerts-announcement.md) - Andy: reply SEND/POST in chat to have it sent
**Next:** Step 18, alert sign-up on the site (item, state, amount).

## 2026-11-12 — Step 16: Pricing page (Free vs Pro, mock checkout)
**Why this step:** every PLAN step was done, and the new money-goal rule says pick what makes the product sellable sooner. A pricing page with checkout behind a mock is the first piece of a paid tier.
**Built:** `src/costwire/pricing.py` writes `site/pricing.html` on every site build: Free ($0, what's live today) vs Pro (coming soon, $9/month or $90/year per BRIEF.md's $9-15 range), plus a short Q&A and the data-not-advice line. "Pricing" is in every page's nav. The Pro button is disabled ("Pro is not open yet") unless `PRO_CHECKOUT_URL` is a Stripe Payment Link (https://buy.stripe.com/...) AND `PRO_CHECKOUT_LIVE=yes`; anything else stays a mock. The free signup box now has `id="signup"` so the pricing page can link to it. Launch check has a new "Pricing page built" line (8 of 11 ready). Added `REVENUE.md`. 8 new tests (201 total, all pass). Pricing and home pages checked at 375px: no sideways scroll.
**Try it:** `PYTHONPATH=src python3 -m pytest -q tests/test_pricing.py`; `PYTHONPATH=src python3 -m costwire.site`, open `site/pricing.html`. Live after the next deploy: https://aatten01-netizen.github.io/the-cost-wire/pricing.html
**Andy:** nothing required now. Later: (1) turn on the signup form (docs/signup-google-sheet.md) — biggest blocker to a first dollar; (2) change the Pro price in `src/costwire/pricing.py` if you want something other than $9; (3) only once alerts exist, make a Stripe Payment Link (https://dashboard.stripe.com/payment-links) and add `PRO_CHECKOUT_URL` + `PRO_CHECKOUT_LIVE=yes` as repo variables. Don't sell Pro before its features work.
Marketing: Pro "would you pay?" reader survey (marketing/pro-interest-survey.md) - Andy: reply SEND/POST in chat to have it sent
**Next:** Step 17, price-move alerts (core Pro feature) behind a mock sender.

## 2026-11-12 — QA (the-cost-wire)
**Checked:** 187 tests pass (needs `pip install -r requirements.txt cffi pytest`; without pdfplumber installed 7 Iowa PDF tests fail, which is a setup issue, not a bug). In a scratch copy ran changes → brief → accuracy check → site → launch check: all pass, `site/feed.xml` is valid XML (7 of 10 launch items ready; the 3 open ones are Andy's: NASS key, test email key, signup go-live). All 5 pages at 375px: no sideways scroll, disclaimer on each, no broken local links, no page errors.
**Fixed:** nothing was broken, so I added tests for the accuracy check (the guard that stops a bad number reaching farmers). 6 new tests cover paths that had none: a duplicated table row, a row missing a column, a source link downgraded to http, a source dropped from the Sources list, the disclaimer deleted, and the whole 12-week trend section deleted. All are caught. 193 tests, all pass.
**Verify:** `PYTHONPATH=src python3 -m pytest -q tests/test_accuracy.py`.

## 2026-11-12 — Step 15: RSS feed
**Built:** every PLAN step was already checked off, so I added step 15 and did it. `src/costwire/feed_rss.py` writes `site/feed.xml` (RSS 2.0) each time the site builds: one item per weekly brief, newest first (max 20), with the brief's own title and headline, its link and date. No new numbers: every word is copied from the brief, which already passed the accuracy check. Every page now has an "RSS" link in the nav and a feed tag in its `<head>` so feed readers find it. Site address comes from optional env var `SITE_URL` (default: the live GitHub Pages address; added to `.env.example`). 5 new tests (187 total, all pass). Site rebuilt; accuracy check passes; all 4 pages checked at 375px, no sideways scroll.
**Try it:** `PYTHONPATH=src python3 -m pytest -q tests/test_feed_rss.py`; `python -m costwire.site` then open `site/feed.xml`. Live after the next Monday job: https://aatten01-netizen.github.io/the-cost-wire/feed.xml
**Andy:** nothing needed. Optional: paste the feed link into a free reader (Feedly, Outlook) to see it.
Marketing: launch checklist (marketing/launch-checklist.md) - Andy: reply SEND/POST in chat to have it sent
**Next:** every PLAN step and all 11 marketing assets are done. Next build needs a new market scan or a new PLAN step from Andy. Still open for Andy (from earlier logs): `NASS_API_KEY` secret, Resend test email, signup form go-live.

## 2026-11-12 — Marketing session (night shift, Cost Wire, asset 10)
**Build step:** none. Every PLAN step, including both "From market scan" items, is checked off. Tests: 182 pass (`pip install -r requirements.txt cffi pytest`, then `PYTHONPATH=src python3 -m pytest -q`).
**Made:** asset 10, `marketing/ad-test-plan.md`: a $0 free-channel baseline week, then a $20 Facebook/Instagram boost test (2 ads × $10, IA/IL/MN/WI farmers, no school/college/FFA targeting), honest measuring (static site has no analytics, so signups are counted in the Sheet), stop rules and win thresholds set ahead of time. Ad images use only real screenshots of the live brief. Meta's minimum daily budget not verified this run.
Marketing: $0-$20 ad test plan - Andy: reply SEND/POST in chat to have it sent
**Andy:** don't spend until the signup form is live; you make the Facebook Page and do the boost yourself.
**Next:** marketing asset 11 (launch checklist marketing piece). New build work needs a new market scan or PLAN step.

## 2026-11-11 — Market-scan step: 12-week price trend
**Built:** `src/costwire/trend.py` draws a small inline SVG line per fertilizer (anhydrous, urea, UAN, DAP, MAP, potash; each state) from every saved price in `data/fertilizer.csv` over the last 12 weeks. No new data source. Same item, state, unit and USDA AMS report only; needs 2+ saved dates, otherwise it is left out. Each chart has one plain sentence under it (first, newest, low, high, each with its date). That sentence is also in the Markdown brief, and the accuracy check now re-checks every trend line against the data. 10 new tests (182 total, all pass). Checked at phone width (375px): no sideways scroll.
**Try it:** `PYTHONPATH=src python -m pytest -q tests/test_trend.py`; `python -m costwire.brief` then open the HTML.
**Andy:** nothing. The section is hidden until the weekly job has saved 2+ report dates (right now each fertilizer has only Oct 30, 2026), so it should first show up after the next new USDA report is pulled.
Marketing: referral offer (forward-to-a-neighbor) (marketing/referral-offer.md) - Andy: reply SEND/POST in chat to have it sent
**Next:** every PLAN step is checked off. Marketing asset 10 ($0-$20 ad test plan).

## 2026-11-11 — QA (the-cost-wire)
**Checked:** 170 tests pass (needs `pip install -r requirements.txt cffi`); built changes → brief → accuracy check → site in a scratch copy (passes); all 4 site pages at 375px: no sideways scroll, disclaimer on each, no broken local links, no page errors. Tried the new bushels-of-corn line with sample NASS rows: renders and passes the accuracy check. (Iowa shows only anhydrous because the Iowa AMS report has no urea or UAN 28% row. The parser is correct.)
**Fixed:** a 0 in `data/corn_price.csv` crashed the whole brief (divide by zero), and a "nan" printed "nan bushels of corn per ton" in the brief. Now `affordability.py` skips any corn price that isn't a real number above zero (uses an older good month if there is one, otherwise leaves the line out). The accuracy check still flags the bad row. 2 new tests (172 total, all pass).
**Verify:** `PYTHONPATH=src python3 -m pytest -q tests/test_affordability.py`.

## 2026-11-11 — Market-scan step: bushels of corn to buy 1 ton (night shift)
**Built:** the affordability line. `src/costwire/corn_price.py` pulls the USDA NASS monthly corn price received for Iowa and Illinois (Quick Stats, key from `NASS_API_KEY`, skips cleanly without it) into `data/corn_price.csv`. `src/costwire/affordability.py` divides the AMS anhydrous, urea and UAN 28% price by that state's newest NASS corn month (no later than the fertilizer date, at most 3 months older), and does the same for 1 year ago (year-ago AMS price ÷ same month a year earlier). The brief gets a "Bushels of corn to buy 1 ton" section, NASS links in Sources and NASS in the credit line. Missing either number = the line (or the year-ago part) is left out. The accuracy check now also re-checks every bushels line and the NASS links. The weekly job runs the corn pull after cash rents; a failure never stops the brief. 13 new tests (170 total, all pass).
**Try it:** `PYTHONPATH=src python -m pytest -q`; with a key: `NASS_API_KEY=... PYTHONPATH=src python -m costwire.corn_price` then `python -m costwire.brief`.
**Andy:** the section stays hidden until `NASS_API_KEY` is set as a repo secret (same key as cash rent; still not set as far as this log shows). The year-ago part also needs ~1 year of saved AMS prices, so it will show "n/a"-style omission for now. Not verified against a live NASS reply (no key in the sandbox): first real run, glance at the section.
Marketing: Commodity Wire cross-promo offer (marketing/cross-promo-commodity-wire.md) - Andy: reply SEND/POST in chat to have it sent
**Next:** market-scan step 2: 12-week price trend SVG per fertilizer on the brief page. Marketing asset 9 (referral offer).

## 2026-11-10 — Marketing session (Cost Wire, asset 7)
**Build step:** none. All PLAN steps are done and there is no "From market scan" section.
**Made:** asset 7, `marketing/seo-fertilizer-vs-last-year.md`: SEO article on Iowa/Illinois fertilizer. Uses only Oct 30, 2026 USDA prices (from the Nov 9 brief, each sourced). No year-ago numbers exist in our data, so it has a marked spot for a year-ago table and a how-to for finding last year's report. No up/down claims.
Marketing: SEO fertilizer vs last year article - Andy: reply SEND/POST in chat to have it sent
**Andy:** confirm the USDA Market News click path; year-ago rows must come from the archived 2025 reports.
**Next:** asset 8 (cross-promo offer for the Commodity Wire list).

## 2026-11-10 — Marketing session (night shift, Cost Wire)
**Build step:** none. All PLAN steps are done and there is no "From market scan" section.
**Made:** asset 6, `marketing/seo-cash-rent-article.md`: SEO article on finding NASS cash rent by county. No dollar figures, because the cash rent page has no data loaded yet (never guess a number). It has a marked spot for a sourced table.
Marketing: SEO cash rent article - Andy: reply SEND/POST in chat to have it sent
**Andy:** set `NASS_API_KEY` so the table can be filled; confirm the Quick Stats click path.
**Next:** asset 7 (SEO article on Iowa/Illinois fertilizer vs last year).

## 2026-11-09 — Marketing session (Cost Wire, asset 5)
**Build step:** none. All PLAN steps are done and there is no "From market scan" section.
**Made:** `marketing/video-script.md`: 30-second script using only Nov 8 brief numbers (Iowa/Illinois anhydrous, EIA diesel), each sourced. No week-over-week change exists yet, so Version A shows price + source only; Version B (for the 2-week change) is ready once the Nov 22 brief has one.
Marketing: short-video script - Andy: reply SEND/POST in chat to have it sent
**Andy:** record in your own voice; swap in the newest brief's numbers if later.
**Next:** asset 6 (SEO article on cash rent by county).

## 2026-11-09 — Marketing session (night shift, Cost Wire)
**Build step:** none. All PLAN steps are done and there is no "From market scan" section.
**Made:** asset 4, `marketing/reddit-post.md`: value-first r/farming post using only Nov 8 brief numbers (USDA/EIA, each sourced), with disclosure line and reply prep. Reddit was unreachable from the sandbox, so r/farming's self-promo rules are NOT verified; the file has a check-before-posting list.
Marketing: Reddit r/farming post - Andy: reply SEND/POST in chat to have it sent
**Andy:** read r/farming's rules before posting.
**Next:** asset 5 (short-video script).

## 2026-11-08 — QA (the-cost-wire)
**Checked:** 156 tests pass; accuracy check passes; all 5 site pages at 375px (no sideways scroll, disclaimer on each, no broken local links); no advice wording; no duplicate rows in `data/fertilizer.csv`.
**Fixed:** brief table sorted regions by code, so Wisconsin feed landed after the Midwest (PADD 2) fuel rows. Now states first (IA, IL, MN, WI), regional averages last. Added 1 test (157 total). Rebuilt the Nov 8 brief and site; accuracy check still passes.
**Verify:** `PYTHONPATH=src python3 -m pytest` (needs `pip install pytest requests pdfplumber pyyaml cffi`).

## 2026-11-08 — LIVE (Andy + Claude in chat)
**Live:** https://aatten01-netizen.github.io/the-cost-wire/ . Andy made the repo public (fixes the Actions billing block; free Actions + Pages) and set Pages to GitHub Actions; Claude added `PAGES_ENABLED=true`, ran "Fetch sample reports" (success) and "Weekly brief" #1 (success: build + deploy). First brief shows Iowa/Illinois fertilizer + diesel + propane, DDGS for IA/IL/MN/WI, and EIA Midwest diesel/propane, all sourced and dated.
**Still open for Andy:** cash rent (needs `NASS_API_KEY` secret if not added yet), email test (Resend), signup form. Step 10b (feed line) can run now that sample reports were fetched.

## 2026-11-08 — Marketing session (Cost Wire, asset 3)
**Build step:** none. All PLAN steps are done.
**Made:** `marketing/agtalk-post.md`: value-first AgTalk post using only numbers from the Nov 2 brief, each with its USDA source link. I could not open AgTalk, so its self-promo rules are NOT verified; the file has a "check before posting" list.
Marketing: AgTalk post - Andy: reply SEND/POST in chat to have it sent
**Andy:** same launch-checklist items (site must be live for [LINK]); read AgTalk's rules before posting.
**Next:** asset 4 (Reddit r/farming post).

## 2026-11-08 — Marketing session (night shift, Cost Wire)
**Build step:** none. All PLAN steps are done and there is no "From market scan" section yet.
**Made:** asset 2, `marketing/outreach-messages.md`: 5 drafts (Brownfield, Farm Week, RFD-TV, Wisconsin State Farmer, Iowa Farmer Today). No FFA/schools. Sandbox couldn't open the sites, so Andy must confirm each contact page; no addresses guessed.
Marketing: outreach messages - Andy: reply SEND/POST in chat to have it sent
**Andy:** same launch-checklist items (site must be live for [LINK]).
**Next:** asset 3 (AgTalk post).

## 2026-11-07 — QA (the-cost-wire)
**Checked:** full test suite (153 passed; sandbox needed `pip install cffi` for pdfplumber, not a repo bug), all 4 site pages at phone width (no sideways scroll, viewport tag + disclaimer on each), advice-wording search (none found).
**Fixed/added:** removed an unused variable in `nass_land.main()`; added 3 tests (exit codes, API key never printed in errors). Now 156 tests.
**Verify:** `python -m pytest`

## 2026-11-07 — Marketing session (Cost Wire)
**What I did:** All PLAN steps were already done, so no build step. Created `marketing/MARKETING-PLAN.md` (buyer, communities, competitors, offer, 11-asset checklist) and asset 1: `marketing/landing-page-copy.md`.
**Note:** Competitor prices are NOT verified (not found online); the plan says not to quote them until checked.
Marketing: landing page copy - Andy: reply SEND/POST in chat to have it sent
**Andy:** same launch-checklist items; please check DTN/farmdoc pricing pages so we can fill competitor prices.
**Next:** asset 2 (outreach messages).

## 2026-11-07 — Step 10b: Check the feed parser against the real PDF (night shift)
**What I built**
- Ran the feed parser on the real `tests/samples/ams_3618.pdf` (report for 10/26-10/30/2026, released Nov 2). It read the real layout correctly with no changes: dried distillers grains 10% = IL $195.00, IA $170.65, MN $175.00, WI $174.00 per ton (not the wet table, not the $/bu column).
- Added a real-PDF test (`tests/test_feed.py`). 153 tests pass.
- Loaded the 4 real prices into `data/fertilizer.csv` (dated 2026-11-02, the report's release date) and rebuilt the Nov 2 brief and site. The feed row now shows in the brief; accuracy check passes.

**How to try it**
`python -m pytest`, then `PYTHONPATH=src python -m costwire.launch_check` (feed line should now be ready).

**What Andy needs to do**
Same open items: GitHub billing, `EIA_API_KEY` and `NASS_API_KEY` secrets, Resend test settings, signup sheet. See `docs/launch-checklist.md`.

**Next:** All PLAN steps are done. Remaining work is Andy's keys; there is no "From market scan" section yet.

## 2026-11-06 — Step 14: Polish + launch checklist
**What I built**
- `src/costwire/launch_check.py`: prints a ready / not-ready list for launch (Iowa + Illinois prices, EIA fuel, feed line, cash rent data, a brief, accuracy check, website pages, test-email settings, signup form live). Each missing item says what to do. `--strict` exits 1 if anything is missing.
- `docs/launch-checklist.md`: the numbered list of everything only you can do, with links, in order.
- README mentions both. 4 new tests (`tests/test_launch_check.py`). 152 pass.

**Right now the check says 5 of 10 ready.** Missing: EIA fuel (no key), feed line (no PDF, Step 10b), cash rent data (no NASS key), test-email settings, signup live.

**How to try it**
`PYTHONPATH=src python -m costwire.launch_check`

**What Andy needs to do**
Follow `docs/launch-checklist.md`. The top three: (1) fix GitHub Actions billing https://github.com/settings/billing (2) add secrets `EIA_API_KEY` and `NASS_API_KEY` https://github.com/aatten01-netizen/the-cost-wire/settings/secrets/actions (3) upload `tests/samples/ams_3618.pdf` https://github.com/aatten01-netizen/the-cost-wire/upload/main/tests/samples

**Next:** Step 10b once the PDF is uploaded. All other steps are done.

## 2026-11-06 — QA (Cost Wire)
**Checked:** full test suite (147 pass; the 6 "real PDF" failures in the old log were a broken system `cryptography`/`cffi` in the sandbox, fixed with `pip install cffi cryptography`, not a code bug), accuracy check passes, site rebuilt, all 4 pages checked at phone width (375px, no sideways scroll, disclaimer present).
**Fixed:** the committed `site/` was out of date: no `cash-rent.html` page and no "Cash rent" nav link on the other pages. Rebuilt it and added a test that every page links to it.
**Verify:** `PYTHONPATH=src python -m costwire.site` should leave `git status` clean; `python -m pytest`.
**Andy:** nothing new. Still open: Step 10b PDF, NASS key (cash rent page says "not loaded yet").

## 2026-11-06 — Step 13: Accuracy check script (night shift)
**What I built**
- `src/costwire/accuracy.py`: checks the saved prices (item, unit, real price above zero, real date not in the future, source name and https source link) and then checks the newest brief row by row against the data: price, date, 2-week and 1-year change and source link must match exactly. It also fails if a row is missing, invented or duplicated, if an earlier price used for a change has no source or date, or if the Sources section or disclaimer is missing. Problems print in plain English and it exits 1.
- `weekly.py`: the check now runs after the brief and before the site build, so a bad number stops the build and nothing is published.
- 11 new tests (`tests/test_accuracy.py`, plus one in `test_weekly.py`). 141 pass; the same 6 real-PDF tests fail in this sandbox only (PDF library problem, see Step 9). The check passes on the current real brief.

**How to try it**
`python -m costwire.accuracy` (checks the newest brief), or `--brief briefs/2026-11-02.md`.

**What Andy needs to do**
1. Step 10b still needs `tests/samples/ams_3618.pdf`: https://github.com/aatten01-netizen/the-cost-wire/upload/main/tests/samples
2. Still open: GitHub billing, EIA/NASS/Resend keys, Pages decision, signup sheet (Step 12).

**Next:** Step 14 (polish + launch checklist), or 10b once the PDF is uploaded.

## 2026-11-05 — Step 12: Signup form wired to a free Google Sheet (stays OFF until you say go)
**What I built**
- `site.py`: the signup box is still the "coming soon" placeholder. It turns into a real email form ONLY when both build settings are present: `SIGNUP_FORM_URL` (an https link) and `SIGNUP_LIVE=yes`. Missing either one, or a non-https link, keeps the placeholder. The live form has a hidden bot-trap field and stores only an email.
- `docs/signup-google-sheet.md`: copy-paste Google Apps Script that saves signups to a Google Sheet (free, no new service).
- Weekly workflow passes the two settings as repo Variables; `.env.example` updated.
- 6 new tests in `tests/test_signup.py`. 130 pass; the same 6 old real-PDF tests fail in this sandbox only (PDF library crash, see Step 9).

**Not verified live:** no Google Sheet exists, so the form post has not been tried for real.

**How to try it**
`SIGNUP_FORM_URL=https://example.com/x SIGNUP_LIVE=yes python -m costwire.site`, open `site/index.html`.

**What Andy needs to do**
1. Follow `docs/signup-google-sheet.md` (about 5 minutes) and add the repo variable `SIGNUP_FORM_URL`: https://github.com/aatten01-netizen/the-cost-wire/settings/variables/actions
2. Test it with one of your own emails, then add variable `SIGNUP_LIVE` = `yes` when you approve.
3. Step 10b still needs `tests/samples/ams_3618.pdf`: https://github.com/aatten01-netizen/the-cost-wire/upload/main/tests/samples
4. Still open: GitHub billing, EIA/NASS/Resend keys, Pages decision.

**Next:** Step 10b if the PDF is uploaded; otherwise Step 13 (accuracy check script).

## 2026-11-05 — Step 11: Test email via Resend (night shift)
**What I built**
- `src/costwire/email_brief.py`: sends the newest brief (HTML plus Markdown as plain text) through Resend to ONE test address, subject starts "[TEST]". Key only from `RESEND_API_KEY`, address from `BRIEF_TEST_EMAIL` (or `--to`). No key or address = skips and sends nothing. More than one address is refused. There is no subscriber sending anywhere in the code.
- `--dry-run` shows what would be sent without sending. `.env.example` updated.
- 8 new tests with a fake sender (Resend never called). 124 pass; the same 6 old real-PDF tests fail in this sandbox only (PDF library crypto crash, noted in Step 9), not caused by this step.

**Not verified live:** no Resend key here, so the real send is untested. Sender is Resend's shared `onboarding@resend.dev`, which only delivers to your own Resend account email until you verify a domain.

**How to try it**
`python -m costwire.email_brief --to you@example.com --dry-run`, then with the key: `RESEND_API_KEY=... BRIEF_TEST_EMAIL=you@x.com python -m costwire.email_brief`

**What Andy needs to do**
1. Add a Resend API key as env var (you already use Resend) and pick your test address.
2. Step 10b still needs `tests/samples/ams_3618.pdf` (my sandbox can't reach usda.gov): https://github.com/aatten01-netizen/the-cost-wire/upload/main/tests/samples
3. Still open: GitHub billing, EIA/NASS secrets, Pages decision.

**Next:** Step 10b if the PDF is uploaded; otherwise Step 12 (signup form wired to a free list, Andy approves before live).

## 2026-11-04 — Step 10a: Feed line (DDGS)
**What I built**
- `src/costwire/feed.py`: reads the USDA AMS **National Weekly Grain Co-Products Report** (https://www.ams.usda.gov/mnreports/ams_3618.pdf, report page https://mymarketnews.ams.usda.gov/viewReport/3618) and keeps the **dried distillers grains (10% moisture), $/ton** price for Iowa, Illinois, Minnesota and Wisconsin. Saved to `data/fertilizer.csv` as item `ddgs` with the report date and link, so the change calculator and brief pick it up like any other item. Wet distillers grains and the report's own $/bushel columns are ignored. A state with no price is left out, never guessed.
- The weekly pull now runs the feed puller too (if it fails, the rest still runs). The brief shows it as "Dried distillers grains (10%)" with Minnesota/Wisconsin names; credit stays "USDA AMS".
- Small fix: saving rows now treats the state as part of "is this row already saved?". Before, four states from one report on the same date would have been squashed into one row.
- The "Fetch sample reports" Action now also downloads `ams_3618.pdf`.
- 13 new tests (120 total, all pass).

**Why only 10a (split the step):** my sandbox can't reach USDA, so I couldn't test against the real PDF. I built the parser from the layout of the Oct 26, 2026 report (seen through a web reader) and tested with made-up numbers. No feed prices are in the data yet. Step 10b checks it against the real PDF and loads real prices.

**How to try it**
`python -m pytest`. Then `python -m costwire.feed` (on a computer that can reach usda.gov) or `python -m costwire.feed --pdf ams_3618.pdf`, then `python -m costwire.brief` and look for the distillers grains rows.

**What Andy needs to do**
1. For Step 10b, either run Actions > "Fetch sample reports" > Run workflow (once billing is fixed): https://github.com/aatten01-netizen/the-cost-wire/actions , or download https://www.ams.usda.gov/mnreports/ams_3618.pdf and upload it to `tests/samples/ams_3618.pdf`: https://github.com/aatten01-netizen/the-cost-wire/upload/main/tests/samples
2. Still open: GitHub billing block, `EIA_API_KEY` and `NASS_API_KEY` secrets, public-repo/Pages decision (see Steps 8 and 9).

**Next:** Step 10b — check the feed parser against the real Grain Co-Products PDF (needs the PDF above). If it isn't there yet, Step 11 (email via Resend to a test address) can go ahead, since it doesn't depend on 10b.

## 2026-11-04 — Step 9: NASS cash rents + land values
**What I built**
- `src/costwire/nass_land.py`: pulls yearly USDA NASS numbers for WI, IA, IL, MN into `data/land.csv`: cash rent (non-irrigated cropland, pasture; state and county) and land value (cropland, farm real estate; state). County numbers NASS withheld "(D)" are left out, never filled in. Key comes only from `NASS_API_KEY`; with no key it skips cleanly. The key is never saved or printed; each row's source link is the exact query without the key.
- `src/costwire/rentpage.py` + `site.py`: new page `site/cash-rent.html` ("Cash rent" in the nav): state table with change vs the year before (only when both years exist), county tables, source links, USDA NASS credit, "data, not advice".
- The weekly job now also runs the NASS pull (a failure there never stops the brief) and passes the `NASS_API_KEY` secret.
- 13 new tests (all pass). 6 older tests that read the real PDFs fail in THIS sandbox only: the PDF library crashes on a broken system crypto package (not caused by this step; they passed in earlier runs). Please check the Actions run is green once billing is fixed.

**Not verified against the live NASS API**: my sandbox can't reach it and there is no key yet. The query names (`short_desc`, `agg_level_desc`, etc.) follow NASS's published Quick Stats format, but the first real run could show a mismatch. The page will say "not loaded yet" rather than show anything wrong.

**How to try it**
`NASS_API_KEY=yourkey python -m costwire.nass_land`, then `python -m costwire.site` and open `site/cash-rent.html`.

**What Andy needs to do**
1. Get the free NASS key: https://quickstats.nass.usda.gov/api and add it as GitHub secret `NASS_API_KEY`: https://github.com/aatten01-netizen/the-cost-wire/settings/secrets/actions
2. Still open: `EIA_API_KEY` secret, GitHub billing block, and the public-repo/Pages decision (see Step 8 entry).

**Next:** Step 10 — feed line (USDA AMS distillers grains / feedstuffs weekly report).

## 2026-11-03 — Step 8: Weekly GitHub Actions job + GitHub Pages
**What I built**
- `src/costwire/weekly.py`: one command that does the whole week: pull prices, work out changes, write the brief, build the site. If every price pull fails (USDA site down), it still rebuilds from the real prices already saved; it never makes numbers up. If there are no saved prices at all, it stops with an error.
- `.github/workflows/weekly.yml` ("Weekly brief"): every Monday at 6 AM Central it installs the code, runs all the tests, runs the weekly build (EIA key from the `EIA_API_KEY` secret), commits any new data/brief/site files, then publishes `site/` to GitHub Pages. You can also start it by hand from the Actions tab.
- 6 AM Central all year: GitHub's timer only knows UTC, so it fires at 11:00 and 12:00 UTC on Mondays and a small check lets through only the one that's 6 AM or later in Chicago (works for both CDT and CST).
- The publish step waits for you: it skips cleanly until a repo variable `PAGES_ENABLED` is set to `true`.
- Tested end to end here (my sandbox can't reach USDA, so it correctly fell back to the saved Oct 30 prices). 12 new tests (97 total, all pass), including checks on the workflow file itself. Added `pyyaml` to requirements (tests only).

**How to try it**
`python -m pytest`. Then `python -m costwire.weekly` and open `site/index.html`. On GitHub (once billing is fixed): Actions > Weekly brief > Run workflow.

**What Andy needs to do**
1. Fix the GitHub billing block (already noted; nothing on Actions runs until it's sorted): https://github.com/settings/billing
2. NEW, a decision: GitHub Pages on a free account only works for **public** repos. This repo is private. Pick one: (a) make the repo public (Settings > General > Danger Zone > Change visibility: https://github.com/aatten01-netizen/the-cost-wire/settings). Nothing secret is in the repo (keys live only in GitHub secrets), but the code and data become visible to anyone. Or (b) keep it private and host the `site/` folder somewhere free later (I'd set that up as a separate step once you say so). Paid GitHub plans also allow private Pages, but I won't add anything paid without your OK.
3. If you pick (a): turn on Pages at https://github.com/aatten01-netizen/the-cost-wire/settings/pages > Source: **GitHub Actions**. Then add a repo variable at https://github.com/aatten01-netizen/the-cost-wire/settings/variables/actions > New repository variable: name `PAGES_ENABLED`, value `true`.
4. Still open: free EIA key as secret `EIA_API_KEY` (https://www.eia.gov/opendata/register.php, then https://github.com/aatten01-netizen/the-cost-wire/settings/secrets/actions). Without it the brief just leaves out EIA diesel/propane.

**Next:** Step 9 — NASS Quick Stats puller: cash rents + land values for WI, IA, IL, MN (key from `NASS_API_KEY`), cash rent page.

## 2026-11-03 — Step 7: Static site
**What I built**
- `src/costwire/site.py` turns the weekly briefs in `briefs/` into a small website in `site/`:
  - `site/index.html` is the latest brief, with a nav bar (Latest / Archive) and a signup box.
  - `site/archive.html` lists every brief, newest first.
  - `site/briefs/<date>.html` holds each brief with the nav bar.
  - `site/.nojekyll` so GitHub Pages serves the files as they are.
- The signup box is a placeholder: the field and button are switched off and it says "coming soon". Nothing is collected or sent (Step 12 wires it up, after you approve).
- The build wipes and rewrites `site/briefs/` each time, so deleted briefs don't linger. No briefs yet gives a simple "coming soon" home page.
- The site shows the Nov 2, 2026 brief already built. No new numbers: the pages reuse the brief HTML.
- 6 new tests (85 total, all pass). README has the new command.

**How to try it**
`python -m pytest`. Then `python -m costwire.site` and open `site/index.html` in your browser.

**What Andy needs to do**
Nothing new for this step. (Still open: the free EIA key as GitHub secret `EIA_API_KEY`, and the GitHub billing block that stops Actions; both matter for Step 8. Step 8 will also need GitHub Pages turned on: repo Settings > Pages > Source: GitHub Actions.)

**Next:** Step 8 — GitHub Actions: weekly Monday 6 AM CT job that pulls data, builds the brief and site, commits, and deploys to GitHub Pages.

## 2026-11-01 — Step 6: Brief writer
**What I built**
- `src/costwire/brief.py` writes the weekly brief from the saved prices, as Markdown and HTML (a plain template, no AI). Output: `briefs/<date>.md` and `briefs/<date>.html`.
- What's in it: a headline (the biggest % move vs 2 weeks ago; if there are none yet, vs a year ago; if there's no history at all, it says so plainly), a table (every price, change vs 2 weeks and 1 year, date, source link), one "what changed" line per item, the sources with dates, a credit line naming only the agencies whose numbers are in that brief (USDA AMS, EIA), and the disclaimer (data, not advice; dealer prices differ; we never say buy or sell).
- Every number comes straight from `data/fertilizer.csv` through the Step 5 change calculator. Missing changes show "n/a", never a guess.
- First real brief is in `briefs/2026-11-02.md` / `.html` (Iowa + Illinois prices from the Oct 30 reports). All changes are "n/a" for now because we only have one week of saved prices; they fill in on their own as weekly pulls add history.
- 16 new tests (79 total, all pass).

**How to try it**
`python -m pytest`. Then `python -m costwire.brief --date 2026-11-02` and open `briefs/2026-11-02.html` in your browser.

**What Andy needs to do**
Nothing new. (Still open from before: the free EIA key as a GitHub secret `EIA_API_KEY`, and the GitHub billing block that stops Actions; both matter for Step 8.)

**Next:** Step 7 — static site (`site/` with latest brief, archive list, signup form placeholder, build script).

## 2026-11-01 — Step 5: Change calculator
**What I built**
- `src/costwire/changes.py` works out, for every price in `data/fertilizer.csv`, how much it moved vs about 2 weeks ago and vs about 1 year ago, in dollars and percent. Results go to `data/changes.csv` (one row per item + region).
- It only compares a price with an earlier real saved price from the same report, same state, same item and same unit (Iowa anhydrous is never compared with Illinois anhydrous). The earlier price must be dated close to the target: within 4 days of "2 weeks ago", within 7 days of "1 year ago". If there isn't one, the change is left blank, never estimated. Each comparison keeps the earlier price's date and source link.
- Right now every change is blank: we've only saved one week of prices (Oct 30, 2026). The 2-week numbers fill in on their own once the weekly pulls build up history; the 1-year numbers need a year of history (or older report data loaded later).
- 11 new tests (63 total, all pass).
- README: added `export PYTHONPATH=src` to the setup steps (without it, `python -m costwire...` can't find the code) and the new command.

**How to try it**
`python -m pytest`. Then `python -m costwire.changes` and open `data/changes.csv`.

**What Andy needs to do**
Nothing new. (Still open from before: the free EIA key as a GitHub secret, and the GitHub billing block that stops Actions; both matter for Step 8.)

**Next:** Step 6 — brief writer (weekly brief as Markdown + HTML: headline = biggest move, table, one line per item, sources, disclaimer).

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
