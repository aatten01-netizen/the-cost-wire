"""Pricing page: what is free, what Pro will cost, and the (mock) checkout button.

Writes site/pricing.html (called from site.build_site).

The Pro checkout button is a MOCK (disabled, nothing is sold) UNLESS both env
vars are set at build time:
  PRO_CHECKOUT_URL   a Stripe Payment Link (must start with https://buy.stripe.com/)
  PRO_CHECKOUT_LIVE  yes   (Andy's go-ahead, only once the Pro features exist)
Anything else (http link, other site, missing flag) keeps the mock button.

Prices below are Andy's to change in one place (PRO_MONTHLY / PRO_YEARLY).
"""

import html
import os

PRO_MONTHLY = 9   # dollars per month (BRIEF.md: paid tier ~$9-15/month)
PRO_YEARLY = 90   # dollars per year (2 months free vs monthly)
CHECKOUT_PREFIX = "https://buy.stripe.com/"

FREE_FEATURES = [
    "Weekly Monday brief: Iowa and Illinois fertilizer, Midwest diesel and propane, distillers grains",
    "Change vs 2 weeks ago and vs 1 year ago, when both prices are published",
    "Cash rent and land value page (USDA NASS)",
    "Every number linked to its USDA or EIA source and date",
    "Archive of past briefs and an RSS feed",
]

PRO_FEATURES = [
    "Your state's numbers first, in a brief built for your state",
    "Email alert when a published price moves more than the amount you pick",
    "Cost-per-acre worksheet using the latest published prices",
    "Everything in Free",
]

FAQ = [
    ("Is Pro open now?",
     "Not yet. The free brief is live today. Pro opens once its features are built. "
     "Nothing on this page charges you."),
    ("Where do the numbers come from?",
     "Public USDA AMS, USDA NASS and EIA reports. Each number shows its source link and date. "
     "If a source is missing, the number is left out."),
    ("Will you tell me when to buy fertilizer?",
     "No. The Cost Wire reports published prices and how they changed. "
     "It is data, not advice. Buying decisions are yours."),
    ("Can I cancel?",
     "Yes, Pro will be month to month (or yearly) with no contract."),
]


def checkout_live(env=None) -> bool:
    """True only when PRO_CHECKOUT_URL is a Stripe Payment Link AND PRO_CHECKOUT_LIVE=yes."""
    env = os.environ if env is None else env
    url = (env.get("PRO_CHECKOUT_URL") or "").strip()
    live = (env.get("PRO_CHECKOUT_LIVE") or "").strip().lower() == "yes"
    return live and url.startswith(CHECKOUT_PREFIX) and len(url) > len(CHECKOUT_PREFIX)


def checkout_button(env=None) -> str:
    env = os.environ if env is None else env
    if checkout_live(env):
        url = html.escape(env["PRO_CHECKOUT_URL"].strip(), quote=True)
        return (f'<a class="buy" href="{url}" rel="noopener">Start Pro, ${PRO_MONTHLY}/month</a>'
                '<p class="note">Secure checkout by Stripe. Cancel any time.</p>')
    return ('<button class="buy" type="button" disabled>Pro is not open yet</button>'
            '<p class="note">Nothing is sold on this page yet. '
            'Free brief readers will be the first told when Pro opens.</p>')


def _ul(items) -> str:
    return "<ul>\n" + "\n".join(f"<li>{html.escape(i)}</li>" for i in items) + "\n</ul>"


def render(env=None) -> str:
    """The pricing page body (goes between the nav and </body>)."""
    faq = "\n".join(f"<h3>{html.escape(q)}</h3>\n<p>{html.escape(a)}</p>" for q, a in FAQ)
    return f"""<h1>Pricing</h1>
<p>The weekly brief is free. Pro is for farmers who want their own state's numbers and an alert when prices move.</p>
<div class="plans">
<section class="plan">
<h2>Free</h2>
<p class="price">$0</p>
{_ul(FREE_FEATURES)}
<a class="buy" href="index.html#signup">Get the free brief</a>
</section>
<section class="plan">
<h2>Pro <span class="soon">(coming soon)</span></h2>
<p class="price">${PRO_MONTHLY}/month or ${PRO_YEARLY}/year</p>
{_ul(PRO_FEATURES)}
{checkout_button(env)}
<p><a href="alerts.html">See the alert choices</a></p>
</section>
</div>
<h2>Questions</h2>
{faq}
<p class="note">Data: USDA and EIA. Data, not advice. The Cost Wire reports published prices; it does not tell anyone what to buy or sell.</p>"""


PRICING_CSS = """
.plans { display: flex; flex-wrap: wrap; gap: 1rem; }
.plan { flex: 1 1 260px; border: 1px solid #ddd; padding: 1rem; background: #fcfcf8; }
.plan .price { font-size: 1.4rem; font-weight: bold; }
.plan .soon { font-size: 0.9rem; font-weight: normal; color: #666; }
.buy { display: inline-block; padding: 0.5rem 1rem; border: 2px solid #222; background: #fff; color: #222; text-decoration: none; font: inherit; }
button.buy[disabled] { color: #888; border-color: #aaa; }
.note { color: #555; font-size: 0.9rem; }
"""
