# Cross-promo offer: The Cost Wire → Commodity Wire list (draft for Andy's approval)

Asset 8 of marketing/MARKETING-PLAN.md. Nothing here is sent or posted until Andy replies SEND/POST in chat.
Rules kept: data, not advice; no subscriber counts, testimonials or income claims; every number links to its source.

## The offer (plain)
Commodity Wire readers get the selling side (grain markets). The Cost Wire is the cost side: one free Monday page of Midwest input prices (fertilizer, diesel, propane, feed, cash rent) from USDA and EIA, each number with its source link and date.
Free, no card, unsubscribe anytime. In return, The Cost Wire's brief carries a one-line "See Commodity Wire" link (already in the landing page copy).

## Placement 1: one-time blurb in a Commodity Wire email (about 70 words)
**Subject line add-on (optional):** + what inputs cost this week

> **New from the same desk: The Cost Wire**
> You know what corn and beans are paying. The Cost Wire is the other half: what fertilizer, diesel, propane and feed cost in Iowa, Illinois, Minnesota and Wisconsin, next to two weeks ago and a year ago. Straight from USDA and EIA, every number linked to its report. Free every Monday.
> [Get the Monday brief → LINK]
> Data, not advice. We report prices; we never tell you to buy or sell.

## Placement 2: standing footer line (every Commodity Wire email)
> Input costs, sourced to USDA and EIA, every Monday: The Cost Wire (free) → LINK

## Placement 3: text/SMS version (only to people who already opted in to Commodity Wire texts)
> Commodity Wire: our sister brief The Cost Wire posts Midwest fertilizer, diesel & feed prices from USDA/EIA every Monday. Free: LINK Reply STOP to opt out.

## Placement 4: YouTube/video mention (10 seconds, end of a Commodity Wire video)
> "That's the selling side. For the cost side, fertilizer, diesel and feed prices straight from USDA every Monday, check out The Cost Wire, free, link below. Not advice, just the numbers."

## The "corn vs fertilizer" hook (use only once real numbers exist)
The new bushels-per-ton line (PLAN market-scan step, built Nov 11) shows "Iowa anhydrous: X bushels of corn per ton" from USDA AMS ÷ USDA NASS. It only appears once `NASS_API_KEY` is set and the weekly job has pulled corn prices. When a real brief shows it, swap this into Placement 1's first sentence:
> "This week it took [X] bushels of [state] corn to buy a ton of [fertilizer] (USDA AMS ÷ USDA NASS, [month])."
Copy X, state, fertilizer and month exactly from that week's brief. Never fill in a number that isn't in a published brief.

## Tracking (free)
Use a different link per placement so Andy can see which works: add `?src=cw-email`, `?src=cw-footer`, `?src=cw-text`, `?src=cw-video` to the Cost Wire site link. (GitHub Pages has no analytics; the signup sheet can store the `src` value if the form passes it along. Optional, Andy's call.)

## Before sending (Andy)
- [ ] Signup form is live (docs/launch-checklist.md), so LINK goes somewhere useful.
- [ ] Replace LINK with https://aatten01-netizen.github.io/the-cost-wire/ (plus the `?src=` tag if wanted).
- [ ] Text version: only to Commodity Wire's own opted-in text list; keep "Reply STOP".
- [ ] Commodity Wire has its own marketing bot: tell it (or paste this file) so the blurb goes in its next send.
