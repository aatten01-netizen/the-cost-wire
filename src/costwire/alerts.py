"""Price-move alerts (the core Pro feature), behind a MOCK sender.

A reader picks an item, a state and a dollar amount. After each weekly pull,
this finds every reader whose price moved at least that much between the two
newest published reports, and writes them a short, sourced alert.

Privacy: reader emails are NEVER stored in this (public) repo. The list comes
from a CSV outside the repo, path in env var ALERTS_FILE, columns:
    email,item,region,threshold          e.g. you@farm.com,anhydrous,IA,25
Alerts already written are remembered in ALERTS_SENT_FILE (default: next to
ALERTS_FILE, named alerts_sent.csv) so the same report never alerts twice.

Sending: MockSender (default) keeps messages in memory / prints them and sends
nothing. ResendSender (Step 19) sends real email through Resend, but ONLY to
Andy's one test address (BRIEF_TEST_EMAIL), never to a reader, and only when
ALERTS_LIVE=yes AND RESEND_API_KEY AND BRIEF_TEST_EMAIL are all set. Each
test email says which reader it was meant for. At most MAX_TEST_SENDS per run.

Product rules: data, not advice (the alert reports a published move, nothing
else); never guess (both prices must be real saved prices from the same
source, item, state and unit, at most MAX_GAP_DAYS apart).

Run it:  ALERTS_FILE=/path/outside/repo/alerts.csv python -m costwire.alerts
"""

import csv
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from . import changes
from .brief import item_in_sentence, region_name

MAX_GAP_DAYS = 45  # previous report must be this recent, or no alert
SENT_COLUMNS = ["email", "item", "region", "as_of"]


def load_subscriptions(path) -> list[dict]:
    """Readers' alert choices. Bad rows (no @, unknown threshold) are skipped with a warning."""
    path = Path(path)
    if not path.exists():
        return []
    subs = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            email = (row.get("email") or "").strip().lower()
            item = (row.get("item") or "").strip().lower()
            region = (row.get("region") or "").strip().upper()
            try:
                threshold = float(row.get("threshold") or "")
            except ValueError:
                threshold = -1
            if "@" not in email or not item or not region or threshold <= 0:
                print("WARNING: skipped an alert row that is missing a field", file=sys.stderr)
                continue
            subs.append({"email": email, "item": item, "region": region, "threshold": threshold})
    return subs


def latest_moves(rows: list[dict]) -> dict:
    """(item, region) -> move between the two newest reports of that series.

    Only series where both reports exist, from the same source and unit,
    no more than MAX_GAP_DAYS apart. If one item/state has more than one
    source, each is checked and the biggest real move is kept.
    """
    series = {}
    for row in rows:
        series.setdefault(changes.series_key(row), []).append(row)
    moves = {}
    for (item, region, unit, _source), history in series.items():
        by_date = {}
        for r in history:  # one row per date (last one saved wins)
            by_date[r["as_of"]] = r
        dates = sorted(by_date)
        if len(dates) < 2:
            continue
        new, old = by_date[dates[-1]], by_date[dates[-2]]
        if new["as_of"] - old["as_of"] > timedelta(days=MAX_GAP_DAYS):
            continue
        dollars, pct = changes.change(new["price"], old["price"])
        move = {"item": item, "region": region, "unit": unit, "now": new, "then": old,
                "dollars": dollars, "pct": pct}
        key = (item, region)
        if key not in moves or abs(dollars) > abs(moves[key]["dollars"]):
            moves[key] = move
    return moves


def _day(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def _money(x: float, unit: str) -> str:
    per = unit.split("/", 1)[1] if "/" in unit else unit
    return f"${x:,.2f}/{per}"


def message(move: dict, threshold: float) -> dict:
    """Subject + plain-text body. Facts only, each with its source and date."""
    now, then = move["now"], move["then"]
    name = f"{region_name(move['region'])} {item_in_sentence(move['item'])}"
    word = "up" if move["dollars"] > 0 else "down"
    amount = f"${abs(move['dollars']):,.2f}"
    pct = f" ({abs(move['pct']):.1f}%)" if move["pct"] is not None else ""
    subject = f"The Cost Wire alert: {name} {word} {amount}"
    body = (
        f"{name}: {_money(now['price'], move['unit'])} on {_day(now['as_of'])}, "
        f"{word} {amount}{pct} from {_money(then['price'], move['unit'])} on {_day(then['as_of'])}.\n"
        f"You asked to hear about moves of ${threshold:,.2f} or more.\n\n"
        f"Source: {now['source_name']}, {now['source_url']}\n"
        f"Earlier price: {then['source_name']}, {then['source_url']}\n\n"
        "Data, not advice. This reports a published average price; it is not a "
        "recommendation to buy or sell.\n"
        "To stop these alerts, reply STOP."
    )
    return {"subject": subject, "body": body}


def _sent_keys(path) -> set:
    path = Path(path)
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["email"], r["item"], r["region"], r["as_of"]) for r in csv.DictReader(f)}


def find_alerts(subs: list[dict], rows: list[dict], already_sent: set = frozenset()) -> list[dict]:
    """Every alert that should go out now: one per reader per item/state per report."""
    moves = latest_moves(rows)
    out = []
    for s in subs:
        move = moves.get((s["item"], s["region"]))
        if move is None or abs(move["dollars"]) < s["threshold"]:
            continue
        key = (s["email"], s["item"], s["region"], move["now"]["as_of"].isoformat())
        if key in already_sent:
            continue
        already_sent = set(already_sent) | {key}  # same reader listed twice = one alert
        out.append({"to": s["email"], "key": key, **message(move, s["threshold"])})
    return out


class MockSender:
    live = False

    """Pretend sender: keeps every message so tests and dry runs can read it. Sends nothing."""

    def __init__(self):
        self.sent = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


MAX_TEST_SENDS = 10  # never flood Andy's inbox in one run
DEFAULT_FROM = "The Cost Wire <onboarding@resend.dev>"  # Resend's shared test sender


def _one_address(addr: str) -> str:
    addr = (addr or "").strip()
    if not addr or "@" not in addr or any(c in addr for c in ",; "):
        raise ValueError("The alert test address must be ONE email address.")
    return addr


class ResendSender:
    """Real email through Resend, but every message goes to ONE test address (Andy).

    The reader it was meant for is named in the subject and first line, so Andy
    can check the alert, but the reader receives nothing. `post` is injectable
    so tests never call Resend.
    """
    live = True

    def __init__(self, api_key: str, test_to: str, post=None, sender=DEFAULT_FROM,
                 max_sends=MAX_TEST_SENDS):
        if not api_key:
            raise ValueError("RESEND_API_KEY is missing.")
        self.api_key = api_key
        self.test_to = _one_address(test_to)
        self.sender = sender
        self.max_sends = max_sends
        if post is None:
            from .email_brief import _post as post
        self.post = post
        self.sent = []

    def send(self, to: str, subject: str, body: str) -> None:
        if len(self.sent) >= self.max_sends:
            raise RuntimeError(f"Test send limit reached ({self.max_sends} per run).")
        from .email_brief import RESEND_URL
        payload = {
            "from": self.sender,
            "to": [self.test_to],  # ALWAYS the test address, never the reader
            "subject": f"[TEST for {to}] {subject}",
            "text": f"(Test alert. Meant for reader {to}; they were NOT emailed.)\n\n{body}",
        }
        self.post(RESEND_URL, {"Authorization": f"Bearer {self.api_key}"}, payload)
        self.sent.append({"to": self.test_to, "subject": payload["subject"], "body": payload["text"]})


def pick_sender(env=None, post=None):
    """ResendSender only if ALERTS_LIVE=yes and the key + test address are set; else MockSender."""
    env = os.environ if env is None else env
    if (env.get("ALERTS_LIVE") or "").strip().lower() != "yes":
        return MockSender()
    key = (env.get("RESEND_API_KEY") or "").strip()
    test_to = (env.get("BRIEF_TEST_EMAIL") or "").strip()
    if not key or not test_to:
        print("ALERTS_LIVE=yes but RESEND_API_KEY or BRIEF_TEST_EMAIL is missing: using the mock sender.")
        return MockSender()
    return ResendSender(key, test_to, post=post)


def run(alerts_file, sent_file, rows, sender) -> int:
    """Find alerts, hand them to `sender`, remember them. Returns how many."""
    subs = load_subscriptions(alerts_file)
    already = _sent_keys(sent_file)
    alerts = find_alerts(subs, rows, already)
    done = []
    try:
        for a in alerts:
            sender.send(a["to"], a["subject"], a["body"])
            done.append(a)
    finally:  # remember only what really went out, even if a send failed midway
        if done:
            sent_file = Path(sent_file)
            new_file = not sent_file.exists()
            with open(sent_file, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if new_file:
                    w.writerow(SENT_COLUMNS)
                w.writerows(a["key"] for a in done)
    return len(done)


def main(argv=None) -> int:
    alerts_file = os.environ.get("ALERTS_FILE", "").strip()
    if not alerts_file:
        print("ALERTS_FILE not set; no alert list, nothing to do.")
        return 0
    sent_file = os.environ.get("ALERTS_SENT_FILE", "").strip() or str(
        Path(alerts_file).with_name("alerts_sent.csv"))
    sender = pick_sender()
    if not sender.live and (os.environ.get("ALERTS_LIVE") or "").strip().lower() == "yes":
        # Live was asked for but the key/address is missing: don't mark alerts as
        # sent, or the real test send later would skip them.
        sent_file = str(Path(sent_file).with_name("alerts_sent_mock.csv"))
    try:
        n = run(alerts_file, sent_file, changes.read_rows(), sender)
    except Exception as e:  # never print the key; error type only
        print(f"Alert send failed: {type(e).__name__}: {e}"[:300], file=sys.stderr)
        return 1
    if sender.live:
        print(f"{n} TEST alert(s) sent to the test address only. No reader was emailed.")
    else:
        for m in sender.sent:  # dry run: show what would go out, without the address
            print(f"--- (mock, not sent) {m['subject']}\n{m['body']}\n")
        print(f"{n} alert(s) written by the mock sender. No real email was sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
