"""Tests for the cost-per-pound-of-nitrogen line. No network."""

from datetime import date

from costwire import accuracy, brief, changes, nitrogen

IA = ("USDA AMS Iowa Production Cost Report", "https://www.ams.usda.gov/mnreports/ams_2863.pdf")
IL = ("USDA AMS Illinois Production Cost Report", "https://www.ams.usda.gov/mnreports/ams_3195.pdf")
D = date(2026, 10, 30)


def row(item, region, price, unit="$/ton", src=IA):
    return {"item": item, "region": region, "price": price, "unit": unit, "as_of": D,
            "source_name": src[0], "source_url": src[1]}


def test_math_per_product():
    assert nitrogen.lb_n_per_ton("anhydrous") == 1640
    assert nitrogen.lb_n_per_ton("urea") == 920
    assert nitrogen.lb_n_per_ton("uan28") == 560
    assert nitrogen.lb_n_per_ton("uan32") == 640
    assert nitrogen.per_lb(902.33, "anhydrous") == 0.55   # 902.33 / 1640 = 0.5502
    assert nitrogen.per_lb(770.0, "urea") == 0.84         # 770 / 920 = 0.8370
    assert nitrogen.per_lb(467.86, "uan28") == 0.84       # 467.86 / 560 = 0.8355
    assert nitrogen.per_lb(510.0, "uan32") == 0.80        # 510 / 640 = 0.7969


def test_compute_keeps_only_n_items_states_and_real_prices():
    rows = changes.compute([
        row("uan32", "IL", 540.0, src=IL), row("anhydrous", "IA", 902.33),
        row("potash", "IA", 499.8),                     # not nitrogen
        row("urea", "PADD2", 700.0),                     # not IA/IL
        row("uan28", "IA", 0.0),                         # not a real price
        row("diesel", "IA", 5.65, "$/gal"),
        row("anhydrous", "IL", 981.11, src=IL),
    ])
    out = nitrogen.compute(rows)
    assert [(n["region"], n["item"]) for n in out] == [("IA", "anhydrous"), ("IL", "anhydrous"),
                                                       ("IL", "uan32")]
    assert out[0]["per_lb"] == 0.55 and out[0]["source_url"] == IA[1]


def test_wrong_unit_is_left_out():
    rows = changes.compute([row("urea", "IA", 38.5, "$/cwt")])
    assert nitrogen.compute(rows) == []


def test_brief_line_shows_math_source_date_and_no_advice():
    results = changes.compute([row("anhydrous", "IA", 902.33)])
    b = brief.build(results, date(2026, 11, 2))
    assert b["nitrogen"] == ["Iowa anhydrous ammonia: $0.55 per lb of N ($902.33/ton as of "
                             "Oct 30, 2026 ÷ 1,640 lb of N per ton, 82-0-0)."]
    md, page = brief.to_markdown(b), brief.to_html(b)
    assert f"## {brief.NITROGEN_TITLE}" in md and brief.NITROGEN_TITLE in page
    assert "$0.55 per lb of N" in page
    assert IA[1] in md.split("## Sources", 1)[1]           # its source is listed
    for word in ("buy", "sell", "should", "cheapest", "best"):
        assert word not in b["nitrogen"][0].lower()


def test_section_left_out_without_n_prices():
    results = changes.compute([row("potash", "IA", 499.8)])
    b = brief.build(results, date(2026, 11, 2))
    assert b["nitrogen"] == []
    assert brief.NITROGEN_TITLE not in brief.to_markdown(b)
    assert brief.NITROGEN_TITLE not in brief.to_html(b)


def test_accuracy_check_passes_and_catches_changed_or_missing_line():
    results = changes.compute([row("anhydrous", "IA", 902.33), row("urea", "IL", 770.0, src=IL)])
    md = brief.to_markdown(brief.build(results, date(2026, 11, 2)))
    assert accuracy.check_nitrogen(md, results) == []
    bad = md.replace("$0.55 per lb of N", "$0.45 per lb of N")
    problems = accuracy.check_nitrogen(bad, results)
    assert any("not in the saved data" in p for p in problems)
    assert any("missing from the brief" in p for p in problems)
    gone = md.split(f"## {brief.NITROGEN_TITLE}")[0] + "## Sources" + md.split("## Sources", 1)[1]
    assert len(accuracy.check_nitrogen(gone, results)) == 2
