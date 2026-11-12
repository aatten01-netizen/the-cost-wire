"""RSS feed for the site: site/feed.xml, one item per weekly brief, newest first.

Why: farmers and farm-news sites can follow The Cost Wire in a feed reader
(or Feedly, Outlook, etc.) without giving an email address. Free, no service.

Each item's title is the brief's own <h1> and its summary is the brief's first
<h2> (the headline). Nothing new is written here: every word comes from the
brief itself, so no number appears that the brief (and its accuracy check)
didn't already have.

The site address comes from env var SITE_URL; default is the live GitHub Pages
address. Run it as part of:  python -m costwire.site
"""

import html
import os
import re
from datetime import date, datetime, time, timezone
from email.utils import format_datetime

DEFAULT_SITE_URL = "https://aatten01-netizen.github.io/the-cost-wire/"
MAX_ITEMS = 20

_TAG = re.compile(r"<[^>]+>")


def site_url(env=None) -> str:
    """The site's base address, always ending in '/'. Must be http(s); else the default."""
    env = os.environ if env is None else env
    url = (env.get("SITE_URL") or "").strip()
    if not url.startswith(("https://", "http://")):
        url = DEFAULT_SITE_URL
    return url if url.endswith("/") else url + "/"


def _first(tag: str, page: str) -> str:
    """Plain text of the first <tag>...</tag> in the page, or '' if there is none."""
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", page, re.S | re.I)
    if not m:
        return ""
    return " ".join(html.unescape(_TAG.sub("", m.group(1))).split())


def _pubdate(d: date) -> str:
    """RFC 822 date (what RSS wants), noon UTC on the brief's date."""
    return format_datetime(datetime.combine(d, time(12, 0), tzinfo=timezone.utc))


def item(d: date, page: str, base: str) -> str:
    link = f"{base}briefs/{d.isoformat()}.html"
    title = _first("h1", page) or f"The Cost Wire — week of {d:%b} {d.day}, {d.year}"
    summary = _first("h2", page)
    e = lambda s: html.escape(s, quote=False)
    parts = [f"<title>{e(title)}</title>", f"<link>{e(link)}</link>",
             f'<guid isPermaLink="true">{e(link)}</guid>', f"<pubDate>{_pubdate(d)}</pubDate>"]
    if summary:
        parts.append(f"<description>{e(summary)}</description>")
    return "<item>" + "".join(parts) + "</item>"


def build_feed(briefs: list, base: str) -> str:
    """briefs = [(date, page_html), ...] in any order. Returns the RSS 2.0 XML text."""
    briefs = sorted(briefs, key=lambda t: t[0], reverse=True)[:MAX_ITEMS]
    items = "\n".join(item(d, page, base) for d, page in briefs)
    last = f"\n<lastBuildDate>{_pubdate(briefs[0][0])}</lastBuildDate>" if briefs else ""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
<channel>
<title>The Cost Wire</title>
<link>{html.escape(base, quote=False)}</link>
<description>Weekly Midwest farm input prices (fertilizer, fuel, feed) from USDA and EIA, each with its source and date. Data, not advice.</description>
<language>en-us</language>{last}
{items}
</channel>
</rss>
"""
