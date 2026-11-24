"""Load one archived pre-March 2026 USDA AMS report for Iowa and Illinois (PLAN step 26).

The "Since early March" section (since_march.py) needs a saved report dated
before March 4, 2026. USDA keeps every old Iowa (2863) and Illinois (3195)
Production Cost Report PDF in its MyMarketNews file repository:

    https://mymarketnews.ams.usda.gov/filerepo/reports?field_slug_id_value=2863

That listing links each PDF with its date in the path, e.g.
    /filerepo/sites/default/files/2863/2026-02-26/1234567/ams_2863_00123.pdf

What this does, per state:
  1. read the listing pages (newest first) and collect every PDF link + its date
  2. pick the newest link dated before the cutoff (Mar 4, 2026)
  3. download it, read it with the SAME parser as the weekly pull
  4. refuse it unless the date printed IN the report is also before the cutoff
     (never trust the link alone; never type a number in by hand)
  5. save the prices to data/fertilizer.csv with the archive PDF as source link

Run it:  python -m costwire.archive_report            (Iowa and Illinois)
         python -m costwire.archive_report IA         (one state)
         python -m costwire.archive_report IA --url <archive pdf url>
The "Fetch archived reports" GitHub Action runs it (this container can't reach
USDA's site).
"""

import re
import sys
from datetime import date
from urllib.parse import urljoin

from . import illinois_cost, iowa_cost
from .since_march import CUTOFF

BASE = "https://mymarketnews.ams.usda.gov"
LISTING = BASE + "/filerepo/reports?field_slug_id_value={slug}&page={page}"
MAX_PAGES = 30   # ~bi-weekly reports: 30 pages is far more than 9 months back

STATES = {
    "IA": {"slug": "2863", "name": "Iowa", "parse": iowa_cost.parse_report_pdf},
    "IL": {"slug": "3195", "name": "Illinois", "parse": illinois_cost.parse_report_pdf},
}

_HREF = re.compile(r"""href\s*=\s*["']([^"']+?\.pdf)["']""", re.I)
_PATH_DATE = re.compile(r"/(\d{4})-(\d{2})-(\d{2})/")


def find_pdf_links(html: str, slug: str) -> list[tuple[date, str]]:
    """Every (date, absolute url) for this report's PDFs on one listing page."""
    out = []
    for href in _HREF.findall(html):
        if f"/{slug}/" not in href and f"ams_{slug}" not in href:
            continue                      # another report's file
        m = _PATH_DATE.search(href)
        if not m:
            continue                      # no date in the link: can't tell its week
        try:
            d = date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            continue
        url = urljoin(BASE, href)
        if (d, url) not in out:
            out.append((d, url))
    return out


def pick_before(links: list[tuple[date, str]], cutoff: date = CUTOFF):
    """Newest (date, url) dated before the cutoff, or None."""
    older = [x for x in links if x[0] < cutoff]
    return max(older) if older else None


def find_archive_url(slug: str, get, cutoff: date = CUTOFF, max_pages: int = MAX_PAGES):
    """Walk the listing pages until a PDF before the cutoff shows up. Returns (date, url)."""
    seen = []
    for page in range(max_pages):
        links = find_pdf_links(get(LISTING.format(slug=slug, page=page)), slug)
        if not links:
            break                         # ran past the last page (or the layout changed)
        seen += links
        best = pick_before(seen, cutoff)
        # listing is newest first: once a page holds an older file, we have the newest older one
        if best and min(d for d, _ in links) < cutoff:
            return best
    best = pick_before(seen, cutoff)
    if best:
        return best
    raise ValueError(f"no report {slug} PDF dated before {cutoff} found "
                     f"({len(seen)} PDF links read on the listing)")


def load_state(state: str, get=None, get_bytes=None, url=None, out=None, cutoff: date = CUTOFF):
    """Find, check and save one archived pre-cutoff report. Returns the saved records."""
    info = STATES[state]
    get = get or iowa_cost._download
    get_bytes = get_bytes or (lambda u: iowa_cost._download(u, as_bytes=True))
    if not url:
        _, url = find_archive_url(info["slug"], get, cutoff)
    if not url.startswith("https://"):
        raise ValueError(f"archive link must be https: {url}")
    pdf = get_bytes(url)
    if not pdf[:5] == b"%PDF-":
        raise ValueError(f"{url} is not a PDF")
    records = info["parse"](pdf, url)
    if not records:
        raise ValueError(f"no prices read from {url}")
    as_of = records[0].as_of
    if as_of >= cutoff:
        raise ValueError(f"{info['name']} report says {as_of}, not before {cutoff}: not saved")
    added = iowa_cost.save_records(records, out or iowa_cost.OUTPUT_FILE)
    print(f"{info['name']} archived report dated {as_of}: {len(records)} prices, "
          f"{added} new rows ({url})")
    return records


def main(argv) -> int:
    states = [a.upper() for a in argv if a.upper() in STATES] or list(STATES)
    url = argv[argv.index("--url") + 1] if "--url" in argv else None
    if url and len(states) != 1:
        print("--url needs exactly one state (IA or IL)", file=sys.stderr)
        return 2
    failed = 0
    for s in states:  # one state failing doesn't stop the other
        try:
            load_state(s, url=url)
        except Exception as exc:
            failed += 1
            print(f"{STATES[s]['name']} archive load failed: {exc}", file=sys.stderr)
    return 1 if failed == len(states) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
