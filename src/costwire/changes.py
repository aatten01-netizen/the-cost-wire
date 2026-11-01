"""Change calculator: how much each price moved vs 2 weeks ago and vs 1 year ago.

Reads data/fertilizer.csv (every pull adds rows, so it builds up history) and
writes data/changes.csv with one row per item + region:
  latest price and date, the price ~2 weeks earlier and ~1 year earlier,
  and the change in dollars and percent.

Product rule: never guess a number. A comparison is only made against a real
saved price from the SAME source, region, item and unit, dated close to the
target (2 weeks: within 4 days; 1 year: within 7 days). If there's no such
price, the change is left blank, never filled in or estimated.

Run it:  python -m costwire.changes
"""

import csv
import sys
from datetime import date, timedelta

from .paths import DATA_DIR

INPUT_FILE = DATA_DIR / "fertilizer.csv"
OUTPUT_FILE = DATA_DIR / "changes.csv"

# name -> (how far back, how many days off the target date is still OK)
LOOKBACKS = {
    "2w": (timedelta(days=14), timedelta(days=4)),
    "1y": (timedelta(days=365), timedelta(days=7)),
}

OUTPUT_COLUMNS = ["item", "region", "unit", "price", "as_of", "source_name", "source_url"]
for _name in LOOKBACKS:
    OUTPUT_COLUMNS += [f"price_{_name}", f"as_of_{_name}", f"source_url_{_name}",
                       f"change_{_name}", f"pct_{_name}"]


def read_rows(path=None) -> list[dict]:
    """Saved prices as dicts with real types (price float, as_of date).

    A row with an unreadable price or date is skipped with a warning.
    """
    path = path or INPUT_FILE
    if not path.exists():
        return []
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                row["price"] = float(row["price"])
                row["as_of"] = date.fromisoformat(row["as_of"])
            except (TypeError, ValueError):
                print(f"WARNING: skipped unreadable row: {row}", file=sys.stderr)
                continue
            if not row.get("source_url") or not row.get("source_name"):
                print(f"WARNING: skipped row with no source: {row}", file=sys.stderr)
                continue
            row["region"] = row.get("region") or ""
            rows.append(row)
    return rows


def series_key(row: dict) -> tuple:
    """Rows with the same key are the same price series over time."""
    return (row["item"], row["region"], row["unit"], row["source_name"])


def find_earlier(history: list[dict], latest: dict, back: timedelta, slack: timedelta):
    """The saved row closest to (latest date - back), within `slack` days. Or None.

    If two rows are equally close, the older one wins (keeps it repeatable).
    """
    target = latest["as_of"] - back
    best = None
    for row in history:
        if row["as_of"] >= latest["as_of"]:
            continue
        gap = abs(row["as_of"] - target)
        if gap > slack:
            continue
        if best is None or gap < best[0] or (gap == best[0] and row["as_of"] < best[1]["as_of"]):
            best = (gap, row)
    return best[1] if best else None


def change(now: float, then: float):
    """(dollar change, percent change). Percent is None if the old price was 0."""
    dollars = round(now - then, 2)
    pct = round((now - then) / then * 100, 1) if then else None
    return dollars, pct


def compute(rows: list[dict]) -> list[dict]:
    """One result row per series: latest price plus each lookback's change."""
    series = {}
    for row in rows:
        series.setdefault(series_key(row), []).append(row)

    results = []
    for key in sorted(series):
        history = series[key]
        latest = max(history, key=lambda r: r["as_of"])
        out = {
            "item": latest["item"],
            "region": latest["region"],
            "unit": latest["unit"],
            "price": latest["price"],
            "as_of": latest["as_of"],
            "source_name": latest["source_name"],
            "source_url": latest["source_url"],
        }
        for name, (back, slack) in LOOKBACKS.items():
            earlier = find_earlier(history, latest, back, slack)
            if earlier is None:
                out.update({f"price_{name}": None, f"as_of_{name}": None,
                            f"source_url_{name}": None, f"change_{name}": None,
                            f"pct_{name}": None})
                continue
            dollars, pct = change(latest["price"], earlier["price"])
            out.update({f"price_{name}": earlier["price"], f"as_of_{name}": earlier["as_of"],
                        f"source_url_{name}": earlier["source_url"],
                        f"change_{name}": dollars, f"pct_{name}": pct})
        results.append(out)
    results.sort(key=lambda r: (r["region"], r["item"]))
    return results


def write_changes(results: list[dict], path=None) -> None:
    path = path or OUTPUT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for r in results:
            writer.writerow({k: ("" if r.get(k) is None else
                                 r[k].isoformat() if isinstance(r[k], date) else r[k])
                             for k in OUTPUT_COLUMNS})


def main(in_path=None, out_path=None) -> int:
    rows = read_rows(in_path)
    if not rows:
        print("No saved prices yet; run python -m costwire.pull_fertilizer first.")
        return 1
    results = compute(rows)
    write_changes(results, out_path)
    with_2w = sum(r["change_2w"] is not None for r in results)
    with_1y = sum(r["change_1y"] is not None for r in results)
    print(f"{len(results)} prices: {with_2w} have a 2-week change, {with_1y} have a 1-year change "
          f"(the rest don't have an earlier saved price yet, so they're left blank).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
