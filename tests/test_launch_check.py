from costwire import launch_check

HEADER = "item,price,unit,as_of,source_name,source_url,region\n"


def names(checks, ok):
    return {n for n, o, _ in checks if o == ok}


def test_empty_project_is_not_ready(tmp_path):
    checks = launch_check.run_checks(tmp_path / "d", tmp_path / "b", tmp_path / "s", env={})
    assert not any(ok for _, ok, _ in checks)
    assert all(todo for _, _, todo in checks)  # every miss says what to do


def test_prices_and_site_detected(tmp_path):
    d, s = tmp_path / "d", tmp_path / "s"
    d.mkdir(); s.mkdir()
    (d / "fertilizer.csv").write_text(
        HEADER
        + "anhydrous,900,$/ton,2026-10-30,Iowa,https://www.ams.usda.gov/mnreports/ams_2863.pdf,IA\n"
        + "ddgs,200,$/ton,2026-10-30,Grain,https://www.ams.usda.gov/mnreports/ams_3618.pdf,IA\n")
    for p in ("index.html", "archive.html", "cash-rent.html"):
        (s / p).write_text("x")
    ok = names(launch_check.run_checks(d, tmp_path / "b", s, env={}), True)
    assert "Fertilizer prices saved (Iowa)" in ok
    assert "Feed line (DDGS) has real prices" in ok
    assert "Website built (home, archive, cash rent)" in ok
    assert "Fertilizer prices saved (Illinois)" not in ok


def test_signup_needs_https_and_go_ahead(tmp_path):
    def signup_ok(env):
        c = launch_check.run_checks(tmp_path, tmp_path, tmp_path, env=env)
        return dict((n, o) for n, o, _ in c)["Signup form is live (SIGNUP_FORM_URL + SIGNUP_LIVE=yes)"]
    assert not signup_ok({"SIGNUP_FORM_URL": "https://x.com/a"})
    assert not signup_ok({"SIGNUP_FORM_URL": "http://x.com/a", "SIGNUP_LIVE": "yes"})
    assert signup_ok({"SIGNUP_FORM_URL": "https://x.com/a", "SIGNUP_LIVE": "yes"})


def test_strict_exit_code(monkeypatch):
    monkeypatch.setattr(launch_check, "run_checks", lambda: [("a", False, "do it")])
    assert launch_check.main(["--strict"]) == 1
    assert launch_check.main([]) == 0
