"""Tests for the EIA Midwest diesel + propane puller. No real network calls."""

import csv
from datetime import date

from costwire import eia_fuel

DIESEL = "EMD_EPD2D_PTE_R20_DPG"
PROPANE = "W_EPLLPA_PRS_R20_DPG"


def reply(series, rows):
    """Shaped like an EIA API v2 reply (values come back as strings)."""
    return {"response": {"total": len(rows), "data": [
        {"period": p, "series": series, "duoarea": "R20", "value": v, "units": "$/GAL"}
        for p, v in rows]}}


def fake_get(replies, calls=None):
    def get_json(url, params):
        if calls is not None:
            calls.append((url, params))
        sid = params["facets[series][]"]
        if isinstance(replies[sid], Exception):
            raise replies[sid]
        return replies[sid]
    return get_json


def test_no_key_skips_cleanly(tmp_path, capsys):
    out = tmp_path / "f.csv"
    def boom(url, params):
        raise AssertionError("must not call EIA without a key")
    assert eia_fuel.pull(get_json=boom, api_key="", out=out) == []
    assert not out.exists()
    assert "EIA_API_KEY not set" in capsys.readouterr().out


def test_no_key_from_env(monkeypatch, tmp_path):
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    assert eia_fuel.pull(get_json=None, out=tmp_path / "f.csv") == []


def test_parse_response_reads_values_and_dates():
    recs = eia_fuel.parse_response(reply(DIESEL, [("2026-10-26", "3.712"), ("2026-10-19", 3.69)]),
                                   "onhwy_diesel", DIESEL, "$/gal")
    assert [(r.as_of, r.price) for r in recs] == [(date(2026, 10, 26), 3.712), (date(2026, 10, 19), 3.69)]
    r = recs[0]
    assert r.region == "PADD2" and r.unit == "$/gal" and r.item == "onhwy_diesel"
    assert r.source_name.startswith("U.S. Energy Information Administration")
    assert r.source_url == f"https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s={DIESEL}&f=W"


def test_missing_or_bad_values_are_left_out():
    recs = eia_fuel.parse_response(
        reply(DIESEL, [("2026-10-26", None), ("2026-10-19", ""), ("2026-10-12", "NA"),
                       ("bad-date", "3.1"), ("2026-10-05", "abc"), ("2026-09-28", "3.55")]),
        "onhwy_diesel", DIESEL, "$/gal")
    assert [(r.as_of, r.price) for r in recs] == [(date(2026, 9, 28), 3.55)]


def test_other_series_ignored_and_empty_reply_ok():
    assert eia_fuel.parse_response(reply("SOMETHING_ELSE", [("2026-10-26", "9.99")]),
                                   "onhwy_diesel", DIESEL, "$/gal") == []
    assert eia_fuel.parse_response({}, "onhwy_diesel", DIESEL, "$/gal") == []
    assert eia_fuel.parse_response({"response": {"data": []}}, "res_propane", PROPANE, "$/gal") == []


def test_pull_saves_both_and_key_not_stored(tmp_path):
    out = tmp_path / "f.csv"
    calls = []
    get = fake_get({DIESEL: reply(DIESEL, [("2026-10-26", "3.712")]),
                    PROPANE: reply(PROPANE, [("2026-10-26", "2.105")])}, calls)
    recs = eia_fuel.pull(get_json=get, api_key="SECRETKEY123", today=date(2026, 10, 31), out=out)
    assert {r.item for r in recs} == {"onhwy_diesel", "res_propane"}
    text = out.read_text()
    assert "SECRETKEY123" not in text
    rows = list(csv.DictReader(out.open()))
    assert {(r["item"], r["price"], r["region"]) for r in rows} == {
        ("onhwy_diesel", "3.712", "PADD2"), ("res_propane", "2.105", "PADD2")}
    # The right API routes and series were asked for, newest first.
    urls = {p["facets[series][]"]: u for u, p in calls}
    assert urls[DIESEL] == "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
    assert urls[PROPANE] == "https://api.eia.gov/v2/petroleum/pri/wfr/data/"
    assert all(p["sort[0][direction]"] == "desc" for _, p in calls)
    # Re-running adds no duplicates.
    eia_fuel.pull(get_json=get, api_key="SECRETKEY123", today=date(2026, 10, 31), out=out)
    assert len(list(csv.DictReader(out.open()))) == 2


def test_one_series_failing_doesnt_stop_other(tmp_path, capsys):
    out = tmp_path / "f.csv"
    get = fake_get({DIESEL: RuntimeError("https://api.eia.gov/...?api_key=SECRETKEY123 down"),
                    PROPANE: reply(PROPANE, [("2026-10-26", "2.105")])})
    recs = eia_fuel.pull(get_json=get, api_key="SECRETKEY123", today=date(2026, 10, 31), out=out)
    assert [r.item for r in recs] == ["res_propane"]
    captured = capsys.readouterr()
    assert "SECRETKEY123" not in captured.out + captured.err


def test_propane_off_season_and_stale_warning(tmp_path, capsys):
    out = tmp_path / "f.csv"
    get = fake_get({DIESEL: reply(DIESEL, [("2026-06-01", "3.50")]),
                    PROPANE: reply(PROPANE, [])})
    recs = eia_fuel.pull(get_json=get, api_key="k", today=date(2026, 7, 1), out=out)
    assert [r.item for r in recs] == ["onhwy_diesel"]
    msg = capsys.readouterr().out
    assert "Oct-Mar" in msg and "WARNING" in msg


def test_pull_all_includes_eia():
    from costwire import pull_fertilizer
    assert "EIA Midwest fuel" in [name for name, _ in pull_fertilizer.PULLERS]
