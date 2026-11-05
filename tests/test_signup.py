from costwire import site


def test_placeholder_by_default():
    assert site.signup_box({}) == site.SIGNUP_BOX


def test_url_without_go_ahead_stays_placeholder():
    assert site.signup_box({"SIGNUP_FORM_URL": "https://script.google.com/x"}) == site.SIGNUP_BOX


def test_go_ahead_without_url_stays_placeholder():
    assert site.signup_box({"SIGNUP_LIVE": "yes"}) == site.SIGNUP_BOX


def test_non_https_url_refused():
    env = {"SIGNUP_FORM_URL": "http://example.com/x", "SIGNUP_LIVE": "yes"}
    assert site.signup_box(env) == site.SIGNUP_BOX


def test_live_form():
    env = {"SIGNUP_FORM_URL": "https://script.google.com/macros/s/ABC/exec?a=1&b=2", "SIGNUP_LIVE": "YES"}
    box = site.signup_box(env)
    assert 'method="post"' in box and 'type="email"' in box and "disabled" not in box
    assert 'action="https://script.google.com/macros/s/ABC/exec?a=1&amp;b=2"' in box
    assert 'name="website"' in box  # honeypot for bots


def test_built_site_uses_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGNUP_FORM_URL", "https://example.com/hook")
    monkeypatch.setenv("SIGNUP_LIVE", "yes")
    site.build_site(briefs_dir=tmp_path / "none", site_dir=tmp_path / "site",
                    land_file=tmp_path / "land.csv")
    assert 'action="https://example.com/hook"' in (tmp_path / "site" / "index.html").read_text()
