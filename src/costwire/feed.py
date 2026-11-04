"""Puller for the feed line: dried distillers grains (DDGS) from USDA AMS.

Source: USDA AMS National Weekly Grain Co-Products Report (weekly, from
Livestock, Poultry and Grain Market News, St. Joseph, MO).
  Report page: https://mymarketnews.ams.usda.gov/viewReport/3618
  PDF:         https://www.ams.usda.gov/mnreports/ams_3618.pdf

The part we read looks like this (layout seen in the Oct 26, 2026 report):

    Distillers Grain Dried 10%
    Region/Location Price ($/Ton) Value ($/Bu)3 Value Change Week Ago Year Ago
    Illinois 202.50 1.67 -0.05 1.72 1.34
    Iowa 181.13 1.49 -0.03 1.52 1.04
    ...
    Distillers Grain Wet 65-70%
    ...

We keep only the first number on each state line: the price in $/ton, for
dried distillers grains (10% moisture). The "Value ($/Bu)" columns are a
different measure, so we don't use them. Our own week-ago and year-ago
changes come from the prices we save, like every other item.

States we keep: Iowa, Illinois, Minnesota, Wisconsin. A state with no price
that week is left out, never guessed. A line we can't read is skipped.

Saved to data/fertilizer.csv (same file as everything else) as item "ddgs",
unit "$/ton", region "IA" / "IL" / "MN" / "WI".

Run it:  python -m costwire.feed              (download the latest)
         python -m costwire.feed --pdf FILE   (read a saved report PDF)
"""

import re
import sys
from datetime import date, datetime

from . import iowa_cost
from .records import PriceRecord

SOURCE_NAME = "USDA AMS National Weekly Grain Co-Products Report"
PDF_URL = "https://www.ams.usda.gov/mnreports/ams_3618.pdf"
ITEM = "ddgs"
UNIT = "$/ton"
STALE_DAYS = 14

STATES = {
    "iowa": "IA",
    "illinois": "IL",
    "minnesota": "MN",
    "wisconsin": "WI",
}

_NUM = r"-?[\d,]+\.\d+"
# "Iowa 181.13 1.49 ..."  -> state name, then the $/ton price, then more numbers
_ROW = re.compile(rf"^(?P<state>[A-Za-z][A-Za-z .]*?)\s+(?P<price>{_NUM})(?:\s|$)")
_DRIED_HEADER = re.compile(r"distillers?\s+grains?\s*,?\s*dried\b", re.I)
# Any other section header ends the dried section.
_NEXT_SECTION = re.compile(r"distillers?\s+grains?|corn\s+gluten|corn\s+oil|soybean|"
                           r"hominy|wet\s+65", re.I)
_MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_DATE = re.compile(rf"\b((?:{_MONTHS})[a-z]*\.?\s+\d{{1,2}},\s+\d{{4}})", re.I)
_NEWS_DATE = re.compile(rf"market news\s+((?:{_MONTHS})[a-z]*\.?\s+\d{{1,2}},\s+\d{{4}})", re.I)


def find_report_date(text: str) -> date:
    """The report date: the 'Market News <Month D, YYYY>' line at the top.

    If that line isn't there, the first 'Month D, YYYY' in the report.
    """
    line = _NEWS_DATE.search(text)
    candidates = [line] if line else []
    candidates += list(_DATE.finditer(text))
    for found in candidates:
        raw = " ".join(found.group(1).replace(".", "").split())
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
    raise ValueError("Can't find the report date in the Grain Co-Products report")


def dried_section(text: str) -> list[str]:
    """The lines of the 'Distillers Grain Dried 10%' table (header line excluded)."""
    lines = [line.strip() for line in text.splitlines()]
    for i, line in enumerate(lines):
        if _DRIED_HEADER.search(line):
            section = []
            for nxt in lines[i + 1:]:
                if _NEXT_SECTION.search(nxt):
                    break
                section.append(nxt)
            return section
    raise ValueError("No 'Distillers Grain Dried' table in the Grain Co-Products report")


def parse_report_text(text: str, source_url: str = PDF_URL) -> list[PriceRecord]:
    """Turn the report's text into one DDGS PriceRecord per state we cover."""
    if "co-products" not in text.lower():
        raise ValueError("This doesn't look like the National Weekly Grain Co-Products Report")
    report_date = find_report_date(text)

    records = []
    seen = set()
    for line in dried_section(text):
        row = _ROW.match(line)
        if not row:
            continue
        region = STATES.get(" ".join(row["state"].lower().split()))
        if region is None or region in seen:
            continue  # a state we don't cover, or a repeat
        price = iowa_cost._parse_number(row["price"])
        if price is None or price <= 0:
            print(f"WARNING: feed: skipped {region}: unreadable price {row['price']!r}",
                  file=sys.stderr)
            continue
        seen.add(region)
        records.append(PriceRecord(ITEM, price, UNIT, report_date, source_url,
                                   SOURCE_NAME, region))
    if not records:
        raise ValueError("No Iowa/Illinois/Minnesota/Wisconsin DDGS prices in the report")
    return records


def parse_report_pdf(pdf_bytes: bytes, source_url: str = PDF_URL) -> list[PriceRecord]:
    return parse_report_text(iowa_cost.pdf_to_text(pdf_bytes), source_url)


def pull(get_bytes=None, today=None, out=None) -> list[PriceRecord]:
    """Download the current report PDF and save the DDGS prices."""
    get_bytes = get_bytes or (lambda url: iowa_cost._download(url, as_bytes=True))
    today = today or date.today()
    out = out or iowa_cost.OUTPUT_FILE

    records = parse_report_pdf(get_bytes(PDF_URL), PDF_URL)
    added = iowa_cost.save_records(records, out)
    print(f"Feed (DDGS) report dated {records[0].as_of}: {len(records)} prices, "
          f"{added} new rows -> {out}")
    age = iowa_cost.days_old(records, today)
    if age > STALE_DAYS:
        print(f"WARNING: newest Grain Co-Products report is {age} days old.")
    return records


def load_pdf_file(path, out=None) -> list[PriceRecord]:
    """Read a Grain Co-Products report PDF saved on disk and save its DDGS prices."""
    from pathlib import Path

    records = parse_report_pdf(Path(path).read_bytes(), PDF_URL)
    added = iowa_cost.save_records(records, out or iowa_cost.OUTPUT_FILE)
    print(f"Feed (DDGS) report dated {records[0].as_of}: {len(records)} prices, {added} new rows")
    return records


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--pdf":
            load_pdf_file(sys.argv[2])
        else:
            pull()
    except Exception as exc:  # network or format problem: say so plainly
        print(f"Feed pull failed: {exc}", file=sys.stderr)
        sys.exit(1)
