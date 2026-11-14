from datetime import date

from costwire import pricing, pro_sample, site

SRC = "USDA AMS Iowa Production Cost Report"
URL = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"


def row(item, price, d, region="IA", unit="$/ton", src=SRC, url=URL):
    return {"item": item, "price": price, "unit": unit, "as_of": date.fromisoformat(d),
            "source_name": src, "source_url": url, "region": region}


def test_no_move_means_no_numbers():
    # one report per item (like data/fertilizer.csv today): nothing to show, no made-up price
    rows = [row("anhydrous", 902.33, "2026-10-30"), row("urea", 770.0, "2026-10-30", region="IL")]
    assert pro_sample.sample_move(rows) is None
    out = pro_sample.render(rows)
    assert "No sample yet" in out and "Oct 30, 2026" in out
    assert "902.33" not in out and "770" not in out and "Subject:" not in out
    assert "Data, not advice" in out
    assert "No sample yet" in pro_sample.render([])


def test_picks_biggest_percent_move_and_matching_setting():
    rows = [row("anhydrous", 862.33, "2026-10-16"), row("anhydrous", 902.33, "2026-10-30"),  # +$40, 4.6%
            row("potash", 450.0, "2026-10-16"), row("potash", 499.8, "2026-10-30")]          # +$49.80, 11.1%
    move, threshold = pro_sample.sample_move(rows)
    assert (move["item"], move["region"]) == ("potash", "IA")
    assert threshold == 25  # biggest alert choice a $49.80 move hits


def test_moves_under_smallest_choice_are_skipped():
    rows = [row("diesel", 5.50, "2026-10-16", unit="$/gal"), row("diesel", 5.65, "2026-10-30", unit="$/gal")]
    assert pro_sample.sample_move(rows) is None


def test_old_gap_is_not_a_move():
    rows = [row("dap", 800, "2026-06-01"), row("dap", 900, "2026-10-30")]
    assert pro_sample.sample_move(rows) is None


def test_sample_shows_real_alert_with_sources_and_no_email():
    rows = [row("anhydrous", 862.33, "2026-10-16"), row("anhydrous", 902.33, "2026-10-30")]
    out = pro_sample.render(rows)
    assert "Subject: The Cost Wire alert: Iowa anhydrous ammonia up $40.00" in out
    assert "$902.33/ton on Oct 30, 2026" in out and "$862.33/ton on Oct 16, 2026" in out
    assert "$25 or more" in out
    assert f'href="{URL}"' in out
    assert "@" not in out  # no reader email anywhere
    assert "Data, not advice" in out


def test_text_is_escaped():
    rows = [row("anhydrous", 862.33, "2026-10-16", src="<b>x</b>"),
            row("anhydrous", 902.33, "2026-10-30", src="<b>x</b>")]
    assert "<b>x</b>" not in pro_sample.render(rows)


def test_pricing_links_to_sample():
    assert 'href="pro-sample.html"' in pricing.render({})


def test_site_build_writes_sample_page(tmp_path):
    prices = tmp_path / "fertilizer.csv"
    prices.write_text(
        "item,price,unit,as_of,source_name,source_url,region\n"
        f"anhydrous,862.33,$/ton,2026-10-16,{SRC},{URL},IA\n"
        f"anhydrous,902.33,$/ton,2026-10-30,{SRC},{URL},IA\n", encoding="utf-8")
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    out = tmp_path / "site"
    site.build_site(briefs, out, price_file=prices)
    page = (out / "pro-sample.html").read_text(encoding="utf-8")
    assert "<title>The Cost Wire — sample Pro alert</title>" in page
    assert 'href="pricing.html"' in page and "up $40.00" in page
    assert 'name="viewport"' in page
