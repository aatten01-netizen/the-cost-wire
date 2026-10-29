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
