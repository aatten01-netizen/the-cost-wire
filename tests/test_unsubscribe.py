"""Step 24: unsubscribe link, mailing address and unsubscribe list. Resend is never called."""

import pytest

from costwire import alerts, email_brief, launch_check, state_email, unsubscribe
from test_alerts import ROWS, subs_file
from test_state_email import D, LIVE as STATE_LIVE, READERS, briefs, editions  # noqa: F401

SET = {"UNSUBSCRIBE_URL": "https://forms.example.com/unsub",
       "MAIL_POSTAL_ADDRESS": "PO Box 1,\n  Ames, IA 50010"}


def test_footer_with_settings():
    t = unsubscribe.footer_text(SET)
    assert "Unsubscribe: https://forms.example.com/unsub" in t
    assert "The Cost Wire, PO Box 1, Ames, IA 50010" in t
    h = unsubscribe.footer_html(SET)
    assert '<a href="https://forms.example.com/unsub">Unsubscribe</a>' in h
    assert unsubscribe.headers(SET) == {"List-Unsubscribe": "<https://forms.example.com/unsub>"}
    assert unsubscribe.ready(SET)


def test_missing_settings_are_flagged_not_guessed():
    t = unsubscribe.footer_text({})
    assert unsubscribe.MISSING_LINK in t and unsubscribe.MISSING_ADDRESS in t
    assert unsubscribe.headers({}) == {} and not unsubscribe.ready({})
    assert not unsubscribe.ready({**SET, "MAIL_POSTAL_ADDRESS": " "})


@pytest.mark.parametrize("url,ok", [
    ("https://x.com/u", True), ("mailto:andy@x.com?subject=unsubscribe", True),
    ("http://x.com/u", False), ("javascript:alert(1)", False), ("mailto:", False), ("", False)])
def test_only_https_or_mailto_links(url, ok):
    assert bool(unsubscribe.unsubscribe_url({"UNSUBSCRIBE_URL": url})) is ok


def test_html_footer_is_escaped():
    h = unsubscribe.footer_html({"UNSUBSCRIBE_URL": 'https://x.com/"><b>',
                                 "MAIL_POSTAL_ADDRESS": "<script>"})
    assert "<script>" not in h and '"><b>' not in h


def test_footer_goes_before_body_end():
    out = unsubscribe.add_footer_html("<html><body><p>hi</p></body></html>", SET)
    assert out.index("Unsubscribe") < out.index("</body>")
    assert "Unsubscribe" in unsubscribe.add_footer_html("<p>no body tag</p>", SET)


def test_load_and_drop(tmp_path):
    f = tmp_path / "unsubs.csv"
    f.write_text("email\nB@Farm.com \nnot-an-email\nc@farm.com\n", encoding="utf-8")
    gone = unsubscribe.load(f)
    assert gone == {"b@farm.com", "c@farm.com"}
    kept = unsubscribe.drop([{"email": "a@farm.com"}, {"email": "b@farm.com"}], gone)
    assert kept == [{"email": "a@farm.com"}]
    assert unsubscribe.load(tmp_path / "missing.csv") == set() and unsubscribe.load("") == set()


def test_brief_email_has_footer_and_header(tmp_path):
    (tmp_path / "2026-11-02.html").write_text("<html><body>brief</body></html>")
    (tmp_path / "2026-11-02.md").write_text("brief")
    m = email_brief.build_message("2026-11-02", "a@b.com", briefs_dir=tmp_path, env=SET)
    assert "forms.example.com/unsub" in m["html"] and "PO Box 1" in m["html"]
    assert "Unsubscribe: https://forms.example.com/unsub" in m["text"]
    assert m["headers"]["List-Unsubscribe"] == "<https://forms.example.com/unsub>"
    assert "headers" not in email_brief.build_message("2026-11-02", "a@b.com",
                                                      briefs_dir=tmp_path, env={})


def test_state_edition_email_has_footer(editions):  # noqa: F811
    calls = []
    post = lambda url, h, p: calls.append(p)
    state_email.run(READERS, editions, D, env={**STATE_LIVE, **SET}, post=post)
    assert calls
    for p in calls:
        assert "Unsubscribe: https://forms.example.com/unsub" in p["text"]
        assert "PO Box 1" in p["html"] and p["to"] == ["andy@test.com"]
        assert "List-Unsubscribe" in p["headers"]


def test_alert_skips_unsubscribed_reader_and_has_footer(tmp_path):
    calls = []
    env = {"ALERTS_LIVE": "yes", "RESEND_API_KEY": "k", "BRIEF_TEST_EMAIL": "andy@test.com", **SET}
    sender = alerts.pick_sender(env, post=lambda u, h, p: calls.append(p))
    p = subs_file(tmp_path, ["keep@farm.com,anhydrous,IA,25", "gone@farm.com,anhydrous,IA,25"])
    n = alerts.run(p, tmp_path / "sent.csv", ROWS, sender, unsubscribed={"gone@farm.com"})
    assert n == 1 and len(calls) == 1
    assert "keep@farm.com" in calls[0]["subject"] and "gone@farm.com" not in calls[0]["text"]
    assert "Unsubscribe: https://forms.example.com/unsub" in calls[0]["text"]
    assert "gone@farm.com" not in (tmp_path / "sent.csv").read_text()


def test_state_email_main_drops_unsubscribed(tmp_path, monkeypatch, capsys):
    readers = tmp_path / "readers.csv"
    readers.write_text("email,state\na@farm.com,IA\nb@farm.com,IA\n", encoding="utf-8")
    unsubs = tmp_path / "unsubs.csv"
    unsubs.write_text("email\nb@farm.com\n", encoding="utf-8")
    seen = {}
    monkeypatch.setattr(state_email, "run",
                        lambda r, e, d: seen.setdefault("r", r) and {"plan": [], "sent": [], "live": False})
    monkeypatch.setattr(state_email, "build_editions", lambda *a, **k: {})
    monkeypatch.setenv("READERS_FILE", str(readers))
    monkeypatch.setenv("UNSUBSCRIBES_FILE", str(unsubs))
    assert state_email.main() == 0
    assert [r["email"] for r in seen["r"]] == ["a@farm.com"]


def test_launch_check_flags_missing_unsubscribe(tmp_path):
    name = "Unsubscribe link + mailing address set (UNSUBSCRIBE_URL + MAIL_POSTAL_ADDRESS)"
    off = dict((n, ok) for n, ok, _ in launch_check.run_checks(tmp_path, tmp_path, tmp_path, env={}))
    on = dict((n, ok) for n, ok, _ in launch_check.run_checks(tmp_path, tmp_path, tmp_path, env=SET))
    assert off[name] is False and on[name] is True
