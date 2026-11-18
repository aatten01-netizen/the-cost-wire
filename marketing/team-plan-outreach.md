# Team plan outreach: ag lenders, agronomists, co-ops (ready to send)

**Goal:** get 3-5 ag businesses onto the Team waitlist (site/team.html) so Andy can set a real Team price.
**Status:** DRAFT. Nothing sent. Andy: reply SEND in chat and say which ones.
**Before sending:** the Team waitlist form only appears once the free signup is live (SIGNUP_FORM_URL + SIGNUP_LIVE=yes). Until then, ask them to reply by email instead (the messages below work either way).
**Rules kept:** data, not advice; no fake users, quotes or testimonials; no price promised (Team price is "ask"); public contact pages/forms only; no schools/colleges/FFA.

## Where to find them (public pages only, Andy checks each before sending)
| Who | Where | Contact route |
|---|---|---|
| Farm Credit lenders (IA) | Farm Credit Services of America, https://www.fcsamerica.com | Public "Contact us" page / local office page |
| Farm Credit lenders (IL) | 1st Farm Credit Services, https://www.1stfarmcredit.com | Public "Contact" page / branch page |
| Community ag bankers | Iowa Bankers Association ag committee, https://www.iowabankers.com ; Illinois Bankers Association, https://www.ilbanks.org | Bank's own public website contact form (find ag lenders by local bank site) |
| Independent agronomists / CCAs | Certified Crop Adviser public "Find a CCA" search, https://www.certifiedcropadviser.org | Listed public business contact only |
| Co-ops / ag retailers | Local co-op websites (e.g. Heartland Co-op https://www.heartlandcoop.com , West Central/Landus https://landus.ag) | Public "Contact us" form |

(Websites above from memory, not opened this run: Andy or the next run verify each link before use.)

---

## 1. Ag lender (Farm Credit / community bank ag lender) - contact form
**Subject:** Free weekly input-cost sheet for your farm clients

Hi,

I run The Cost Wire, a free Monday brief of published Midwest input prices: Iowa and Illinois fertilizer from USDA AMS, Midwest diesel and propane from EIA, distillers grains, and county cash rents from USDA NASS. Every number links to its USDA or EIA source and date.

Input costs are a big part of every operating-loan budget, so I'm building a Team plan: state editions (IA, IL, MN, WI) you can share with clients, plus an email alert when a published price moves more than the amount you pick. It reports prices only; it never tells anyone what to buy.

The price isn't set yet. If this would help your office, could you reply with your role and roughly how many farm clients you work with? I'll send a price before anything is charged.

Free brief and Team page: https://aatten01-netizen.github.io/the-cost-wire/team.html

Thanks,
Andy Atten, The Cost Wire

## 2. Independent agronomist / CCA - public business email or form
**Subject:** Published fertilizer prices by state, one page, every Monday

Hi,

Quick one: The Cost Wire puts the week's published USDA AMS fertilizer prices (anhydrous, urea, UAN, DAP, MAP, potash) for Iowa and Illinois on one page, with change vs 2 weeks and 1 year ago, cost per pound of N, and the source link on every number. It's free.

I'm adding a Team plan for agronomists who go over input costs with lots of growers: a state edition you can forward, price-move alerts, and a cost-per-acre worksheet where the grower types their own rates. Data only, no recommendations.

Would something like that be useful? If yes, a reply with how many growers you work with helps me set a fair price. Nothing is charged until you say yes to a price.

https://aatten01-netizen.github.io/the-cost-wire/team.html

Andy Atten, The Cost Wire

## 3. Co-op / ag retailer (marketing or agronomy manager) - contact form
**Subject:** A sourced weekly price sheet your agronomists can share

Hi,

I publish The Cost Wire, a free Monday brief of public USDA and EIA input prices for Iowa, Illinois, Minnesota and Wisconsin. It never names a dealer or shows anyone's quote; it's only the published state averages with their source and date.

I'm opening a Team plan for co-ops and retailers whose staff talk input costs with members every week. Would your agronomy or member-services team want a shared state edition and price-move alerts? The price isn't set; if you reply with roughly how many staff would use it, I'll come back with one. Nothing is charged until you agree.

https://aatten01-netizen.github.io/the-cost-wire/team.html

Andy Atten, The Cost Wire

## 4. Farm management / farm business consultant - contact form
**Subject:** Weekly published input prices for your client budgets

Hi,

When you build crop budgets for clients, The Cost Wire may save a step: every Monday it lists the latest published USDA AMS fertilizer prices for IA and IL, EIA Midwest diesel and propane, and NASS cash rents, each with its source link and date. Free to read.

I'm building a Team plan for consultants with many clients (state editions, price-move alerts, a cost-per-acre worksheet the farmer fills in with their own rates). Would that be worth a look? Reply with how many clients you serve and I'll send a price. Nothing is charged until you say yes.

https://aatten01-netizen.github.io/the-cost-wire/team.html

Andy Atten, The Cost Wire

## 5. Short follow-up (send 7 days later, only to anyone who didn't reply)
**Subject:** Re: weekly input-cost sheet

Hi, just following up once. Here's this week's free brief so you can see the format: https://aatten01-netizen.github.io/the-cost-wire/ . If a Team version for your clients isn't useful, no reply needed and I won't follow up again.

Andy

---
**After replies:** run `PYTHONPATH=src python -m costwire.team signups.csv` (counts only), note the numbers (no names) in LOG.md, then pick a Team price and set `TEAM_MONTHLY` in `src/costwire/team.py`.
