"""Since early March: each fertilizer's newest price vs its last report before March 4, 2026.

Farmers remember this spring's fertilizer price jump. This puts a number on it,
straight from the saved USDA AMS prices (data/fertilizer.csv):

  newest IA/IL price  vs  the last saved report from the SAME source, item,
  region and unit dated before 2026-03-04  ->  change in $ and %

Product rules: never guess a number. If no saved report before March 4 exists for
a fertilizer, its line is simply left out (today none is saved, so the section
does not show until an older report is added to the data). Both prices carry
their own date and source link. Numbers only: nothing here says buy or sell.
"""

import math
from datetime import date

from . import changes

CUTOFF = date(2026, 3, 4)          # baseline = newest saved report dated BEFORE this day
FERTILIZERS = ("anhydrous", "urea", "uan28", "uan32", "dap", "map", "potash")
STATES = ("IA", "IL")


def _usable(price) -> bool:
    return isinstance(price, (int, float)) and math.isfinite(price) and price > 0


def baseline(result: dict, history: list[dict]):
    """Newest saved row of the same series dated before CUTOFF, or None."""
    key = changes.series_key(result)
    older = [r for r in history
             if changes.series_key(r) == key and r["as_of"] < CUTOFF and _usable(r["price"])]
    return max(older, key=lambda r: r["as_of"]) if older else None


def compute(results: list[dict], history: list[dict]) -> list[dict]:
    """One row per IA/IL fertilizer that has both a newest price and a pre-March baseline."""
    out = []
    for r in results:
        if (r["item"] not in FERTILIZERS or r["region"] not in STATES
                or not _usable(r["price"]) or r["as_of"] < CUTOFF):
            continue
        b = baseline(r, history)
        if b is None:
            continue
        change = round(r["price"] - b["price"], 2)
        out.append({"item": r["item"], "region": r["region"], "unit": r["unit"],
                    "price": r["price"], "as_of": r["as_of"], "source_url": r["source_url"],
                    "base_price": b["price"], "base_as_of": b["as_of"],
                    "base_source_url": b["source_url"],
                    "change": change, "pct": round(change / b["price"] * 100, 1)})
    out.sort(key=lambda x: (STATES.index(x["region"]), FERTILIZERS.index(x["item"])))
    return out
