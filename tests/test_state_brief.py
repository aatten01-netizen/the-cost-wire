import html
from datetime import date

import pytest

from costwire import brief, changes, pricing, site, state_brief

IA_SRC = ("USDA AMS Iowa Production Cost Report", "https://www.ams.usda.gov/mnreports/ams_2863.pdf")
IL_SRC = ("USDA AMS Illinois Production Cost Report", "https://www.ams.usda.gov/mnreports/ams_3195.pdf")
EIA_SRC = ("EIA Midwest (PADD 2) on-highway diesel", "https://www.eia.gov/petroleum/gasdiesel/")


def row(item, price, d, region, src, unit="$/ton"):
    return {"item": item, "price": price, "unit": unit, "as_of": date.fromisoformat(d),
            "source_name": src[0], "source_url": src[1], "region": region}


ROWS = [
    row("anhydrous", 880.00, "2026-10-16", "IA", IA_SRC),
    row("anhydrous", 902.33, "2026-10-30", "IA", IA_SRC),
    row("anhydrous", 950.00, "2026-10-30", "IL", IL_SRC),
    row("urea", 700.00, "2026-10-16", "IL", IL_SRC),
    row("urea", 770.00, "2026-10-30", "IL", IL_SRC),  # IL's +10% is the biggest move overall
    row("onhwy_diesel", 4.10, "2026-11-02", "PADD2", EIA_SRC, unit="$/gal"),
]
BRIEF_DATE = date(2026, 11, 9)


def test_filter_keeps_state_and_midwest_only():
    results = changes.compute(ROWS)
    ia = state_brief.filter_results(results, "IA")
    assert {(r["region"], r["item"]) for r in ia} == {("IA", "anhydrous"), ("PADD2", "onhwy_diesel")}
    # A state with no prices of its own gets nothing, not just the Midwest rows.
    assert state_brief.filter_results(results, "MN") == []


def test_edition_headline_is_the_states_own_move():
    results = changes.compute(ROWS)
    b, md = state_brief.build_edition(results, "IA", BRIEF_DATE)
    # Overall biggest move is Illinois urea; the Iowa edition leads with Iowa.
    assert b["headline"].startswith("Iowa anhydrous ammonia up $22.33/ton")
    assert md.startswith("# The Cost Wire — Iowa edition, week of Nov 9, 2026")
    assert "Illinois" not in md
    assert "On-highway diesel" in md and brief.DISCLAIMER in md


def test_main_brief_title_unchanged():
    b = brief.build(changes.compute(ROWS), BRIEF_DATE)
    assert brief.to_markdown(b).startswith("# The Cost Wire — week of Nov 9, 2026\n")
    assert "<title>The Cost Wire — week of Nov 9, 2026</title>" in brief.to_html(b)


def test_bad_number_stops_the_edition(monkeypatch):
    real = brief.to_markdown
    monkeypatch.setattr(brief, "to_markdown",
                        lambda b: real(b).replace("$902.33/ton", "$999.99/ton"))
    with pytest.raises(ValueError, match="accuracy check"):
        state_brief.build_edition(changes.compute(ROWS), "IA", BRIEF_DATE)


def test_build_all_only_states_with_data():
    pages = state_brief.build_all(ROWS, BRIEF_DATE)
    assert list(pages) == ["IA", "IL"]
    il = pages["IL"]
    assert "Illinois edition" in il and "Pro preview" in il
    assert "Iowa" not in il.split("<h2>Sources</h2>")[0]


def test_site_writes_state_pages_and_pricing_link(tmp_path):
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    (briefs / "2026-11-09.html").write_text(
        brief.to_html(brief.build(changes.compute(ROWS), BRIEF_DATE)), encoding="utf-8")
    prices = tmp_path / "fertilizer.csv"
    with prices.open("w", encoding="utf-8") as f:
        f.write("item,price,unit,as_of,source_name,source_url,region\n")
        for r in ROWS:
            f.write(f"{r['item']},{r['price']},{r['unit']},{r['as_of']},"
                    f"{r['source_name']},{r['source_url']},{r['region']}\n")
    out = tmp_path / "site"
    site.build_site(briefs_dir=briefs, site_dir=out, land_file=tmp_path / "none.csv",
                    price_file=prices, corn_file=tmp_path / "no-corn.csv")
    ia = (out / "state" / "ia.html").read_text(encoding="utf-8")
    assert '<a href="../pricing.html">Pricing</a>' in ia  # site nav, one folder down
    assert "Iowa edition" in ia
    assert html.escape(brief.DISCLAIMER) in ia
    assert not (out / "state" / "mn.html").exists()
    index = (out / "state" / "index.html").read_text(encoding="utf-8")
    assert 'href="ia.html"' in index and 'href="il.html"' in index and "mn.html" not in index
    assert 'href="../feed.xml"' in index
    assert 'href="state/index.html"' in pricing.render({})


def test_no_briefs_means_empty_state_index(tmp_path):
    out = tmp_path / "site"
    site.build_site(briefs_dir=tmp_path / "nobriefs", site_dir=out,
                    land_file=tmp_path / "none.csv", price_file=tmp_path / "none.csv",
                    corn_file=tmp_path / "no-corn.csv")
    assert "No state editions yet." in (out / "state" / "index.html").read_text(encoding="utf-8")
    assert list((out / "state").glob("*.html")) == [out / "state" / "index.html"]
