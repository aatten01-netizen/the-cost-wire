from costwire import pricing, site

STRIPE = "https://buy.stripe.com/test_abc123"


def test_mock_checkout_by_default():
    out = pricing.render({})
    assert "Pro is not open yet" in out and "disabled" in out
    assert "buy.stripe.com" not in out


def test_live_needs_both_link_and_go_ahead():
    assert not pricing.checkout_live({"PRO_CHECKOUT_URL": STRIPE})
    assert not pricing.checkout_live({"PRO_CHECKOUT_LIVE": "yes"})
    assert pricing.checkout_live({"PRO_CHECKOUT_URL": STRIPE, "PRO_CHECKOUT_LIVE": "YES "})


def test_live_rejects_non_stripe_or_http_links():
    for url in ("http://buy.stripe.com/abc", "https://evil.example/pay",
                "https://buy.stripe.com/", "javascript:alert(1)"):
        assert not pricing.checkout_live({"PRO_CHECKOUT_URL": url, "PRO_CHECKOUT_LIVE": "yes"}), url


def test_live_button_links_to_checkout():
    out = pricing.render({"PRO_CHECKOUT_URL": STRIPE, "PRO_CHECKOUT_LIVE": "yes"})
    assert f'href="{STRIPE}"' in out and "Pro is not open yet" not in out
    assert f"${pricing.PRO_MONTHLY}/month" in out


def test_link_is_escaped():
    url = STRIPE + '"><script>'
    out = pricing.render({"PRO_CHECKOUT_URL": url, "PRO_CHECKOUT_LIVE": "yes"})
    assert "<script>" not in out


def test_prices_and_disclaimer_shown():
    out = pricing.render({})
    assert f"${pricing.PRO_MONTHLY}/month or ${pricing.PRO_YEARLY}/year" in out
    assert "$0" in out and "Data, not advice" in out


def test_no_advice_or_hype_wording():
    text = pricing.render({}).lower()
    for bad in ("buy now", "sell now", "you should buy", "guaranteed", "save money", "customers love"):
        assert bad not in text, bad


def test_site_builds_pricing_page_and_nav_links_it(tmp_path):
    d = tmp_path / "briefs"
    d.mkdir()
    (d / "2026-11-02.html").write_text(
        "<!doctype html><html><head><style>\n</style></head><body>\n<h1>B</h1>\n</body></html>", encoding="utf-8")
    out = tmp_path / "site"
    site.build_site(d, out)
    page = (out / "pricing.html").read_text(encoding="utf-8")
    assert "<title>The Cost Wire — pricing</title>" in page
    assert '<nav class="sitenav">' in page and "Data, not advice" in page
    assert 'href="index.html#signup"' in page
    assert 'id="signup"' in (out / "index.html").read_text(encoding="utf-8")
    for p in ("index.html", "archive.html", "cash-rent.html", "briefs/2026-11-02.html"):
        assert "pricing.html" in (out / p).read_text(encoding="utf-8"), p
