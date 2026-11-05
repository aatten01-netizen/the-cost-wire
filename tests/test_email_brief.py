"""Tests for the test-email sender. Resend is never called."""

import pytest

from costwire import email_brief


def make(tmp_path, dates=("2026-10-26", "2026-11-02")):
    for d in dates:
        (tmp_path / f"{d}.html").write_text(f"<p>brief {d}</p>")
        (tmp_path / f"{d}.md").write_text(f"brief {d}")
    return tmp_path


def test_latest_date(tmp_path):
    assert email_brief.latest_brief_date(make(tmp_path)) == "2026-11-02"
    assert email_brief.latest_brief_date(tmp_path / "none") is None


def test_message_shape(tmp_path):
    m = email_brief.build_message("2026-11-02", "a@b.com", briefs_dir=make(tmp_path))
    assert m["to"] == ["a@b.com"]
    assert m["subject"].startswith("[TEST]")
    assert "brief 2026-11-02" in m["html"] and m["text"] == "brief 2026-11-02"


def test_sends_latest_with_key(tmp_path):
    calls = []
    post = lambda url, h, p: calls.append((url, h, p)) or {"id": "x"}
    r = email_brief.send(to="a@b.com", api_key="k", post=post, briefs_dir=make(tmp_path))
    assert r == {"id": "x"}
    url, headers, payload = calls[0]
    assert url == email_brief.RESEND_URL and headers["Authorization"] == "Bearer k"
    assert "2026-11-02" in payload["subject"]


def boom(*a):
    raise AssertionError("must not call Resend")


def test_no_key_skips(tmp_path, capsys):
    assert email_brief.send(to="a@b.com", api_key="", post=boom, briefs_dir=make(tmp_path)) is None
    assert "RESEND_API_KEY not set" in capsys.readouterr().out


def test_no_address_skips(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("BRIEF_TEST_EMAIL", raising=False)
    assert email_brief.send(api_key="k", post=boom, briefs_dir=make(tmp_path)) is None
    assert "nothing sent" in capsys.readouterr().out


def test_dry_run_sends_nothing(tmp_path, capsys):
    email_brief.send(to="a@b.com", api_key="k", post=boom, briefs_dir=make(tmp_path), dry_run=True)
    assert "DRY RUN" in capsys.readouterr().out


@pytest.mark.parametrize("to", ["a@b.com,c@d.com", "a@b.com c@d.com", "a@b.com;c@d.com"])
def test_only_one_recipient(tmp_path, to):
    with pytest.raises(ValueError):
        email_brief.send(to=to, api_key="k", post=boom, briefs_dir=make(tmp_path))


def test_no_briefs(tmp_path, capsys):
    assert email_brief.send(to="a@b.com", api_key="k", post=boom, briefs_dir=tmp_path) is None
