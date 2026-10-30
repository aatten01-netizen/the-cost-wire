from datetime import date

import pytest

from costwire import iowa_cost
from costwire.paths import TESTS_DIR

SAMPLE = TESTS_DIR / "samples" / "NW_GR910_2024-04-02.TXT"
PDF_SAMPLE = TESTS_DIR / "samples" / "ams_2863.pdf"
URL = "https://esmis.nal.usda.gov/sites/default/release-files/f1881k91k/0g356357r/js958418d/NW_GR910.TXT"


def sample_records():
    return iowa_cost.parse_report_csv(SAMPLE.read_text(), URL)


def test_parses_all_priced_items_from_sample():
    by_item = {r.item: r for r in sample_records()}
    assert set(by_item) == {"anhydrous", "urea", "uan32", "dap", "map", "potash", "propane", "diesel"}
    assert by_item["anhydrous"].price == 770.00
    assert by_item["urea"].price == 576.67
    assert by_item["uan32"].price == 396.67
    assert by_item["dap"].price == 785.00
    assert by_item["map"].price == 843.17
    assert by_item["potash"].price == 550.75
    assert by_item["propane"].price == 1.61
    assert by_item["diesel"].price == 3.45


def test_na_rows_are_left_out_not_guessed():
    items = {r.item for r in sample_records()}
    assert "uan28" not in items  # NA in the sample


def test_every_record_has_date_source_and_unit():
    for r in sample_records():
        assert r.as_of == date(2024, 4, 2)
        assert r.source_url == URL
        assert r.source_name == iowa_cost.SOURCE_NAME
    units = {r.item: r.unit for r in sample_records()}
    assert units["anhydrous"] == "$/ton"
    assert units["diesel"] == "$/gal"


def test_white_potash_does_not_overwrite_red():
    text = SAMPLE.read_text().replace("Potash (White) (0-0-62),NA,NA,NA",
                                      "Potash (White) (0-0-62),900,900,900.00")
    potash = [r for r in iowa_cost.parse_report_csv(text, URL) if r.item == "potash"]
    assert len(potash) == 1 and potash[0].price == 550.75


def test_rejects_wrong_file():
    with pytest.raises(ValueError):
        iowa_cost.parse_report_csv("<html>not a report</html>", URL)


def test_rejects_report_with_no_prices():
    text = "NW_GR910,Iowa Production Cost Report,04/2/2024,\nCommodity,Low Price,High Price,Average\nAnhydrous ammonia,NA,NA,NA\n"
    with pytest.raises(ValueError):
        iowa_cost.parse_report_csv(text, URL)


def test_find_latest_csv_url_takes_first_link():
    html = (f'<a href="{URL}">Apr 02</a>'
            '<a href="https://esmis.nal.usda.gov/sites/default/release-files/f1881k91k/ft84bb521/v405tz585/NW_GR910.TXT">Mar 22</a>')
    assert iowa_cost.find_latest_csv_url(html) == URL
    with pytest.raises(ValueError):
        iowa_cost.find_latest_csv_url("<html></html>")


def test_save_is_repeatable(tmp_path):
    out = tmp_path / "fertilizer.csv"
    assert iowa_cost.save_records(sample_records(), out) == 8
    assert iowa_cost.save_records(sample_records(), out) == 0  # same report twice = no dupes
    rows = iowa_cost.read_saved(out)
    assert len(rows) == 8
    assert list(rows[0].keys()) == iowa_cost.CSV_COLUMNS
    assert all(r["source_url"] == URL and r["as_of"] == "2024-04-02" for r in rows)


def test_pull_switches_to_pdf_when_csv_is_stale(tmp_path, capsys):
    out = tmp_path / "fertilizer.csv"
    pages = {iowa_cost.ESMIS_PAGE: f'<a href="{URL}">latest</a>', URL: SAMPLE.read_text()}
    pdfs = {iowa_cost.PDF_URL: PDF_SAMPLE.read_bytes()}
    records = iowa_cost.pull(get=pages.__getitem__, get_bytes=pdfs.__getitem__,
                             today=date(2026, 10, 31), out=out)
    assert {r.as_of for r in records} == {date(2026, 10, 30)}
    assert {r.source_url for r in records} == {iowa_cost.PDF_URL}
    assert len(iowa_cost.read_saved(out)) == 6
    assert "using the PDF" in capsys.readouterr().out


def test_pull_uses_pdf_when_csv_download_fails(tmp_path):
    def broken(url):
        raise ConnectionError("ESMIS down")
    pdfs = {iowa_cost.PDF_URL: PDF_SAMPLE.read_bytes()}
    records = iowa_cost.pull(get=broken, get_bytes=pdfs.__getitem__,
                             today=date(2026, 10, 31), out=tmp_path / "f.csv")
    assert len(records) == 6


def test_pull_quiet_when_fresh(tmp_path, capsys):
    pages = {iowa_cost.ESMIS_PAGE: f'<a href="{URL}">latest</a>', URL: SAMPLE.read_text()}
    iowa_cost.pull(get=pages.__getitem__, today=date(2024, 4, 10), out=tmp_path / "f.csv")
    assert "WARNING" not in capsys.readouterr().out


# --- PDF edition -----------------------------------------------------------

# A small text fixture shaped like the real report, with the extra cases the
# real sample doesn't have (urea, UAN28 NA, DAP, white potash, single price).
PDF_TEXT = """Iowa Production Cost Report (Bi-Weekly)
Report for week ending 3/6/2026
Fertilizer (Synthetic)
Class Sale Type Package Price Range Average Change Freight Delivery Period
Anhydrous Ammonia Ask 800.00 - 820.00 810.00 (3.17) F.O.B. Current
Urea (46-0-0) Ask 1,000.00 - 1,050.00 1,025.50 5.00 F.O.B. Current
Liquid Nitrogen (28-0-0) Ask NA
DAP (Diammonium Ask 900.00 900.00 0.00 F.O.B. Current
Phosphate 18-46-0)
Potash (White 0-0-62) Ask 700.00 - 720.00 710.00 0.00 F.O.B. Current
Potash (Red 0-0-60) Ask 480.00 - 520.00 499.80 5.80 F.O.B. Current
Propane Ask 1.58 - 1.84 9.99 0.10 F.O.B. Current
"""


def test_real_pdf_sample_parses():
    by_item = {r.item: r for r in iowa_cost.parse_report_pdf(PDF_SAMPLE.read_bytes())}
    # Numbers below are copied from tests/samples/ams_2863.pdf (week ending 10/30/2026)
    assert set(by_item) == {"anhydrous", "uan32", "map", "potash", "diesel", "propane"}
    assert by_item["anhydrous"].price == 902.33
    assert by_item["uan32"].price == 510.00
    assert by_item["map"].price == 976.00
    assert by_item["potash"].price == 499.80
    assert by_item["diesel"].price == 5.65
    assert by_item["propane"].price == 1.69
    for r in by_item.values():
        assert r.as_of == date(2026, 10, 30)
        assert r.source_url == iowa_cost.PDF_URL
        assert r.source_name == iowa_cost.SOURCE_NAME
    assert by_item["anhydrous"].unit == "$/ton"
    assert by_item["diesel"].unit == "$/gal"


def test_pdf_text_fixture_edge_cases(capsys):
    by_item = {r.item: r for r in iowa_cost.parse_report_pdf_text(PDF_TEXT, iowa_cost.PDF_URL)}
    assert by_item["urea"].price == 1025.50          # commas handled
    assert "uan28" not in by_item                    # NA left out, not guessed
    assert by_item["dap"].price == 900.00            # single price, no range
    assert by_item["potash"].price == 499.80         # red, not white
    assert "propane" not in by_item                  # average outside range: skipped
    assert "skipped propane" in capsys.readouterr().err
    assert by_item["anhydrous"].as_of == date(2026, 3, 6)


def test_pdf_rejects_wrong_text():
    with pytest.raises(ValueError):
        iowa_cost.parse_report_pdf_text("some other report", iowa_cost.PDF_URL)


def test_pdf_rejects_missing_date():
    with pytest.raises(ValueError):
        iowa_cost.parse_report_pdf_text("Iowa Production Cost Report\nAnhydrous Ammonia Ask 1.00 - 2.00 1.50",
                                         iowa_cost.PDF_URL)


def test_pdf_and_csv_rows_do_not_duplicate(tmp_path):
    out = tmp_path / "f.csv"
    records = iowa_cost.parse_report_pdf(PDF_SAMPLE.read_bytes())
    assert iowa_cost.save_records(records, out) == 6
    assert iowa_cost.save_records(records, out) == 0
