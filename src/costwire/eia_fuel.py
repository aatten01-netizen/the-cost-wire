"""Puller for EIA weekly Midwest (PADD 2) diesel and propane prices.

Source: U.S. Energy Information Administration (EIA), API v2 (free key).
  - On-highway diesel, Midwest retail, $/gal (weekly, every Monday):
    https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EMD_EPD2D_PTE_R20_DPG&f=W
  - Residential propane, Midwest, $/gal (weekly, heating season Oct-Mar only):
    https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=W_EPLLPA_PRS_R20_DPG&f=W

These are different products from the "farm diesel" and "propane" in the
USDA state reports (on-highway diesel includes road taxes), so they get their
own item names: "onhwy_diesel" and "res_propane", region "PADD2".

The API key comes ONLY from the EIA_API_KEY environment variable. If it's
missing, we print a note and skip cleanly (no crash, no data). The key is
never saved anywhere: the source link we store is the public EIA page above.

Run it:  python -m costwire.eia_fuel
"""

import os
import sys
from datetime import date, datetime

from . import iowa_cost
from .records import PriceRecord

SOURCE_NAME = "U.S. Energy Information Administration (EIA)"
REGION = "PADD2"
API_ROOT = "https://api.eia.gov/v2"
STALE_DAYS = 14

# Our item name -> (EIA API route, EIA series id, unit)
SERIES = {
    "onhwy_diesel": ("petroleum/pri/gnd", "EMD_EPD2D_PTE_R20_DPG", "$/gal"),
    "res_propane": ("petroleum/pri/wfr", "W_EPLLPA_PRS_R20_DPG", "$/gal"),
}


def series_page(series_id: str) -> str:
    """Public EIA page for a weekly series (what we store as the source link)."""
    return f"https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s={series_id}&f=W"


def api_params(series_id: str, api_key: str, weeks: int = 1) -> dict:
    """Query for the newest `weeks` weekly values of one series."""
    return {
        "api_key": api_key,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": series_id,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": weeks,
    }


def parse_response(payload: dict, item: str, series_id: str, unit: str) -> list[PriceRecord]:
    """Turn an EIA API v2 JSON reply into PriceRecords.

    Rows without a value or a readable date are left out, never guessed.
    Rows for a different series (shouldn't happen) are ignored.
    """
    rows = (payload.get("response") or {}).get("data") or []
    records = []
    for row in rows:
        if row.get("series") not in (None, series_id):
            continue
        value = row.get("value")
        if value in (None, "", "NA"):
            continue
        try:
            price = float(value)
            as_of = datetime.strptime(str(row.get("period")), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            print(f"WARNING: skipped unreadable EIA row for {item}: {row}", file=sys.stderr)
            continue
        records.append(PriceRecord(item, price, unit, as_of, series_page(series_id),
                                   SOURCE_NAME, REGION))
    return records


def _get_json(url: str, params: dict) -> dict:
    import requests

    resp = requests.get(url, params=params, timeout=60,
                        headers={"User-Agent": "TheCostWire/0.1"})
    resp.raise_for_status()
    return resp.json()


def pull(get_json=None, api_key=None, today=None, out=None, weeks: int = 1) -> list[PriceRecord]:
    """Fetch the newest weekly prices and save them to data/fertilizer.csv.

    Returns [] (and saves nothing) when EIA_API_KEY isn't set.
    One series failing doesn't stop the other.
    """
    api_key = api_key if api_key is not None else os.environ.get("EIA_API_KEY", "")
    if not api_key.strip():
        print("EIA_API_KEY not set: skipping EIA diesel + propane. "
              "Free key: https://www.eia.gov/opendata/register.php")
        return []
    get_json = get_json or _get_json
    today = today or date.today()
    out = out or iowa_cost.OUTPUT_FILE

    records = []
    for item, (route, series_id, unit) in SERIES.items():
        try:
            payload = get_json(f"{API_ROOT}/{route}/data/", api_params(series_id, api_key, weeks))
        except Exception as exc:
            # Don't echo the request URL: it would contain the key.
            print(f"EIA {item} pull failed: {type(exc).__name__}", file=sys.stderr)
            continue
        got = parse_response(payload, item, series_id, unit)
        if not got:
            note = " (EIA only publishes it Oct-Mar)" if item == "res_propane" else ""
            print(f"No EIA {item} price returned{note}.")
            continue
        records.extend(got)
        newest = max(r.as_of for r in got)
        if (today - newest).days > STALE_DAYS:
            print(f"WARNING: newest EIA {item} price is from {newest}.")

    if records:
        added = iowa_cost.save_records(records, out)
        print(f"EIA: {len(records)} prices, {added} new rows -> {out}")
    return records


if __name__ == "__main__":
    try:
        pull()
    except Exception as exc:
        print(f"EIA pull failed: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
