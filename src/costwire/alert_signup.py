"""Alert sign-up: readers choose an item, a state and a dollar amount on the site.

Two parts:

1. The form (site/alerts.html). It posts to the SAME Google Sheet web app as
   the free signup (SIGNUP_FORM_URL, see docs/signup-google-sheet.md), with
   three extra fields: alert_item, alert_region, alert_threshold. The choices
   come only from items and states that have published prices in
   data/fertilizer.csv, so nobody can ask for an alert we have no data for.
   The form is a placeholder (collects nothing) UNLESS SIGNUP_FORM_URL is an
   https link AND ALERTS_SIGNUP_LIVE=yes (Andy's go-ahead, separate from the
   free signup because alerts are a Pro feature).

2. The export. Andy downloads the Sheet as CSV (File > Download > CSV) to a
   folder OUTSIDE this repo, then runs:
       python -m costwire.alert_signup /path/signups.csv /path/alerts.csv
   That writes the ALERTS_FILE format (email,item,region,threshold) that
   costwire.alerts reads. Rows with no alert choice (brief-only signups) or a
   bad choice are skipped. If a reader signed up for the same item and state
   twice, their newest amount wins. The export refuses to write inside the
   repo, because the file holds reader emails.

Data, not advice: an alert only reports a published price move.
"""

import csv
import html
import os
import sys
from pathlib import Path

from . import changes
from .brief import REGION_NAMES, item_name, region_name, sort_key
from .paths import ROOT

ALERT_COLUMNS = ["email", "item", "region", "threshold"]
THRESHOLDS = [5, 10, 25, 50, 100]  # dollars; the form offers these
MAX_THRESHOLD = 1000  # anything bigger is a typo, skip it


def alert_options(rows: list[dict]) -> list[tuple[str, str]]:
    """(item, region) pairs that have a published price, in brief order. One per pair."""
    seen = {}
    for r in rows:
        if r.get("item") and r.get("region") in REGION_NAMES:
            seen.setdefault((r["item"], r["region"]), r)
    return [(r["item"], r["region"]) for r in sorted(seen.values(), key=sort_key)]


def _choice_list(options) -> str:
    out = []
    for item, region in options:
        value = html.escape(f"{item}|{region}", quote=True)
        label = html.escape(f"{region_name(region)}: {item_name(item)}")
        out.append(f'<option value="{value}">{label}</option>')
    return "\n".join(out)


def _amount_list() -> str:
    return "\n".join(f'<option value="{t}">${t} or more</option>' for t in THRESHOLDS)


def is_live(env=None) -> bool:
    env = os.environ if env is None else env
    url = (env.get("SIGNUP_FORM_URL") or "").strip()
    live = (env.get("ALERTS_SIGNUP_LIVE") or "").strip().lower() == "yes"
    return live and url.startswith("https://")


def render(rows: list[dict], env=None) -> str:
    """The alerts page body (goes between the nav and </body>)."""
    env = os.environ if env is None else env
    options = alert_options(rows)
    intro = ("<h1>Price-move alerts</h1>\n"
             "<p>Pick an item, a state and a dollar amount. After each new USDA or EIA "
             "report, we email you if that published price moved at least that much, "
             "up or down, with both prices, both dates and the source link.</p>")
    rules = ('<p class="note">Data, not advice. An alert reports a published average '
             "price; it is not a recommendation to buy or sell. Reply STOP to any alert "
             'to stop them. See <a href="pricing.html">Pricing</a>.</p>')
    if not options:
        return intro + "\n<p>No published prices yet, so there is nothing to pick. Check back after the next weekly brief.</p>\n" + rules
    if is_live(env):
        action = html.escape(env["SIGNUP_FORM_URL"].strip(), quote=True)
        form = f"""<form class="alertform" method="post" action="{action}">
<label>Email <input type="email" name="email" placeholder="you@example.com" required></label>
<label>Item and state <select name="alert_pick" required>
{_choice_list(options)}
</select></label>
<label>Alert me when it moves <select name="alert_threshold" required>
{_amount_list()}
</select></label>
<input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px">
<button type="submit">Set my alert</button>
</form>
<p class="note">We store your email and your alert choice only. You also get the free Monday brief.</p>"""
    else:
        form = f"""<form class="alertform" onsubmit="return false;">
<label>Email <input type="email" placeholder="you@example.com" disabled></label>
<label>Item and state <select disabled>
{_choice_list(options)}
</select></label>
<label>Alert me when it moves <select disabled>
{_amount_list()}
</select></label>
<button type="button" disabled>Set my alert (coming soon)</button>
</form>
<p class="note">Alert sign-up is not open yet. Nothing you pick here is saved or sent.</p>"""
    return f"{intro}\n{form}\n{rules}"


ALERTS_CSS = """
.alertform { display: flex; flex-direction: column; gap: 0.6rem; max-width: 420px; padding: 1rem; border: 1px solid #ddd; background: #f8f8f4; }
.alertform label { display: flex; flex-direction: column; gap: 0.2rem; }
.alertform input, .alertform select { padding: 0.4rem; max-width: 100%; font: inherit; }
"""


# ---------- export: Google Sheet CSV -> ALERTS_FILE ----------

def parse_signups(sheet_rows, known: set) -> list[dict]:
    """Sheet rows -> alert rows. `known` = the (item, region) pairs we publish.

    Accepts either alert_pick ("anhydrous|IA") or alert_item + alert_region.
    Skips rows with no alert choice, a bad email, an unknown pair or a bad amount.
    Newest row (later in the sheet) wins for the same email + item + region.
    """
    picked = {}
    for row in sheet_rows:
        email = (row.get("email") or "").strip().lower()
        pick = (row.get("alert_pick") or "").strip()
        if "|" in pick:
            item, region = pick.split("|", 1)
        else:
            item, region = row.get("alert_item") or "", row.get("alert_region") or ""
        item, region = item.strip().lower(), region.strip().upper()
        raw = (row.get("alert_threshold") or "").strip().lstrip("$")
        if not item and not region and not raw:
            continue  # brief-only signup, no alert asked for
        try:
            threshold = float(raw)
        except ValueError:
            threshold = -1
        email_ok = "@" in email and "." in email.split("@")[-1] and "," not in email
        if not email_ok or (item, region) not in known or not 0 < threshold <= MAX_THRESHOLD:
            print("WARNING: skipped a signup row with a bad or unknown alert choice", file=sys.stderr)
            continue
        key = (email, item, region)
        picked.pop(key, None)  # re-insert so the newest choice keeps its place at the end
        picked[key] = {"email": email, "item": item, "region": region,
                       "threshold": f"{threshold:g}"}
    return list(picked.values())


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def export(sheet_csv, out_csv, rows=None) -> int:
    """Write the ALERTS_FILE. Returns how many alert rows were written."""
    out_csv = Path(out_csv)
    if _inside_repo(out_csv):
        raise ValueError("Refusing to write reader emails inside the repo. Pick a folder outside it.")
    rows = changes.read_rows() if rows is None else rows
    known = set(alert_options(rows))
    with open(sheet_csv, newline="", encoding="utf-8-sig") as f:
        alerts = parse_signups(csv.DictReader(f), known)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ALERT_COLUMNS)
        w.writeheader()
        w.writerows(alerts)
    return len(alerts)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("Usage: python -m costwire.alert_signup <sheet.csv> <alerts.csv (outside the repo)>")
        return 2
    try:
        n = export(argv[0], argv[1])
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Wrote {n} alert choice(s) to {argv[1]}. Use it as ALERTS_FILE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
