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
4. Stripe Payment Link made by Andy and set as `PRO_CHECKOUT_URL` + `PRO_CHECKOUT_LIVE=yes` (only after alerts exist).
- Done: pricing page with mock checkout (`site/pricing.html`, Nov 12, 2026); price-move alert logic with mock sender (`src/costwire/alerts.py`, Nov 12, 2026); alert sign-up page `site/alerts.html` + Sheet-to-alert-list export (Nov 13, 2026); weekly Action now passes the Pro checkout switch; real alert sender via Resend, test address only, off unless ALERTS_LIVE=yes (Nov 13, 2026).

## Fastest next step to the first dollar
Andy turns on the signup form (SIGNUP_FORM_URL + SIGNUP_LIVE=yes), then sends the Pro survey to the first readers. Next bot build: market-scan step "Sample Pro alert page" (site/pro-sample.html), picked ahead of the cost-per-pound-of-N line because it helps sell Pro.
