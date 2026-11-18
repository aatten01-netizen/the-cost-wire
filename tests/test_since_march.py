from datetime import date

from costwire import accuracy, brief, changes, since_march, state_brief

IA = "USDA AMS Iowa Production Cost Report"
IA_URL = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"
IA_OLD_URL = "https://example.gov/ams_2863_2026-02-26.pdf"   # test-only link
IL = "USDA AMS Illinois Production Cost Report"
IL_URL = "https://www.ams.usda.gov/mnreports/ams_3195.pdf"
NOW = date(2026, 11, 13)


def row(item, price, as_of, region="IA", source=IA, url=IA_URL, unit="$/ton"):
    return {"item": item, "price": price, "unit": unit, "as_of": as_of,
            "source_name": source, "source_url": url, "region": region}


def sample():
    return [
        row("anhydrous", 700.0, date(2026, 2, 12), url=IA_OLD_URL),
        row("anhydrous", 720.0, date(2026, 2, 26), url=IA_OLD_URL),   # newest before Mar 4
        row("anhydrous", 960.0, date(2026, 3, 12)),                   # after cutoff: not the base
        row("anhydrous", 941.75, NOW),
        row("potash", 507.8, NOW),                                    # no pre-March report
        row("urea", 600.0, date(2026, 2, 27), region="IL", source=IL, url=IL_URL),
        row("urea", 570.0, NOW, region="IL", source=IL, url=IL_URL),
        row("diesel", 4.0, date(2026, 2, 26), unit="$/gal"),          # fuel: not in this section
        row("diesel", 5.28, NOW, unit="$/gal"),
    ]


def test_math_uses_newest_report_before_march_4():
    rows = sample()
    out = since_march.compute(changes.compute(rows), rows)
    assert [(s["region"], s["item"]) for s in out] == [("IA", "anhydrous"), ("IL", "urea")]
    a = out[0]
    assert a["base_price"] == 720.0 and a["base_as_of"] == date(2026, 2, 26)
    assert a["base_source_url"] == IA_OLD_URL and a["source_url"] == IA_URL
    assert a["change"] == 221.75 and a["pct"] == 30.8
    u = out[1]
    assert u["change"] == -30.0 and u["pct"] == -5.0


def test_left_out_with_no_pre_march_report_or_other_source():
    rows = [row("anhydrous", 941.75, NOW),
            row("anhydrous", 700.0, date(2026, 2, 26), source="Some other report")]
    assert since_march.compute(changes.compute(rows), rows) == []
    # report dated exactly Mar 4 is not "before"
    rows = [row("anhydrous", 941.75, NOW), row("anhydrous", 700.0, date(2026, 3, 4))]
    assert since_march.compute(changes.compute(rows), rows) == []


def test_bad_baseline_price_is_skipped():
    rows = [row("anhydrous", 941.75, NOW), row("anhydrous", 0.0, date(2026, 2, 26))]
    assert since_march.compute(changes.compute(rows), rows) == []


def test_brief_line_has_both_prices_dates_links_and_no_advice():
    rows = sample()
    b = brief.build(changes.compute(rows), NOW, None, rows)
    md = brief.to_markdown(b)
    assert "## Since early March" in md
    line = b["since_march"][0]["md"]
    assert line.startswith("Iowa anhydrous ammonia: $941.75/ton (Nov 13, 2026) vs "
                           "$720.00/ton (Feb 26, 2026), +$221.75 (+30.8%).")
    assert IA_URL in line and IA_OLD_URL in line
    assert "-$30.00 (-5.0%)" in b["since_march"][1]["line"]
    page = brief.to_html(b)
    assert "<h2>Since early March</h2>" in page and f'href="{IA_OLD_URL}"' in page
    for word in ("buy", "sell", "should", "lock in"):
        assert word not in " ".join(s["md"].lower() for s in b["since_march"])


def test_section_left_out_without_baseline():
    rows = [row("anhydrous", 941.75, NOW)]
    b = brief.build(changes.compute(rows), NOW, None, rows)
    assert b["since_march"] == []
    assert "Since early March" not in brief.to_markdown(b)
    assert "Since early March" not in brief.to_html(b)


def test_accuracy_check_passes_and_catches_changed_or_missing_line():
    rows = sample()
    results = changes.compute(rows)
    md = brief.to_markdown(brief.build(results, NOW, None, rows))
    assert accuracy.check_since_march(md, results, rows) == []
    assert accuracy.check_since_march(md.replace("+30.8%", "+33.0%"), results, rows)
    gone = md.replace("- Illinois urea:", "Illinois urea:")
    assert any("missing" in p for p in accuracy.check_since_march(gone, results, rows))


def test_state_edition_shows_only_its_state():
    rows = sample()
    b, md = state_brief.build_edition(changes.compute(rows), "IL", NOW, None, rows)
    assert [s["line"].split(":")[0] for s in b["since_march"]] == ["Illinois urea"]
    assert "Iowa anhydrous" not in md
