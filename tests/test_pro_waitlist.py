from costwire import pricing, pro_waitlist, site

FORM = "https://script.google.com/macros/s/abc/exec"
LIVE = {"SIGNUP_FORM_URL": FORM, "SIGNUP_LIVE": "yes"}
STRIPE = {"PRO_CHECKOUT_URL": "https://buy.stripe.com/test_abc", "PRO_CHECKOUT_LIVE": "yes"}


def test_no_form_unless_signup_live():
    for env in ({}, {"SIGNUP_FORM_URL": FORM}, {"SIGNUP_LIVE": "yes"},
                {"SIGNUP_FORM_URL": "http://x.example/exec", "SIGNUP_LIVE": "yes"}):
        assert pro_waitlist.render(env) == "", env
        assert "Join the Pro waitlist" not in pricing.render(env)


def test_form_shown_when_signup_live_and_checkout_not():
    out = pricing.render(LIVE)
    assert "Join the Pro waitlist" in out and f'action="{FORM}"' in out
    for v in ("monthly", "yearly", "maybe"):
        assert f'name="pro_plan" value="{v}"' in out
    assert f"Yes, ${pricing.PRO_MONTHLY}/month" in out and f"Yes, ${pricing.PRO_YEARLY}/year" in out
    assert 'name="website"' in out and "Nothing is charged" in out
    assert "Pro is not open yet" in out  # checkout stays a mock


def test_form_hidden_once_checkout_live():
    out = pricing.render({**LIVE, **STRIPE})
    assert "Join the Pro waitlist" not in out and "buy.stripe.com" in out


def test_form_url_escaped():
    out = pro_waitlist.render({"SIGNUP_FORM_URL": FORM + '"><script>', "SIGNUP_LIVE": "yes"})
    assert "<script>" not in out


def _rows():
    return [
        {"email": "a@x.com", "state": "IA", "pro_plan": "maybe"},
        {"email": "A@x.com ", "state": "", "pro_plan": "monthly"},   # newer answer wins, keeps IA
        {"email": "b@x.com", "state": "IL", "pro_plan": "yearly"},
        {"email": "b@x.com", "state": "", "pro_plan": ""},            # plain signup doesn't wipe it
        {"email": "c@x.com", "state": "MN", "pro_plan": "maybe"},
        {"email": "d@x.com", "state": "", "pro_plan": "monthly"},
        {"email": "e@x.com", "state": "IA", "pro_plan": ""},           # signup only: not counted
        {"email": "bad", "state": "IA", "pro_plan": "monthly"},        # bad email skipped
        {"email": "f@x.com", "state": "IA", "pro_plan": "free!!"},     # unknown answer ignored
    ]


def test_parse_newest_answer_wins_and_keeps_state():
    a = pro_waitlist.parse(_rows())
    assert a == {
        "a@x.com": {"plan": "monthly", "state": "IA"},
        "b@x.com": {"plan": "yearly", "state": "IL"},
        "c@x.com": {"plan": "maybe", "state": "MN"},
        "d@x.com": {"plan": "monthly", "state": ""},
    }


def test_tally_counts_only_clear_yes():
    t = pro_waitlist.tally(pro_waitlist.parse(_rows()))
    assert (t["monthly"], t["yearly"], t["maybe"], t["yes"]) == (2, 1, 1, 3)
    assert t["yes_by_state"] == {"IA": 1, "IL": 1, "": 1}


def test_report_has_numbers_not_emails():
    out = pro_waitlist.report(pro_waitlist.tally(pro_waitlist.parse(_rows())))
    assert "3 clear yes (goal 5)" in out and "2 more clear yes needed" in out
    assert "Iowa 1" in out and "Illinois 1" in out and "no state 1" in out
    assert "@" not in out


def test_report_goal_met():
    rows = [{"email": f"r{i}@x.com", "pro_plan": "monthly"} for i in range(5)]
    out = pro_waitlist.report(pro_waitlist.tally(pro_waitlist.parse(rows)))
    assert "Goal met" in out and "none yet" not in out


def test_cli_reads_old_sheet_without_column(tmp_path, capsys):
    f = tmp_path / "s.csv"
    f.write_text("time,email,state\n1,a@x.com,IA\n", encoding="utf-8")
    assert pro_waitlist.main([str(f)]) == 0
    out = capsys.readouterr().out
    assert "0 clear yes" in out and "@" not in out
    assert pro_waitlist.main([]) == 2
    assert pro_waitlist.main([str(tmp_path / "missing.csv")]) == 1


def test_site_pricing_page_gets_form_and_css(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGNUP_FORM_URL", FORM)
    monkeypatch.setenv("SIGNUP_LIVE", "yes")
    monkeypatch.delenv("PRO_CHECKOUT_LIVE", raising=False)
    page = site.pricing_page()
    assert "Join the Pro waitlist" in page and ".waitlist" in page and "Data, not advice" in page
