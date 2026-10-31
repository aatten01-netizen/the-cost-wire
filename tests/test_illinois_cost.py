from datetime import date

import pytest

from costwire import illinois_cost, iowa_cost, pull_fertilizer
from costwire.paths import TESTS_DIR

# Shaped like the older Illinois layout (text edition, Feb 24 2022).
# These are test fixtures, not data we publish.
OLD_LAYOUT = """Springfield, IL Thu Feb 24, 2022 USDA-IL Dept of Ag Market News
Illinois Production Cost Report (Bi-weekly)
Prices are cash, FOB distributor, per ton unless otherwise stated.
Product                                     Offer        Average     Change
Anhydrous ammonia                       1460.00-1550.00  1503.50   UP 5.00
Urea 46-0-0                              875.00-900.00    889.00   DN 8.33
Liquid Nitrogen 28% spread               552.00-630.00    579.63   UP 2.63
DAP(Diammonium Phosphate 18%N 46%P)      850.00-885.00    860.00   UNCH
MAP (Monoammonium Phosphate 11%N 52%P)   825.00-920.00    881.00   UP 4.00
Potash (Potassium)                       770.00-830.00    808.33   UP 1.83
Farm Diesel Fuel per gal <1000 gallons     3.40-3.54        3.46   UP 0.14
"""

# Shaped like the newer USDA My Market News layout (same as the Iowa PDF),
# with the edge cases: commas, NA, single price, white potash, bad average.
NEW_LAYOUT = """Illinois Production Cost Report (Bi-Weekly)
Springfield, IL Report for week ending 10/16/2026
Class Sale Type Package Price Range Average Change Freight Delivery Period
Anhydrous Ammonia Offer 1,150.00 - 1,250.00 1,200.00 (5.00) F.O.B. Current
Urea (46-0-0) Offer NA
Liquid Nitrogen (28-0-0) Offer 400.00 400.00 0.00 F.O.B. Current
Liquid Nitrogen (32-0-0) Offer 450.00 - 470.00 460.00 0.00 F.O.B. Current
Potash (White 0-0-62) Offer 700.00 - 720.00 710.00 0.00 F.O.B. Current
Potash (Red 0-0-60) Offer 480.00 - 520.00 500.00 5.80 F.O.B. Current
Farm Diesel Offer 3.80 - 4.00 3.90 0.05 F.O.B. Current
Propane Offer 1.50 - 1.70 9.99 0.10 F.O.B. Current
"""


def by_item(text):
    return {r.item: r for r in illinois_cost.parse_report_text(text)}


def test_old_layout_reads_every_item():
    got = by_item(OLD_LAYOUT)
    assert {k: v.price for k, v in got.items()} == {
        "anhydrous": 1503.50, "urea": 889.00, "uan28": 579.63, "dap": 860.00,
        "map": 881.00, "potash": 808.33, "diesel": 3.46,
    }
    assert got["anhydrous"].as_of == date(2022, 2, 24)
    assert got["diesel"].unit == "$/gal"
    assert got["potash"].unit == "$/ton"


def test_new_layout_edge_cases(capsys):
    got = by_item(NEW_LAYOUT)
    assert got["anhydrous"].price == 1200.00   # commas handled
    assert "urea" not in got                   # NA left out, not guessed
    assert got["uan28"].price == 400.00        # single price, no range
    assert got["uan32"].price == 460.00
    assert got["potash"].price == 500.00       # red, not white
    assert got["diesel"].price == 3.90
    assert "propane" not in got                # average outside range: skipped
    assert "skipped propane" in capsys.readouterr().err
    assert got["anhydrous"].as_of == date(2026, 10, 16)


def test_every_record_is_tagged_illinois_with_source():
    for r in illinois_cost.parse_report_text(NEW_LAYOUT):
        assert r.region == "IL"
        assert r.source_name == illinois_cost.SOURCE_NAME
        assert r.source_url == illinois_cost.PDF_URL


@pytest.mark.parametrize("text", [
    "Iowa Production Cost Report\nweek ending 1/1/2026\nAnhydrous Ammonia Ask 1.00 - 2.00 1.50",
    "some other report",
])
def test_rejects_wrong_report(text):
    with pytest.raises(ValueError):
        illinois_cost.parse_report_text(text)


def test_rejects_missing_date():
    with pytest.raises(ValueError, match="date"):
        illinois_cost.parse_report_text(
            "Illinois Production Cost Report\nAnhydrous ammonia 1.00-2.00 1.50")


def test_rejects_report_with_no_prices():
    with pytest.raises(ValueError, match="No prices"):
        illinois_cost.parse_report_text(
            "Illinois Production Cost Report\nweek ending 1/2/2026\nAnhydrous Ammonia Offer NA")


def test_date_formats():
    f = illinois_cost.find_report_date
    assert f("Report for week ending 3/6/2026") == date(2026, 3, 6)
    assert f("Springfield, IL Thu Feb 24, 2022") == date(2022, 2, 24)
    assert f("September 8, 2022") == date(2022, 9, 8)


def test_white_potash_alone_is_not_potash():
    assert illinois_cost.match_item("Potash (White 0-0-62)") is None
    assert illinois_cost.match_item("Potash") == ("potash", "$/ton")


def test_iowa_and_illinois_share_one_file_without_clashing(tmp_path):
    out = tmp_path / "fertilizer.csv"
    ia = iowa_cost.parse_report_pdf((TESTS_DIR / "samples" / "ams_2863.pdf").read_bytes())
    il = illinois_cost.parse_report_text(NEW_LAYOUT)
    assert iowa_cost.save_records(ia, out) == 6
    assert iowa_cost.save_records(il, out) == len(il)   # same items, different state: all new
    assert iowa_cost.save_records(il, out) == 0         # re-run adds nothing
    rows = iowa_cost.read_saved(out)
    assert {r["region"] for r in rows} == {"IA", "IL"}
    anhydrous = {r["region"]: r["price"] for r in rows if r["item"] == "anhydrous"}
    assert anhydrous == {"IA": "902.33", "IL": "1200.0"}


def test_old_files_without_region_get_iowa(tmp_path):
    out = tmp_path / "old.csv"
    out.write_text("item,price,unit,as_of,source_name,source_url\n"
                   "map,976.0,$/ton,2026-10-30,USDA AMS Iowa Production Cost Report,"
                   "https://www.ams.usda.gov/mnreports/ams_2863.pdf\n")
    assert iowa_cost.read_saved(out)[0]["region"] == "IA"


def test_pull_reads_pdf_and_warns_when_stale(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(iowa_cost, "pdf_to_text", lambda b: NEW_LAYOUT)
    asked = []
    out = tmp_path / "f.csv"
    records = illinois_cost.pull(get_bytes=lambda url: asked.append(url) or b"%PDF",
                                 today=date(2026, 12, 1), out=out)
    assert asked == [illinois_cost.PDF_URL]
    assert len(records) == 5
    assert "WARNING: newest Illinois report" in capsys.readouterr().out
    assert len(iowa_cost.read_saved(out)) == 5


def test_one_state_failing_does_not_stop_the_other(capsys):
    def broken():
        raise ConnectionError("site down")

    calls = []
    results = pull_fertilizer.pull_all([("Iowa", broken), ("Illinois", lambda: calls.append(1) or ["ok"])])
    assert isinstance(results["Iowa"], ConnectionError)
    assert results["Illinois"] == ["ok"]
    assert "Iowa pull failed: site down" in capsys.readouterr().err
    assert pull_fertilizer.main([("Iowa", broken), ("Illinois", lambda: [])]) == 0
    assert pull_fertilizer.main([("Iowa", broken), ("Illinois", broken)]) == 1


def test_real_illinois_pdf_week_ending_oct_30_2026():
    """The real report Andy uploaded (tests/samples/ams_3195.pdf)."""
    pdf = (TESTS_DIR / "samples" / "ams_3195.pdf").read_bytes()
    records = illinois_cost.parse_report_pdf(pdf)
    prices = {r.item: r.price for r in records}
    assert prices == {
        "anhydrous": 981.11,
        "dap": 932.14,
        "uan28": 467.86,
        "uan32": 540.00,   # single price, no range
        "map": 948.00,
        "potash": 517.73,
        "urea": 770.00,
        "diesel": 5.71,    # No. 2 Diesel (Farm); Biodiesel is not read as diesel
    }
    assert "propane" not in prices  # this report has no propane row
    for r in records:
        assert r.as_of == date(2026, 10, 30)
        assert r.region == "IL"
        assert r.source_url == "https://www.ams.usda.gov/mnreports/ams_3195.pdf"
        assert r.unit == ("$/gal" if r.item == "diesel" else "$/ton")


def test_biodiesel_is_not_diesel():
    assert illinois_cost.match_item("Biodiesel (Farm)") is None
    assert illinois_cost.match_item("No. 2 Diesel (Farm)") == ("diesel", "$/gal")
