# $0-$20 Ad Test Plan — The Cost Wire (draft for Andy's approval)
Created 2026-11-12 (night shift). Nothing here has been bought, boosted or posted. Andy approves in chat and pays himself.
Rules kept: data not advice (no "buy now", no "prices will rise"); no fake user counts or testimonials; NO targeting of FFA, schools, colleges, students or campus groups (Andy's rule).

## Before spending a cent (all must be true)
1. Site is live: https://aatten01-netizen.github.io/the-cost-wire/ (live since Nov 8).
2. Signup form is live (`SIGNUP_LIVE` = `yes`, see docs/launch-checklist.md, part D). **No form = no ads.** Clicks with nowhere to sign up are wasted money.
3. The newest brief has real numbers with source links (the accuracy check passed).

## The one question this test answers
"Will Midwest farmers give us their email for a free Monday input-cost brief, and at what cost per signup?"
Goal: learn, not grow. $20 total, hard cap.

## Step 0 — free ($0) first
Do these before paying. They cost nothing and tell us which message to pay for.
- Post the AgTalk and r/farming drafts (marketing/agtalk-post.md, marketing/reddit-post.md) once Andy approves.
- Send the Commodity Wire cross-promo (marketing/cross-promo-commodity-wire.md).
- Count signups in the signup Google Sheet for 1 week. Write the number in LOG.md.

## Paid test — Facebook/Instagram boosted post, $20 total
Why Facebook: lots of Midwest farmers use it, a boost can be as small as a few dollars a day, and Andy can stop it any time. (Check the current minimum daily budget in Meta Ads Manager; not verified this run.)

Two ads, $10 each, same audience, run at the same time, so the only difference is the message.

| | Ad A: "One page" | Ad B: "Source on every number" |
|---|---|---|
| Budget | $2/day × 5 days = $10 | $2/day × 5 days = $10 |
| Run | Mon–Fri (brief comes out Monday) | same days |
| Link | site home page + `?utm_source=fb&utm_campaign=adA` | `?utm_source=fb&utm_campaign=adB` |

### Audience (both ads)
- Location: Iowa, Illinois, Minnesota, Wisconsin.
- Age: 25–65+.
- Interests (pick what Meta offers): Agriculture, Farm, Farmer, Corn, Soybean, John Deere, Tractor.
- Do NOT add: any school, college, university, FFA, 4-H, student or education interest. Do not use "Education level" or "Field of study" targeting.

### Ad A copy
**Text:** Fertilizer, diesel, propane and feed for the Midwest on one page, every Monday. Compared with 2 weeks ago and a year ago. Straight from USDA and EIA. Free.
**Headline:** What it costs to grow it
**Button:** Sign Up
**Image:** screenshot of the newest brief's price table (real numbers only, from the live site, with the source line visible).

### Ad B copy
**Text:** Every number in The Cost Wire links to the USDA or EIA report it came from, with the date. Anhydrous, urea, UAN, DAP, potash, diesel, propane, DDGS. Free weekly brief for IA, IL, MN, WI.
**Headline:** Input prices with the receipts
**Button:** Sign Up
**Image:** screenshot of one price row next to its "Source: USDA AMS, Oct 30, 2026" style link (use whatever the newest brief really shows).

Small print to add to both (in the post text if there's room): "Data, not advice. Not affiliated with USDA or EIA."

## How we measure (honest version)
- Meta Ads Manager shows: people reached, link clicks, cost per click.
- Signups: count new rows in the signup Google Sheet during the 5 days. The static site has no analytics, so we cannot tell Ad A signups from Ad B signups for sure. The UTM tags show up in Meta's report only. Compare click-through rate between A and B; compare total signups to the week before (Step 0 baseline).
- Write results in LOG.md: spend, clicks, cost per click, signups, cost per signup.

## Stop rules
- Stop an ad early if it gets 0 clicks after $4.
- Stop everything at $20. No "just one more day".
- Stop at once if comments ask "should I buy now?". Reply only with: "We just report the USDA/EIA numbers; we can't give buying advice." (Andy replies, not the bot.)

## What counts as a win (decide before looking at results)
- Cost per signup under $2 → worth a $50 second test (Andy decides).
- $2–$5 → try the better ad's message in the free posts instead.
- Over $5 or 0 signups → no more paid ads for now; stick to free channels and the Commodity Wire cross-promo.

## Andy's checklist
- [ ] Signup form live (`SIGNUP_LIVE` = `yes`).
- [ ] Facebook Page for The Cost Wire (Andy makes it; the bot never signs up).
- [ ] Take the 2 screenshots from the live brief.
- [ ] Boost Ad A and Ad B, $10 each, settings above.
- [ ] After 5 days, paste the Ads Manager numbers in chat; the bot logs them.
