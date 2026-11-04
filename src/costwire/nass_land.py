"""Puller for USDA NASS cash rents and farmland values (Quick Stats API).

Source: USDA National Agricultural Statistics Service (NASS), Quick Stats
(free key): https://quickstats.nass.usda.gov/api
Yearly numbers from the NASS Land Values and Cash Rents surveys:
  - cash rent, cropland (non-irrigated), $/acre: state AND county
  - cash rent, pasture, $/acre: state AND county
  - land value, cropland, $/acre: state only
  - land value, farm real estate (incl. buildings), $/acre: state only
for Wisconsin, Iowa, Illinois and Minnesota. County numbers are only there
where NASS published them; a county NASS left out ("(D)", "(NA)") is left out
here too. Nothing is ever filled in or guessed.

Saved to data/land.csv (separate from the weekly prices in fertilizer.csv).
Each row keeps the year, the value and a source link. The link is the exact
Quick Stats query we ran, WITHOUT the key (anyone with a free key can repeat it).

The key comes ONLY from the NASS_API_KEY environment variable. If it's
missing we print a note and skip cleanly. The key is never saved.

Run it:  python -m costwire.nass_land
"""

import csv
import os
import sys
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlencode

from .paths import DATA_DIR

SOURCE_NAME = "USDA National Agricultural Statistics Service (NASS)"
API_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
OUTPUT_FILE = DATA_DIR / "land.csv"
STATES = ["WI", "IA", "IL", "MN"]
YEARS_BACK = 2  # this year and the two before (cash rents lag; the newest year may be missing)

# NASS short_desc -> (our item name, whether NASS also publishes it by county)
ITEMS = {
    "RENT, CASH, CROPLAND, NON-IRRIGATED - EXPENSE, MEASURED IN $ / ACRE":
        ("cash_rent_cropland", True),
    "RENT, CASH, PASTURELAND - EXPENSE, MEASURED IN $ / ACRE":
        ("cash_rent_pasture", True),
    "AG LAND, CROPLAND - ASSET VALUE, MEASURED IN $ / ACRE":
        ("land_value_cropland", False),
    "AG LAND, INCL BUILDINGS - ASSET VALUE, MEASURED IN $ / ACRE":
        ("land_value_farm", False),
}
UNIT = "$/acre"
COLUMNS = ["item", "state", "county", "year", "value", "unit", "source_url", "source_name"]


@dataclass(frozen=True)
class LandRecord:
    item: str
    state: str
    county: str      # "" for a state-level number
    year: int
    value: float
    unit: str
    source_url: str
    source_name: str = SOURCE_NAME

    @property
    def key(self):
        return (self.item, self.state, self.county, self.year)


def query_params(short_desc: str, state: str, level: str, first_year: int) -> dict:
    """Quick Stats query (no key) for one measure, one state, STATE or COUNTY level."""
    return {
        "source_desc": "SURVEY",
        "short_desc": short_desc,
        "state_alpha": state,
        "agg_level_desc": level,
        "freq_desc": "ANNUAL",
        "reference_period_desc": "YEAR",
        "year__GE": first_year,
        "format": "JSON",
    }


def source_url(params: dict) -> str:
    """The public link to repeat a query: same parameters, no key."""
    return f"{API_URL}?{urlencode(params)}"


def parse_value(raw):
    """'1,234' -> 1234.0. NASS notes like '(D)' or '(NA)', and blanks, -> None."""
    text = str(raw if raw is not None else "").strip().replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def parse_response(payload: dict, url: str) -> list[LandRecord]:
    """Turn a Quick Stats JSON reply into LandRecords.

    Rows with no usable number, an unknown measure, or a bad year are skipped.
    """
    records = []
    for row in (payload or {}).get("data") or []:
        spec = ITEMS.get(row.get("short_desc"))
        if not spec:
            continue
        value = parse_value(row.get("Value"))
        try:
            year = int(row.get("year"))
        except (TypeError, ValueError):
            continue
        if value is None:
            continue
        level = row.get("agg_level_desc")
        county = (row.get("county_name") or "").strip().title() if level == "COUNTY" else ""
        if level == "COUNTY" and not county:
            continue
        if level not in ("STATE", "COUNTY"):
            continue
        state = (row.get("state_alpha") or "").strip().upper()
        if not state:
            continue
        records.append(LandRecord(spec[0], state, county, year, value, UNIT, url))
    return records


def load_records(path=None) -> list[LandRecord]:
    path = path or OUTPUT_FILE
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [LandRecord(r["item"], r["state"], r["county"], int(r["year"]), float(r["value"]),
                           r["unit"], r["source_url"], r["source_name"])
                for r in csv.DictReader(f)]


def save_records(records, path=None) -> int:
    """Add records to the CSV. A repeat of (item, state, county, year) replaces the old
    row (NASS can revise a number). Returns how many rows were new."""
    path = path or OUTPUT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = {r.key: r for r in load_records(path)}
    new = sum(1 for r in records if r.key not in merged)
    for r in records:
        merged[r.key] = r
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for r in sorted(merged.values(), key=lambda r: (r.item, r.state, r.county, r.year)):
            w.writerow([r.item, r.state, r.county, r.year, f"{r.value:g}", r.unit,
                        r.source_url, r.source_name])
    return new


def _get_json(url: str, params: dict) -> dict:
    import requests

    resp = requests.get(url, params=params, timeout=90,
                        headers={"User-Agent": "TheCostWire/0.1"})
    if resp.status_code == 400:
        return {"data": []}  # Quick Stats answers 400 when a query matches nothing
    resp.raise_for_status()
    return resp.json()


def pull(get_json=None, api_key=None, today=None, out=None, states=None) -> list[LandRecord]:
    """Fetch the newest cash rents and land values and save them to data/land.csv.

    Returns [] (and saves nothing) when NASS_API_KEY isn't set.
    One query failing doesn't stop the others.
    """
    api_key = api_key if api_key is not None else os.environ.get("NASS_API_KEY", "")
    if not api_key.strip():
        print("NASS_API_KEY not set: skipping NASS cash rents + land values. "
              "Free key: https://quickstats.nass.usda.gov/api")
        return []
    get_json = get_json or _get_json
    first_year = (today or date.today()).year - YEARS_BACK
    out = out or OUTPUT_FILE

    records, failed = [], 0
    for state in states or STATES:
        for short_desc, (item, has_county) in ITEMS.items():
            for level in (["STATE", "COUNTY"] if has_county else ["STATE"]):
                params = query_params(short_desc, state, level, first_year)
                try:
                    payload = get_json(API_URL, {**params, "key": api_key})
                except Exception as exc:
                    # Don't echo the request URL: it would contain the key.
                    print(f"NASS {item} {state} {level} pull failed: {type(exc).__name__}",
                          file=sys.stderr)
                    failed += 1
                    continue
                records.extend(parse_response(payload, source_url(params)))

    if records:
        added = save_records(records, out)
        print(f"NASS: {len(records)} numbers, {added} new rows -> {out}")
    else:
        print("NASS: no numbers returned.")
    if failed:
        print(f"WARNING: {failed} NASS queries failed.", file=sys.stderr)
    return records


def main() -> int:
    try:
        records = pull()
    except Exception as exc:
        print(f"NASS pull failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
