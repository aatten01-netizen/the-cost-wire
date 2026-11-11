"""Tests for the NASS corn price puller and the bushels-of-corn-per-ton line. No network."""

from datetime import date

from costwire import accuracy, affordability, brief, changes, corn_price, weekly
from costwire.corn_price import CornPrice

AMS = "https://www.ams.usda.gov/mnreports/ams_2863.pdf"
NASS_IA = "https://quickstats.nass.usda.gov/api/api_GET/?state_alpha=IA"
NASS_IL = "https://quickstats.nass.usda.gov/api/api_GET/?state_alpha=IL"


def nass_row(value, year, month="SEP", state="IA"):
    return {"short_desc": corn_price.SHORT_DESC, "Value": value, "year": str(year),
            "state_alpha": state, "agg_level_desc": "STATE", "reference_period_desc": month}


def fert(item, region, price, as_of):
    return {"item": item, "region": region, "unit": "$/ton", "price": price, "as_of": as_of,
            "source_name": "USDA AMS Iowa Production Cost Report", "source_url": AMS}


# ---------- corn price puller ----------

def test_parse_response_keeps_months_skips_the_rest():
    payload = {"data": [
        nass_row("4.17", 2026, "SEP"),
        nass_row("(D)", 2026, "AUG"),                 # withheld
        nass_row("4.50", 2026, "MARKETING YEAR"),     # not a month
        nass_row("4.00", "bad", "JUL"),               # bad year
        {**nass_row("9", 2026), "short_desc": "SOYBEANS - PRICE RECEIVED"},
        nass_row("4.30", 2025, "SEP", state="IL"),
    ]}
    got = corn_price.parse_response(payload, "https://x")
    assert [(p.state, p.year, p.month, p.value) for p in got] == [
        ("IA", 2026, 9, 4.17), ("IL", 2025, 9, 4.30)]
    assert all(p.unit == "$/bu" and p.source_url == "https://x" for p in got)


def test_source_url_has_no_key():
    url = corn_price.source_url(corn_price.query_params("IA", 2024))
    assert "key" not in url and "state_alpha=IA" in url and "MONTHLY" in url


def test_no_key_skips_cleanly(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("NASS_API_KEY", raising=False)
    out = tmp_path / "corn.csv"
    def boom(url, params):
        raise AssertionError("must not call NASS without a key")
    assert corn_price.pull(get_json=boom, out=out) == []
    assert not out.exists()
    assert "NASS_API_KEY not set" in capsys.readouterr().out
    assert corn_price.main() == 0


def test_pull_saves_replaces_revisions_and_hides_key(tmp_path, capsys):
    out = tmp_path / "corn.csv"
    value = {"v": "4.10"}
    def get_json(url, params):
        if params["state_alpha"] == "IL":
            raise RuntimeError("boom " + params["key"])
        assert params["year__GE"] == 2024
        return {"data": [nass_row(value["v"], 2026), nass_row("4.60", 2025)]}
    got = corn_price.pull(get_json=get_json, api_key="SECRET", today=date(2026, 11, 11), out=out)
    assert len(got) == 2
    assert "SECRET" not in capsys.readouterr().err and "SECRET" not in out.read_text()
    value["v"] = "4.17"  # NASS revised the preliminary number
    corn_price.pull(get_json=get_json, api_key="SECRET", today=date(2026, 11, 11), out=out)
    saved = {p.key: p.value for p in corn_price.load_prices(out)}
    assert saved == {("IA", 2025, 9): 4.6, ("IA", 2026, 9): 4.17}


# ---------- the math ----------

CORN = [CornPrice("IA", 2026, 9, 4.17, NASS_IA), CornPrice("IA", 2025, 9, 3.80, NASS_IA),
        CornPrice("IL", 2026, 4, 4.40, NASS_IL)]


def test_pick_corn_newest_month_not_after_and_not_too_old():
    more = CORN + [CornPrice("IA", 2026, 10, 4.20, NASS_IA)]
    assert affordability.pick_corn(more, "IA", date(2026, 10, 30)).month == 10
    assert affordability.pick_corn(more, "IA", date(2026, 9, 30)).month == 9
    # Illinois only has April: 6 months before Oct 30 is too old
    assert affordability.pick_corn(more, "IL", date(2026, 10, 30)) is None
    assert affordability.pick_corn(more, "IL", date(2026, 7, 2)).month == 4
    assert affordability.pick_corn(more, "WI", date(2026, 10, 30)) is None


def test_compute_now_and_year_ago():
    rows = [fert("anhydrous", "IA", 902.33, date(2026, 10, 2)),
            fert("anhydrous", "IA", 760.00, date(2025, 10, 3))]
    [a] = affordability.compute(changes.compute(rows), CORN)
    assert a["corn"].month == 9 and a["bushels"] == round(902.33 / 4.17, 1) == 216.4
    assert a["bushels_1y"] == round(760 / 3.80, 1) == 200.0
    assert a["change_1y"] == 16.4


def test_compute_leaves_out_missing_numbers():
    rows = [fert("anhydrous", "IL", 981.11, date(2026, 10, 30)),   # no recent IL corn
            fert("potash", "IA", 499.80, date(2026, 10, 30)),      # not in the list
            fert("urea", "IA", 770.00, date(2026, 10, 30))]        # no year-ago fert price
    out = affordability.compute(changes.compute(rows), CORN)
    assert [(a["item"], a["region"]) for a in out] == [("urea", "IA")]
    assert out[0]["bushels_1y"] is None and out[0]["change_1y"] is None
    assert affordability.compute(changes.compute(rows), []) == []


# ---------- the brief + accuracy check ----------

def two_years():
    rows = [fert("anhydrous", "IA", 902.33, date(2026, 10, 2)),
            fert("anhydrous", "IA", 760.00, date(2025, 10, 3)),
            fert("urea", "IA", 770.00, date(2026, 10, 2))]
    return changes.compute(rows)


def test_brief_has_bushels_section_sources_and_credit():
    b = brief.build(two_years(), date(2026, 11, 9), CORN)
    md, page = brief.to_markdown(b), brief.to_html(b)
    assert "## Bushels of corn to buy 1 ton" in md
    assert ("- Iowa anhydrous ammonia: 216.4 bushels of corn per ton ($902.33/ton as of "
            "Oct 2, 2026 ÷ $4.17/bu Iowa corn price received, Sep 2026); 16.4 more bushels "
            "than 1 year earlier: 200.0 bushels ($760.00/ton as of Oct 3, 2025 ÷ $3.80/bu, "
            "Sep 2025).") in md
    assert "- Iowa urea: 184.7 bushels" in md and "Iowa urea: 184.7 bushels of corn per ton (" in md
    sources = md.split("## Sources", 1)[1]
    assert NASS_IA in sources and "Iowa corn price received, Sep 2025, Sep 2026" in sources
    assert "National Agricultural Statistics Service (NASS)" in b["credit"]
    assert "Bushels of corn to buy 1 ton" in page and NASS_IA in page
    for word in ("buy now", "sell", "should", "cheap", "good time"):
        assert word not in " ".join(b["afford"]).lower()


def test_brief_without_corn_has_no_section():
    b = brief.build(two_years(), date(2026, 11, 9), [])
    md = brief.to_markdown(b)
    assert "Bushels of corn" not in md and "NASS" not in md
    assert "Bushels of corn" not in brief.to_html(b)


def test_accuracy_passes_and_catches_a_changed_bushels_number():
    results = two_years()
    md = brief.to_markdown(brief.build(results, date(2026, 11, 9), CORN))
    assert accuracy.check_afford(md, results, CORN) == []
    bad = md.replace("216.4 bushels", "199.0 bushels")
    problems = accuracy.check_afford(bad, results, CORN)
    assert any("not in the saved data" in p for p in problems)
    assert any("missing from the brief" in p for p in problems)
    no_src = md.replace(f"- [USDA National Agricultural Statistics Service (NASS)]({NASS_IA})", "-")
    assert any("not listed in the Sources" in p for p in accuracy.check_afford(no_src, results, CORN))


def test_accuracy_flags_bad_corn_rows():
    bad = [CornPrice("IA", 2026, 9, 4.17, "http://insecure"), CornPrice("IA", 2026, 8, 0.0, NASS_IA)]
    problems = accuracy.check_corn_data(bad)
    assert len(problems) == 2


def test_write_brief_uses_saved_corn_file(tmp_path):
    data = tmp_path / "fert.csv"
    data.write_text("item,price,unit,as_of,source_name,source_url,region\n"
                    f"urea,770.0,$/ton,2026-10-02,USDA AMS Iowa Production Cost Report,{AMS},IA\n")
    corn = tmp_path / "corn.csv"
    corn_price.save_prices(CORN, corn)
    md_path, _ = brief.write_brief(date(2026, 11, 9), data, tmp_path / "b", corn)
    assert "Iowa urea: 184.7 bushels" in md_path.read_text()
    assert accuracy.run_checks(md_path, data, date(2026, 11, 9), corn) == []


def test_weekly_runs_corn_step_and_survives_its_failure():
    calls = []
    def step(name, code=0):
        return lambda: (calls.append(name), code)[1]
    steps = {"pull": step("pull"), "land": step("land"), "corn": step("corn", 1),
             "changes": step("changes"), "brief": step("brief"), "site": step("site")}
    assert weekly.run(date(2026, 11, 9), steps) == 0
    assert calls == ["pull", "land", "corn", "changes", "brief", "site"]
