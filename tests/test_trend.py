from datetime import date, timedelta

from costwire import accuracy, brief, changes, trend

IA = "USDA AMS Iowa Production Cost Report"
IA_URL = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"
IL = "USDA AMS Illinois Production Cost Report"
IL_URL = "https://www.ams.usda.gov/mnreports/ams_3195.pdf"
LAST = date(2026, 10, 30)


def row(item, price, as_of, region="IA", source=IA, url=IA_URL, unit="$/ton"):
    return {"item": item, "price": price, "unit": unit, "as_of": as_of,
            "source_name": source, "source_url": url, "region": region}


def weekly(item, prices, region="IA", source=IA, url=IA_URL, unit="$/ton"):
    """One row per week, oldest first, ending on LAST."""
    n = len(prices)
    return [row(item, p, LAST - timedelta(weeks=n - 1 - i), region, source, url, unit)
            for i, p in enumerate(prices)]


def test_window_is_12_weeks_and_oldest_first():
    rows = weekly("anhydrous", [700.0] + [800.0 + i for i in range(13)])  # 14 weeks
    res = changes.compute(rows)
    pts = trend.series_points(rows, res[0])
    assert pts[0] == (LAST - timedelta(weeks=12), 800.0)   # 13 dates: day 0 and 12 weeks back
    assert pts[-1] == (LAST, 812.0)
    assert len(pts) == 13
    assert 700.0 not in [p for _, p in pts]


def test_only_fertilizer_with_two_or_more_dates():
    rows = (weekly("anhydrous", [900.0, 910.0]) + [row("potash", 500.0, LAST)]
            + weekly("diesel", [5.0, 5.5], unit="$/gal"))
    out = trend.compute(changes.compute(rows), rows)
    assert [t["item"] for t in out] == ["anhydrous"]


def test_series_do_not_mix_regions_or_sources():
    rows = weekly("anhydrous", [900.0, 910.0]) + weekly("anhydrous", [1000.0], "IL", IL, IL_URL)
    out = trend.compute(changes.compute(rows), rows)
    assert [(t["region"], [p for _, p in t["points"]]) for t in out] == [("IA", [900.0, 910.0])]


def test_same_date_saved_twice_uses_last_row():
    rows = weekly("urea", [600.0, 650.0]) + [row("urea", 655.0, LAST)]
    res = changes.compute(rows)
    assert trend.series_points(rows, res[0])[-1] == (LAST, 655.0)


def test_low_and_high_with_dates():
    rows = weekly("dap", [800.0, 780.0, 820.0, 780.0])
    t = trend.compute(changes.compute(rows), rows)[0]
    assert t["low"] == (LAST - timedelta(weeks=2), 780.0)   # tie: earliest date
    assert t["high"] == (LAST - timedelta(weeks=1), 820.0)


def test_svg_shape_and_flat_line():
    pts = [(LAST - timedelta(weeks=1), 900.0), (LAST, 950.0)]
    s = trend.svg(pts, "IA <test>")
    assert s.startswith("<svg") and s.endswith("</svg>")
    assert 'points="6.0,50.0 234.0,6.0"' in s          # low bottom-left, high top-right
    assert "&lt;test&gt;" in s                          # label escaped
    flat = trend.svg([(LAST - timedelta(weeks=1), 900.0), (LAST, 900.0)], "flat")
    assert 'points="6.0,28.0 234.0,28.0"' in flat


def test_brief_has_trend_section_in_md_and_html():
    rows = weekly("anhydrous", [880.0, 902.33])
    b = brief.build(changes.compute(rows), date(2026, 11, 2), None, rows)
    line = ("Iowa anhydrous ammonia: 2 saved prices from Oct 23, 2026 ($880.00/ton) "
            "to Oct 30, 2026 ($902.33/ton); low $880.00/ton (Oct 23, 2026), "
            "high $902.33/ton (Oct 30, 2026).")
    md = brief.to_markdown(b)
    assert f"## {brief.TREND_TITLE}" in md and f"- {line}" in md
    page = brief.to_html(b)
    assert '<svg class="trend"' in page and brief.TREND_TITLE in page


def test_no_history_no_trend_section():
    rows = [row("anhydrous", 900.0, LAST)]
    b = brief.build(changes.compute(rows), date(2026, 11, 2), None, rows)
    assert b["trends"] == []
    assert brief.TREND_TITLE not in brief.to_markdown(b)
    assert brief.TREND_TITLE not in brief.to_html(b)


def test_accuracy_check_catches_changed_trend_line():
    rows = weekly("anhydrous", [880.0, 902.33])
    results = changes.compute(rows)
    md = brief.to_markdown(brief.build(results, date(2026, 11, 2), None, rows))
    assert accuracy.check_trend(md, results, rows) == []
    bad = md.replace("low $880.00/ton", "low $870.00/ton")
    problems = accuracy.check_trend(bad, results, rows)
    assert len(problems) == 2   # one line not in data, one data line missing


def test_write_brief_includes_trend(tmp_path):
    import csv
    rows = weekly("urea", [600.0, 610.0, 620.0])
    data = tmp_path / "fert.csv"
    with open(data, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({**r, "as_of": r["as_of"].isoformat()})
    md_path, html_path = brief.write_brief(date(2026, 11, 2), data, tmp_path / "b",
                                           tmp_path / "no_corn.csv")
    assert "3 saved prices" in md_path.read_text()
    assert accuracy.run_checks(md_path, data, date(2026, 11, 2), tmp_path / "no_corn.csv") == []
