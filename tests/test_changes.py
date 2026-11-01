import csv
from datetime import date

from costwire import changes

IA = "USDA AMS Iowa Production Cost Report"
IL = "USDA AMS Illinois Production Cost Report"
URL = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"


def row(item, price, as_of, region="IA", source=IA, unit="$/ton", url=URL):
    return {"item": item, "price": price, "unit": unit, "as_of": as_of,
            "source_name": source, "source_url": url, "region": region}


def only(results, item, region="IA"):
    [r] = [r for r in results if r["item"] == item and r["region"] == region]
    return r


def test_two_week_and_one_year_change():
    rows = [
        row("anhydrous", 900.0, date(2026, 10, 30)),
        row("anhydrous", 880.0, date(2026, 10, 16)),
        row("anhydrous", 750.0, date(2025, 10, 31)),
    ]
    r = only(changes.compute(rows), "anhydrous")
    assert r["price"] == 900.0 and r["as_of"] == date(2026, 10, 30)
    assert r["price_2w"] == 880.0 and r["as_of_2w"] == date(2026, 10, 16)
    assert r["change_2w"] == 20.0 and r["pct_2w"] == 2.3
    assert r["price_1y"] == 750.0 and r["change_1y"] == 150.0 and r["pct_1y"] == 20.0


def test_price_drop_is_negative():
    rows = [row("urea", 700.0, date(2026, 10, 30)), row("urea", 800.0, date(2026, 10, 16))]
    r = only(changes.compute(rows), "urea")
    assert r["change_2w"] == -100.0 and r["pct_2w"] == -12.5


def test_no_history_leaves_changes_blank():
    r = only(changes.compute([row("map", 976.0, date(2026, 10, 30))]), "map")
    for name in ("2w", "1y"):
        assert r[f"price_{name}"] is None
        assert r[f"change_{name}"] is None
        assert r[f"pct_{name}"] is None


def test_too_far_from_target_is_not_used():
    # 1 week ago and 5 weeks ago are both too far from "2 weeks ago" -> blank, not guessed
    rows = [row("dap", 900.0, date(2026, 10, 30)),
            row("dap", 890.0, date(2026, 10, 23)),
            row("dap", 850.0, date(2026, 9, 25))]
    assert only(changes.compute(rows), "dap")["change_2w"] is None


def test_closest_date_wins_within_slack():
    rows = [row("potash", 500.0, date(2026, 10, 30)),
            row("potash", 490.0, date(2026, 10, 13)),   # 3 days off target
            row("potash", 495.0, date(2026, 10, 17))]   # 1 day off target
    r = only(changes.compute(rows), "potash")
    assert r["as_of_2w"] == date(2026, 10, 17) and r["change_2w"] == 5.0


def test_regions_and_sources_never_mix():
    rows = [row("anhydrous", 900.0, date(2026, 10, 30), region="IA"),
            row("anhydrous", 980.0, date(2026, 10, 16), region="IL", source=IL)]
    results = changes.compute(rows)
    assert only(results, "anhydrous", "IA")["change_2w"] is None
    assert only(results, "anhydrous", "IL")["change_2w"] is None


def test_units_never_mix():
    rows = [row("diesel", 5.6, date(2026, 10, 30), unit="$/gal"),
            row("diesel", 900.0, date(2026, 10, 16), unit="$/ton")]
    assert all(r["change_2w"] is None for r in changes.compute(rows))


def test_zero_old_price_gives_no_percent():
    rows = [row("x", 5.0, date(2026, 10, 30)), row("x", 0.0, date(2026, 10, 16))]
    r = only(changes.compute(rows), "x")
    assert r["change_2w"] == 5.0 and r["pct_2w"] is None


def test_read_write_round_trip(tmp_path):
    src = tmp_path / "fertilizer.csv"
    with open(src, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item", "price", "unit", "as_of",
                                          "source_name", "source_url", "region"])
        w.writeheader()
        w.writerow(row("anhydrous", "900.0", "2026-10-30"))
        w.writerow(row("anhydrous", "880.0", "2026-10-16"))
        w.writerow(row("anhydrous", "oops", "2026-10-09"))         # bad price: skipped
        w.writerow(row("anhydrous", "870.0", "2026-10-02", url=""))  # no source: skipped
    out = tmp_path / "changes.csv"
    assert changes.main(src, out) == 0
    [saved] = list(csv.DictReader(open(out)))
    assert saved["change_2w"] == "20.0" and saved["as_of_2w"] == "2026-10-16"
    assert saved["change_1y"] == "" and saved["pct_1y"] == ""
    assert saved["source_url"] == URL


def test_missing_input_file(tmp_path):
    assert changes.main(tmp_path / "nope.csv", tmp_path / "out.csv") == 1


def test_real_data_file_runs():
    rows = changes.read_rows()
    results = changes.compute(rows)
    assert len(results) == len({changes.series_key(r) for r in rows})
    assert all(r["source_url"].startswith("https://") for r in results)
