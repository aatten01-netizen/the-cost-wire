# Pro alerts: founding-tester invite (asset 15)

**Goal:** get the first 5 farmers to try price-move alerts before Pro opens, and hear whether they'd pay $9/month. No money changes hands in the beta.
**Who gets it:** readers who already signed up for the free brief (the Google Sheet list) or who replied to the Pro survey. Not schools, colleges, FFA or student groups.
**When:** only after (1) the signup form is live and (2) Andy has received a few test alerts himself (ALERTS_LIVE=yes sends them to his test address only).
**How it's sent:** Andy sends it himself, one reader at a time, from his own email. Bots never send it.

---

## Email (to one free reader)

**Subject:** Want a heads-up when your fertilizer price moves?

Hi {first name},

Thanks for reading The Cost Wire. I'm building one paid add-on and I'd like a few farmers to try it first, free.

It's a price-move alert: you pick one item (anhydrous, urea, UAN, DAP, MAP, potash, diesel, propane or DDGS), your state, and a dollar amount. When a new USDA or EIA report shows that price moved at least that much, you get a short email with both prices, both report dates and the source link. That's it. Data, not advice; it never tells you to buy or sell.

If you want in, just reply with:
1. Item
2. State (IA, IL, MN or WI)
3. Dollar move you care about (for example $20/ton)

After a few weeks I'll ask one question: would this be worth $9 a month to you? A "no" helps just as much as a "yes".

Thanks,
Andy
The Cost Wire
Reply STOP and I won't email you about this again.

---

## Short version (text or Facebook message to someone who already knows you)

Building a price-move alert for The Cost Wire: pick an item, your state and a $ amount, get an email when the USDA/EIA price moves that much (source + dates included, no advice). Free while I test it. Want in? Reply with item, state and $ amount.

---

## Rules for this asset
- No numbers in the invite. Real moves only show up in the alerts themselves, straight from `data/fertilizer.csv`.
- No user counts, testimonials or "farmers are saving $X" claims.
- Testers' choices go in the alert CSV outside the repo (ALERTS_FILE), never in this repo.
- Keep the "STOP" line; honor it right away.
