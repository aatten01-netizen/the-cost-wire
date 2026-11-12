from datetime import date

from costwire import alerts

SRC = "USDA AMS Iowa Production Cost Report"
URL = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"


def row(item, price, d, region="IA", unit="$/ton", src=SRC, url=URL):
    return {"item": item, "price": price, "unit": unit, "as_of": date.fromisoformat(d),
            "source_name": src, "source_url": url, "region": region}


ROWS = [row("anhydrous", 862.33, "2026-10-16"), row("anhydrous", 902.33, "2026-10-30"),
        row("urea", 600.0, "2026-10-16", region="IL"), row("urea", 590.0, "2026-10-30", region="IL")]


def subs_file(tmp_path, lines):
    p = tmp_path / "alerts.csv"
    p.write_text("email,item,region,threshold\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_load_subscriptions_cleans_and_skips_bad_rows(tmp_path):
    p = subs_file(tmp_path, ["A@Farm.com,Anhydrous,ia,25", "nobody,urea,IL,10",
                             "b@farm.com,urea,IL,abc", "c@farm.com,urea,IL,0", "d@farm.com,,IL,5"])
    assert alerts.load_subscriptions(p) == [
        {"email": "a@farm.com", "item": "anhydrous", "region": "IA", "threshold": 25.0}]
    assert alerts.load_subscriptions(tmp_path / "missing.csv") == []


def test_move_uses_two_newest_reports():
    m = alerts.latest_moves(ROWS)[("anhydrous", "IA")]
    assert m["dollars"] == 40.0 and m["pct"] == 4.6
    assert m["then"]["as_of"] == date(2026, 10, 16)


def test_no_move_with_one_report_or_old_gap():
    assert alerts.latest_moves([row("dap", 800, "2026-10-30")]) == {}
    old = [row("dap", 800, "2026-06-01"), row("dap", 900, "2026-10-30")]
    assert alerts.latest_moves(old) == {}  # never compare against a stale price


def test_never_mixes_sources_or_units():
    mixed = [row("diesel", 3.0, "2026-10-16", unit="$/gal", src="EIA", url="https://www.eia.gov/x"),
             row("diesel", 5.0, "2026-10-30", unit="$/gal")]
    assert alerts.latest_moves(mixed) == {}


def test_threshold_both_directions():
    subs = [{"email": "a@f.com", "item": "anhydrous", "region": "IA", "threshold": 40},
            {"email": "b@f.com", "item": "anhydrous", "region": "IA", "threshold": 41},
            {"email": "c@f.com", "item": "urea", "region": "IL", "threshold": 10},
            {"email": "d@f.com", "item": "potash", "region": "IA", "threshold": 1}]
    out = alerts.find_alerts(subs, ROWS)
    assert [a["to"] for a in out] == ["a@f.com", "c@f.com"]
    assert "up $40.00 (4.6%)" in out[0]["body"]
    assert "down $10.00" in out[1]["subject"]


def test_message_is_sourced_dated_and_not_advice():
    m = alerts.find_alerts([{"email": "a@f.com", "item": "anhydrous", "region": "IA",
                             "threshold": 25}], ROWS)[0]
    assert m["subject"] == "The Cost Wire alert: Iowa anhydrous ammonia up $40.00"
    body = m["body"]
    assert "$902.33/ton on Oct 30, 2026" in body and "$862.33/ton on Oct 16, 2026" in body
    assert URL in body and "Data, not advice" in body and "reply STOP" in body
    for bad in ("buy now", "sell now", "you should", "lock in", "good time"):
        assert bad not in body.lower()


def test_run_uses_mock_and_never_repeats(tmp_path):
    p = subs_file(tmp_path, ["a@farm.com,anhydrous,IA,25", "a@farm.com,anhydrous,IA,30"])
    sent = tmp_path / "alerts_sent.csv"
    s1 = alerts.MockSender()
    assert alerts.run(p, sent, ROWS, s1) == 1  # listed twice -> one alert
    assert s1.sent[0]["to"] == "a@farm.com"
    s2 = alerts.MockSender()
    assert alerts.run(p, sent, ROWS, s2) == 0  # same report again -> nothing
    newer = ROWS + [row("anhydrous", 950.0, "2026-11-13")]
    assert alerts.run(p, sent, newer, s2) == 1  # new report -> new alert
    assert "up $47.67" in s2.sent[0]["body"]


def test_main_without_list_does_nothing(monkeypatch, capsys):
    monkeypatch.delenv("ALERTS_FILE", raising=False)
    assert alerts.main() == 0
    assert "nothing to do" in capsys.readouterr().out
