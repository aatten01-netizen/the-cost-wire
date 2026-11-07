"""Tests for the NASS cash rent / land value puller and the cash rent page. No network."""

from costwire import nass_land, rentpage, site

RENT = "RENT, CASH, CROPLAND, NON-IRRIGATED - EXPENSE, MEASURED IN $ / ACRE"
LAND = "AG LAND, CROPLAND - ASSET VALUE, MEASURED IN $ / ACRE"


def row(desc, value, year, state="IA", level="STATE", county=""):
    return {"short_desc": desc, "Value": value, "year": str(year), "state_alpha": state,
            "agg_level_desc": level, "county_name": county}


def test_parse_value():
    assert nass_land.parse_value("1,234") == 1234.0
    assert nass_land.parse_value("236") == 236.0
    for bad in ("(D)", "(NA)", "", None, "(Z)"):
        assert nass_land.parse_value(bad) is None


def test_parse_response_state_and_county_and_skips():
    payload = {"data": [
        row(RENT, "236", 2025),
        row(RENT, "250", 2025, level="COUNTY", county="STORY"),
        row(RENT, "(D)", 2025, level="COUNTY", county="LYON"),      # withheld by NASS
        row(LAND, "11,500", 2025),
        row("SOMETHING ELSE", "5", 2025),                           # unknown measure
        row(RENT, "200", "bad"),                                    # bad year
        row(RENT, "200", 2025, level="COUNTY", county=""),          # county level, no county
    ]}
    recs = nass_land.parse_response(payload, "http://x")
    assert [(r.item, r.state, r.county, r.year, r.value) for r in recs] == [
        ("cash_rent_cropland", "IA", "", 2025, 236.0),
        ("cash_rent_cropland", "IA", "Story", 2025, 250.0),
        ("land_value_cropland", "IA", "", 2025, 11500.0)]
    assert all(r.unit == "$/acre" and r.source_url == "http://x" for r in recs)


def test_source_url_has_no_key():
    p = nass_land.query_params(RENT, "WI", "STATE", 2024)
    assert "key" not in nass_land.source_url(p) and "state_alpha=WI" in nass_land.source_url(p)


def test_no_key_skips_cleanly(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("NASS_API_KEY", raising=False)
    out = tmp_path / "land.csv"
    def boom(url, params):
        raise AssertionError("must not call NASS without a key")
    assert nass_land.pull(get_json=boom, out=out) == []
    assert not out.exists()
    assert "NASS_API_KEY not set" in capsys.readouterr().out


def test_pull_saves_dedupes_and_survives_failures(tmp_path, capsys):
    out = tmp_path / "land.csv"
    calls = []
    def get_json(url, params):
        calls.append(params)
        if params["state_alpha"] == "MN":
            raise RuntimeError("boom " + params["key"])
        if params["short_desc"] == RENT and params["agg_level_desc"] == "STATE":
            return {"data": [row(RENT, "200", 2024, params["state_alpha"]),
                             row(RENT, "210", 2025, params["state_alpha"])]}
        return {"data": []}
    from datetime import date
    recs = nass_land.pull(get_json=get_json, api_key="SECRET", today=date(2026, 11, 4), out=out,
                          states=["IA", "MN"])
    assert len(recs) == 2 and all(c["year__GE"] == 2024 for c in calls)
    err = capsys.readouterr().err
    assert "SECRET" not in err and "failed" in err
    assert "SECRET" not in out.read_text()
    # run again: same rows, nothing new, no duplicates
    nass_land.pull(get_json=get_json, api_key="SECRET", today=date(2026, 11, 4), out=out,
                   states=["IA"])
    assert len(nass_land.load_records(out)) == 2


def test_save_replaces_revised_number(tmp_path):
    out = tmp_path / "land.csv"
    a = nass_land.LandRecord("cash_rent_cropland", "IA", "", 2025, 200.0, "$/acre", "u")
    b = nass_land.LandRecord("cash_rent_cropland", "IA", "", 2025, 205.0, "$/acre", "u")
    assert nass_land.save_records([a], out) == 1
    assert nass_land.save_records([b], out) == 0
    assert [r.value for r in nass_land.load_records(out)] == [205.0]


def recs():
    mk = lambda item, st, co, yr, v: nass_land.LandRecord(item, st, co, yr, v, "$/acre", "http://src")
    return [mk("cash_rent_cropland", "IA", "", 2024, 200), mk("cash_rent_cropland", "IA", "", 2025, 210),
            mk("land_value_cropland", "WI", "", 2025, 7000),
            mk("cash_rent_cropland", "IA", "Story", 2025, 250)]


def test_change_text():
    assert rentpage.change_text(210, 200) == "+$10 (+5.0%)"
    assert rentpage.change_text(190, 200) == "-$10 (-5.0%)"
    assert rentpage.change_text(210, None) == "n/a"


def test_page_content():
    page = rentpage.render(recs())
    assert "$210" in page and "+$10 (+5.0%)" in page and "$7,000" in page
    assert "Story" in page and "$250" in page and "http://src" in page
    assert "n/a" in page          # Wisconsin has only one year: no change shown
    assert "Data, not advice" in page and "NASS" in page


def test_page_empty():
    assert "not loaded yet" in rentpage.render([])


def test_site_builds_cash_rent_page(tmp_path):
    land = tmp_path / "land.csv"
    nass_land.save_records(recs(), land)
    out = tmp_path / "site"
    site.build_site(tmp_path / "briefs", out, land_file=land)
    page = (out / "cash-rent.html").read_text()
    assert "$210" in page and 'href="index.html"' in page and "Cash rent" in page
    assert 'cash-rent.html' in (out / "index.html").read_text()


def test_main_returns_0_when_pull_works(monkeypatch):
    monkeypatch.setattr(nass_land, "pull", lambda: [])
    assert nass_land.main() == 0


def test_main_returns_1_and_hides_error_details(monkeypatch, capsys):
    def boom():
        raise RuntimeError("secret-key-123 in url")
    monkeypatch.setattr(nass_land, "pull", boom)
    assert nass_land.main() == 1
    err = capsys.readouterr().err
    assert "RuntimeError" in err and "secret-key-123" not in err


def test_failed_query_message_never_contains_key(tmp_path, capsys):
    def bad(url, params):
        raise ConnectionError(f"failed {params['key']}")
    nass_land.pull(get_json=bad, api_key="SECRETKEY", out=tmp_path / "l.csv", states=["IA"])
    assert "SECRETKEY" not in capsys.readouterr().err
