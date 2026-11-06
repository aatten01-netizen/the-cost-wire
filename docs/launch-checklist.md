# Launch checklist for Andy

Check your progress any time with `PYTHONPATH=src python -m costwire.launch_check`.
It shows what is ready on this computer. It cannot see GitHub secrets or Pages, so do those by hand below.

Do these in order. Nothing here costs money except step 1 if GitHub asks for a card.

## A. Get the weekly job running
1. **Fix GitHub Actions billing.** Actions is blocked until this is sorted: https://github.com/settings/billing . Public repos get free minutes; check the repo is public or the spending limit allows it.
2. **Add the free EIA key** (Midwest diesel + propane). Get it: https://www.eia.gov/opendata/register.php . Save as repo secret `EIA_API_KEY`: https://github.com/aatten01-netizen/the-cost-wire/settings/secrets/actions
3. **Add the free NASS key** (cash rent + land values). Get it: https://quickstats.nass.usda.gov/api . Save as repo secret `NASS_API_KEY` (same page).
4. **Turn on GitHub Pages:** https://github.com/aatten01-netizen/the-cost-wire/settings/pages . Source: "GitHub Actions". Then add repo variable `PAGES_ENABLED` = `true`: https://github.com/aatten01-netizen/the-cost-wire/settings/variables/actions
5. **Run it once by hand:** Actions tab > "Weekly brief" > Run workflow: https://github.com/aatten01-netizen/the-cost-wire/actions

## B. Feed line (Step 10b)
6. Download https://www.ams.usda.gov/mnreports/ams_3618.pdf and upload it as `tests/samples/ams_3618.pdf`: https://github.com/aatten01-netizen/the-cost-wire/upload/main/tests/samples . (Or run Actions > "Fetch sample reports".) Then ask Claude to run Step 10b.

## C. Email (test first)
7. Put your Resend key in `RESEND_API_KEY` and your own address in `BRIEF_TEST_EMAIL` on the computer you send from. Send: `python -m costwire.email_brief`. Read the email on your phone.
8. Real subscribers are NOT emailed by any code yet. That is a decision for you later.

## D. Signup form
9. Follow `docs/signup-google-sheet.md` (about 5 minutes), add repo variable `SIGNUP_FORM_URL`.
10. Test with your own email. When you approve, add repo variable `SIGNUP_LIVE` = `yes`.

## E. Before you tell anyone
11. Open the live site on your phone. Click three source links. Confirm each number matches the USDA/EIA page.
12. Read the disclaimer line: data, not advice.
13. Wait for the success test from BRIEF.md: 4 weekly briefs in a row with zero wrong numbers (the accuracy check runs before every build).
14. Check each source's terms of use once (USDA AMS, EIA, NASS) before you publish widely. All three credit lines are already in every brief.

## What "launched" means here
Site is public on Pages, the Monday job ran at least once with real keys, the signup form is live, and you have emailed yourself a test brief.
