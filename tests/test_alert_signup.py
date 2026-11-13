import csv
from datetime import date

import pytest

from costwire import alert_signup, site


def row(item, region, price=500.0, as_of=date(2026, 10, 30)):
    return {"item": item, "region": region, "price": price, "unit": "$/ton", "as_of": as_of,
            "source_name": "USDA AMS", "source_url": "https://www.ams.usda.gov/x.pdf"}


ROWS = [row("urea", "IL"), row("anhydrous", "IA"), row("anhydrous", "IA", as_of=date(2026, 10, 16)),
        row("anhydrous", "IL"), row("diesel", "PADD2")]
LIVE = {"SIGNUP_FORM_URL": "https://script.google.com/macros/s/ABC/exec", "ALERTS_SIGNUP_LIVE": "yes"}


def test_options_only_published_states_once_each():
    opts = alert_signup.alert_options(ROWS)
    assert opts.count(("anhydrous", "IA")) == 1
    assert set(opts) == {("anhydrous", "IA"), ("anhydrous", "IL"), ("urea", "IL"), ("diesel", "PADD2")}
    assert alert_signup.alert_options([row("urea", "TX")]) == []  # unknown region: not offered


def test_placeholder_unless_both_url_and_go_ahead():
    for env in ({}, {"SIGNUP_FORM_URL": LIVE["SIGNUP_FORM_URL"]}, {"ALERTS_SIGNUP_LIVE": "yes"},
                {"SIGNUP_FORM_URL": "http://x.com", "ALERTS_SIGNUP_LIVE": "yes"},
                {"SIGNUP_FORM_URL": LIVE["SIGNUP_FORM_URL"], "SIGNUP_LIVE": "yes"}):
        body = alert_signup.render(ROWS, env)
        assert "disabled" in body and 'method="post"' not in body and "name=" not in body


def test_live_form_posts_choices():
    body = alert_signup.render(ROWS, LIVE)
    assert 'action="https://script.google.com/macros/s/ABC/exec"' in body
    assert 'name="email"' in body and 'name="alert_pick"' in body and 'name="alert_threshold"' in body
    assert 'value="anhydrous|IA">Iowa: Anhydrous ammonia<' in body
    assert 'name="website"' in body and "disabled" not in body
    assert "Data, not advice" in body and "STOP" in body


def test_no_prices_no_form():
    body = alert_signup.render([], LIVE)
    assert "<form" not in body and "No published prices yet" in body


KNOWN = {("anhydrous", "IA"), ("urea", "IL")}


def test_parse_signups_rules():
    sheet = [
        {"time": "t", "email": "only@brief.com"},                          # brief-only: skipped quietly
        {"email": "A@Farm.com", "alert_pick": "anhydrous|IA", "alert_threshold": "25"},
        {"email": "a@farm.com", "alert_item": "anhydrous", "alert_region": "ia", "alert_threshold": "$10"},
        {"email": "b@farm.com", "alert_item": "urea", "alert_region": "IL", "alert_threshold": "50"},
        {"email": "c@farm.com", "alert_pick": "potash|IA", "alert_threshold": "25"},   # not published
        {"email": "nope", "alert_pick": "anhydrous|IA", "alert_threshold": "25"},      # bad email
        {"email": "d@farm.com", "alert_pick": "anhydrous|IA", "alert_threshold": "0"},  # bad amount
        {"email": "e@farm.com", "alert_pick": "anhydrous|IA", "alert_threshold": "5000"},  # typo
        {"email": "f@farm.com", "alert_pick": "anhydrous|IA", "alert_threshold": "abc"},
    ]
    out = alert_signup.parse_signups(sheet, KNOWN)
    assert out == [
        {"email": "a@farm.com", "item": "anhydrous", "region": "IA", "threshold": "10"},  # newest wins
        {"email": "b@farm.com", "item": "urea", "region": "IL", "threshold": "50"},
    ]


def test_export_matches_alerts_format(tmp_path):
    sheet = tmp_path / "sheet.csv"
    sheet.write_text("time,email,alert_item,alert_region,alert_threshold\n"
                     "2026-11-13,x@farm.com,anhydrous,IA,25\n2026-11-13,y@farm.com,,,\n",
                     encoding="utf-8")
    out = tmp_path / "alerts.csv"
    assert alert_signup.export(sheet, out, rows=ROWS) == 1
    with open(out, newline="") as f:
        got = list(csv.DictReader(f))
    assert got == [{"email": "x@farm.com", "item": "anhydrous", "region": "IA", "threshold": "25"}]
    from costwire import alerts
    assert alerts.load_subscriptions(out) == [
        {"email": "x@farm.com", "item": "anhydrous", "region": "IA", "threshold": 25.0}]


def test_export_refuses_inside_repo(tmp_path):
    sheet = tmp_path / "sheet.csv"
    sheet.write_text("email\n", encoding="utf-8")
    with pytest.raises(ValueError):
        alert_signup.export(sheet, alert_signup.ROOT / "data" / "alerts.csv", rows=ROWS)
    assert not (alert_signup.ROOT / "data" / "alerts.csv").exists()


def test_site_builds_alerts_page_and_nav(tmp_path):
    prices = tmp_path / "fert.csv"
    prices.write_text("item,price,unit,as_of,source_name,source_url,region\n"
                      "urea,770.0,$/ton,2026-10-30,USDA AMS,https://www.ams.usda.gov/x.pdf,IL\n",
                      encoding="utf-8")
    site.build_site(briefs_dir=tmp_path / "none", site_dir=tmp_path / "site",
                    land_file=tmp_path / "land.csv", price_file=prices)
    page = (tmp_path / "site" / "alerts.html").read_text()
    assert "Illinois: Urea" in page and "Price-move alerts" in page
    assert 'href="alerts.html">Alerts<' in (tmp_path / "site" / "index.html").read_text()
    assert 'href="alerts.html"' in (tmp_path / "site" / "pricing.html").read_text()
