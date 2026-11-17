# "Tell me when Pro opens" waitlist push (asset 23)

**Goal:** get 5 clear "yes, I'd pay" answers (BRIEF.md) on the pricing page's waitlist form, so Andy knows when to open Pro checkout. Count them with `python -m costwire.pro_waitlist signups.csv` (numbers only).
**When:** only after the signup form is live (SIGNUP_LIVE=yes). Before that the form does not show.
**Who:** free brief readers and farmers in the brand's own channels. Never schools, colleges, FFA or student groups. Bots don't post or send these; Andy approves in chat.
**Rules:** no fake counts ("100 farmers joined"), no income or savings claims, data not advice.

---

## 1. Monday brief P.S. (paste at the bottom of the brief email)

P.S. I'm deciding whether to open The Cost Wire Pro: your state's brief, an email when a published price moves more than the amount you pick, and a cost-per-acre worksheet. $9/month or $90/year. If that's worth it to you, there's a one-question "tell me when Pro opens" box on the pricing page: https://aatten01-netizen.github.io/the-cost-wire/pricing.html#waitlist. Nothing is charged. A "no" or "maybe" helps too.

## 2. Facebook post (brand page only)

Should The Cost Wire add a paid tier?

The free Monday brief stays free: Iowa and Illinois fertilizer, Midwest diesel and propane, distillers grains, each number linked to its USDA or EIA report.

Pro would add your state's own brief, an email alert when a published price moves by the amount you pick, and a cost-per-acre worksheet. $9/month.

If you'd pay for that (or wouldn't), answer one question here: https://aatten01-netizen.github.io/the-cost-wire/pricing.html#waitlist
Nothing is charged. Data, not advice.

## 3. Reply to a reader who asks "when will alerts be ready?" (email reply)

Thanks for asking. Alerts are built and tested; I'm opening them as part of Pro once enough readers say they'd use it. If you add your answer to the one-question box on the pricing page (https://aatten01-netizen.github.io/the-cost-wire/pricing.html#waitlist), you'll be told first when it opens. Nothing is charged until you choose to start.

Andy, The Cost Wire. Data, not advice.

---

**After it runs:** put the tally (numbers only, never names or emails) in LOG.md. At 5 clear yes, Andy makes the Stripe Payment Link (PRO_CHECKOUT_URL + PRO_CHECKOUT_LIVE=yes).
