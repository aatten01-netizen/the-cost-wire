# REVENUE — The Cost Wire

Part of Andy's $100K/month goal across all businesses (end of 2027). Updated every build run.

## Price and tiers
- **Free:** weekly Monday brief (IA/IL fertilizer, Midwest diesel/propane, DDGS), cash rent page, archive, RSS. Builds the list.
- **Pro (planned, not open):** $9/month or $90/year. Your state's brief, price-move email alerts, cost-per-acre worksheet. Price lives in `src/costwire/pricing.py`; Andy can change it.
- Later: a team/ag-business tier (co-ops, agronomists, lenders) is possible but not planned yet.

## Who pays
Midwest corn/soy and livestock farmers who buy fertilizer, fuel and feed and rent ground (IA, IL, MN, WI first).

## Path to this product's share (ESTIMATE, not a promise)
- Assumed share for The Cost Wire: ~$5K/month of the $100K (the biggest path is Commodity Wire; see later-projects GOAL-100K.md).
- $5,000 / $9 ≈ **560 Pro subscribers**. At a guessed 3-5% free-to-paid rate that needs roughly **11,000-19,000 free readers**. These are assumptions for planning, not data.
- Nearer milestone: first 5 paying farmers = $45/month.

## Still missing before the first dollar
1. Signup form live (Andy: docs/signup-google-sheet.md), so there is a free list to sell to. **Biggest blocker.**
2. 5 readers say they'd pay (marketing/pro-interest-survey.md).
3. Andy checks a few real test alerts in his own inbox (ALERTS_LIVE=yes, test address only), then a few free beta testers (marketing/pro-alerts-beta-invite.md). Alert logic, sign-up page, Sheet export and the Resend sender (test address only) are all built.
4. Unsubscribe link + mailing address set (UNSUBSCRIBE_URL + MAIL_POSTAL_ADDRESS, docs/unsubscribe.md): the law requires both before any reader email. Code done Nov 17, 2026; Andy makes a free Google Form and picks the address.
5. Stripe Payment Link made by Andy and set as `PRO_CHECKOUT_URL` + `PRO_CHECKOUT_LIVE=yes` (only after alerts exist).
- Done: pricing page with mock checkout (`site/pricing.html`, Nov 12, 2026); price-move alert logic with mock sender (`src/costwire/alerts.py`, Nov 12, 2026); alert sign-up page `site/alerts.html` + Sheet-to-alert-list export (Nov 13, 2026); weekly Action now passes the Pro checkout switch; real alert sender via Resend, test address only, off unless ALERTS_LIVE=yes (Nov 13, 2026); sample Pro alert page `site/pro-sample.html`, linked from pricing (Nov 14, 2026; shows a real move once a second report is saved); cost-per-pound-of-N line on the free brief (Nov 14, 2026), a reason for farmers to read and share it; cost-per-acre worksheet `site/worksheet.html` (Nov 15, 2026); state editions of the brief `site/state/` (Nov 15, 2026); state choice on the free signup + per-state reader list export `costwire.state_list` (Nov 16, 2026); welcome email draft that asks each reader's state (marketing/welcome-email.md). State-edition email sender `costwire.state_email`: dry run by default, test address only when live (Nov 16, 2026). **All three Pro features on the pricing page now exist** (state brief, alerts, worksheet). Every email now carries an unsubscribe link + mailing address and honors an unsubscribe list (Nov 17, 2026). What's left before a first dollar is Andy's switches and real readers, not code.

## Fastest next step to the first dollar
Andy turns on the signup form (SIGNUP_FORM_URL + SIGNUP_LIVE=yes) and makes the free unsubscribe form + picks a mailing address (docs/unsubscribe.md), then sends the Pro survey to the first readers. Every PLAN step is done and every Pro feature is built. Andy decides whether the state editions and worksheet stay free previews or go Pro-only once checkout opens. Emailing each reader their state edition is built (dry run / test address only); real sends wait for readers and Andy's OK.
