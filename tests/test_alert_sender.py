"""Step 19: real alert sender (Resend), test address only. Resend is never called."""

import pytest

from costwire import alerts
from test_alerts import ROWS, subs_file


def fake_post(calls):
    return lambda url, headers, payload: calls.append((url, headers, payload)) or {"id": "x"}


def boom(*a):
    raise AssertionError("must not call Resend")


LIVE = {"ALERTS_LIVE": "yes", "RESEND_API_KEY": "k", "BRIEF_TEST_EMAIL": "andy@test.com"}


def test_off_by_default_uses_mock():
    assert isinstance(alerts.pick_sender({}, post=boom), alerts.MockSender)
    assert isinstance(alerts.pick_sender({**LIVE, "ALERTS_LIVE": "no"}, post=boom), alerts.MockSender)


@pytest.mark.parametrize("missing", ["RESEND_API_KEY", "BRIEF_TEST_EMAIL"])
def test_live_without_key_or_address_falls_back_to_mock(missing):
    env = {**LIVE, missing: ""}
    assert isinstance(alerts.pick_sender(env, post=boom), alerts.MockSender)


def test_live_sends_only_to_test_address(tmp_path):
    calls = []
    sender = alerts.pick_sender(LIVE, post=fake_post(calls))
    assert isinstance(sender, alerts.ResendSender)
    p = subs_file(tmp_path, ["reader@farm.com,anhydrous,IA,25"])
    n = alerts.run(p, tmp_path / "sent.csv", ROWS, sender)
    assert n == 1 and len(calls) == 1
    url, headers, payload = calls[0]
    assert url == "https://api.resend.com/emails" and headers["Authorization"] == "Bearer k"
    assert payload["to"] == ["andy@test.com"]
    assert "reader@farm.com" not in payload["to"]
    assert payload["subject"].startswith("[TEST for reader@farm.com]")
    assert "NOT emailed" in payload["text"] and "Data, not advice" in payload["text"]


@pytest.mark.parametrize("bad", ["a@b.com,c@d.com", "a@b.com c@d.com", "a@b.com;c@d.com", "nope"])
def test_test_address_must_be_one_address(bad):
    with pytest.raises(ValueError):
        alerts.ResendSender("k", bad, post=boom)


def test_send_limit_per_run(tmp_path):
    calls = []
    sender = alerts.ResendSender("k", "andy@test.com", post=fake_post(calls), max_sends=2)
    lines = [f"r{i}@farm.com,anhydrous,IA,25" for i in range(5)]
    with pytest.raises(RuntimeError):
        alerts.run(subs_file(tmp_path, lines), tmp_path / "sent.csv", ROWS, sender)
    assert len(calls) == 2
    # only the 2 that really went out are remembered, so the rest can go next run
    assert len((tmp_path / "sent.csv").read_text().strip().splitlines()) == 1 + 2


def test_failed_send_is_not_marked_sent(tmp_path):
    def fail(*a):
        raise ConnectionError("down")
    sender = alerts.ResendSender("k", "andy@test.com", post=fail)
    with pytest.raises(ConnectionError):
        alerts.run(subs_file(tmp_path, ["reader@farm.com,anhydrous,IA,25"]),
                   tmp_path / "sent.csv", ROWS, sender)
    assert not (tmp_path / "sent.csv").exists()


def test_main_live_without_key_does_not_mark_real_sent_file(tmp_path, monkeypatch):
    p = subs_file(tmp_path, ["reader@farm.com,anhydrous,IA,25"])
    monkeypatch.setenv("ALERTS_FILE", str(p))
    monkeypatch.setenv("ALERTS_LIVE", "yes")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("ALERTS_SENT_FILE", raising=False)
    monkeypatch.setattr(alerts.changes, "read_rows", lambda: ROWS)
    assert alerts.main() == 0
    assert not (tmp_path / "alerts_sent.csv").exists()
    assert (tmp_path / "alerts_sent_mock.csv").exists()
