# The Cost Wire

This repo is **The Cost Wire**: a weekly input-cost brief for Midwest farmers (fertilizer, fuel, feed, cash rent, land values).
Owner: Andy Atten (solo founder, agribusiness student, not a pro developer). Part of his Claude-run businesses.

Read BRIEF.md first (what we're building and why), then PLAN.md (the build steps in order).

## How to work here
- Do ONE step from PLAN.md at a time: the first unchecked one. Finish it, test it, check it off.
- Keep code simple and readable. Explain each change in plain English in LOG.md.
- Use free tools and free tiers. Never sign up for, buy, or upgrade anything; never add a paid service without Andy's OK. Write down what Andy needs to do instead.
- Secrets (API keys, tokens) only from environment variables. Never commit keys. Keep `.env.example` up to date.
- Write tests for logic and run them before committing.
- Never delete Andy's data or files outside this repo.

## Product rules
- Data, not advice. Never tell farmers to buy or sell.
- Never guess a number. Every number needs a source URL and date; if a source is missing, leave the number out.
- Credit USDA/EIA/NASS as the source.

## Logging
After each session, add an entry at the top of LOG.md:
`## YYYY-MM-DD — Step N: <name>` then: what you built, how to try it, anything Andy needs to do (keys, sign-ups, decisions), what's next.

## ANDY'S RULE: NO FFA, NO COLLEGES, NO SCHOOLS (Nov 6, 2026, applies to every bot and every project)
Never target, market to, pitch, recruit, list as leads, or plan outreach, partnerships, events, speaking or ads aimed at FFA chapters, ag teachers, high schools, colleges, universities, college ag clubs, student groups or campus events. Instead, every bot actively markets its own business and works on getting it real customers, aimed at whoever that business actually serves: farmers and ag businesses for the ag products, and for the non-ag products their own buyers (small-business owners, trades, traders, creators, everyday adults, etc.). (Andy's own classes, handled by the School bot, are not affected.)

## MARKETING SESSION (Andy, Nov 6, 2026 - every bot, every business, ag and non-ag)
Every build bot is also its business's marketer. Each run: do your normal build step, THEN a short marketing session for the same business/product:
1. If it has no marketing/MARKETING-PLAN.md (inside the product's own folder), create it: who the real buyer is, where they hang out (real, named communities/sites, cited), top 2 competitors with prices, the offer, and a checklist of 8-12 marketing assets.
2. Build the next unmade asset completely, ready to use: landing page copy, 5 ready-to-send outreach messages to real public prospects (public pages/emails/contact forms only), value-first community posts with each group's self-promo rules, short-video scripts, an SEO article, a partnership or referral offer, a $0-$20 ad test plan, or a launch checklist.
3. Save it in marketing/, check it off, and add one line to LOG.md: "Marketing: <asset> - Andy: reply SEND/POST in chat to have it sent".
Rules: never send, post, DM, comment, sign up or spend on your own - Andy approves in chat. No fake testimonials, user counts or income claims. Keep the product's own rules (data not advice, education only, etc.). Skip only if a separate marketing bot already covers this exact business (Commodity Wire has one).
