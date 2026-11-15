"""State editions of the weekly brief (the "your state's numbers first" Pro feature).

Writes site/state/<st>.html for each state we have published prices for
(Iowa, Illinois, Minnesota, Wisconsin), plus site/state/index.html listing them.
Called from site.build_site. Linked from the pricing page.

Each state edition is the same brief, built by the same template, but with
only that state's prices plus the Midwest-wide (PADD 2) EIA fuel prices,
which cover every one of these states. Its headline is the biggest move in
that state. Labeled "Pro preview" while Pro is not open.

Product rules:
- Never guess a number: the edition uses only rows already in the saved data
  (via the change calculator). A state with no published price of its own
  gets no page (we never fill one in from another state).
- Before a page is written, the accuracy check runs on that edition's text
  (table, nitrogen, bushels and trend lines must match the data exactly).
  Any problem stops the site build.
- Data, not advice: the disclaimer is part of every edition.
"""

import html
from datetime import date

from . import accuracy, brief, changes

STATES = ["IA", "IL", "MN", "WI"]
# Regional averages that cover every state above (EIA Midwest, PADD 2).
MIDWEST = {"PADD2"}

PREVIEW_NOTE = ("Pro preview: free to look at while Pro is not open. "
                "This edition shows only {state} prices, plus Midwest-wide (PADD 2) "
                "fuel prices from EIA. The full brief covers every state.")


def filter_results(results: list[dict], state: str) -> list[dict]:
    """The state's own rows plus Midwest-wide rows; [] if the state has none of its own."""
    if not any(r["region"] == state for r in results):
        return []
    return [r for r in results if r["region"] == state or r["region"] in MIDWEST]


def build_edition(results: list[dict], state: str, brief_date: date,
                  corn_prices=None, history=None):
    """(brief dict, markdown) for one state, or None when the state has no prices.

    Raises ValueError if the accuracy check finds any problem.
    """
    rows = filter_results(results, state)
    if not rows:
        return None
    b = brief.build(rows, brief_date, corn_prices, history, edition=state)
    md = brief.to_markdown(b)
    problems = (accuracy.check_brief(md, rows)
                + accuracy.check_afford(md, rows, corn_prices or [])
                + accuracy.check_trend(md, rows, history or [])
                + accuracy.check_nitrogen(md, rows))
    if problems:
        raise ValueError(f"{brief.region_name(state)} edition failed the accuracy check: "
                         + " | ".join(problems))
    return b, md


def edition_html(b: dict) -> str:
    """The edition as a full HTML page (before the site adds its nav)."""
    page = brief.to_html(b)
    note = html.escape(PREVIEW_NOTE.format(state=brief.region_name(b["edition"])))
    return page.replace("</h1>", f'</h1>\n<p class="note preview">{note} '
                                 f'<a href="../pricing.html">See Pro</a> · '
                                 f'<a href="../index.html">Full brief</a></p>', 1)


def index_body(states: list[str], brief_date) -> str:
    """Body of site/state/index.html (goes between the nav and </body>)."""
    if not states:
        items = "<p>No state editions yet.</p>"
    else:
        links = "\n".join(
            f'<li><a href="{s.lower()}.html">{html.escape(brief.region_name(s))}</a></li>'
            for s in states)
        items = f"<ul>\n{links}\n</ul>"
    when = f" Week of {brief.short_date(brief_date)}." if brief_date else ""
    return (f"<h1>Your state's brief</h1>\n"
            f"<p>The weekly brief with only your state's published prices, plus "
            f"Midwest-wide fuel.{when} Pro preview: free to look at while Pro is not open.</p>\n"
            f"{items}\n"
            f'<p class="note">Data: USDA and EIA. Data, not advice. '
            f'<a href="../pricing.html">Pricing</a></p>')


def build_all(rows: list[dict], brief_date: date, corn_prices=None) -> dict:
    """{state: html page} for every state with published prices, in STATES order."""
    results = changes.compute(rows)
    pages = {}
    for state in STATES:
        made = build_edition(results, state, brief_date, corn_prices, rows)
        if made is not None:
            pages[state] = edition_html(made[0])
    return pages
