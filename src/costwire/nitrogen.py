"""Cost per pound of nitrogen (N): compare N sources on the same footing.

  $ per lb of N = fertilizer price ($/ton, USDA AMS) / (2,000 lb x N share)

N share is the product's grade (its fixed guaranteed nitrogen content, the first
number on the label): anhydrous ammonia 82-0-0, urea 46-0-0, UAN 28-0-0, UAN 32-0-0.
These are product definitions, not prices, so they are constants here.

For Iowa and Illinois, from the newest saved AMS price for each item.

Product rule: never guess a number. An item with no saved price (or a price that
isn't a real number above zero, or isn't in $/ton) is simply left out. Numbers
only: nothing here says which product to buy.
"""

import math

# Nitrogen share by weight, from each product's grade.
N_SHARE = {"anhydrous": 0.82, "urea": 0.46, "uan28": 0.28, "uan32": 0.32}
GRADE = {"anhydrous": "82-0-0", "urea": "46-0-0", "uan28": "28-0-0", "uan32": "32-0-0"}
ITEMS = list(N_SHARE)
STATES = ["IA", "IL"]
LB_PER_TON = 2000


def lb_n_per_ton(item: str) -> int:
    """Pounds of N in one ton of the product (anhydrous: 1,640)."""
    return round(LB_PER_TON * N_SHARE[item])


def per_lb(price: float, item: str) -> float:
    """Dollars per pound of N, to the cent."""
    return round(price / (LB_PER_TON * N_SHARE[item]), 2)


def usable(price) -> bool:
    return isinstance(price, (int, float)) and math.isfinite(price) and price > 0


def compute(results: list[dict]) -> list[dict]:
    """One row per N item + state with a usable price. `results` = changes.compute() output."""
    rows = []
    for r in results:
        if (r["item"] not in N_SHARE or r["region"] not in STATES
                or r["unit"] != "$/ton" or not usable(r["price"])):
            continue
        rows.append({"item": r["item"], "region": r["region"], "price": r["price"],
                     "as_of": r["as_of"], "source_name": r["source_name"],
                     "source_url": r["source_url"], "lb_n": lb_n_per_ton(r["item"]),
                     "per_lb": per_lb(r["price"], r["item"])})
    rows.sort(key=lambda x: (STATES.index(x["region"]), ITEMS.index(x["item"])))
    return rows
