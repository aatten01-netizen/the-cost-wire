from datetime import date

from costwire import brief, site

PAGE = "<!doctype html><html><head><style>\nbody{}\n</style></head><body>\n<h1>Brief</h1>\n</body></html>"


def make_briefs(tmp_path, names):
    d = tmp_path / "briefs"
    d.mkdir()
    for n in names:
        (d / n).write_text(PAGE.replace("Brief", n), encoding="utf-8")
    return d


def test_brief_files_newest_first_and_skips_junk(tmp_path):
    d = make_briefs(tmp_path, ["2026-10-26.html", "2026-11-02.html", "notes.html", "2026-13-45.html"])
    assert [x for x, _ in site.brief_files(d)] == [date(2026, 11, 2), date(2026, 10, 26)]


def test_build_site_writes_pages(tmp_path):
    d = make_briefs(tmp_path, ["2026-10-26.html", "2026-11-02.html"])
    out = tmp_path / "site"
    dates = site.build_site(d, out)
    assert dates == [date(2026, 11, 2), date(2026, 10, 26)]
    index = (out / "index.html").read_text()
    assert "2026-11-02.html" in index           # latest brief content
    assert "Sign up (coming soon)" in index      # placeholder signup
    assert 'href="archive.html"' in index
    old = (out / "briefs" / "2026-10-26.html").read_text()
    assert 'href="../index.html"' in old         # nav works from subfolder
    assert "Sign up" not in old
    archive = (out / "archive.html").read_text()
    assert 'href="briefs/2026-11-02.html"' in archive
    assert archive.index("Nov 2, 2026") < archive.index("Oct 26, 2026")
    assert (out / ".nojekyll").exists()


def test_signup_is_disabled_placeholder():
    assert "disabled" in site.SIGNUP_BOX and "action=" not in site.SIGNUP_BOX


def test_no_briefs_still_builds(tmp_path):
    d = tmp_path / "briefs"
    d.mkdir()
    out = tmp_path / "site"
    assert site.build_site(d, out) == []
    assert "coming soon" in (out / "index.html").read_text()
    assert "No briefs yet" in (out / "archive.html").read_text()


def test_rebuild_drops_removed_briefs(tmp_path):
    d = make_briefs(tmp_path, ["2026-11-02.html"])
    out = tmp_path / "site"
    site.build_site(d, out)
    (d / "2026-11-02.html").unlink()
    site.build_site(d, out)
    assert not (out / "briefs" / "2026-11-02.html").exists()


def test_works_on_real_brief_html(tmp_path):
    d = tmp_path / "briefs"
    d.mkdir()
    b = brief.build([], date(2026, 11, 2))
    (d / "2026-11-02.html").write_text(brief.to_html(b), encoding="utf-8")
    out = tmp_path / "site"
    site.build_site(d, out)
    index = (out / "index.html").read_text()
    assert '<nav class="sitenav">' in index and "Cost Wire" in index and ".signup" in index


def test_every_page_links_to_cash_rent_and_has_disclaimer(tmp_path):
    d = make_briefs(tmp_path, ["2026-11-02.html"])
    out = tmp_path / "site"
    site.build_site(d, out)
    pages = ["index.html", "archive.html", "cash-rent.html", "briefs/2026-11-02.html"]
    for p in pages:
        text = (out / p).read_text(encoding="utf-8")
        assert "cash-rent.html" in text, p
    # the cash rent page exists even before any NASS data is loaded
    assert "not loaded yet" in (out / "cash-rent.html").read_text(encoding="utf-8")
