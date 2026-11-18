"""Team plan page (site/team.html) and the team waitlist tally.

Who it is for: ag lenders, agronomists / crop consultants and co-ops or ag
retailers who want the same published prices for many clients (state editions,
price-move alerts, the cost-per-acre worksheet).

1. The price. TEAM_MONTHLY is None until Andy picks one, so the page says
   "Price: ask" and never shows a made-up number.

2. The checkout is a MOCK (disabled button) UNLESS all three are true:
   TEAM_MONTHLY is set here, TEAM_CHECKOUT_URL is a Stripe Payment Link
   (https://buy.stripe.com/...) and TEAM_CHECKOUT_LIVE=yes.

3. The form "Tell me when Team opens" shows only when the free signup is live
   (SIGNUP_FORM_URL is https and SIGNUP_LIVE=yes) and Team checkout is not.
   It posts plan=team, team_role and team_size to the same Google Sheet
   (docs/signup-google-sheet.md, columns H-I). Nothing is charged.

4. The tally: python -m costwire.team /path/signups.csv
   Prints COUNTS ONLY (never an email or a business name): team signups by
   role and by size. Writes no file.
"""

import csv
import html
import os
import sys

from .state_list import _email_ok

TEAM_MONTHLY = None  # dollars per month; None = "ask" (Andy sets the price)
CHECKOUT_PREFIX = "https://buy.stripe.com/"

ROLES = [
    ("lender", "Ag lender / farm credit"),
    ("agronomist", "Agronomist / crop consultant"),
    ("coop", "Co-op or ag retailer"),
    ("other", "Other ag business"),
]
SIZES = [
    ("1-10", "1-10 clients"),
    ("11-50", "11-50 clients"),
    ("51+", "51 or more clients"),
]

TEAM_FEATURES = [
    "State editions of the weekly brief (Iowa, Illinois, Minnesota, Wisconsin) to share with clients",
    "Price-move email alerts on the published prices you pick",
    "Cost-per-acre worksheet using the latest published USDA prices",
    "Every number linked to its USDA or EIA source and date",
    "One bill for your team instead of one Pro plan per person",
]

FAQ = [
    ("Who is Team for?",
     "Ag lenders, agronomists, crop consultants, co-ops and ag retailers who talk input costs "
     "with many farmers and want the same sourced numbers in front of everyone."),
    ("What does it cost?",
     "Not set yet. Tell us your role and client count with the form on this page (it opens with the free signup) and we will reply "
     "with a price before anything is charged."),
    ("Will it tell my clients what to buy?",
     "No. The Cost Wire reports published prices and how they changed. It is data, not advice."),
    ("Do you share any farmer's quote or a dealer's name?",
     "No. We only use public USDA AMS, USDA NASS and EIA reports."),
]


def price_text() -> str:
    return f"${TEAM_MONTHLY}/month" if TEAM_MONTHLY else "Price: ask"


def checkout_live(env=None) -> bool:
    env = os.environ if env is None else env
    url = (env.get("TEAM_CHECKOUT_URL") or "").strip()
    live = (env.get("TEAM_CHECKOUT_LIVE") or "").strip().lower() == "yes"
    return (bool(TEAM_MONTHLY) and live and url.startswith(CHECKOUT_PREFIX)
            and len(url) > len(CHECKOUT_PREFIX))


def checkout_button(env=None) -> str:
    env = os.environ if env is None else env
    if checkout_live(env):
        url = html.escape(env["TEAM_CHECKOUT_URL"].strip(), quote=True)
        return (f'<a class="buy" href="{url}" rel="noopener">Start Team, {price_text()}</a>'
                '<p class="note">Secure checkout by Stripe. Cancel any time.</p>')
    return ('<button class="buy" type="button" disabled>Team is not open yet</button>'
            '<p class="note">Nothing is sold on this page yet.</p>')


def form_live(env) -> bool:
    url = (env.get("SIGNUP_FORM_URL") or "").strip()
    live = (env.get("SIGNUP_LIVE") or "").strip().lower() == "yes"
    return live and url.startswith("https://") and not checkout_live(env)


def _options(pairs, placeholder) -> str:
    out = [f'<option value="">{html.escape(placeholder)}</option>']
    out += [f'<option value="{v}">{html.escape(t)}</option>' for v, t in pairs]
    return "\n".join(out)


def form(env) -> str:
    """The 'Tell me when Team opens' form, or '' when it should not show."""
    if not form_live(env):
        return ""
    action = html.escape(env["SIGNUP_FORM_URL"].strip(), quote=True)
    return f"""<form class="waitlist" id="team-waitlist" method="post" action="{action}">
<h3>Tell me when Team opens</h3>
<input type="hidden" name="plan" value="team">
<select name="team_role" aria-label="Your role" required>
{_options(ROLES, "Your role")}
</select>
<select name="team_size" aria-label="How many farm clients" required>
{_options(SIZES, "How many farm clients?")}
</select>
<input type="email" name="email" placeholder="you@example.com" aria-label="Work email" required>
<input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px">
<button type="submit">Join the Team waitlist</button>
<p class="note">Nothing is charged. We store your email, role and client-count range, and reply with a price. You also get the free Monday brief.</p>
</form>"""


def render(env=None) -> str:
    """The team page body (goes between the nav and </body>)."""
    env = os.environ if env is None else env
    faq_html = "\n".join(f"<h3>{html.escape(q)}</h3>\n<p>{html.escape(a)}</p>" for q, a in FAQ)
    soon = "" if checkout_live(env) else ' <span class="soon">(coming soon)</span>'
    features = "<ul>\n" + "\n".join(f"<li>{html.escape(f)}</li>" for f in TEAM_FEATURES) + "\n</ul>"
    return f"""<h1>The Cost Wire for ag businesses</h1>
<p>For lenders, agronomists and co-ops who go over input costs with many farmers: the same published USDA and EIA prices, by state, with an alert when they move.</p>
<div class="plans">
<section class="plan">
<h2>Team{soon}</h2>
<p class="price">{html.escape(price_text())}</p>
{features}
{checkout_button(env)}
{form(env)}
<p><a href="state/index.html">Preview the state editions</a> · <a href="pro-sample.html">See a sample alert</a> · <a href="worksheet.html">Try the worksheet</a> · <a href="pricing.html">Farmer plans (Free and Pro)</a></p>
</section>
</div>
<h2>Questions</h2>
{faq_html}
<p class="note">Data: USDA and EIA. Data, not advice. The Cost Wire reports published prices; it does not tell anyone what to buy or sell.</p>"""


# ---- tally (counts only) ----

ROLE_KEYS = [v for v, _ in ROLES]
SIZE_KEYS = [v for v, _ in SIZES]


def parse(sheet_rows) -> dict:
    """Sheet rows -> {email: {"role", "size"}} for team rows, newest row wins."""
    out = {}
    for row in sheet_rows:
        if (row.get("plan") or "").strip().lower() != "team":
            continue
        email = (row.get("email") or "").strip().lower()
        if not _email_ok(email):
            continue
        role = (row.get("team_role") or "").strip().lower()
        size = (row.get("team_size") or "").strip()
        out[email] = {"role": role if role in ROLE_KEYS else "",
                      "size": size if size in SIZE_KEYS else ""}
    return out


def tally(answers: dict) -> dict:
    t = {"total": len(answers), "role": {}, "size": {}}
    for v in answers.values():
        t["role"][v["role"]] = t["role"].get(v["role"], 0) + 1
        t["size"][v["size"]] = t["size"].get(v["size"], 0) + 1
    return t


def report(t: dict) -> str:
    def part(counts, pairs):
        bits = [f"{label} {counts[k]}" for k, label in pairs if k in counts]
        if "" in counts:
            bits.append(f"not given {counts['']}")
        return ", ".join(bits) or "none yet"
    return "\n".join([
        f"Team waitlist: {t['total']} business(es).",
        "By role: " + part(t["role"], ROLES),
        "By size: " + part(t["size"], SIZES),
        "Counts only; no emails or names shown. Andy replies to each with a price before anything is charged.",
    ])


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: python -m costwire.team <sheet.csv>")
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
