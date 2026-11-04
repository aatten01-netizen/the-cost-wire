"""Cash rent + land value page (site/cash-rent.html), built from data/land.csv.

Shows, per state, the newest state-level cash rent and land value with the
change from the year before (only when both years exist), and a county table
for each state where NASS published county cash rents. Every row links to its
source. No data yet gives a plain "not loaded yet" page. Data, not advice.
"""

import html

from . import nass_land

TITLES = {
    "cash_rent_cropland": "Cash rent, non-irrigated cropland",
    "cash_rent_pasture": "Cash rent, pasture",
    "land_value_cropland": "Land value, cropland",
    "land_value_farm": "Land value, farm real estate (with buildings)",
}
STATE_NAMES = {"WI": "Wisconsin", "IA": "Iowa", "IL": "Illinois", "MN": "Minnesota"}


def money(v: float) -> str:
    return f"${v:,.0f}"


def change_text(new: float, old) -> str:
    if old is None or old == 0:
        return "n/a"
    diff = new - old
    sign = "+" if diff >= 0 else "-"
    return f"{sign}${abs(diff):,.0f} ({sign}{abs(diff) / old * 100:.1f}%)"


def state_rows(records):
    """[(item, state, newest, previous_year_value_or_None, source_url)] for state-level numbers."""
    by = {}
    for r in records:
        if not r.county:
            by.setdefault((r.item, r.state), {})[r.year] = r
    rows = []
    for (item, state), years in by.items():
        newest = years[max(years)]
        prev = years.get(newest.year - 1)
        rows.append((item, state, newest, prev.value if prev else None, newest.source_url))
    order = list(TITLES)
    return sorted(rows, key=lambda t: (order.index(t[0]), t[1]))


def county_rows(records):
    """{state: [(county, newest LandRecord)]} for county cash rent on cropland, A-Z."""
    best = {}
    for r in records:
        if r.county and r.item == "cash_rent_cropland":
            k = (r.state, r.county)
            if k not in best or r.year > best[k].year:
                best[k] = r
    out = {}
    for (state, county), rec in sorted(best.items()):
        out.setdefault(state, []).append((county, rec))
    return out


def link(url: str, text: str) -> str:
    return f'<a href="{html.escape(url, quote=True)}">{html.escape(text)}</a>'


def render(records) -> str:
    esc = html.escape
    if not records:
        body = "<p>Cash rent and land value numbers are not loaded yet.</p>"
    else:
        parts = ["<h2>State numbers</h2>",
                 "<table><tr><th>Measure</th><th>State</th><th>Year</th><th>$/acre</th>"
                 "<th>Change from year before</th><th>Source</th></tr>"]
        for item, state, rec, prev, url in state_rows(records):
            parts.append(
                f"<tr><td>{esc(TITLES[item])}</td><td>{esc(STATE_NAMES.get(state, state))}</td>"
                f"<td>{rec.year}</td><td>{money(rec.value)}</td>"
                f"<td>{esc(change_text(rec.value, prev))}</td><td>{link(url, 'NASS')}</td></tr>")
        parts.append("</table>")
        counties = county_rows(records)
        if counties:
            parts.append("<h2>Cash rent by county (non-irrigated cropland)</h2>"
                         "<p>Only counties where NASS published a number are listed.</p>")
            for state, rows in counties.items():
                parts.append(f"<h3>{esc(STATE_NAMES.get(state, state))}</h3>"
                             "<table><tr><th>County</th><th>Year</th><th>$/acre</th>"
                             "<th>Source</th></tr>")
                for county, rec in rows:
                    parts.append(f"<tr><td>{esc(county)}</td><td>{rec.year}</td>"
                                 f"<td>{money(rec.value)}</td>"
                                 f"<td>{link(rec.source_url, 'NASS')}</td></tr>")
                parts.append("</table>")
        body = "\n".join(parts)
    return body_page(body)


def body_page(body: str) -> str:
    return f"""<h1>Cash rent and land values</h1>
<p>Yearly numbers from the USDA NASS Cash Rents and Land Values surveys, in dollars per acre.</p>
{body}
<p class="note">Source: {html.escape(nass_land.SOURCE_NAME)}. Survey averages, not what any one
farm pays or gets. Data, not advice.</p>"""
