import json
import shutil
import subprocess
from datetime import date

import pytest

from costwire import pricing, site, worksheet

SRC = "USDA AMS Iowa Production Cost Report"
URL = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"


def row(item, price, d, region="IA", unit="$/ton", src=SRC, url=URL):
    return {"item": item, "price": price, "unit": unit, "as_of": date.fromisoformat(d),
            "source_name": src, "source_url": url, "region": region}


def test_line_cost_math():
    # 180 lb/acre anhydrous at $902.33/ton = $81.21/acre
    assert worksheet.money(worksheet.line_cost(902.33, "$/ton", 180)) == "$81.21"
    # 3.5 gal/acre farm diesel at $5.65/gal = $19.775 -> shown to the cent
    assert worksheet.line_cost(5.65, "$/gal", 3.5) == pytest.approx(19.775)
    assert worksheet.line_cost(500, "$/ton", 0) == 0
    with pytest.raises(ValueError):
        worksheet.line_cost(1, "$/bu", 1)


def test_newest_published_price_per_state_only():
    rows = [row("anhydrous", 880.0, "2026-10-16"), row("anhydrous", 902.33, "2026-10-30"),
            row("urea", 770.0, "2026-10-30", region="IL"),
            row("ddgs", 170.0, "2026-11-02"),                     # feed: not on the worksheet
            row("onhwy_diesel", 6.4, "2026-11-02", region="PADD2", unit="$/gal"),  # not a state
            row("potash", 0.0, "2026-10-30"),                     # not a real price: left out
            row("diesel", 5.65, "2026-10-30", unit="$/gal")]
    opts = worksheet.price_options(rows)
    assert set(opts) == {"IA", "IL"}
    ia = {p["item"]: p for p in opts["IA"]}
    assert set(ia) == {"anhydrous", "diesel"}
    assert ia["anhydrous"]["price"] == 902.33 and ia["anhydrous"]["as_of"] == "2026-10-30"
    assert ia["diesel"]["rate_unit"] == "gal/acre"
    assert [p["item"] for p in opts["IL"]] == ["urea"]


def test_wrong_unit_is_left_out():
    assert worksheet.price_options([row("urea", 770.0, "2026-10-30", unit="$/cwt")]) == {}


def test_no_prices_means_no_numbers():
    out = worksheet.render([])
    assert "No published prices are saved yet" in out
    assert "<script" not in out and "Data, not advice" in out


def test_page_has_sources_dates_no_default_rates():
    rows = [row("anhydrous", 902.33, "2026-10-30"), row("urea", 770.0, "2026-10-30", region="IL")]
    out = worksheet.render(rows)
    assert f'href="{URL}"' in out and "Oct 30" in out
    assert "$902.33/ton" in out  # no-JavaScript fallback lists the published price
    assert "Data, not advice" in out and "sends nothing" in out
    assert "<form" not in out  # nothing gets submitted anywhere
    data = json.loads(out.split('id="ws-data">')[1].split("</script>")[0])
    assert all("rate" not in p for lines in data.values() for p in lines)  # rates are the farmer's
    assert not any(w in out.lower() for w in ("you should", "buy now", "recommend "))


def test_script_tag_cannot_be_broken_by_data():
    out = worksheet.render([row("anhydrous", 902.33, "2026-10-30", src="</script><b>x</b>")])
    assert "</script><b>x</b>" not in out


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_page_math_matches_python():
    cases = [(902.33, "$/ton", 180), (770.0, "$/ton", 215.5), (5.65, "$/gal", 3.5),
             (499.8, "$/ton", 100), (1234567.0, "$/ton", 2000)]
    js = worksheet.CALC_JS + "console.log(JSON.stringify(%s.map(c => money(lineCost(c[0], c[1], c[2])))));" % json.dumps(cases)
    got = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    assert got == [worksheet.money(worksheet.line_cost(*c)) for c in cases]


def test_pricing_links_to_worksheet_and_site_builds_it(tmp_path):
    assert 'href="worksheet.html"' in pricing.render({})
    prices = tmp_path / "fertilizer.csv"
    prices.write_text("item,price,unit,as_of,source_name,source_url,region\n"
                      f"anhydrous,902.33,$/ton,2026-10-30,{SRC},{URL},IA\n", encoding="utf-8")
    out = tmp_path / "site"
    site.build_site(briefs_dir=tmp_path / "none", site_dir=out,
                    land_file=tmp_path / "land.csv", price_file=prices)
    page = (out / "worksheet.html").read_text(encoding="utf-8")
    assert "<title>The Cost Wire — cost-per-acre worksheet</title>" in page
    assert "Cost-per-acre worksheet" in page and "sitenav" in page
    assert "Data, not advice" in page
