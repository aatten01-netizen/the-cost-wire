import xml.etree.ElementTree as ET
from datetime import date

from costwire import feed_rss, site

PAGE = ("<html><head><style></style></head><body><h1>The Cost Wire &mdash; week of Nov 9, 2026</h1>"
        "<h2>Urea <b>up</b> &amp; diesel flat</h2></body></html>")
BASE = "https://example.com/cw/"


def test_site_url_default_and_env():
    assert feed_rss.site_url({}) == feed_rss.DEFAULT_SITE_URL
    assert feed_rss.site_url({"SITE_URL": "https://x.org/a"}) == "https://x.org/a/"
    assert feed_rss.site_url({"SITE_URL": "javascript:alert(1)"}) == feed_rss.DEFAULT_SITE_URL


def test_feed_is_valid_xml_newest_first_with_brief_text():
    xml = feed_rss.build_feed([(date(2026, 11, 2), PAGE), (date(2026, 11, 9), PAGE)], BASE)
    items = ET.fromstring(xml).find("channel").findall("item")
    assert [i.findtext("link") for i in items] == [
        BASE + "briefs/2026-11-09.html", BASE + "briefs/2026-11-02.html"]
    assert items[0].findtext("title") == "The Cost Wire — week of Nov 9, 2026"
    assert items[0].findtext("description") == "Urea up & diesel flat"   # tags stripped, entities ok
    assert items[0].findtext("pubDate").startswith("Mon, 09 Nov 2026")


def test_page_without_headings_gets_date_title_and_no_description():
    xml = feed_rss.build_feed([(date(2026, 11, 9), "<body>x</body>")], BASE)
    it = ET.fromstring(xml).find("channel/item")
    assert it.findtext("title") == "The Cost Wire — week of Nov 9, 2026"
    assert it.find("description") is None


def test_empty_feed_and_item_limit():
    root = ET.fromstring(feed_rss.build_feed([], BASE))
    assert root.find("channel/item") is None
    many = [(date(2026, 1, 1).fromordinal(date(2026, 1, 1).toordinal() + 7 * i), PAGE) for i in range(30)]
    assert len(ET.fromstring(feed_rss.build_feed(many, BASE)).findall("channel/item")) == feed_rss.MAX_ITEMS


def test_build_site_writes_feed_and_links_it(tmp_path, monkeypatch):
    monkeypatch.setenv("SITE_URL", BASE)
    d = tmp_path / "briefs"
    d.mkdir()
    (d / "2026-11-09.html").write_text(PAGE, encoding="utf-8")
    out = tmp_path / "site"
    site.build_site(d, out)
    root = ET.fromstring((out / "feed.xml").read_text(encoding="utf-8"))
    assert root.find("channel/item/link").text == BASE + "briefs/2026-11-09.html"
    assert 'href="feed.xml"' in (out / "index.html").read_text()
    assert 'href="feed.xml"' in (out / "archive.html").read_text()
    assert 'href="../feed.xml"' in (out / "briefs" / "2026-11-09.html").read_text()
