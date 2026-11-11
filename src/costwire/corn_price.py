"""Puller for the USDA NASS monthly corn price received (Iowa and Illinois).

Source: USDA National Agricultural Statistics Service (NASS), Quick Stats
(free key): https://quickstats.nass.usda.gov/api
Measure: "CORN, GRAIN - PRICE RECEIVED, MEASURED IN $ / BU", state level,
monthly. This is the average price farmers in that state were paid for corn
in that month (from the NASS Agricultural Prices report).

Used for the brief's "bushels of corn to buy 1 ton" line (see affordability.py).

Saved to data/corn_price.csv: one row per state + month, with the value and a
source link. The link is the exact Quick Stats query we ran, WITHOUT the key.
A month NASS left out ("(D)", "(NA)", blank) is left out here too.
NASS can revise a month (preliminary -> final): the newer pull replaces it.

The key comes ONLY from the NASS_API_KEY environment variable. If it's
missing we print a note and skip cleanly. The key is never saved or printed.

Run it:  python -m costwire.corn_price
"""

import csv
import os
import sys
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode

from .nass_land import API_URL, SOURCE_NAME, _get_json, parse_value
from .paths import DATA_DIR

OUTPUT_FILE = DATA_DIR / "corn_price.csv"
SHORT_DESC = "CORN, GRAIN - PRICE RECEIVED, MEASURED IN $ / BU"
STATES = ["IA", "IL"]
YEARS_BACK = 2  # this year and the two before, so a year-ago month is always there
UNIT = "$/bu"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
COLUMNS = ["state", "year", "month", "value", "unit", "source_url", "source_name"]


@dataclass(frozen=True)
class CornPrice:
    state: str
    year: int
    month: int        # 1-12
    value: float      # $/bu
    source_url: str
    source_name: str = SOURCE_NAME
    unit: str = UNIT

    @property
    def key(self):
        return (self.state, self.year, self.month)

    @property
    def month_start(self) -> date:
        return date(self.year, self.month, 1)


def query_params(state: str, first_year: int) -> dict:
    """Quick Stats query (no key) for one state's monthly corn price received."""
    return {
        "source_desc": "SURVEY",
        "short_desc": SHORT_DESC,
        "state_alpha": state,
        "agg_level_desc": "STATE",
        "freq_desc": "MONTHLY",
        "year__GE": first_year,
        "format": "JSON",
    }


def source_url(params: dict) -> str:
    """The public link to repeat a query: same parameters, no key."""
    return f"{API_URL}?{urlencode(params)}"


def parse_response(payload: dict, url: str) -> list[CornPrice]:
    """Quick Stats JSON reply -> CornPrice list. Unusable rows are skipped."""
    out = []
    for row in (payload or {}).get("data") or []:
        if row.get("short_desc") != SHORT_DESC:
            continue
        if row.get("agg_level_desc") not in (None, "STATE"):
            continue
        period = (row.get("reference_period_desc") or "").strip().upper()
        if period not in MONTHS:
            continue  # e.g. "MARKETING YEAR" or "YEAR": not a month
        try:
            year = int(row.get("year"))
        except (TypeError, ValueError):
            continue
        value = parse_value(row.get("Value"))
        if value is None or value <= 0:
            continue
        state = (row.get("state_alpha") or "").strip().upper()
        if not state:
            continue
        out.append(CornPrice(state, year, MONTHS.index(period) + 1, value, url))
    return out


def load_prices(path=None) -> list[CornPrice]:
    path = path or OUTPUT_FILE
    if not path.exists():
        return []
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                out.append(CornPrice(r["state"], int(r["year"]), int(r["month"]),
                                     float(r["value"]), r["source_url"], r["source_name"],
                                     r["unit"]))
            except (KeyError, TypeError, ValueError):
                print(f"WARNING: skipped unreadable corn price row: {r}", file=sys.stderr)
    return out


def save_prices(prices, path=None) -> int:
    """Merge into the CSV (a repeat state+month replaces the old row). Returns new-row count."""
    path = path or OUTPUT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = {p.key: p for p in load_prices(path)}
    new = sum(1 for p in prices if p.key not in merged)
    for p in prices:
        merged[p.key] = p
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for p in sorted(merged.values(), key=lambda p: p.key):
            w.writerow([p.state, p.year, p.month, f"{p.value:g}", p.unit,
                        p.source_url, p.source_name])
    return new


def pull(get_json=None, api_key=None, today=None, out=None, states=None) -> list[CornPrice]:
    """Fetch monthly corn prices received and save them. [] when NASS_API_KEY isn't set."""
    api_key = api_key if api_key is not None else os.environ.get("NASS_API_KEY", "")
    if not api_key.strip():
        print("NASS_API_KEY not set: skipping NASS corn price received "
              "(the bushels-per-ton line is left out). Free key: https://quickstats.nass.usda.gov/api")
        return []
    get_json = get_json or _get_json
    first_year = (today or date.today()).year - YEARS_BACK
    prices, failed = [], 0
    for state in states or STATES:
        params = query_params(state, first_year)
        try:
            payload = get_json(API_URL, {**params, "key": api_key})
        except Exception as exc:
            # Don't echo the request URL: it would contain the key.
            print(f"NASS corn price {state} pull failed: {type(exc).__name__}", file=sys.stderr)
            failed += 1
            continue
        prices.extend(parse_response(payload, source_url(params)))
    if prices:
        added = save_prices(prices, out or OUTPUT_FILE)
        print(f"NASS corn price: {len(prices)} months, {added} new rows -> {out or OUTPUT_FILE}")
    else:
        print("NASS corn price: no numbers returned.")
    if failed:
        print(f"WARNING: {failed} NASS corn price queries failed.", file=sys.stderr)
    return prices


def main() -> int:
    try:
        pull()
    except Exception as exc:
        print(f"NASS corn price pull failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
