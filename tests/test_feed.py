"""Tests for the feed line (DDGS from the USDA AMS Grain Co-Products Report).

The sample text below copies the LAYOUT of the real report (Oct 26, 2026).
The numbers are made up for testing only; they are never saved as data.
"""

import csv
from datetime import date

import pytest

from costwire import brief, changes, feed, iowa_cost, pull_fertilizer

SAMPLE = """\
National Weekly Grain Co-Products Report
Livestock, Poultry and Grain Market News October 26, 2026
Distillers Grain Dried 10%
Region/Location Price ($/Ton) Value ($/Bu)3 Value Change Week Ago Year Ago
Illinois 200.00 1.60 -0.05 1.65 1.30
Indiana 180.00 1.50 -0.03 1.53 1.20
Iowa 1,180.50 1.45 -0.03 1.48 1.00
Kansas 220.00 1.80 UNCH 1.80 1.30
Minnesota 181.25 1.50 -0.03 1.53 1.09
South Dakota 188.00 1.55 -0.04 1.59 1.09
Wisconsin 174.00 1.44 UNCH 1.44 1.09
Distillers Grain Wet 65-70%
Region/Location Price ($/Ton) Value ($/Bu)3 Value Change Week Ago Year Ago
Iowa 56.00 1.39 -0.06 1.45 1.13
Minnesota 55.00 1.36 UNCH 1.36 1.36
"""


def test_reads_dried_ddgs_for_our_states():
    records = feed.parse_report_text(SAMPLE)
    got = {r.region: r.price for r in records}
    assert got == {"IL": 200.0, "IA": 1180.5, "MN": 181.25, "WI": 174.0}
    for r in records:
        assert r.item == "ddgs"
        assert r.unit == "$/ton"
        assert r.as_of == date(2026, 10, 26)
        assert r.source_url == feed.PDF_URL
        assert r.source_name == feed.SOURCE_NAME


def test_wet_distillers_never_read_as_dried():
    # Iowa wet is 56.00; the dried Iowa price must win and wet must not add rows.
    records = feed.parse_report_text(SAMPLE)
    assert len(records) == 4
    assert all(r.price != 56.0 and r.price != 55.0 for r in records)


def test_state_missing_from_report_is_left_out():
    text = SAMPLE.replace("Wisconsin 174.00 1.44 UNCH 1.44 1.09\n", "")
    regions = {r.region for r in feed.parse_report_text(text)}
    assert regions == {"IL", "IA", "MN"}


def test_state_with_no_price_is_left_out():
    text = SAMPLE.replace("Wisconsin 174.00 1.44 UNCH 1.44 1.09", "Wisconsin NA NA")
    regions = {r.region for r in feed.parse_report_text(text)}
    assert "WI" not in regions


def test_report_date_prefers_the_market_news_date_line():
    text = "Released Oct 23, 2026\n" + SAMPLE
    assert feed.find_report_date(text) == date(2026, 10, 26)


def test_wrong_report_is_refused():
    with pytest.raises(ValueError, match="Grain Co-Products"):
        feed.parse_report_text("Iowa Production Cost Report\nOctober 30, 2026\nIowa 1.00")


def test_missing_dried_table_is_an_error():
    text = SAMPLE.split("Distillers Grain Dried 10%")[0]
    with pytest.raises(ValueError, match="Dried"):
        feed.parse_report_text(text)


def test_missing_date_is_an_error():
    text = SAMPLE.replace("October 26, 2026", "")
    with pytest.raises(ValueError, match="date"):
        feed.parse_report_text(text)


def test_no_states_we_cover_is_an_error():
    text = "\n".join(l for l in SAMPLE.splitlines()
                     if not l.startswith(("Illinois", "Iowa", "Minnesota", "Wisconsin")))
    with pytest.raises(ValueError, match="No Iowa"):
        feed.parse_report_text(text)


def test_pull_saves_all_four_states_and_rerun_adds_nothing(tmp_path, monkeypatch):
    out = tmp_path / "fertilizer.csv"
    monkeypatch.setattr(iowa_cost, "pdf_to_text", lambda b: SAMPLE)
    feed.pull(get_bytes=lambda url: b"pdf", today=date(2026, 10, 27), out=out)
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    assert sorted(r["region"] for r in rows) == ["IA", "IL", "MN", "WI"]
    assert all(r["source_url"] == feed.PDF_URL for r in rows)
    # same report again: no duplicate rows
    feed.pull(get_bytes=lambda url: b"pdf", today=date(2026, 10, 27), out=out)
    with open(out, newline="") as f:
        assert len(list(csv.DictReader(f))) == 4


def test_pull_warns_when_report_is_stale(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(iowa_cost, "pdf_to_text", lambda b: SAMPLE)
    feed.pull(get_bytes=lambda url: b"pdf", today=date(2026, 11, 30), out=tmp_path / "f.csv")
    assert "days old" in capsys.readouterr().out


def test_feed_is_part_of_the_weekly_pull():
    names = [name for name, _ in pull_fertilizer.PULLERS]
    assert "Feed (DDGS)" in names


def test_feed_row_shows_in_the_brief(tmp_path, monkeypatch):
    out = tmp_path / "fertilizer.csv"
    monkeypatch.setattr(iowa_cost, "pdf_to_text", lambda b: SAMPLE)
    feed.pull(get_bytes=lambda url: b"pdf", today=date(2026, 10, 27), out=out)
    b = brief.build(changes.compute(changes.read_rows(out)), date(2026, 11, 2))
    md = brief.to_markdown(b)
    assert "Dried distillers grains (10%) | Iowa | $1,180.50/ton" in md
    assert "Wisconsin" in md and "Minnesota" in md
    assert feed.SOURCE_NAME in md
    assert "USDA Agricultural Marketing Service" in b["credit"]


def test_real_feed_pdf_report_dated_nov_2_2026():
    """The real report Andy uploaded (tests/samples/ams_3618.pdf)."""
    from pathlib import Path

    pdf = (Path(__file__).parent / "samples" / "ams_3618.pdf").read_bytes()
    records = feed.parse_report_pdf(pdf)
    prices = {r.region: r.price for r in records}
    # Dried 10% table, $/ton (not the wet table, not the $/bu value column).
    assert prices == {"IL": 195.00, "IA": 170.65, "MN": 175.00, "WI": 174.00}
    for r in records:
        assert r.item == "ddgs" and r.unit == "$/ton"
        assert r.as_of == date(2026, 11, 2)
        assert r.source_url == "https://www.ams.usda.gov/mnreports/ams_3618.pdf"
