"""Static site builder: turns the weekly briefs into a small website in site/.

Pages it writes:
  site/index.html              the latest brief, with a nav bar and signup box
  site/archive.html            list of every brief, newest first
  site/briefs/<date>.html      each brief (same content as briefs/<date>.html)
  site/.nojekyll               tells GitHub Pages to serve files as they are

The signup box is a placeholder only (Step 12 wires it up, after Andy
approves). It does not collect or send anything.

Run it:  python -m costwire.site
"""

import html
import re
import shutil
import sys
from datetime import date

from .paths import BRIEFS_DIR, SITE_DIR

BRIEF_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.html$")

SIGNUP_BOX = """<section class="signup">
<h2>Get the brief by email</h2>
<p>A short email every Monday with fertilizer, fuel and feed prices and what changed.</p>
<form onsubmit="return false;">
<input type="email" placeholder="you@example.com" aria-label="Email address" disabled>
<button type="button" disabled>Sign up (coming soon)</button>
</form>
<p class="note">Signup is not open yet. Nothing you type here is saved or sent.</p>
</section>"""

SITE_CSS = """
.sitenav { display: flex; gap: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #222; font-family: Georgia, serif; }
.sitenav a { color: #222; }
.sitenav .brand { font-weight: bold; margin-right: auto; text-decoration: none; }
.signup { margin-top: 2rem; padding: 1rem; border: 1px solid #ddd; background: #f8f8f4; }
.signup input { padding: 0.4rem; max-width: 100%; }
"""


def brief_files(briefs_dir=None) -> list[tuple[date, object]]:
    """(date, path) for each briefs/YYYY-MM-DD.html, newest first. Bad dates are skipped."""
    found = []
    for path in (briefs_dir or BRIEFS_DIR).glob("*.html"):
        m = BRIEF_NAME.match(path.name)
        if not m:
            continue
        try:
            found.append((date.fromisoformat(m.group(1)), path))
        except ValueError:
            continue
    return sorted(found, key=lambda t: t[0], reverse=True)


def nav(prefix: str) -> str:
    """Nav bar. prefix is '' for pages in site/ and '../' for pages in site/briefs/."""
    return (f'<nav class="sitenav"><a class="brand" href="{prefix}index.html">The Cost Wire</a>'
            f'<a href="{prefix}index.html">Latest</a>'
            f'<a href="{prefix}archive.html">Archive</a></nav>')


def wrap_brief(brief_html: str, prefix: str, with_signup: bool) -> str:
    """Add the nav (and optionally the signup box) to a finished brief page."""
    page = brief_html.replace("</style>", SITE_CSS + "</style>", 1)
    page = page.replace("<body>", "<body>\n" + nav(prefix), 1)
    if with_signup:
        page = page.replace("</body>", SIGNUP_BOX + "\n</body>", 1)
    return page


def archive_page(dates: list[date]) -> str:
    if dates:
        items = "\n".join(
            f'<li><a href="briefs/{d.isoformat()}.html">Week of {d:%b} {d.day}, {d.year}</a></li>'
            for d in dates)
        body = f"<ul>\n{items}\n</ul>"
    else:
        body = "<p>No briefs yet.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Cost Wire — archive</title>
<style>
body {{ font-family: Georgia, serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #222; }}
{SITE_CSS}
</style>
</head>
<body>
{nav('')}
<h1>Archive</h1>
{body}
<p class="note">Data: USDA and EIA. Data, not advice.</p>
</body>
</html>
"""


def empty_home() -> str:
    return archive_page([]).replace("<h1>Archive</h1>", "<h1>The Cost Wire</h1>").replace(
        "<p>No briefs yet.</p>", "<p>The first brief is coming soon.</p>" + SIGNUP_BOX)


def build_site(briefs_dir=None, site_dir=None) -> list:
    """Write the site. Returns the list of brief dates published (newest first)."""
    site_dir = site_dir or SITE_DIR
    files = brief_files(briefs_dir)
    out_briefs = site_dir / "briefs"
    # Rebuild our own output folder from scratch so removed briefs don't linger.
    if out_briefs.exists():
        shutil.rmtree(out_briefs)
    out_briefs.mkdir(parents=True, exist_ok=True)
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")

    for d, path in files:
        text = path.read_text(encoding="utf-8")
        (out_briefs / path.name).write_text(wrap_brief(text, "../", False), encoding="utf-8")

    if files:
        latest = files[0][1].read_text(encoding="utf-8")
        index = wrap_brief(latest, "", True)
    else:
        index = empty_home()
    (site_dir / "index.html").write_text(index, encoding="utf-8")
    (site_dir / "archive.html").write_text(archive_page([d for d, _ in files]), encoding="utf-8")
    return [d for d, _ in files]


def main(argv=None) -> int:
    dates = build_site()
    if dates:
        print(f"Built site/ with {len(dates)} brief(s); latest is {dates[0].isoformat()}.")
    else:
        print("Built site/ with no briefs yet; run python -m costwire.brief first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
