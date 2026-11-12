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
3. Alert sign-up on the site (Step 18) and a real sender (Step 19). The alert logic itself is built (Step 17, mock sender).
4. Stripe Payment Link made by Andy and set as `PRO_CHECKOUT_URL` + `PRO_CHECKOUT_LIVE=yes` (only after alerts exist).
- Done: pricing page with mock checkout (`site/pricing.html`, Nov 12, 2026); price-move alert logic with mock sender (`src/costwire/alerts.py`, Nov 12, 2026).

## Fastest next step to the first dollar
Andy turns on the signup form (SIGNUP_FORM_URL + SIGNUP_LIVE=yes), then sends the Pro survey to the first readers. Next bot build: Step 18, alert sign-up (item, state, dollar amount) on the site.
