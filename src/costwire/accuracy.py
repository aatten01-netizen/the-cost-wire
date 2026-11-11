"""Accuracy check: every number in the brief must have a source and a date.

Runs before each weekly build. It checks two things:
  1. The saved prices (data/fertilizer.csv): each row needs an item, unit,
     a real price, a real date (not in the future) and an https source link
     and source name.
  2. The newest brief (briefs/<date>.md): each price row in the table must match
     the saved data exactly (price, date, change, source link), the brief must
     have a Sources section and the disclaimer, and it must not hold a row we
     can't trace back to the data.
  3. The "bushels of corn to buy 1 ton" lines: each must match the saved
     fertilizer + NASS corn prices exactly, and each NASS link must be listed
     in Sources. The saved corn prices need a real value and an https link.

Anything wrong is printed as a plain-English problem and the check fails
(exit code 1), which stops the weekly build so a bad number never goes out.

Run it:  python -m costwire.accuracy            (checks the newest brief)
         python -m costwire.accuracy --brief briefs/2026-11-02.md
"""

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

from . import brief, changes, corn_price
from .paths import BRIEFS_DIR


# ---------- check 1: the saved prices ----------

def check_data(path=None, today=None) -> list[str]:
    """Problems found in the saved price file (empty list = all good)."""
    path = Path(path or changes.INPUT_FILE)
    today = today or brief.today_central()
    if not path.exists():
        return [f"No saved prices found at {path}."]
    problems = []
    with open(path, newline="") as f:
        for n, row in enumerate(csv.DictReader(f), start=2):  # line 1 is the header
            label = f"data line {n} ({row.get('region') or '?'} {row.get('item') or '?'})"
            if not (row.get("item") or "").strip():
                problems.append(f"{label}: no item name.")
            if not (row.get("unit") or "").strip():
                problems.append(f"{label}: no unit.")
            try:
                price = float(row.get("price"))
                if price <= 0:
                    problems.append(f"{label}: price {price} is not above zero.")
            except (TypeError, ValueError):
                problems.append(f"{label}: price '{row.get('price')}' is not a number.")
            try:
                as_of = date.fromisoformat(row.get("as_of") or "")
                if as_of > today:
                    problems.append(f"{label}: date {as_of} is in the future.")
            except ValueError:
                problems.append(f"{label}: date '{row.get('as_of')}' is missing or not YYYY-MM-DD.")
            if not (row.get("source_name") or "").strip():
                problems.append(f"{label}: no source name.")
            if not (row.get("source_url") or "").startswith("https://"):
                problems.append(f"{label}: source link is missing or not https.")
    return problems


# ---------- check 2: the brief ----------

def table_rows(markdown: str) -> list[list[str]]:
    """Cells of each price row in the brief's table (header and divider skipped)."""
    rows = []
    for line in markdown.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        if cells[0] == "Item":
            continue
        rows.append(cells)
    return rows


def expected_cells(r: dict) -> list[str]:
    """What the brief table row for this result should say."""
    return [
        brief.item_name(r["item"]),
        brief.region_name(r["region"]),
        f"{brief.money(r['price'])}{brief.per_unit(r['unit'])}",
        brief.signed_change(r["change_2w"], r["pct_2w"]),
        brief.signed_change(r["change_1y"], r["pct_1y"]),
        brief.short_date(r["as_of"]),
        f"[{r['source_name']}]({r['source_url']})",
    ]


def check_brief(markdown: str, results: list[dict]) -> list[str]:
    """Problems found comparing the brief text to the computed results."""
    problems = []
    found = table_rows(markdown)
    wanted = {}
    for r in results:
        cells = expected_cells(r)
        wanted[(cells[0], cells[1])] = (cells, r)

    seen = set()
    for cells in found:
        key = (cells[0], cells[1]) if len(cells) >= 2 else None
        label = f"{cells[1]} {cells[0]}" if len(cells) >= 2 else "a table row"
        if len(cells) != 7:
            problems.append(f"Brief: {label} does not have all 7 columns.")
            continue
        if key in seen:
            problems.append(f"Brief: {label} appears more than once.")
        seen.add(key)
        if key not in wanted:
            problems.append(f"Brief: {label} is not in the saved data.")
            continue
        exp, _ = wanted[key]
        names = ["item", "region", "price", "2-week change", "1-year change", "date", "source"]
        for name, got, want in zip(names, cells, exp):
            if got != want:
                problems.append(f"Brief: {label} {name} says '{got}' but the data says '{want}'.")
        if "](https://" not in cells[6]:
            problems.append(f"Brief: {label} has no https source link.")
    for key in wanted:
        if key not in seen:
            problems.append(f"Brief: {key[1]} {key[0]} is in the data but missing from the brief.")

    # Every earlier price used for a change needs its own source and date.
    for r in results:
        for period in ("2w", "1y"):
            if r.get(f"change_{period}") is not None:
                label = f"{brief.region_name(r['region'])} {brief.item_name(r['item'])}"
                if not r.get(f"source_url_{period}"):
                    problems.append(f"Data: {label} {period} change has no source link for the earlier price.")
                if not r.get(f"as_of_{period}"):
                    problems.append(f"Data: {label} {period} change has no date for the earlier price.")

    if "## Sources" not in markdown:
        problems.append("Brief: no Sources section.")
    else:
        sources_part = markdown.split("## Sources", 1)[1]
        for s in brief.sources(results):
            if s["url"] not in sources_part:
                problems.append(f"Brief: source {s['url']} is not listed in the Sources section.")
    if brief.DISCLAIMER not in markdown:
        problems.append("Brief: the disclaimer is missing.")
    return problems


def check_corn_data(prices) -> list[str]:
    """Problems in the saved NASS corn prices (data/corn_price.csv)."""
    problems = []
    for p in prices:
        label = f"corn price {p.state} {p.year}-{p.month:02d}"
        if not p.value > 0:
            problems.append(f"Data: {label} is not above zero.")
        if not p.source_url.startswith("https://"):
            problems.append(f"Data: {label} source link is missing or not https.")
        if not p.source_name.strip():
            problems.append(f"Data: {label} has no source name.")
    return problems


def section_lines(markdown: str, title: str) -> list[str]:
    """The '- ' bullet lines under a '## title' heading (up to the next heading)."""
    if f"## {title}" not in markdown:
        return []
    part = markdown.split(f"## {title}", 1)[1].split("\n## ", 1)[0]
    return [line[2:] for line in part.splitlines() if line.startswith("- ")]


def check_afford(markdown: str, results: list[dict], corn_prices) -> list[str]:
    """The bushels-per-ton lines must match the data exactly, nothing extra or missing."""
    b = brief.build(results, date.today(), corn_prices)
    found, wanted = section_lines(markdown, brief.AFFORD_TITLE), b["afford"]
    problems = [f"Brief: bushels line not in the saved data: '{line}'"
                for line in found if line not in wanted]
    problems += [f"Brief: bushels line in the data but missing from the brief: '{line}'"
                 for line in wanted if line not in found]
    sources_part = markdown.split("## Sources", 1)[1] if "## Sources" in markdown else ""
    for s in b["afford_sources"]:
        if s["url"] not in sources_part:
            problems.append(f"Brief: NASS source {s['url']} is not listed in the Sources section.")
    return problems


def newest_brief(out_dir=None):
    files = sorted(Path(out_dir or BRIEFS_DIR).glob("*.md"))
    return files[-1] if files else None


def run_checks(brief_path=None, data_path=None, today=None, corn_path=None) -> list[str]:
    corn_prices = corn_price.load_prices(corn_path)
    problems = check_data(data_path, today) + check_corn_data(corn_prices)
    path = Path(brief_path) if brief_path else newest_brief()
    if path is None or not path.exists():
        return problems + ["No brief found to check."]
    rows = changes.read_rows(data_path)
    results = changes.compute(rows)
    text = path.read_text(encoding="utf-8")
    return problems + check_brief(text, results) + check_afford(text, results, corn_prices)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check the brief's numbers against sources and dates.")
    parser.add_argument("--brief", default=None, help="brief .md to check (default: newest in briefs/)")
    args = parser.parse_args(argv)
    problems = run_checks(args.brief)
    if problems:
        print(f"ACCURACY CHECK FAILED: {len(problems)} problem(s)", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("Accuracy check passed: every number has a source and a date and matches the data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
