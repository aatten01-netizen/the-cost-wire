"""Puller for the USDA AMS Iowa Production Cost Report (fertilizer + fuel).

The CSV edition of this report (file NW_GR910.TXT on ESMIS) looks like:

    NW_GR910,Iowa Production Cost Report,04/2/2024,
    Commodity,Low Price,High Price,Average
    Anhydrous ammonia,725.00,835.00,770.00
    ...

We keep the "Average" column for each item we care about. "NA" means the
report had no price that week, so we leave that item out (never guess).

Since April 2024 the report is only published as a PDF
(https://www.ams.usda.gov/mnreports/ams_2863.pdf). Its table lines look like:

    Anhydrous Ammonia Ask 892.00 - 915.00 902.33 (3.17) F.O.B. Current

so for the PDF we pull out the text (with the free pdfplumber library) and read
the "Average" number on each line. `pull()` uses the PDF whenever the CSV is
stale.

Run it:  python -m costwire.iowa_cost              (download the latest)
         python -m costwire.iowa_cost --pdf FILE   (read a saved report PDF)
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
PDF_URL = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"
OUTPUT_FILE = DATA_DIR / "fertilizer.csv"
STALE_DAYS = 21

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

REGION = "IA"
CSV_COLUMNS = ["item", "price", "unit", "as_of", "source_name", "source_url", "region"]


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
        records.append(PriceRecord(item, price, unit, report_date, source_url, SOURCE_NAME, REGION))
    if not records:
        raise ValueError("No prices found in report")
    return records


# ---------------------------------------------------------------------------
# PDF edition (current report)
# ---------------------------------------------------------------------------

# How each PDF row name maps to our item names. Matched on the start of the
# row text, lower-cased. First match wins. White potash is NOT listed, so it
# can never be mistaken for red potash.
PDF_ITEMS = [
    ("anhydrous ammonia", "anhydrous", "$/ton"),
    ("urea", "urea", "$/ton"),
    ("liquid nitrogen (28", "uan28", "$/ton"),
    ("liquid nitrogen (32", "uan32", "$/ton"),
    ("dap", "dap", "$/ton"),
    ("diammonium", "dap", "$/ton"),
    ("map", "map", "$/ton"),
    ("monoammonium", "map", "$/ton"),
    ("potash (red", "potash", "$/ton"),
    ("no. 2 diesel", "diesel", "$/gal"),
    ("farm diesel", "diesel", "$/gal"),
    ("diesel", "diesel", "$/gal"),
    ("propane", "propane", "$/gal"),
]

_NUM = r"[\d,]+\.\d+"
# name, sale type, low price, optional "- high price", average
_PDF_ROW = re.compile(
    rf"^(?P<name>.+?)\s+(?:Ask|Bid|Offer|Sale|Sell|Buy)\s+"
    rf"(?P<low>{_NUM})(?:\s*-\s*(?P<high>{_NUM}))?\s+(?P<avg>{_NUM})\b"
)
_PDF_DATE = re.compile(r"week ending\s+(\d{1,2}/\d{1,2}/\d{4})", re.I)


def _match_pdf_item(name: str):
    text = name.strip().lower()
    for prefix, item, unit in PDF_ITEMS:
        if text.startswith(prefix):
            return item, unit
    return None


def parse_report_pdf_text(text: str, source_url: str) -> list[PriceRecord]:
    """Turn the text of the report PDF into PriceRecords.

    Rows with no numbers (e.g. "NA") are skipped: we never guess a price.
    A row whose average isn't between its low and high is also skipped,
    because that means we read the line wrong.
    """
    if "production cost report" not in text.lower():
        raise ValueError("This doesn't look like the Iowa Production Cost Report PDF")
    found = _PDF_DATE.search(text)
    if not found:
        raise ValueError("Can't find 'week ending' date in report PDF")
    report_date = datetime.strptime(found.group(1), "%m/%d/%Y").date()

    records = []
    seen = set()
    for line in text.splitlines():
        row = _PDF_ROW.match(line.strip())
        if not row:
            continue
        match = _match_pdf_item(row["name"])
        if match is None:
            continue  # lime, white potash, etc.
        item, unit = match
        if item in seen:
            continue
        low, avg = _parse_number(row["low"]), _parse_number(row["avg"])
        high = _parse_number(row["high"]) if row["high"] else low
        if not (low <= avg <= high):
            print(f"WARNING: skipped {item}: average {avg} not between {low} and {high}",
                  file=sys.stderr)
            continue
        seen.add(item)
        records.append(PriceRecord(item, avg, unit, report_date, source_url, SOURCE_NAME, REGION))
    if not records:
        raise ValueError("No prices found in report PDF")
    return records


def pdf_to_text(pdf_bytes: bytes) -> str:
    """Pull the text out of a PDF (all pages)."""
    import pdfplumber

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def parse_report_pdf(pdf_bytes: bytes, source_url: str = PDF_URL) -> list[PriceRecord]:
    return parse_report_pdf_text(pdf_to_text(pdf_bytes), source_url)


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
        rows = list(csv.DictReader(f))
    for row in rows:  # files saved before Illinois was added had no region column
        if not row.get("region"):
            row["region"] = "IA" if "Iowa" in row["source_name"] else ""
    return rows


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
    rows.sort(key=lambda r: (r["as_of"], r["region"], r["item"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(new_rows)


def days_old(records: list[PriceRecord], today: date) -> int:
    return (today - max(r.as_of for r in records)).days


def _download(url, as_bytes=False):
    import requests

    resp = requests.get(url, timeout=60, headers={"User-Agent": "TheCostWire/0.1"})
    resp.raise_for_status()
    return resp.content if as_bytes else resp.text


def pull(get=None, get_bytes=None, today=None, out=None) -> list[PriceRecord]:
    """Download the newest report and save it.

    Tries the CSV edition first. If it's more than 3 weeks old (or fails),
    reads the current PDF instead. `get` / `get_bytes` are swappable for tests.
    """
    get = get or _download
    get_bytes = get_bytes or (lambda url: _download(url, as_bytes=True))
    today = today or date.today()
    out = out or OUTPUT_FILE

    records = []
    try:
        url = find_latest_csv_url(get(ESMIS_PAGE))
        records = parse_report_csv(get(url), url)
    except Exception as exc:
        print(f"Iowa CSV edition unavailable ({exc}); trying the PDF.", file=sys.stderr)

    if not records or days_old(records, today) > STALE_DAYS:
        if records:
            print(f"Iowa CSV is {days_old(records, today)} days old; using the PDF edition.")
        records = parse_report_pdf(get_bytes(PDF_URL), PDF_URL)

    added = save_records(records, out)
    age = days_old(records, today)
    print(f"Iowa report dated {records[0].as_of}: {len(records)} prices, {added} new rows -> {out}")
    if age > STALE_DAYS:
        print(f"WARNING: newest Iowa report is {age} days old.")
    return records


def load_pdf_file(path, out=None) -> list[PriceRecord]:
    """Read a report PDF saved on disk (e.g. downloaded by hand) and save it."""
    from pathlib import Path

    records = parse_report_pdf(Path(path).read_bytes(), PDF_URL)
    added = save_records(records, out or OUTPUT_FILE)
    print(f"Iowa report dated {records[0].as_of}: {len(records)} prices, {added} new rows")
    return records


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--pdf":
            load_pdf_file(sys.argv[2])
        else:
            pull()
    except Exception as exc:  # network or format problem: say so plainly
        print(f"Iowa pull failed: {exc}", file=sys.stderr)
        sys.exit(1)
