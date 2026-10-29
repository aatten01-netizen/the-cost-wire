from datetime import date

import pytest

from costwire import iowa_cost
from costwire.paths import TESTS_DIR

SAMPLE = TESTS_DIR / "samples" / "NW_GR910_2024-04-02.TXT"
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


def test_pull_uses_fake_network_and_warns_when_stale(tmp_path, capsys):
    out = tmp_path / "fertilizer.csv"
    pages = {iowa_cost.ESMIS_PAGE: f'<a href="{URL}">latest</a>', URL: SAMPLE.read_text()}
    records = iowa_cost.pull(get=pages.__getitem__, today=date(2026, 10, 29), out=out)
    assert len(records) == 8
    assert len(iowa_cost.read_saved(out)) == 8
    assert "WARNING" in capsys.readouterr().out


def test_pull_quiet_when_fresh(tmp_path, capsys):
    pages = {iowa_cost.ESMIS_PAGE: f'<a href="{URL}">latest</a>', URL: SAMPLE.read_text()}
    iowa_cost.pull(get=pages.__getitem__, today=date(2024, 4, 10), out=tmp_path / "f.csv")
    assert "WARNING" not in capsys.readouterr().out
