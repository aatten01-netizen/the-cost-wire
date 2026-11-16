from datetime import date

import pytest

from costwire import brief, state_email

IA_SRC = ("USDA AMS Iowa Production Cost Report", "https://www.ams.usda.gov/mnreports/ams_2863.pdf")
IL_SRC = ("USDA AMS Illinois Production Cost Report", "https://www.ams.usda.gov/mnreports/ams_3195.pdf")
EIA_SRC = ("EIA Midwest (PADD 2) on-highway diesel", "https://www.eia.gov/petroleum/gasdiesel/")


def row(item, price, d, region, src, unit="$/ton"):
    return {"item": item, "price": price, "unit": unit, "as_of": date.fromisoformat(d),
            "source_name": src[0], "source_url": src[1], "region": region}


ROWS = [
    row("anhydrous", 880.00, "2026-10-16", "IA", IA_SRC),
    row("anhydrous", 902.33, "2026-10-30", "IA", IA_SRC),
    row("urea", 770.00, "2026-10-30", "IL", IL_SRC),
    row("onhwy_diesel", 4.10, "2026-11-02", "PADD2", EIA_SRC, unit="$/gal"),
]
D = date(2026, 11, 9)
LIVE = {"STATE_EMAIL_LIVE": "yes", "RESEND_API_KEY": "re_fake", "BRIEF_TEST_EMAIL": "andy@test.com"}


@pytest.fixture
def briefs(tmp_path):
    (tmp_path / "2026-11-09.html").write_text("<html>MAIN BRIEF</html>", encoding="utf-8")
    (tmp_path / "2026-11-09.md").write_text("# MAIN BRIEF", encoding="utf-8")
    return tmp_path


@pytest.fixture
def editions(briefs):
    return state_email.build_editions(ROWS, D, [], briefs_dir=briefs)


READERS = [
    {"email": "a@farm.com", "state": "IA"},
    {"email": "b@farm.com", "state": "IA"},
    {"email": "c@farm.com", "state": "MN"},  # MN has no prices in ROWS -> main brief
    {"email": "d@farm.com", "state": ""},
    {"email": "e@farm.com", "state": "IL"},
]


def test_load_readers_cleans_and_dedupes(tmp_path):
    p = tmp_path / "readers.csv"
    p.write_text("email,state\nA@Farm.com,ia\nbad,IL\nx@farm.com,NE\na@farm.com,IL\n", encoding="utf-8")
    assert state_email.load_readers(p) == [
        {"email": "x@farm.com", "state": ""},
        {"email": "a@farm.com", "state": "IL"},  # last row wins
    ]


def test_editions_only_for_states_with_prices(editions):
    assert set(editions) == {"", "IA", "IL"}
    assert editions["IA"]["title"] == "The Cost Wire — Iowa edition"
    assert "Illinois" not in editions["IA"]["text"] and brief.DISCLAIMER in editions["IA"]["text"]
    assert editions["IA"]["web"].endswith("/state/ia.html")
    assert editions[""]["html"] == "<html>MAIN BRIEF</html>"


def test_plan_groups_and_falls_back_to_main(editions):
    assert state_email.plan(READERS, editions) == [("IA", 2), ("IL", 1), ("", 2)]


def test_dry_run_by_default_sends_nothing(editions):
    calls = []
    out = state_email.run(READERS, editions, D, env={"RESEND_API_KEY": "re_fake",
                                                    "BRIEF_TEST_EMAIL": "andy@test.com"},
                          post=lambda *a: calls.append(a))
    assert calls == [] and out["sent"] == [] and out["live"] is False


def test_live_without_key_stays_dry(editions):
    calls = []
    out = state_email.run(READERS, editions, D, env={"STATE_EMAIL_LIVE": "yes"},
                          post=lambda *a: calls.append(a))
    assert calls == [] and out["live"] is False


def test_live_sends_one_per_edition_to_test_address_only(editions):
    calls = []
    out = state_email.run(READERS, editions, D, env=LIVE, post=lambda *a: calls.append(a))
    assert len(calls) == 3
    for url, headers, payload in calls:
        assert url == state_email.RESEND_URL
        assert payload["to"] == ["andy@test.com"]  # never a reader
        body = payload["html"] + payload["text"] + payload["subject"]
        assert "@farm.com" not in body  # reader emails never appear
        assert "none of them were emailed" in payload["text"]
    assert out["sent"][0] == "[TEST x2] The Cost Wire — Iowa edition — week of 2026-11-09"
    assert out["sent"][2].startswith("[TEST x2] The Cost Wire — week of")


def test_test_address_must_be_one_address(editions):
    env = dict(LIVE, BRIEF_TEST_EMAIL="a@x.com,b@x.com")
    with pytest.raises(ValueError):
        state_email.run(READERS, editions, D, env=env, post=lambda *a: None)


def test_missing_main_brief_is_an_error_when_needed(tmp_path):
    eds = state_email.build_editions(ROWS, D, [], briefs_dir=tmp_path)  # no briefs saved
    assert "" not in eds
    with pytest.raises(ValueError):
        state_email.run([{"email": "d@farm.com", "state": ""}], eds, D, env={})
    # Only state readers: fine without the main brief.
    assert state_email.run([{"email": "a@farm.com", "state": "IA"}], eds, D, env={})["plan"] == [("IA", 1)]


def test_main_without_readers_file_does_nothing(monkeypatch, capsys):
    monkeypatch.delenv("READERS_FILE", raising=False)
    assert state_email.main() == 0
    assert "nothing to do" in capsys.readouterr().out
