"""Affordability line: how many bushels of corn it takes to buy 1 ton of fertilizer.

  bushels per ton = fertilizer price ($/ton, USDA AMS) / corn price received ($/bu, USDA NASS)

For anhydrous, urea and UAN 28% in Iowa and Illinois, now and 1 year ago.

Which corn price goes with which fertilizer price:
  the newest NASS month that STARTS on or before the fertilizer price date and is
  at most MAX_MONTH_GAP months older than it (NASS publishes a month's price about
  a month later, so the newest is usually last month or the month before).
  Same state only. The year-ago figure uses the fertilizer price from ~1 year
  earlier (the change calculator's 1-year match) and the SAME month one year earlier.

Product rule: never guess a number. If either price is missing, the line (or
the year-ago part) is left out. Nothing here says whether to buy or sell.
"""

import math
from datetime import date

ITEMS = ["anhydrous", "urea", "uan28"]
STATES = ["IA", "IL"]
MAX_MONTH_GAP = 3


def months_between(later: date, earlier: date) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


def usable(corn) -> bool:
    """A real corn price: a finite number above zero. A 0, blank or "nan" row in the
    saved CSV would crash the division or print "nan bushels", so it's left out
    (the accuracy check still flags the bad row)."""
    return isinstance(corn.value, (int, float)) and math.isfinite(corn.value) and corn.value > 0


def pick_corn(prices, state: str, as_of: date):
    """The corn price to pair with a fertilizer price dated `as_of`, or None."""
    ok = [p for p in prices
          if usable(p) and p.state == state and p.month_start <= as_of
          and months_between(as_of, p.month_start) <= MAX_MONTH_GAP]
    return max(ok, key=lambda p: p.month_start) if ok else None


def year_before(prices, corn):
    """The same state's corn price for the same month one year earlier, or None."""
    for p in prices:
        if usable(p) and p.state == corn.state and p.year == corn.year - 1 and p.month == corn.month:
            return p
    return None


def bushels(fert_price: float, corn_price: float) -> float:
    return round(fert_price / corn_price, 1)


def compute(results: list[dict], corn_prices) -> list[dict]:
    """One row per item + state that has both prices. `results` = changes.compute() output."""
    rows = []
    for r in results:
        if r["item"] not in ITEMS or r["region"] not in STATES or r["unit"] != "$/ton":
            continue
        corn = pick_corn(corn_prices, r["region"], r["as_of"])
        if corn is None:
            continue
        row = {"item": r["item"], "region": r["region"],
               "fert_price": r["price"], "fert_as_of": r["as_of"],
               "fert_source_name": r["source_name"], "fert_source_url": r["source_url"],
               "corn": corn, "bushels": bushels(r["price"], corn.value),
               "fert_price_1y": None, "fert_as_of_1y": None, "corn_1y": None,
               "bushels_1y": None, "change_1y": None}
        corn_1y = year_before(corn_prices, corn)
        if r.get("price_1y") is not None and corn_1y is not None:
            row.update({"fert_price_1y": r["price_1y"], "fert_as_of_1y": r["as_of_1y"],
                        "corn_1y": corn_1y, "bushels_1y": bushels(r["price_1y"], corn_1y.value)})
            row["change_1y"] = round(row["bushels"] - row["bushels_1y"], 1)
        rows.append(row)
    rows.sort(key=lambda x: (STATES.index(x["region"]), ITEMS.index(x["item"])))
    return rows
