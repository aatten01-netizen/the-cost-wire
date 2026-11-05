"""Email the weekly brief through Resend, to ONE TEST ADDRESS only (PLAN step 11).

Safety rules:
  - It sends to a single address you give it (--to, or env BRIEF_TEST_EMAIL).
    There is no "send to subscribers" option in this file. Real subscribers
    wait until Andy says so.
  - The key only comes from env RESEND_API_KEY. With no key or no address it
    skips cleanly and sends nothing.
  - Tests never call Resend; they pass in a fake sender.

Run it:  RESEND_API_KEY=... BRIEF_TEST_EMAIL=you@example.com python -m costwire.email_brief
         (add --date 2026-11-02 for a specific brief; default is the newest)
         add --dry-run to print what would be sent without sending.
"""

import argparse
import os
import re
import sys

from .paths import BRIEFS_DIR

RESEND_URL = "https://api.resend.com/emails"
# Resend's shared test sender works without verifying a domain.
DEFAULT_FROM = "The Cost Wire <onboarding@resend.dev>"


def latest_brief_date(briefs_dir=BRIEFS_DIR):
    """Newest date that has an .html brief, or None."""
    dates = sorted(p.stem for p in briefs_dir.glob("*.html")
                   if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem))
    return dates[-1] if dates else None


def build_message(brief_date, to, sender=DEFAULT_FROM, briefs_dir=BRIEFS_DIR):
    """The Resend payload: HTML body plus the Markdown as plain text."""
    html_path = briefs_dir / f"{brief_date}.html"
    md_path = briefs_dir / f"{brief_date}.md"
    if not html_path.exists():
        raise FileNotFoundError(f"No brief for {brief_date}: {html_path}")
    msg = {
        "from": sender,
        "to": [to],
        "subject": f"[TEST] The Cost Wire — week of {brief_date}",
        "html": html_path.read_text(encoding="utf-8"),
    }
    if md_path.exists():
        msg["text"] = md_path.read_text(encoding="utf-8")
    return msg


def _post(url, headers, payload):
    import requests
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def send(brief_date=None, to=None, api_key=None, post=_post, briefs_dir=BRIEFS_DIR,
         dry_run=False):
    """Send one brief to one test address. Returns Resend's reply, or None if skipped."""
    api_key = os.environ.get("RESEND_API_KEY", "") if api_key is None else api_key
    to = os.environ.get("BRIEF_TEST_EMAIL", "") if to is None else to
    to = to.strip()
    if "," in to or ";" in to or " " in to:
        raise ValueError("Test email goes to ONE address only.")
    if not to:
        print("BRIEF_TEST_EMAIL (or --to) not set: nothing sent.")
        return None
    brief_date = brief_date or latest_brief_date(briefs_dir)
    if not brief_date:
        print("No brief found in briefs/: run python -m costwire.brief first.")
        return None
    msg = build_message(brief_date, to, briefs_dir=briefs_dir)
    if dry_run:
        print(f"DRY RUN: would send '{msg['subject']}' to {to} ({len(msg['html'])} chars of HTML).")
        return None
    if not api_key:
        print("RESEND_API_KEY not set: nothing sent.")
        return None
    reply = post(RESEND_URL, {"Authorization": f"Bearer {api_key}"}, msg)
    print(f"Sent test brief {brief_date} to {to}.")
    return reply


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date")
    ap.add_argument("--to")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        send(a.date, a.to, dry_run=a.dry_run)
    except Exception as e:  # never show the key; message only
        print(f"Email failed: {type(e).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
