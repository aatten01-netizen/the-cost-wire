"""Tests for the archived pre-March report loader. Never touches the network.

The listing HTML below is a small hand-made stand-in for the MyMarketNews file
repository page (only the links matter). The PDFs are the real saved samples.
"""

from datetime import date
from pathlib import Path

import pytest

from costwire import archive_report as ar
from costwire import iowa_cost

SAMPLES = Path(__file__).parent / "samples"

PAGE0 = """
<a href="/filerepo/sites/default/files/2863/2026-11-13/1300000/ams_2863_00200.pdf">Nov 13</a>
<a href="/filerepo/sites/default/files/2863/2026-03-12/1200000/ams_2863_00150.pdf">Mar 12</a>
<a href="/filerepo/sites/default/files/3195/2026-02-20/1100000/ams_3195_00100.pdf">other report</a>
<a href="/about.pdf">no date</a>
"""
PAGE1 = """
<a href='/filerepo/sites/default/files/2863/2026-02-26/1190000/ams_2863_00149.pdf'>Feb 26</a>
<a href="/filerepo/sites/default/files/2863/2026-02-12/1180000/ams_2863_00148.pdf">Feb 12</a>
"""


def fake_get(pages):
    def get(url):
        page = int(url.rsplit("page=", 1)[1])
        return pages[page] if page < len(pages) else ""
    return get


def test_find_pdf_links_keeps_only_this_report_with_dates():
    links = ar.find_pdf_links(PAGE0, "2863")
    assert [d for d, _ in links] == [date(2026, 11, 13), date(2026, 3, 12)]
    assert links[0][1].startswith("https://mymarketnews.ams.usda.gov/filerepo/")


def test_pick_before_is_strictly_before_cutoff():
    links = [(date(2026, 3, 4), "a"), (date(2026, 3, 3), "b"), (date(2026, 2, 1), "c")]
    assert ar.pick_before(links) == (date(2026, 3, 3), "b")
    assert ar.pick_before([(date(2026, 3, 4), "a")]) is None


def test_find_archive_url_walks_pages_to_newest_before_march():
    d, url = ar.find_archive_url("2863", fake_get([PAGE0, PAGE1]))
    assert d == date(2026, 2, 26)
    assert url.endswith("ams_2863_00149.pdf")


def test_find_archive_url_raises_when_none_old_enough():
    with pytest.raises(ValueError, match="before 2026-03-04"):
        ar.find_archive_url("2863", fake_get([PAGE0]))


def test_load_state_refuses_report_dated_after_cutoff(tmp_path):
    # the saved Iowa sample is dated Oct 30, 2026: even if a link says Feb, it is refused
    pdf = (SAMPLES / "ams_2863.pdf").read_bytes()
    out = tmp_path / "fert.csv"
    with pytest.raises(ValueError, match="not before"):
        ar.load_state("IA", get=fake_get([PAGE0, PAGE1]), get_bytes=lambda u: pdf, out=out)
    assert not out.exists()


def test_load_state_saves_with_archive_link(tmp_path):
    pdf = (SAMPLES / "ams_2863.pdf").read_bytes()
    out = tmp_path / "fert.csv"
    url = "https://mymarketnews.ams.usda.gov/filerepo/sites/default/files/2863/2026-10-30/1/ams_2863_1.pdf"
    recs = ar.load_state("IA", get_bytes=lambda u: pdf, url=url, out=out, cutoff=date(2027, 1, 1))
    assert recs and all(r.source_url == url and r.region == "IA" for r in recs)
    rows = iowa_cost.read_saved(out)
    assert len(rows) == len(recs) and rows[0]["source_url"] == url
    # running again adds nothing
    ar.load_state("IA", get_bytes=lambda u: pdf, url=url, out=out, cutoff=date(2027, 1, 1))
    assert len(iowa_cost.read_saved(out)) == len(recs)


def test_load_state_illinois_uses_illinois_parser(tmp_path):
    pdf = (SAMPLES / "ams_3195.pdf").read_bytes()
    url = "https://mymarketnews.ams.usda.gov/filerepo/sites/default/files/3195/x/ams_3195.pdf"
    recs = ar.load_state("IL", get_bytes=lambda u: pdf, url=url, out=tmp_path / "f.csv",
                         cutoff=date(2027, 1, 1))
    assert recs and all(r.region == "IL" for r in recs)


def test_load_state_rejects_non_pdf_and_http(tmp_path):
    with pytest.raises(ValueError, match="not a PDF"):
        ar.load_state("IA", get_bytes=lambda u: b"<html>", url="https://x/y.pdf",
                      out=tmp_path / "f.csv")
    with pytest.raises(ValueError, match="https"):
        ar.load_state("IA", get_bytes=lambda u: b"%PDF-", url="http://x/y.pdf",
                      out=tmp_path / "f.csv")


def test_main_url_needs_one_state(capsys):
    assert ar.main(["--url", "https://x/y.pdf"]) == 2
