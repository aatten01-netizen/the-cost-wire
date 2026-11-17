"""Unsubscribe link, mailing address and unsubscribe list for every email (PLAN step 24).

The US email law (CAN-SPAM) says every marketing email must have a working way
to opt out and the sender's postal address, and an opt-out must be honored.
This file gives every email we build the same footer and lets every sender
drop readers who opted out.

Settings (environment only, never committed):
  UNSUBSCRIBE_URL      where a reader opts out: an https:// link (e.g. a free
                       Google Form) or mailto:you@example.com?subject=unsubscribe
  MAIL_POSTAL_ADDRESS  the mailing address printed in the footer (Andy picks it:
                       business address, PO box or registered mailbox)
  UNSUBSCRIBES_FILE    CSV OUTSIDE this repo with an `email` column (or one email
                       per line): everyone on it is skipped by every sender.

With a setting missing, the footer says so in brackets (test emails still work),
and `ready()` is False so the launch check flags it before any reader send.
"""

import csv
import os
from pathlib import Path

MISSING_LINK = "[unsubscribe link not set: UNSUBSCRIBE_URL]"
MISSING_ADDRESS = "[mailing address not set: MAIL_POSTAL_ADDRESS]"


def _env(env):
    return os.environ if env is None else env


def unsubscribe_url(env=None) -> str:
    """The opt-out link, or "" if not set or not https:// / mailto:."""
    url = (_env(env).get("UNSUBSCRIBE_URL") or "").strip()
    if url.startswith("https://") or (url.startswith("mailto:") and "@" in url):
        return url
    return ""


def postal_address(env=None) -> str:
    return " ".join((_env(env).get("MAIL_POSTAL_ADDRESS") or "").split())


def ready(env=None) -> bool:
    """True when both the opt-out link and the mailing address are set."""
    return bool(unsubscribe_url(env) and postal_address(env))


def footer_text(env=None) -> str:
    url = unsubscribe_url(env) or MISSING_LINK
    addr = postal_address(env) or MISSING_ADDRESS
    return ("--\nYou get this because you signed up for The Cost Wire.\n"
            f"Unsubscribe: {url}\n"
            f"The Cost Wire, {addr}")


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def footer_html(env=None) -> str:
    url = unsubscribe_url(env)
    link = f'<a href="{_esc(url)}">Unsubscribe</a>' if url else _esc(MISSING_LINK)
    addr = _esc(postal_address(env) or MISSING_ADDRESS)
    return ('<p style="font-family:sans-serif;font-size:12px;color:#666;'
            'border-top:1px solid #ddd;padding-top:8px;margin-top:24px">'
            f"You get this because you signed up for The Cost Wire. {link}.<br>"
            f"The Cost Wire, {addr}</p>")


def add_footer_html(html: str, env=None) -> str:
    """Put the footer just before </body> (or at the end if there is none)."""
    foot = footer_html(env)
    i = html.lower().rfind("</body>")
    return html[:i] + foot + "\n" + html[i:] if i >= 0 else html + "\n" + foot


def headers(env=None) -> dict:
    """List-Unsubscribe header (shows the mail app's own unsubscribe button), or {}."""
    url = unsubscribe_url(env)
    return {"List-Unsubscribe": f"<{url}>"} if url else {}


def load(path) -> set:
    """Lower-cased emails from the unsubscribe file; empty set if no file."""
    if not path:
        return set()
    path = Path(path)
    if not path.exists():
        return set()
    out = set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            for cell in row:
                cell = cell.strip().lower()
                if "@" in cell:
                    out.add(cell)
    return out


def load_from_env(env=None) -> set:
    return load((_env(env).get("UNSUBSCRIBES_FILE") or "").strip())


def drop(records: list[dict], unsubscribed: set, key="email") -> list[dict]:
    """Records whose email is not on the unsubscribe list."""
    return [r for r in records if (r.get(key) or "").strip().lower() not in unsubscribed]
