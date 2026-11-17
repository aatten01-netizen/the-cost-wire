"""Pro waitlist: "Tell me when Pro opens" on the pricing page, and the tally.

Why: BRIEF.md says Pro is worth opening once 5 farmers say they'd pay. Until
Stripe checkout is live, the pricing page can still collect that answer.

1. The form. When the free signup is live (SIGNUP_FORM_URL is https and
   SIGNUP_LIVE=yes) AND Pro checkout is NOT live, the pricing page shows a
   small form under the Pro plan: email, optional state, and one question,
   "Would you pay for Pro?" with three answers:
       monthly  Yes, $9/month
       yearly   Yes, $90/year
       maybe    Maybe, at a lower price
   It posts `pro_plan` to the same Google Sheet web app as the free signup
   (docs/signup-google-sheet.md, column G). Nothing is charged; it is a list.
   Otherwise no form is shown (nothing collected, nothing pretended).

2. The tally. Andy downloads the Sheet as CSV (outside the repo), then runs:
       python -m costwire.pro_waitlist /path/signups.csv
   It prints NUMBERS ONLY (never an email): how many readers said yes monthly,
   yes yearly, maybe, and the clear-yes count per state, against the goal of 5.
   Newest answer per reader wins. Only "monthly"/"yearly" count as a clear yes.
   It writes no file.
"""

import csv
import html
import sys

from . import pricing
from .brief import region_name
from .state_brief import STATES
from .state_list import _email_ok, clean_state, options_html

PLANS = ("monthly", "yearly", "maybe")
YES_PLANS = ("monthly", "yearly")
GOAL = 5  # BRIEF.md: "5 farmers say they'd pay for their state + alerts"


def plan_labels() -> list[tuple[str, str]]:
    return [
        ("monthly", f"Yes, ${pricing.PRO_MONTHLY}/month"),
        ("yearly", f"Yes, ${pricing.PRO_YEARLY}/year"),
        ("maybe", "Maybe, at a lower price"),
    ]


def form_live(env) -> bool:
    """Show the waitlist form only when the signup is live and checkout is not."""
    url = (env.get("SIGNUP_FORM_URL") or "").strip()
    live = (env.get("SIGNUP_LIVE") or "").strip().lower() == "yes"
    return live and url.startswith("https://") and not pricing.checkout_live(env)


def render(env) -> str:
    """The waitlist form HTML, or '' when it should not be shown."""
    if not form_live(env):
        return ""
    action = html.escape(env["SIGNUP_FORM_URL"].strip(), quote=True)
    radios = "\n".join(
        f'<label><input type="radio" name="pro_plan" value="{v}" required> {html.escape(t)}</label>'
        for v, t in plan_labels())
    return f"""<form class="waitlist" id="waitlist" method="post" action="{action}">
<h3>Tell me when Pro opens</h3>
<p>Would you pay for Pro?</p>
{radios}
<input type="email" name="email" placeholder="you@example.com" aria-label="Email address" required>
<select name="state" aria-label="Your state (optional)">
{options_html()}
</select>
<input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px">
<button type="submit">Join the Pro waitlist</button>
<p class="note">Nothing is charged. You also get the free Monday brief. We store your email, your answer and the state you pick (optional).</p>
</form>"""


WAITLIST_CSS = """
.waitlist { margin-top: 1rem; padding-top: 0.5rem; border-top: 1px dashed #bbb; }
.waitlist label { display: block; margin: 0.2rem 0; }
.waitlist input[type=email], .waitlist select { display: block; margin: 0.4rem 0; padding: 0.4rem; max-width: 100%; font: inherit; }
"""


def clean_plan(raw) -> str:
    p = (raw or "").strip().lower()
    return p if p in PLANS else ""


def parse(sheet_rows) -> dict:
    """Sheet rows -> {email: {"plan", "state"}}, newest answer per reader wins.

    A later row with no pro_plan (e.g. a plain signup) never wipes an answer,
    and a later row with no state keeps the state picked before.
    """
    out = {}
    for row in sheet_rows:
        email = (row.get("email") or "").strip().lower()
        if not _email_ok(email):
            continue
        plan = clean_plan(row.get("pro_plan"))
        state = clean_state(row.get("state"))
        prev = out.get(email, {"plan": "", "state": ""})
        out[email] = {"plan": plan or prev["plan"], "state": state or prev["state"]}
    return {e: v for e, v in out.items() if v["plan"]}


def tally(answers: dict) -> dict:
    """Counts only. 'yes' = monthly + yearly; 'yes_by_state' uses '' for no state."""
    t = {p: 0 for p in PLANS}
    by_state = {}
    for v in answers.values():
        t[v["plan"]] += 1
        if v["plan"] in YES_PLANS:
            by_state[v["state"]] = by_state.get(v["state"], 0) + 1
    t["yes"] = t["monthly"] + t["yearly"]
    t["yes_by_state"] = by_state
    return t


def report(t: dict) -> str:
    lines = [
        f"Pro waitlist: {t['yes']} clear yes (goal {GOAL}): "
        f"{t['monthly']} monthly, {t['yearly']} yearly. Maybe: {t['maybe']}.",
    ]
    parts = [f"{region_name(st)} {t['yes_by_state'][st]}" for st in STATES if st in t["yes_by_state"]]
    if "" in t["yes_by_state"]:
        parts.append(f"no state {t['yes_by_state']['']}")
    lines.append("Clear yes by state: " + (", ".join(parts) or "none yet"))
    if t["yes"] >= GOAL:
        lines.append("Goal met. Next: Andy makes the Stripe Payment Link (PRO_CHECKOUT_URL + PRO_CHECKOUT_LIVE=yes).")
    else:
        lines.append(f"{GOAL - t['yes']} more clear yes needed before opening Pro checkout.")
    lines.append("Counts only; no emails shown. Write the tally (numbers only) in LOG.md.")
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: python -m costwire.pro_waitlist <sheet.csv>")
        return 2
    try:
        with open(argv[0], newline="", encoding="utf-8-sig") as f:
            t = tally(parse(csv.DictReader(f)))
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(report(t))
    return 0


if __name__ == "__main__":
    sys.exit(main())
