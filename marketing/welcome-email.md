# Welcome email for new signups (with the state question)

Use: the first email a new free reader gets after signing up. Andy sends it by hand from Resend (or Gmail) until there's an automated welcome. **Not sent yet - Andy: reply SEND in chat.**
Rules kept: data, not advice; no user counts; no dealer names; no fake quotes.

---

**Subject:** You're on The Cost Wire - one quick question

**Preview text:** Monday's input prices, plus your state's page if you want it.

Hi,

Thanks for signing up for The Cost Wire. Here's what to expect:

- **Every Monday:** one short email with fertilizer (anhydrous, urea, UAN, DAP, potash), Midwest diesel and propane, and distillers grains prices, each compared to 2 weeks ago and a year ago.
- **Every number has its source and date** (USDA AMS, EIA, USDA NASS). If a report is missing, we leave the number out and say so. We never guess.
- **Data, not advice.** We tell you what prices did. We never tell you when to buy.

**One quick question:** which state do you farm in?
Just hit reply with **IA, IL, MN or WI** (or "other"). We're building a version of the brief with only your state's numbers on top. You can see this week's preview here:
https://aatten01-netizen.github.io/the-cost-wire/state/index.html

While you wait for Monday:
- This week's brief: https://aatten01-netizen.github.io/the-cost-wire/
- Cash rent and land values by state: https://aatten01-netizen.github.io/the-cost-wire/cash-rent.html
- Cost-per-acre worksheet (type your own rates, nothing is sent): https://aatten01-netizen.github.io/the-cost-wire/worksheet.html

If a number ever looks wrong to you, reply and tell me. I'd rather fix it than have you trust a bad one.

Andy
The Cost Wire

*Data from USDA AMS, USDA NASS and the U.S. Energy Information Administration. Not financial advice. To stop these emails, reply STOP.*

---

## When a reader replies with a state
Add their state to the `state` column (column F) of the "Cost Wire signups" Sheet on their row. Then `python -m costwire.state_list` (docs/signup-google-sheet.md) puts them on the right state list.

## Short version (text/DM, for someone Andy already knows who signed up)
> Thanks for signing up for The Cost Wire. Monday's email has fertilizer, fuel and feed prices with sources. Which state do you farm, IA, IL, MN or WI? We're building a state-only version.
