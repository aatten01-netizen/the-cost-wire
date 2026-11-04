import csv
from datetime import date

from costwire import brief, changes

IA = "USDA AMS Iowa Production Cost Report"
IL = "USDA AMS Illinois Production Cost Report"
IA_URL = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"
IL_URL = "https://www.ams.usda.gov/mnreports/ams_3195.pdf"
DAY = date(2026, 11, 2)


def row(item, price, as_of, region="IA", source=IA, url=IA_URL, unit="$/ton"):
    return {"item": item, "price": price, "unit": unit, "as_of": as_of,
            "source_name": source, "source_url": url, "region": region}


def sample():
    return changes.compute([
        row("anhydrous", 900.0, date(2026, 10, 30)),
        row("anhydrous", 880.0, date(2026, 10, 16)),
        row("urea", 700.0, date(2026, 10, 30)),
        row("urea", 800.0, date(2026, 10, 16)),           # -12.5%: biggest move
        row("anhydrous", 981.11, date(2026, 10, 30), "IL", IL, IL_URL),
        row("diesel", 5.65, date(2026, 10, 30), unit="$/gal"),
    ])


def test_headline_is_biggest_percent_move():
    assert brief.headline(sample()) == "Iowa urea down $100.00/ton (12.5%) vs 2 weeks ago"


def test_headline_falls_back_to_one_year():
    results = changes.compute([row("potash", 500.0, date(2026, 10, 30)),
                               row("potash", 400.0, date(2025, 10, 31))])
    assert brief.headline(results) == "Iowa potash up $100.00/ton (25.0%) vs a year ago"


def test_headline_with_no_history_says_so():
    results = changes.compute([row("potash", 500.0, date(2026, 10, 30))])
    assert "no earlier prices saved yet" in brief.headline(results)


def test_headline_ties_are_repeatable():
    results = changes.compute([
        row("urea", 110.0, date(2026, 10, 30)), row("urea", 100.0, date(2026, 10, 16)),
        row("dap", 110.0, date(2026, 10, 30)), row("dap", 100.0, date(2026, 10, 16)),
    ])
    assert brief.headline(results).startswith("Iowa DAP up")
    assert brief.headline(list(reversed(results))).startswith("Iowa DAP up")


def test_signed_change():
    assert brief.signed_change(20.0, 2.3) == "+$20.00 (+2.3%)"
    assert brief.signed_change(-100.0, -12.5) == "-$100.00 (-12.5%)"
    assert brief.signed_change(0.0, 0.0) == "$0.00 (0.0%)"
    assert brief.signed_change(None, None) == "n/a"
    assert brief.signed_change(1234.5, None) == "+$1,234.50"


def test_what_changed_lines():
    by_item = {(r["item"], r["region"]): r for r in sample()}
    assert brief.what_changed(by_item[("anhydrous", "IA")]) == (
        "Iowa anhydrous ammonia: $900.00/ton as of Oct 30, 2026"
        + ", up $20.00 (2.3%) from $880.00 on Oct 16, 2026.")
    assert brief.what_changed(by_item[("diesel", "IA")]) == (
        "Iowa farm diesel: $5.65/gal as of Oct 30, 2026. No earlier price saved yet to compare.")


def test_unchanged_price_says_unchanged():
    results = changes.compute([row("map", 900.0, date(2026, 10, 30)),
                               row("map", 900.0, date(2026, 10, 16))])
    assert "unchanged from $900.00 on Oct 16, 2026" in brief.what_changed(results[0])
    assert brief.biggest_move(results) is None


def test_markdown_has_every_number_with_source_and_disclaimer():
    md = brief.to_markdown(brief.build(sample(), DAY))
    assert md.startswith("# The Cost Wire — week of Nov 2, 2026")
    for text in ("$900.00/ton", "$981.11/ton", "$5.65/gal", "+$20.00 (+2.3%)",
                 "-$100.00 (-12.5%)", IA_URL, IL_URL, "Data, not advice",
                 "Data: USDA Agricultural Marketing Service (AMS)."):
        assert text in md, text
    # every table row links its source
    table_rows = [l for l in md.splitlines() if l.startswith("| ") and "](" in l]
    assert len(table_rows) == 4
    # never tells anyone what to do
    lowered = md.lower().replace("does not tell anyone to buy or sell", "")
    for word in ("buy now", "sell now", "should buy", "should sell", " buy ", " sell "):
        assert word not in lowered


def test_rows_are_grouped_by_region_fertilizer_before_fuel():
    rows = brief.build(sample(), DAY)["rows"]
    assert [(r["region"], r["item"]) for r in rows] == [
        ("IA", "anhydrous"), ("IA", "urea"), ("IA", "diesel"), ("IL", "anhydrous")]


def test_sources_list_is_unique_with_newest_date():
    srcs = brief.sources(sample())
    assert [s["name"] for s in srcs] == [IL, IA]
    assert all(s["as_of"] == date(2026, 10, 30) for s in srcs)


def test_html_escapes_and_links():
    results = changes.compute([row("potash", 500.0, date(2026, 10, 30),
                                   source="A <b>bad</b> & name", url=IA_URL + "?a=1&b=2")])
    page = brief.to_html(brief.build(results, DAY))
    assert "<b>bad</b>" not in page and "A &lt;b&gt;bad&lt;/b&gt; &amp; name" in page
    assert 'href="https://www.ams.usda.gov/mnreports/ams_2863.pdf?a=1&amp;b=2"' in page
    assert page.startswith("<!doctype html>") and "Data, not advice" in page


def test_write_brief_files(tmp_path):
    data = tmp_path / "fertilizer.csv"
    with open(data, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item", "price", "unit", "as_of",
                                          "source_name", "source_url", "region"])
        w.writeheader()
        w.writerow({"item": "urea", "price": "770.0", "unit": "$/ton", "as_of": "2026-10-30",
                    "source_name": IL, "source_url": IL_URL, "region": "IL"})
    md_path, html_path = brief.write_brief(DAY, data, tmp_path / "briefs")
    assert md_path.name == "2026-11-02.md" and html_path.name == "2026-11-02.html"
    assert "$770.00/ton" in md_path.read_text() and "$770.00/ton" in html_path.read_text()


def test_write_brief_with_no_data_returns_none(tmp_path):
    assert brief.write_brief(DAY, tmp_path / "missing.csv", tmp_path / "briefs") is None
    assert not (tmp_path / "briefs").exists()


def test_unknown_item_and_region_use_raw_names():
    results = changes.compute([row("sulfur", 300.0, date(2026, 10, 30), region="ND")])
    assert "ND sulfur: $300.00/ton" in brief.what_changed(results[0])


def test_acronyms_stay_capitalized_in_sentences():
    results = changes.compute([row("dap", 900.0, date(2026, 10, 30), "IL", IL, IL_URL),
                               row("uan28", 460.0, date(2026, 10, 30), "IL", IL, IL_URL)])
    lines = [brief.what_changed(r) for r in results]
    assert lines[0].startswith("Illinois DAP: ") and lines[1].startswith("Illinois UAN 28%: ")
    assert brief.item_in_sentence("onhwy_diesel") == "on-highway diesel (retail)"


def test_credit_names_only_agencies_in_the_brief():
    eia = {"name": "U.S. Energy Information Administration (EIA)", "url": "https://www.eia.gov", "as_of": DAY}
    usda = {"name": IA, "url": IA_URL, "as_of": DAY}
    assert "EIA" not in brief.credit_line([usda])
    assert brief.credit_line([usda, eia]) == ("Data: USDA Agricultural Marketing Service (AMS) and "
                                              "U.S. Energy Information Administration (EIA).")
