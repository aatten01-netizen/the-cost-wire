"""Puller for the USDA AMS Illinois Production Cost Report (fertilizer + fuel).

Bi-weekly, from USDA AMS + Illinois Dept. of Agriculture Market News
(Springfield, IL). Current report: https://www.ams.usda.gov/mnreports/ams_3195.pdf
(the old text edition, gx_gr210.txt, stopped in February 2022).

We have seen two table layouts, so the parser accepts both:

  Older layout (2022):
      Anhydrous ammonia                 1460.00-1550.00   1503.50   UP 5.00
      Farm Diesel Fuel per gal <1000 gallons  3.40-3.54   3.46      UP 0.14

  Newer USDA "My Market News" layout (same as the current Iowa report):
      Anhydrous Ammonia Offer 1,150.00 - 1,250.00 1,200.00 (5.00) F.O.B. Current

Either way we keep the "Average" number. No price ("NA") = left out, never
guessed. A row whose average isn't between its low and high is skipped,
because that means we read the line wrong.

Prices are saved to the same file as Iowa (data/fertilizer.csv) with
region "IL".

Run it:  python -m costwire.illinois_cost              (download the latest)
         python -m costwire.illinois_cost --pdf FILE   (read a saved report PDF)
"""

import re
import sys
from datetime import date, datetime

from . import iowa_cost
from .records import PriceRecord

SOURCE_NAME = "USDA AMS Illinois Production Cost Report"
PDF_URL = "https://www.ams.usda.gov/mnreports/ams_3195.pdf"
REGION = "IL"
STALE_DAYS = 21

# Row name (start of line, lower-cased) -> our item name and unit.
# First match wins. White potash is not listed, so it can't be read as potash.
ITEMS = [
    ("anhydrous ammonia", "anhydrous", "$/ton"),
    ("urea", "urea", "$/ton"),
    ("liquid nitrogen 28", "uan28", "$/ton"),
    ("liquid nitrogen (28", "uan28", "$/ton"),
    ("liquid nitrogen 32", "uan32", "$/ton"),
    ("liquid nitrogen (32", "uan32", "$/ton"),
    ("dap", "dap", "$/ton"),
    ("diammonium", "dap", "$/ton"),
    ("map", "map", "$/ton"),
    ("monoammonium", "map", "$/ton"),
    ("potash (red", "potash", "$/ton"),
    ("potash (potassium", "potash", "$/ton"),
    ("potash 0-0-60", "potash", "$/ton"),
    ("farm diesel", "diesel", "$/gal"),
    ("no. 2 diesel", "diesel", "$/gal"),
    ("propane", "propane", "$/gal"),
]
# Plain "Potash" with nothing after it is the only potash in the older layout.
_PLAIN_POTASH = re.compile(r"^potash\s*$")

_NUM = r"[\d,]+\.\d+"
# name, optional sale type, low, optional "-high", average
_ROW = re.compile(
    rf"^(?P<name>[A-Za-z].*?)\s+(?:(?:Ask|Bid|Offer|Sale|Sell|Buy)\s+)?"
    rf"(?P<low>{_NUM})(?:\s*-\s*(?P<high>{_NUM}))?\s+(?P<avg>{_NUM})(?!\S)"
)
_MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
# Tried in order; the first one found is the report date.
_DATES = [
    (re.compile(r"week ending\s+(\d{1,2}/\d{1,2}/\d{4})", re.I), ["%m/%d/%Y"]),
    (re.compile(r"report for\s+(\d{1,2}/\d{1,2}/\d{4})", re.I), ["%m/%d/%Y"]),
    (re.compile(rf"\b((?:{_MONTHS})[a-z]*\.?\s+\d{{1,2}},\s+\d{{4}})", re.I),
     ["%B %d, %Y", "%b %d, %Y", "%b. %d, %Y"]),
]


def match_item(name: str):
    text = " ".join(name.strip().lower().split())
    if _PLAIN_POTASH.match(text):
        return "potash", "$/ton"
    for prefix, item, unit in ITEMS:
        if text.startswith(prefix):
            return item, unit
    return None


def find_report_date(text: str) -> date:
    for pattern, formats in _DATES:
        found = pattern.search(text)
        if not found:
            continue
        raw = " ".join(found.group(1).split())
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
    raise ValueError("Can't find the report date in the Illinois report")


def parse_report_text(text: str, source_url: str = PDF_URL) -> list[PriceRecord]:
    """Turn the report's text into PriceRecords (one per item with a price)."""
    lowered = text.lower()
    if "illinois" not in lowered or "production cost" not in lowered:
        raise ValueError("This doesn't look like the Illinois Production Cost Report")
    report_date = find_report_date(text)

    records = []
    seen = set()
    for line in text.splitlines():
        row = _ROW.match(line.strip())
        if not row:
            continue
        match = match_item(row["name"])
        if match is None:
            continue  # lime, white potash, etc.
        item, unit = match
        if item in seen:
            continue
        low = iowa_cost._parse_number(row["low"])
        avg = iowa_cost._parse_number(row["avg"])
        high = iowa_cost._parse_number(row["high"]) if row["high"] else low
        if not (low <= avg <= high):
            print(f"WARNING: Illinois: skipped {item}: average {avg} not between {low} and {high}",
                  file=sys.stderr)
            continue
        seen.add(item)
        records.append(PriceRecord(item, avg, unit, report_date, source_url, SOURCE_NAME, REGION))
    if not records:
        raise ValueError("No prices found in the Illinois report")
    return records


def parse_report_pdf(pdf_bytes: bytes, source_url: str = PDF_URL) -> list[PriceRecord]:
    return parse_report_text(iowa_cost.pdf_to_text(pdf_bytes), source_url)


def pull(get_bytes=None, today=None, out=None) -> list[PriceRecord]:
    """Download the current Illinois report PDF and save it to data/fertilizer.csv."""
    get_bytes = get_bytes or (lambda url: iowa_cost._download(url, as_bytes=True))
    today = today or date.today()
    out = out or iowa_cost.OUTPUT_FILE

    records = parse_report_pdf(get_bytes(PDF_URL), PDF_URL)
    added = iowa_cost.save_records(records, out)
    age = iowa_cost.days_old(records, today)
    print(f"Illinois report dated {records[0].as_of}: {len(records)} prices, {added} new rows -> {out}")
    if age > STALE_DAYS:
        print(f"WARNING: newest Illinois report is {age} days old.")
    return records


def load_pdf_file(path, out=None) -> list[PriceRecord]:
    """Read an Illinois report PDF saved on disk and save its prices."""
    from pathlib import Path

    records = parse_report_pdf(Path(path).read_bytes(), PDF_URL)
    added = iowa_cost.save_records(records, out or iowa_cost.OUTPUT_FILE)
    print(f"Illinois report dated {records[0].as_of}: {len(records)} prices, {added} new rows")
    return records


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--pdf":
            load_pdf_file(sys.argv[2])
        else:
            pull()
    except Exception as exc:  # network or format problem: say so plainly
        print(f"Illinois pull failed: {exc}", file=sys.stderr)
        sys.exit(1)
