"""Sample Pro alert page: shows the alert a Pro reader WOULD have gotten.

Writes site/pro-sample.html (called from site.build_site), linked from pricing.html.

Built only from data/fertilizer.csv, using the same move finder and message
as the real alerts (alerts.latest_moves + alerts.message), so the sample can
never say anything a real alert wouldn't.

Never guesses: if no item/state has two saved reports (same source and unit,
at most alerts.MAX_GAP_DAYS apart) that moved at least the smallest alert
amount, the page says so plainly and shows no numbers. It fills in by itself
after a later pull saves a second report.

Which move is shown: among real moves of at least $5 (the smallest choice on
the alerts page), the biggest one in percent. The reader setting shown is the
biggest alert amount the move would have hit (e.g. a $42 move -> "$25 or more").
No reader email is ever on the page.
"""

import html

from . import alerts
from .alert_signup import THRESHOLDS
from .brief import item_in_sentence, region_name


def sample_move(rows: list[dict]):
    """(move, threshold) for the sample, or None if no real move qualifies."""
    best = None
    for move in alerts.latest_moves(rows).values():
        size = abs(move["dollars"])
        hit = [t for t in THRESHOLDS if t <= size]
        if not hit:
            continue
        pct = abs(move["pct"]) if move["pct"] is not None else 0.0
        # tie-break on item/region so the pick never depends on file order
        rank = (pct, size, move["item"], move["region"])
        if best is None or rank > best[0]:
            best = (rank, move, max(hit))
    if best is None:
        return None
    return best[1], best[2]


def _saved_dates(rows: list[dict]) -> list:
    return sorted({r["as_of"] for r in rows})


def render(rows: list[dict]) -> str:
    """The sample page body (goes between the nav and </body>)."""
    intro = ("<h1>Sample Pro alert</h1>\n"
             "<p>Pro readers pick an item, a state and a dollar amount. When a new USDA or EIA "
             "report shows that published price moved at least that much, up or down, "
             "they get a short email like the one below.</p>")
    rules = ('<p class="note">Data, not advice. An alert reports a published average price; '
             "it is not a recommendation to buy or sell. Pro is not open yet: see "
             '<a href="pricing.html">Pricing</a> and the <a href="alerts.html">alert choices</a>.</p>')
    picked = sample_move(rows)
    if picked is None:
        dates = _saved_dates(rows)
        if dates:
            saved = "; ".join(f"{d:%b} {d.day}, {d.year}" for d in dates)
            why = (f"<p>No sample yet. Our saved prices so far come from reports dated {html.escape(saved)}, "
                   "and no item has two reports from the same source yet, so there is "
                   "no real price move to show. We don't make one up.</p>")
        else:
            why = "<p>No sample yet: no published prices are saved so far. We don't make one up.</p>"
        what = ("<p>Every alert will show:</p>\n<ul>\n"
                "<li>the item and state</li>\n"
                "<li>the new price and its report date</li>\n"
                "<li>the earlier price and its report date</li>\n"
                "<li>the move in dollars and percent</li>\n"
                "<li>the USDA or EIA source link for both prices</li>\n</ul>\n"
                "<p>This page fills in by itself with a real move once the next report is saved.</p>")
        return f"{intro}\n{why}\n{what}\n{rules}"

    move, threshold = picked
    msg = alerts.message(move, threshold)
    now, then = move["now"], move["then"]
    name = f"{region_name(move['region'])} {item_in_sentence(move['item'])}"
    setup = (f"<p>This is a real move from our saved data. A Pro reader who picked "
             f"<strong>{html.escape(name)}</strong> and <strong>${threshold} or more</strong> "
             f"would have gotten this email after the {now['as_of']:%b} {now['as_of'].day}, "
             f"{now['as_of'].year} report:</p>")
    sources = {now["source_url"]: now["source_name"], then["source_url"]: then["source_name"]}
    links = "\n".join(
        f'<li><a href="{html.escape(u, quote=True)}">{html.escape(n)}</a></li>'
        for u, n in sources.items())
    email = (f'<div class="sample-email">\n<p class="subject">Subject: {html.escape(msg["subject"])}</p>\n'
             f'<pre>{html.escape(msg["body"])}</pre>\n</div>')
    return f"{intro}\n{setup}\n{email}\n<h2>Sources</h2>\n<ul>\n{links}\n</ul>\n{rules}"


SAMPLE_CSS = """
.sample-email { border: 1px solid #ddd; background: #f8f8f4; padding: 1rem; max-width: 640px; }
.sample-email .subject { font-weight: bold; margin-top: 0; }
.sample-email pre { white-space: pre-wrap; overflow-wrap: anywhere; font: inherit; margin: 0; }
"""
