from costwire import pricing, site, team

FORM = "https://script.google.com/macros/s/abc/exec"
LIVE = {"SIGNUP_FORM_URL": FORM, "SIGNUP_LIVE": "yes"}
STRIPE = {"TEAM_CHECKOUT_URL": "https://buy.stripe.com/test_team", "TEAM_CHECKOUT_LIVE": "yes"}


def test_price_is_ask_until_andy_sets_one(monkeypatch):
    monkeypatch.setattr(team, "TEAM_MONTHLY", None)
    out = team.render({})
    assert "Price: ask" in out and "$" not in out.split('class="price">')[1].split("<")[0]


def test_checkout_is_mock_without_price_even_if_stripe_set(monkeypatch):
    monkeypatch.setattr(team, "TEAM_MONTHLY", None)
    out = team.render(STRIPE)
    assert "Team is not open yet" in out and "buy.stripe.com" not in out
    assert "(coming soon)" in out


def test_checkout_live_only_with_price_stripe_link_and_flag(monkeypatch):
    monkeypatch.setattr(team, "TEAM_MONTHLY", 49)
    assert not team.checkout_live({"TEAM_CHECKOUT_URL": "https://buy.stripe.com/x"})
    assert not team.checkout_live({"TEAM_CHECKOUT_URL": "https://evil.example/x", "TEAM_CHECKOUT_LIVE": "yes"})
    assert not team.checkout_live({"TEAM_CHECKOUT_URL": "https://buy.stripe.com/", "TEAM_CHECKOUT_LIVE": "yes"})
    out = team.render(STRIPE)
    assert "Start Team, $49/month" in out and "(coming soon)" not in out
    assert "Join the Team waitlist" not in team.render({**LIVE, **STRIPE})


def test_no_form_unless_signup_live():
    for env in ({}, {"SIGNUP_FORM_URL": FORM}, {"SIGNUP_LIVE": "yes"},
                {"SIGNUP_FORM_URL": "http://x.example/exec", "SIGNUP_LIVE": "yes"}):
        assert "Join the Team waitlist" not in team.render(env), env


def test_form_posts_plan_team_role_and_size():
    out = team.render(LIVE)
    assert f'action="{FORM}"' in out
    assert 'name="plan" value="team"' in out
    for v, _ in team.ROLES:
        assert f'<option value="{v}">' in out
    for v, _ in team.SIZES:
        assert f'<option value="{v}">' in out
    assert 'name="website"' in out and "Nothing is charged" in out


def test_form_url_escaped():
    out = team.render({"SIGNUP_FORM_URL": FORM + '"><script>', "SIGNUP_LIVE": "yes"})
    assert "<script>" not in out


def test_data_not_advice_and_no_buy_words():
    out = team.render(LIVE).lower()
    assert "data, not advice" in out
    for bad in ("you should buy", "time to buy", "lock in now", "sell now"):
        assert bad not in out


def test_pricing_links_to_team_and_team_links_back():
    assert 'href="team.html"' in pricing.render({})
    assert 'href="pricing.html"' in team.render({})


def test_team_page_has_nav_disclaimer_and_title():
    page = site.team_page({})
    assert "<title>The Cost Wire — Team plan for ag businesses</title>" in page
    assert 'class="sitenav"' in page and "Data, not advice" in page
    assert page.count("<h1>") == 1


def _rows():
    return [
        {"email": "a@x.com", "plan": "team", "team_role": "lender", "team_size": "11-50"},
        {"email": "A@x.com ", "plan": "team", "team_role": "coop", "team_size": "51+"},  # newer wins
        {"email": "b@x.com", "plan": "team", "team_role": "agronomist", "team_size": "1-10"},
        {"email": "c@x.com", "plan": "", "pro_plan": "monthly"},          # not team
        {"email": "d@x.com", "plan": "team", "team_role": "hacker", "team_size": "9999"},  # bad values
        {"email": "bad", "plan": "team", "team_role": "lender", "team_size": "1-10"},     # bad email
    ]


def test_parse_and_tally_counts_only():
    a = team.parse(_rows())
    assert a == {
        "a@x.com": {"role": "coop", "size": "51+"},
        "b@x.com": {"role": "agronomist", "size": "1-10"},
        "d@x.com": {"role": "", "size": ""},
    }
    t = team.tally(a)
    assert t["total"] == 3
    out = team.report(t)
    assert "Team waitlist: 3" in out and "Co-op or ag retailer 1" in out and "not given 1" in out
    assert "@" not in out


def test_main_reads_csv(tmp_path, capsys):
    f = tmp_path / "s.csv"
    f.write_text("time,email,plan,team_role,team_size\n1,a@x.com,team,lender,1-10\n", encoding="utf-8")
    assert team.main([str(f)]) == 0
    out = capsys.readouterr().out
    assert "Team waitlist: 1" in out and "a@x.com" not in out
    assert team.main([]) == 2
    assert team.main([str(tmp_path / "missing.csv")]) == 1
