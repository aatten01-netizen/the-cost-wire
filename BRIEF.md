# The Cost Wire — Build Brief

**One line:** A weekly input-cost brief for Midwest farmers: fertilizer, fuel, feed, cash rent and land values in one place, with the trend and what changed. Commodity Wire tells farmers what they can *sell* for; The Cost Wire tells them what it *costs* to grow.

## Problem
Farmers make big buying decisions (fall fertilizer, diesel, feed, renting ground) with scattered, stale price info. The public numbers exist (USDA, EIA, NASS) but they're buried in PDFs on a dozen sites and nobody puts them side by side with last year.

## Who pays and how much
- **Free tier (v1):** weekly email + web page. Builds the list.
- **Paid tier (v2, ~$9–15/month):** your state's numbers, price alerts ("anhydrous dropped $40/ton"), cost-per-acre calculator, and (later) prices other farmers nearby actually paid — this is where the Input & Feed Price Checker plugs in.
- Same brand family as Commodity Wire; cross-promote both lists.

## v1 — what ships first (keep it this small)
1. **Weekly data pull** from free public sources (below), saved as clean CSV/JSON.
2. **Weekly brief page + email** (Monday): fertilizer prices (anhydrous, urea, UAN, DAP, potash) vs 2 weeks ago and a year ago; Midwest diesel and propane; a feed line; one "biggest move" headline; disclaimer.
3. **Simple website**: latest brief, archive, signup form.
4. **Cash rent + land value page** (annual NASS data, Wisconsin + neighbor states, by county where published).
5. **Accuracy check**: every number links to its source and date.

Later (not v1): state picker, alerts, cost-per-acre calculator, user-reported prices, paid tier.

## Data sources (all free)
| What | Source | How often |
|---|---|---|
| Fertilizer + fuel (Iowa) | USDA AMS Iowa Production Cost Report (report 2863), also published as CSV on ESMIS | Bi-weekly |
| Fertilizer (Illinois) | USDA AMS Illinois Production Cost Report | Bi-weekly |
| Diesel, propane | EIA open data API (free key) — Midwest (PADD 2) on-highway diesel, propane | Weekly |
| Feed | USDA AMS feedstuffs / distillers grains reports | Weekly |
| Cash rent, land values | USDA NASS Quick Stats API (free key) — Cash Rents survey, Land Values | Yearly |

Check each source's terms before publishing. Always credit USDA/EIA.

## Stack (free)
- **Python** scripts for the data pull and the brief (same language as Market Sentry).
- **GitHub Actions** (free) runs the pull on a schedule and builds the site.
- **GitHub Pages** (free) hosts the static site.
- **Resend** (Andy already uses it) for the email; free tier to start.
- **Stripe Payment Links** later for the paid tier (no monthly fee).

## Rules
- Data, not advice. Never "buy now." Describe prices and changes.
- Never guess a number. Missing source = leave it out and say so.
- Plain farmer voice, short sentences.

## How we'll know it works
- 4 weekly briefs in a row with zero wrong numbers.
- 100 free signups (cross-promoted from Commodity Wire) before building the paid tier.
- 5 farmers say they'd pay for their state + alerts.
