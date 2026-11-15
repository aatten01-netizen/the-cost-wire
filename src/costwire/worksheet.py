"""Cost-per-acre worksheet (a Pro feature on the pricing page).

Writes site/worksheet.html (called from site.build_site), linked from pricing.html.

The farmer picks a state and types their OWN rates per acre (lb/acre for
fertilizer, gal/acre for farm diesel). The page multiplies each rate by the
newest published USDA AMS price and adds up a total $/acre:

  fertilizer: $/acre = price ($/ton) x rate (lb/acre) / 2,000
  farm diesel: $/acre = price ($/gal) x rate (gal/acre)

A farmer can also type their own quote for any line; then that line uses
their quote and says so. Everything they type stays in their browser: the
page has no form submit and sends nothing anywhere.

Product rules:
- Never guess a number: there are NO default rates (rates are the farmer's),
  and a product with no saved published price is left out of the list.
- Every published price shows its report date and source link.
- Data, not advice: the page does math on numbers; it never suggests a rate
  or a product.
"""

import html
import json
import math

from . import changes
from .brief import item_name, region_name, short_date

# item -> rate unit typed by the farmer; price unit must match
ITEMS = {
    "anhydrous": ("$/ton", "lb/acre"),
    "urea": ("$/ton", "lb/acre"),
    "uan28": ("$/ton", "lb/acre"),
    "uan32": ("$/ton", "lb/acre"),
    "dap": ("$/ton", "lb/acre"),
    "map": ("$/ton", "lb/acre"),
    "potash": ("$/ton", "lb/acre"),
    "diesel": ("$/gal", "gal/acre"),
}
STATES = ["IA", "IL"]
LB_PER_TON = 2000


def line_cost(price: float, unit: str, rate: float) -> float:
    """Dollars per acre for one product (not rounded; round when shown)."""
    if unit == "$/ton":
        return price * rate / LB_PER_TON
    if unit == "$/gal":
        return price * rate
    raise ValueError(f"unknown unit {unit}")


def money(value: float) -> str:
    """Same rounding as the page's JavaScript (toFixed(2))."""
    return f"${value:,.2f}"


def _usable(price) -> bool:
    return isinstance(price, (int, float)) and math.isfinite(price) and price > 0


def price_options(rows: list[dict]) -> dict:
    """{state: [one dict per product]} from the newest published price of each.

    If one item/state has prices from two sources, the newest date wins
    (ties: source name, so the pick never depends on file order).
    """
    best = {}
    for r in changes.compute(rows):
        item, region = r["item"], r["region"]
        if item not in ITEMS or region not in STATES:
            continue
        if r["unit"] != ITEMS[item][0] or not _usable(r["price"]):
            continue
        key = (region, item)
        rank = (r["as_of"], r["source_name"])
        if key not in best or rank > best[key][0]:
            best[key] = (rank, r)
    out = {}
    for state in STATES:
        lines = []
        for item in ITEMS:
            if (state, item) not in best:
                continue
            r = best[(state, item)][1]
            lines.append({"item": item, "name": item_name(item), "price": r["price"],
                          "unit": r["unit"], "rate_unit": ITEMS[item][1],
                          "as_of": r["as_of"].isoformat(), "as_of_text": short_date(r["as_of"]),
                          "source_name": r["source_name"], "source_url": r["source_url"]})
        if lines:
            out[state] = lines
    return out


# The page's math. Kept tiny and in one place so a test can run it with Node
# and check it matches line_cost() above.
CALC_JS = """
function lineCost(price, unit, rate) {
  if (unit === "$/ton") return price * rate / 2000;
  if (unit === "$/gal") return price * rate;
  return NaN;
}
function money(v) {
  return "$" + v.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ",");
}
"""

PAGE_JS = """
(function () {
  var data = JSON.parse(document.getElementById("ws-data").textContent);
  var pick = document.getElementById("ws-state");
  var body = document.getElementById("ws-body");
  var total = document.getElementById("ws-total");
  function num(el) {
    var t = el.value.trim();
    if (t === "") return null;
    var v = Number(t);
    return (isFinite(v) && v >= 0) ? v : NaN;
  }
  function cell(row, label) {
    var td = row.insertCell();
    td.setAttribute("data-label", label);
    return td;
  }
  function draw() {
    body.innerHTML = "";
    data[pick.value].forEach(function (p) {
      var tr = body.insertRow();
      cell(tr, "Product").textContent = p.name;
      var pub = cell(tr, "Published price");
      pub.appendChild(document.createTextNode(money(p.price) + "/" + p.unit.slice(2) + ", " + p.as_of_text + " "));
      var a = document.createElement("a");
      a.href = p.source_url; a.textContent = "(source)"; a.title = p.source_name;
      pub.appendChild(a);
      var r = document.createElement("input");
      r.type = "number"; r.min = "0"; r.step = "any"; r.inputMode = "decimal";
      r.setAttribute("aria-label", "Your rate for " + p.name + " (" + p.rate_unit + ")");
      r.className = "rate";
      var rc = cell(tr, "Your rate (" + p.rate_unit + ")");
      rc.appendChild(r);
      var q = document.createElement("input");
      q.type = "number"; q.min = "0"; q.step = "any"; q.inputMode = "decimal";
      q.setAttribute("aria-label", "Your own quote for " + p.name + " (" + p.unit + "), optional");
      q.className = "quote";
      cell(tr, "Your quote (" + p.unit + ", optional)").appendChild(q);
      var out = cell(tr, "$/acre");
      out.className = "cost";
      r.oninput = q.oninput = sum;
      tr._p = p; tr._r = r; tr._q = q; tr._out = out;
    });
    sum();
  }
  function sum() {
    var t = 0, n = 0, bad = false;
    Array.prototype.forEach.call(body.rows, function (tr) {
      var rate = num(tr._r), quote = num(tr._q);
      if (rate === null) { tr._out.textContent = ""; return; }
      if (isNaN(rate) || isNaN(quote)) { tr._out.textContent = "check number"; bad = true; return; }
      var price = (quote !== null && quote > 0) ? quote : tr._p.price;
      var c = lineCost(price, tr._p.unit, rate);
      t += c; n += 1;
      tr._out.textContent = money(c) + ((quote !== null && quote > 0) ? " (your quote)" : "");
    });
    total.textContent = n ? money(t) + " per acre (" + n + " product" + (n > 1 ? "s" : "") + ")" + (bad ? ", some lines skipped" : "")
                          : "Type a rate to see your cost per acre.";
  }
  pick.onchange = draw;
  document.getElementById("ws-js").hidden = false;
  document.getElementById("ws-nojs").hidden = true;
  draw();
})();
"""


def _static_table(state: str, lines: list[dict]) -> str:
    """Plain list of published prices, shown if JavaScript is off."""
    rows = "\n".join(
        f"<li>{html.escape(region_name(state))} {html.escape(p['name'])}: "
        f"{money(p['price'])}/{html.escape(p['unit'][2:])}, {html.escape(p['as_of_text'])} "
        f"(<a href=\"{html.escape(p['source_url'], quote=True)}\">{html.escape(p['source_name'])}</a>)</li>"
        for p in lines)
    return f"<ul>\n{rows}\n</ul>"


def render(rows: list[dict]) -> str:
    """The worksheet page body (goes between the nav and </body>)."""
    intro = ("<h1>Cost-per-acre worksheet</h1>\n"
             "<p>Type your own rates per acre. The worksheet multiplies each one by the newest "
             "published USDA price for your state and adds up your cost per acre. "
             "Got your own quote? Type it in and that line uses your number instead.</p>\n"
             '<p class="note">Pro preview: free to try while Pro is not open '
             '(<a href="pricing.html">Pricing</a>).</p>')
    rules = ('<p class="note">Data, not advice. This is math on numbers: the published prices '
             "are government averages and the rates are yours. It does not suggest a rate or a "
             "product. What you type stays in your browser; this page sends nothing anywhere.</p>")
    data = price_options(rows)
    if not data:
        return (f"{intro}\n<p>No published prices are saved yet, so the worksheet has nothing "
                f"to work with. We don't make prices up.</p>\n{rules}")
    options = "\n".join(f'<option value="{s}">{html.escape(region_name(s))}</option>' for s in data)
    nojs = "\n".join(f"<h2>{html.escape(region_name(s))}</h2>\n{_static_table(s, l)}"
                     for s, l in data.items())
    sources = {}
    for lines in data.values():
        for p in lines:
            sources.setdefault(p["source_url"], (p["source_name"], set()))[1].add(p["as_of_text"])
    src_list = "\n".join(
        f'<li><a href="{html.escape(u, quote=True)}">{html.escape(n)}</a>, report dated '
        f'{html.escape(", ".join(sorted(d)))}</li>' for u, (n, d) in sources.items())
    # "</" is escaped so the JSON can never close the <script> tag early
    blob = json.dumps(data).replace("</", "<\\/")
    return f"""{intro}
<div id="ws-js" hidden>
<p><label for="ws-state">State:</label> <select id="ws-state">
{options}
</select></p>
<table class="ws">
<thead><tr><th>Product</th><th>Published price</th><th>Your rate</th><th>Your quote (optional)</th><th>$/acre</th></tr></thead>
<tbody id="ws-body"></tbody>
</table>
<p class="ws-total">Total: <strong id="ws-total">Type a rate to see your cost per acre.</strong></p>
<p class="note">Rates: fertilizer in pounds of product per acre (not pounds of N), farm diesel in gallons per acre. Products with no published price for a state are left out.</p>
</div>
<div id="ws-nojs">
<p>The worksheet needs JavaScript. Here are the published prices it uses:</p>
{nojs}
</div>
<h2>Sources</h2>
<ul>
{src_list}
</ul>
{rules}
<script type="application/json" id="ws-data">{blob}</script>
<script>{CALC_JS}{PAGE_JS}</script>"""


WORKSHEET_CSS = """
.ws { border-collapse: collapse; width: 100%; }
.ws th, .ws td { border-bottom: 1px solid #ddd; padding: 0.35rem; text-align: left; vertical-align: top; }
.ws input { width: 6.5rem; font: inherit; }
.ws .cost { font-weight: bold; white-space: nowrap; }
.ws-total { font-size: 1.15rem; }
.note { color: #555; font-size: 0.9rem; }
@media (max-width: 600px) {
  .ws thead { display: none; }
  .ws tr { display: block; border: 1px solid #ddd; margin-bottom: 0.6rem; padding: 0.3rem; }
  .ws td { display: block; border: none; padding: 0.2rem 0.3rem; }
  .ws td::before { content: attr(data-label) ": "; font-weight: bold; }
}
"""
