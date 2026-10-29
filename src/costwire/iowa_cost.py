"""Puller for the USDA AMS Iowa Production Cost Report (fertilizer + fuel).

The CSV edition of this report (file NW_GR910.TXT on ESMIS) looks like:

    NW_GR910,Iowa Production Cost Report,04/2/2024,
    Commodity,Low Price,High Price,Average
    Anhydrous ammonia,725.00,835.00,770.00
    ...

We keep the "Average" column for each item we care about. "NA" means the
report had no price that week, so we leave that item out (never guess).

Run it:  python -m costwire.iowa_cost
"""

import csv
import io
import re
import sys
from datetime import date, datetime

from .paths import DATA_DIR
from .records import PriceRecord

SOURCE_NAME = "USDA AMS Iowa Production Cost Report"
ESMIS_PAGE = "https://esmis.nal.usda.gov/publication/iowa-production-cost-report-bi-weekly-csv"
OUTPUT_FILE = DATA_DIR / "fertilizer.csv"

# How each report row maps to our short item names. Matched on the start of
# the "Commodity" text, lower-cased. Order matters: first match wins.
ITEMS = [
    ("anhydrous ammonia", "anhydrous", "$/ton"),
    ("urea", "urea", "$/ton"),
    ("liquid nitrogen 28%", "uan28", "$/ton"),
    ("liquid nitrogen 32%", "uan32", "$/ton"),
    ("dap", "dap", "$/ton"),
    ("map", "map", "$/ton"),
    ("potash (red)", "potash", "$/ton"),
    ("propane", "propane", "$/gal"),
    ("farm diesel", "diesel", "$/gal"),
]

CSV_COLUMNS = ["item", "price", "unit", "as_of", "source_name", "source_url"]


def _match_item(commodity: str):
    text = commodity.strip().lower()
    for prefix, item, unit in ITEMS:
        if text.startswith(prefix):
            return item, unit
    return None


def _parse_number(text: str):
    """'770.00' -> 770.0; 'NA' or blank -> None."""
    text = text.strip().replace(",", "")
    if not text or text.upper() == "NA":
        return None
    return float(text)


def parse_report_csv(text: str, source_url: str) -> list[PriceRecord]:
    """Turn the report's CSV text into PriceRecords (one per item with a price)."""
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) < 3 or "production cost" not in rows[0][1].lower():
        raise ValueError("This doesn't look like the Iowa Production Cost Report CSV")
    report_date = datetime.strptime(rows[0][2].strip(), "%m/%d/%Y").date()

    header = [cell.strip().lower() for cell in rows[1]]
    if "average" not in header:
        raise ValueError("Report CSV has no 'Average' column")
    avg_col = header.index("average")

    records = []
    seen = set()
    for row in rows[2:]:
        if not row or len(row) <= avg_col:
            continue
        match = _match_item(row[0])
        if match is None:
            continue  # lime, white potash, footer lines, etc.
        item, unit = match
        if item in seen:
            continue
        price = _parse_number(row[avg_col])
        if price is None:
            continue  # no price this report: leave it out
        seen.add(item)
        records.append(PriceRecord(item, price, unit, report_date, source_url, SOURCE_NAME))
    if not records:
        raise ValueError("No prices found in report")
    return records


def find_latest_csv_url(esmis_html: str) -> str:
    """Pick the newest NW_GR910.TXT link from the ESMIS publication page.

    ESMIS lists the latest release first, so the first link is the newest.
    """
    links = re.findall(r'https://esmis\.nal\.usda\.gov/sites/default/release-files/[^"\s]+?NW_GR910\.TXT', esmis_html, re.I)
    if not links:
        raise ValueError("No NW_GR910.TXT link found on the ESMIS page")
    return links[0]


def read_saved(path=None) -> list[dict]:
    path = path or OUTPUT_FILE
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def save_records(records: list[PriceRecord], path=None) -> int:
    """Add new records to the CSV. Re-running for the same report adds nothing.

    Returns how many new rows were added.
    """
    path = path or OUTPUT_FILE
    existing = read_saved(path)
    keys = {(r["item"], r["as_of"], r["source_name"]) for r in existing}
    new_rows = [r.to_row() for r in records
                if (r.item, r.as_of.isoformat(), r.source_name) not in keys]
    rows = existing + new_rows
    rows.sort(key=lambda r: (r["as_of"], r["item"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(new_rows)


def days_old(records: list[PriceRecord], today: date) -> int:
    return (today - max(r.as_of for r in records)).days


def pull(get=None, today=None, out=None) -> list[PriceRecord]:
    """Download the newest CSV edition and save it. `get` is swappable for tests."""
    if get is None:
        import requests

        def get(url):
            resp = requests.get(url, timeout=60, headers={"User-Agent": "TheCostWire/0.1"})
            resp.raise_for_status()
            return resp.text

    url = find_latest_csv_url(get(ESMIS_PAGE))
    records = parse_report_csv(get(url), url)
    out = out or OUTPUT_FILE
    added = save_records(records, out)
    age = days_old(records, today or date.today())
    print(f"Iowa report dated {records[0].as_of}: {len(records)} prices, {added} new rows -> {out}")
    if age > 21:
        print(f"WARNING: newest Iowa CSV is {age} days old. The CSV edition may have stopped; "
              "the current report is the PDF at https://www.ams.usda.gov/mnreports/ams_2863.pdf")
    return records


if __name__ == "__main__":
    try:
        pull()
    except Exception as exc:  # network or format problem: say so plainly
        print(f"Iowa pull failed: {exc}", file=sys.stderr)
        sys.exit(1)
