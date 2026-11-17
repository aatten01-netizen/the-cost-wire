"""Email each reader their state edition of the brief (PLAN step 23).

Reads the reader list made by `costwire.state_list` (email,state; a file
OUTSIDE this repo) and works out which brief each reader should get:
  - a reader who picked IA / IL / MN / WI gets that state's edition
    (state_brief.build_edition: only that state's prices + Midwest fuel,
    accuracy-checked),
  - a reader with no state, or a state with no published prices, gets the
    main brief (briefs/<date>.html).

Safety rules (same as Steps 11 and 19):
  - Default is a DRY RUN: it prints how many readers would get each edition.
    Nothing is sent.
  - Only with STATE_EMAIL_LIVE=yes AND RESEND_API_KEY AND BRIEF_TEST_EMAIL set
    does it send real email, and then it sends ONE test email PER EDITION to
    Andy's test address only (at most 5 per run). No reader is ever emailed;
    the subject says how many readers that edition would go to.
  - Reader emails are never printed, never written to the repo.
  - Tests never call Resend (the `post` function is passed in).

Run it:
  READERS_FILE=/path/readers.csv PYTHONPATH=src python -m costwire.state_email
  (add STATE_EMAIL_LIVE=yes RESEND_API_KEY=... BRIEF_TEST_EMAIL=you@x.com to get
   the test emails in your own inbox)
"""

import csv
import os
import sys
from pathlib import Path

from . import brief, changes, corn_price, state_brief, unsubscribe
from .email_brief import DEFAULT_FROM, RESEND_URL, latest_brief_date
from .feed_rss import site_url
from .paths import BRIEFS_DIR
from .state_list import clean_state

MAIN = ""  # edition key for "the main brief"
MAX_TEST_SENDS = 5  # one per edition: IA, IL, MN, WI, main


def load_readers(path) -> list[dict]:
    """email,state CSV -> [{email, state}]; bad rows skipped, duplicate emails keep the last."""
    readers = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            email = (row.get("email") or "").strip().lower()
            if "@" not in email or any(c in email for c in ",; "):
                continue
            readers.pop(email, None)
            readers[email] = {"email": email, "state": clean_state(row.get("state"))}
    return list(readers.values())


def group_readers(readers: list[dict], editions: set) -> dict:
    """{edition: [emails]}. A state with no edition falls back to the main brief."""
    groups = {}
    for r in readers:
        key = r["state"] if r["state"] in editions else MAIN
        groups.setdefault(key, []).append(r["email"])
    return groups


def build_editions(rows, brief_date, corn_prices=None, briefs_dir=BRIEFS_DIR) -> dict:
    """{edition: {"title", "html", "text", "web"}} for the main brief + every state edition.

    The state editions run the accuracy check (ValueError on any problem).
    """
    iso = brief_date.isoformat()
    base = site_url()
    out = {}
    main_html = Path(briefs_dir) / f"{iso}.html"
    if main_html.exists():
        md = Path(briefs_dir) / f"{iso}.md"
        out[MAIN] = {"title": "The Cost Wire",
                     "html": main_html.read_text(encoding="utf-8"),
                     "text": md.read_text(encoding="utf-8") if md.exists() else "",
                     "web": base}
    results = changes.compute(rows) if rows else []
    for st in state_brief.STATES:
        made = state_brief.build_edition(results, st, brief_date, corn_prices, rows)
        if made is None:
            continue
        b, md = made
        out[st] = {"title": f"The Cost Wire — {brief.region_name(st)} edition",
                   "html": brief.to_html(b), "text": md,
                   "web": f"{base}state/{st.lower()}.html"}
    return out


def test_message(edition_key, ed, n_readers, brief_date, test_to, sender=DEFAULT_FROM,
                 env=None) -> dict:
    """The Resend payload for one edition, addressed ONLY to the test address.
    Carries the unsubscribe + mailing-address footer (Step 24)."""
    who = "no state picked" if edition_key == MAIN else brief.region_name(edition_key)
    note = (f"(Test send. This edition would go to {n_readers} reader(s) ({who}); "
            f"none of them were emailed. Web version: {ed['web']})")
    msg = {
        "from": sender,
        "to": [test_to],  # ALWAYS the test address, never a reader
        "subject": f"[TEST x{n_readers}] {ed['title']} — week of {brief_date.isoformat()}",
        "html": unsubscribe.add_footer_html(
            f'<p style="font-family:sans-serif;color:#555">{note}</p>\n' + ed["html"], env),
        "text": f"{note}\n\n{ed['text'].rstrip()}\n\n{unsubscribe.footer_text(env)}",
    }
    if unsubscribe.headers(env):
        msg["headers"] = unsubscribe.headers(env)
    return msg


def plan(readers, editions) -> list[tuple]:
    """[(edition_key, n_readers)] for every edition with readers, main brief last."""
    groups = group_readers(readers, set(editions) - {MAIN})
    order = [s for s in state_brief.STATES if s in groups] + ([MAIN] if MAIN in groups else [])
    return [(k, len(groups[k])) for k in order]


def run(readers, editions, brief_date, env=None, post=None) -> dict:
    """Dry run, or test sends if live. Returns {"plan": [...], "sent": [subjects], "live": bool}."""
    env = os.environ if env is None else env
    todo = plan(readers, editions)
    if any(k == MAIN for k, _ in todo) and MAIN not in editions:
        raise ValueError(f"No main brief in briefs/ for {brief_date}: run python -m costwire.brief first.")
    live = (env.get("STATE_EMAIL_LIVE") or "").strip().lower() == "yes"
    key = (env.get("RESEND_API_KEY") or "").strip()
    test_to = (env.get("BRIEF_TEST_EMAIL") or "").strip()
    if live and (not key or not test_to):
        print("STATE_EMAIL_LIVE=yes but RESEND_API_KEY or BRIEF_TEST_EMAIL is missing: dry run only.")
        live = False
    if live and ("@" not in test_to or any(c in test_to for c in ",; ")):
        raise ValueError("BRIEF_TEST_EMAIL must be ONE email address.")
    sent = []
    if live:
        if post is None:
            from .email_brief import _post as post
        for k, n in todo[:MAX_TEST_SENDS]:
            msg = test_message(k, editions[k], n, brief_date, test_to, env=env)
            post(RESEND_URL, {"Authorization": f"Bearer {key}"}, msg)
            sent.append(msg["subject"])
    return {"plan": todo, "sent": sent, "live": live}


def main(argv=None) -> int:
    path = (os.environ.get("READERS_FILE") or "").strip()
    if not path:
        print("READERS_FILE not set (make it with python -m costwire.state_list): nothing to do.")
        return 0
    newest = latest_brief_date()
    if not newest:
        print("No brief found in briefs/: run python -m costwire.brief first.")
        return 0
    from datetime import date
    brief_date = date.fromisoformat(newest)
    try:
        # Readers who unsubscribed are dropped before anything else (Step 24).
        readers = unsubscribe.drop(load_readers(path), unsubscribe.load_from_env())
        rows = changes.read_rows()
        editions = build_editions(rows, brief_date, corn_price.load_prices())
        result = run(readers, editions, brief_date)
    except Exception as e:  # never print the key; error type + message only
        print(f"State email failed: {type(e).__name__}: {e}"[:300], file=sys.stderr)
        return 1
    for k, n in result["plan"]:
        name = "Main brief (no state)" if k == MAIN else editions[k]["title"]
        print(f"{name}: {n} reader(s)")
    if result["live"]:
        print(f"{len(result['sent'])} TEST email(s) sent to the test address only. No reader was emailed.")
    else:
        print("Dry run: nothing was sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
