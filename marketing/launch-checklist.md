# Marketing launch checklist (asset 11)

Asset 11 of marketing/MARKETING-PLAN.md. The tech side is in `docs/launch-checklist.md`; this is the
order to use the marketing assets already drafted in `marketing/`. Nothing here is sent, posted or spent
until Andy replies SEND/POST in chat. No FFA, schools or colleges. No subscriber counts, testimonials or
income claims anywhere. Data, not advice.

## Gate: don't announce until all four are true
- [ ] Signup form is live (`SIGNUP_LIVE=yes`, tested with Andy's own email). Without it, every post sends people to a page that can't collect them.
- [ ] Andy emailed himself a test brief and read it on his phone (`python -m costwire.email_brief`).
- [ ] Andy clicked three source links on the live site and each number matched the USDA/EIA page.
- [ ] The newest brief is from this week (Monday job ran).

## Launch week (one thing a day, ~20 minutes each)
| Day | Asset | File | Who does it |
|---|---|---|---|
| Mon | Update site copy from the landing page draft (if not done) | `marketing/landing-page-copy.md` | Claude, after Andy says OK |
| Mon | Tell the Commodity Wire list (Andy's own list) | `marketing/cross-promo-commodity-wire.md` | Andy sends |
| Tue | AgTalk post (read the forum rules first) | `marketing/agtalk-post.md` | Andy posts |
| Wed | r/farming post (read the sidebar rules first) | `marketing/reddit-post.md` | Andy posts |
| Thu | 5 outreach messages to ag news desks (confirm each contact page first) | `marketing/outreach-messages.md` | Andy sends |
| Fri | Record the 30-second video with this week's numbers | `marketing/video-script.md` | Andy records/posts |
| Sat | Add the "forward it to a neighbor" footer to the email | `marketing/referral-offer.md` | Claude, after Andy says OK |

Before each post: swap in the numbers from the newest brief (each with its source link and date). Never reuse an old week's numbers as "this week".

## Week 2-3
- [ ] Publish the two SEO articles on the site (`marketing/seo-cash-rent-article.md`, `marketing/seo-fertilizer-vs-last-year.md`). The cash rent one waits for `NASS_API_KEY` so its table has real numbers.
- [ ] Only after a free week is counted: the $20 ad test (`marketing/ad-test-plan.md`). Andy makes the Facebook Page and pays himself; Claude never spends.

## New this week: the RSS feed
The site now has a free RSS feed: https://aatten01-netizen.github.io/the-cost-wire/feed.xml (live after the next Monday build).
Use it in pitches: ag news desks and farm-media aggregators can follow the feed instead of an email signup.
Ready-to-paste line for the outreach messages (asset 2):
> Prefer a feed? The Cost Wire has a free RSS feed of every weekly brief: https://aatten01-netizen.github.io/the-cost-wire/feed.xml . Every number in it links back to the USDA or EIA report it came from.

## What to write down each week (free, no tools)
1. Signups this week (count rows in the Google Sheet).
2. Which post or message went out that day (date + link).
3. Any reader who says a number looks wrong: fix it and reply with the source.
No analytics on the static site, so no pageview numbers are claimed anywhere.
