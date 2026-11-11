"""Brief writer: turns the saved prices into the weekly brief (Markdown + HTML).

No AI, just a template. The brief has:
  - a headline: the biggest price move (by percent) vs 2 weeks ago
    (or vs 1 year ago if there are no 2-week changes yet)
  - a table: every price, its change vs 2 weeks and 1 year ago, date, source
  - one "what changed" line per item
  - the sources (with links and dates)
  - a disclaimer (data, not advice)

Product rules: never guess a number. Every number comes straight from the
saved data (data/fertilizer.csv, via the change calculator), which only keeps
prices that have a source link and date. A missing change is shown as
"n/a", never filled in. We describe prices; we never say buy or sell.

Run it:  python -m costwire.brief            (brief dated today)
         python -m costwire.brief --date 2026-11-02
Writes briefs/<date>.md and briefs/<date>.html
"""

import argparse
import html
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from . import affordability, changes, corn_price
from .paths import BRIEFS_DIR

ITEM_NAMES = {
    "anhydrous": "Anhydrous ammonia",
    "urea": "Urea",
    "uan28": "UAN 28%",
    "uan32": "UAN 32%",
    "dap": "DAP",
    "map": "MAP",
    "potash": "Potash",
    "diesel": "Farm diesel",
    "propane": "Propane",
    "onhwy_diesel": "On-highway diesel (retail)",
    "res_propane": "Residential propane",
    "ddgs": "Dried distillers grains (10%)",
}

REGION_NAMES = {
    "IA": "Iowa",
    "IL": "Illinois",
    "MN": "Minnesota",
    "WI": "Wisconsin",
    "PADD2": "Midwest (PADD 2)",
}

# Order items show up in the table: fertilizer first, then fuel, then feed.
ITEM_ORDER = list(ITEM_NAMES)

PERIOD_WORDS = {"2w": "2 weeks", "1y": "a year"}

DISCLAIMER = (
    "Data, not advice. These are average prices published by the government "
    "sources listed above, "
    "not quotes. Your dealer's price may differ. The Cost Wire does not tell "
    "anyone to buy or sell. Check each source link for the full report."
)


# ---------- small formatting helpers ----------

def item_name(item: str) -> str:
    return ITEM_NAMES.get(item, item)


def item_in_sentence(item: str) -> str:
    """'Anhydrous ammonia' -> 'anhydrous ammonia', but keep 'DAP' and 'UAN 28%' as is."""
    name = item_name(item)
    if len(name) > 1 and name[0].isupper() and name[1].islower():
        return name[0].lower() + name[1:]
    return name


def region_name(region: str) -> str:
    return REGION_NAMES.get(region, region)


def money(value: float) -> str:
    return f"${value:,.2f}"


def per_unit(unit: str) -> str:
    """'$/ton' -> '/ton' so we can write '$902.33/ton'."""
    return unit[1:] if unit.startswith("$") else f" {unit}"


def short_date(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def signed_change(dollars, pct) -> str:
    """'+$20.00 (+2.3%)', '-$5.00 (-1.0%)', or 'n/a' when we have no earlier price."""
    if dollars is None:
        return "n/a"
    sign = "+" if dollars > 0 else "-" if dollars < 0 else ""
    text = f"{sign}{money(abs(dollars))}"
    if pct is not None:
        text += f" ({'+' if pct > 0 else ''}{pct:.1f}%)"
    return text


# States first (in the order of REGION_NAMES), regional averages like PADD 2 last.
REGION_ORDER = list(REGION_NAMES)


def sort_key(r: dict) -> tuple:
    order = ITEM_ORDER.index(r["item"]) if r["item"] in ITEM_ORDER else len(ITEM_ORDER)
    reg = REGION_ORDER.index(r["region"]) if r["region"] in REGION_ORDER else len(REGION_ORDER)
    return (reg, r["region"], order, r["item"])


# ---------- the content ----------

def biggest_move(results: list[dict]):
    """(row, period) for the biggest percent move, or None if nothing moved yet.

    Uses 2-week changes; falls back to 1-year changes only if there are no
    2-week changes at all. Ties go to the bigger dollar move, then name order.
    """
    for period in ("2w", "1y"):
        candidates = sorted((r for r in results
                             if r.get(f"pct_{period}") is not None and r[f"change_{period}"] != 0),
                            key=lambda r: (r["item"], r["region"]))
        if candidates:
            # max() keeps the first of equal values, so ties go to name order
            best = max(candidates, key=lambda r: (abs(r[f"pct_{period}"]),
                                                   abs(r[f"change_{period}"])))
            return best, period
    return None


def headline(results: list[dict]) -> str:
    move = biggest_move(results)
    if move is None:
        return "Input prices this week (no earlier prices saved yet to compare)"
    r, period = move
    dollars, pct = r[f"change_{period}"], r[f"pct_{period}"]
    way = "up" if dollars > 0 else "down"
    return (f"{region_name(r['region'])} {item_in_sentence(r['item'])} {way} "
            f"{money(abs(dollars))}{per_unit(r['unit'])} ({abs(pct):.1f}%) "
            f"vs {PERIOD_WORDS[period]} ago")


def what_changed(r: dict) -> str:
    """One plain sentence per item."""
    name = f"{region_name(r['region'])} {item_in_sentence(r['item'])}"
    price = f"{money(r['price'])}{per_unit(r['unit'])}"
    parts = []
    for period in ("2w", "1y"):
        dollars = r.get(f"change_{period}")
        if dollars is None:
            continue
        then = f"{money(r[f'price_{period}'])} on {short_date(r[f'as_of_{period}'])}"
        if dollars == 0:
            parts.append(f"unchanged from {then}")
        else:
            way = "up" if dollars > 0 else "down"
            pct = r.get(f"pct_{period}")
            pct_text = f" ({abs(pct):.1f}%)" if pct is not None else ""
            parts.append(f"{way} {money(abs(dollars))}{pct_text} from {then}")
    if not parts:
        return f"{name}: {price} as of {short_date(r['as_of'])}. No earlier price saved yet to compare."
    return f"{name}: {price} as of {short_date(r['as_of'])}, " + "; ".join(parts) + "."


def sources(results: list[dict]) -> list[dict]:
    """Unique sources with the newest date we used from each."""
    found = {}
    for r in results:
        key = (r["source_name"], r["source_url"])
        if key not in found or r["as_of"] > found[key]:
            found[key] = r["as_of"]
    return [{"name": n, "url": u, "as_of": d} for (n, u), d in sorted(found.items())]


def credit_line(srcs: list[dict], nass: bool = False) -> str:
    """Credit only the agencies whose numbers are actually in this brief."""
    names = " ".join(s["name"] for s in srcs)
    agencies = []
    if "USDA" in names:
        agencies.append("USDA Agricultural Marketing Service (AMS)")
    if nass:
        agencies.append("USDA National Agricultural Statistics Service (NASS)")
    if "EIA" in names or "Energy Information" in names:
        agencies.append("U.S. Energy Information Administration (EIA)")
    if not agencies:
        return ""
    joined = agencies[0] if len(agencies) == 1 else ", ".join(agencies[:-1]) + " and " + agencies[-1]
    return "Data: " + joined + "."


def month_label(corn) -> str:
    return f"{date(corn.year, corn.month, 1):%b %Y}"


AFFORD_TITLE = "Bushels of corn to buy 1 ton"
AFFORD_NOTE = ("Fertilizer price (USDA AMS) divided by the state's average corn price "
               "received by farmers for the newest month NASS has published (USDA NASS). "
               "Left out when either number is missing.")


def afford_line(a: dict) -> str:
    """One plain sentence per fertilizer + state. Numbers only, no advice."""
    name = f"{region_name(a['region'])} {item_in_sentence(a['item'])}"
    corn = a["corn"]
    text = (f"{name}: {a['bushels']:,.1f} bushels of corn per ton "
            f"({money(a['fert_price'])}/ton as of {short_date(a['fert_as_of'])} "
            f"÷ {money(corn.value)}/bu {region_name(a['region'])} corn price received, "
            f"{month_label(corn)})")
    if a["bushels_1y"] is not None:
        diff = a["change_1y"]
        way = ("the same as" if diff == 0 else
               f"{abs(diff):,.1f} {'more' if diff > 0 else 'fewer'} bushels than")
        text += (f"; {way} 1 year earlier: {a['bushels_1y']:,.1f} bushels "
                 f"({money(a['fert_price_1y'])}/ton as of {short_date(a['fert_as_of_1y'])} "
                 f"÷ {money(a['corn_1y'].value)}/bu, {month_label(a['corn_1y'])})")
    return text + "."


def afford_sources(afford: list[dict]) -> list[dict]:
    """The NASS corn price queries used, one per state, with the months used."""
    found = {}
    for a in afford:
        for corn in (a["corn"], a["corn_1y"]):
            if corn is None:
                continue
            entry = found.setdefault(corn.source_url, {"name": corn.source_name,
                                                        "url": corn.source_url,
                                                        "state": corn.state, "months": set()})
            entry["months"].add((corn.year, corn.month))
    out = []
    for e in sorted(found.values(), key=lambda e: e["url"]):
        months = ", ".join(f"{date(y, m, 1):%b %Y}" for y, m in sorted(e["months"]))
        out.append({"name": e["name"], "url": e["url"],
                    "what": f"{region_name(e['state'])} corn price received, {months}"})
    return out


def build(results: list[dict], brief_date: date, corn_prices=None) -> dict:
    """Everything the templates need, in one dict."""
    rows = sorted(results, key=sort_key)
    afford = affordability.compute(results, corn_prices or [])
    return {
        "date": brief_date,
        "headline": headline(rows),
        "rows": rows,
        "lines": [what_changed(r) for r in rows],
        "afford": [afford_line(a) for a in afford],
        "afford_sources": afford_sources(afford),
        "sources": sources(rows),
        "credit": credit_line(sources(rows), nass=bool(afford)),
    }


# ---------- the two templates ----------

def to_markdown(b: dict) -> str:
    out = [f"# The Cost Wire — week of {short_date(b['date'])}", "",
           f"## {b['headline']}", "",
           "| Item | Region | Price | vs 2 weeks ago | vs 1 year ago | As of | Source |",
           "|---|---|---|---|---|---|---|"]
    for r in b["rows"]:
        out.append(
            f"| {item_name(r['item'])} | {region_name(r['region'])} "
            f"| {money(r['price'])}{per_unit(r['unit'])} "
            f"| {signed_change(r['change_2w'], r['pct_2w'])} "
            f"| {signed_change(r['change_1y'], r['pct_1y'])} "
            f"| {short_date(r['as_of'])} | [{r['source_name']}]({r['source_url']}) |")
    out += ["", "n/a = no earlier price saved yet for that date, so no change is shown.", "",
            "## What changed", ""]
    out += [f"- {line}" for line in b["lines"]]
    if b.get("afford"):
        out += ["", f"## {AFFORD_TITLE}", "", AFFORD_NOTE, ""]
        out += [f"- {line}" for line in b["afford"]]
    out += ["", "## Sources", ""]
    out += [f"- [{s['name']}]({s['url']}) — data as of {short_date(s['as_of'])}"
            for s in b["sources"]]
    out += [f"- [{s['name']}]({s['url']}) — {s['what']}" for s in b.get("afford_sources", [])]
    out += ["", b["credit"], "", f"*{DISCLAIMER}*", ""]
    return "\n".join(out)


def to_html(b: dict) -> str:
    e = html.escape
    title = f"The Cost Wire — week of {short_date(b['date'])}"
    rows = "\n".join(
        "<tr>"
        f"<td>{e(item_name(r['item']))}</td><td>{e(region_name(r['region']))}</td>"
        f"<td class=num>{e(money(r['price']) + per_unit(r['unit']))}</td>"
        f"<td class=num>{e(signed_change(r['change_2w'], r['pct_2w']))}</td>"
        f"<td class=num>{e(signed_change(r['change_1y'], r['pct_1y']))}</td>"
        f"<td>{e(short_date(r['as_of']))}</td>"
        f"<td><a href=\"{e(r['source_url'])}\">{e(r['source_name'])}</a></td>"
        "</tr>" for r in b["rows"])
    lines = "\n".join(f"<li>{e(line)}</li>" for line in b["lines"])
    srcs = "\n".join(
        f"<li><a href=\"{e(s['url'])}\">{e(s['name'])}</a> — data as of {e(short_date(s['as_of']))}</li>"
        for s in b["sources"])
    srcs += "".join(f"\n<li><a href=\"{e(s['url'])}\">{e(s['name'])}</a> — {e(s['what'])}</li>"
                    for s in b.get("afford_sources", []))
    afford = ""
    if b.get("afford"):
        items = "\n".join(f"<li>{e(line)}</li>" for line in b["afford"])
        afford = (f"<h2>{e(AFFORD_TITLE)}</h2>\n<p class=\"note\">{e(AFFORD_NOTE)}</p>\n"
                  f"<ul>\n{items}\n</ul>\n")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>
body {{ font-family: Georgia, serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #222; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.95rem; }}
th, td {{ border-bottom: 1px solid #ddd; padding: 0.4rem; text-align: left; }}
td.num {{ text-align: right; white-space: nowrap; }}
.table-wrap {{ overflow-x: auto; }}
.note, .disclaimer {{ color: #555; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>{e(title)}</h1>
<h2>{e(b['headline'])}</h2>
<div class="table-wrap">
<table>
<thead><tr><th>Item</th><th>Region</th><th>Price</th><th>vs 2 weeks ago</th><th>vs 1 year ago</th><th>As of</th><th>Source</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
<p class="note">n/a = no earlier price saved yet for that date, so no change is shown.</p>
<h2>What changed</h2>
<ul>
{lines}
</ul>
{afford}<h2>Sources</h2>
<ul>
{srcs}
</ul>
<p>{e(b['credit'])}</p>
<p class="disclaimer"><em>{e(DISCLAIMER)}</em></p>
</body>
</html>
"""


# ---------- running it ----------

def today_central() -> date:
    return datetime.now(ZoneInfo("America/Chicago")).date()


def write_brief(brief_date: date, in_path=None, out_dir=None, corn_path=None):
    """Build the brief from saved prices. Returns (md_path, html_path), or None if no data."""
    rows = changes.read_rows(in_path)
    if not rows:
        return None
    b = build(changes.compute(rows), brief_date, corn_price.load_prices(corn_path))
    out_dir = out_dir or BRIEFS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{brief_date.isoformat()}.md"
    html_path = out_dir / f"{brief_date.isoformat()}.html"
    md_path.write_text(to_markdown(b), encoding="utf-8")
    html_path.write_text(to_html(b), encoding="utf-8")
    return md_path, html_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Write the weekly Cost Wire brief.")
    parser.add_argument("--date", type=date.fromisoformat, default=None,
                        help="brief date YYYY-MM-DD (default: today, Central time)")
    args = parser.parse_args(argv)
    written = write_brief(args.date or today_central())
    if written is None:
        print("No saved prices yet; run python -m costwire.pull_fertilizer first.")
        return 1
    print(f"Wrote {written[0]} and {written[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
