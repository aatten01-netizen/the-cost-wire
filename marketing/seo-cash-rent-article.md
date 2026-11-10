# SEO article: Midwest cash rent by county

Status: DRAFT for Andy's OK. Not published. Contains NO dollar figures on purpose:
`site/cash-rent.html` says cash rent numbers are not loaded yet (needs `NASS_API_KEY`),
and we never guess a number. Once the key is set and the page has real data, add a
sourced table where marked [ADD TABLE].

- Target search: "cash rent by county Iowa", "NASS cash rent county Wisconsin", "average cash rent per acre by county"
- Title tag (under 60 chars): Midwest Cash Rent by County: Where the Real Numbers Are
- Meta description (under 155): Where to find USDA NASS cash rent by county for WI, IA, IL and MN, how to read it, and why it is an average, not a quote for your field.
- URL slug: /cash-rent-by-county

---

# Midwest cash rent by county: where to find the real numbers

If you rent ground, or rent it out, you have heard a number at the coffee shop. Here is where the published numbers come from, and how to read them.

## The source: USDA NASS Cash Rents Survey
The U.S. Department of Agriculture's National Agricultural Statistics Service (NASS) surveys farmers and landowners every year on what land rents for in cash. Results are published as dollars per acre for:
- Non-irrigated cropland
- Irrigated cropland
- Pasture

NASS publishes state averages, and county averages where enough responses came in. If your county is missing, NASS did not have enough responses to publish without exposing individual farms.

## How to look up your county
1. Go to NASS Quick Stats: https://quickstats.nass.usda.gov/
2. Choose Survey, then Economics, then Land & Rent, then Rent.
3. Pick your state and county, the year, and the land type.
4. Note the year. Rent averages describe a past survey, not today's lease talks.

(Click paths can change. Check them on the live site before publishing.)

## How to read it
- **It is an average.** Soil, field size, drainage, lease terms and who the landlord is all move one farm's rent away from the county number.
- **Counties with few responses can swing** year to year.
- **Compare year to year,** not one number alone. Look at the change and the survey year.
- **It is not a quote.** It is data about what was reported, not a statement of what any farm should pay or charge.

## Cash rent next to input costs
Rent is only one cost. Fertilizer, diesel and feed move more often. The Cost Wire puts those side by side each week, from USDA and EIA, with a source link and date on every number: [LINK].

[ADD TABLE: county cash rent, last 3 survey years, WI/IA/IL/MN, from the Cash Rents page once loaded. Each row: value, survey year, "Source: USDA NASS". Only counties NASS published.]

## Sources
- USDA NASS Cash Rents Survey and Quick Stats: https://quickstats.nass.usda.gov/
- The Cost Wire cash rent page: [LINK]/cash-rent.html

*Data, not advice. The Cost Wire shows published numbers and does not tell anyone what to rent, buy or sell.*

---
## Before publishing (Andy)
- Set `NASS_API_KEY` so the cash rent page has real data, then fill [ADD TABLE].
- Confirm the Quick Stats click path and the latest survey year on the live site.
- Replace [LINK] with the live URL.
