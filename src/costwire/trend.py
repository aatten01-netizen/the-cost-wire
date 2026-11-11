"""12-week price trend: a small line chart per fertilizer for the brief page.

Built only from the saved prices (data/fertilizer.csv). No new data source.
For each fertilizer series (same item, region, unit and source report) we take
every saved price from the newest date back 12 weeks (84 days). A line needs at
least 2 saved dates; with fewer, the trend is left out (never filled in).

Each trend comes with one plain sentence (first price, newest price, low and
high, with dates) so the numbers on the chart can be checked against the data.
The sentence goes in the Markdown brief (checked by the accuracy check) and
under the chart on the HTML page.
"""

import html
from datetime import timedelta

from . import changes

WINDOW = timedelta(weeks=12)
FERTILIZERS = ("anhydrous", "urea", "uan28", "uan32", "dap", "map", "potash")

# chart size in pixels
WIDTH, HEIGHT, PAD = 240, 56, 6


def series_points(rows: list[dict], result: dict) -> list[tuple]:
    """(date, price) pairs for this result's series, last 12 weeks, oldest first.

    If one date was saved twice, the last saved row wins (a re-pull of the same report).
    """
    key = changes.series_key(result)
    start = result["as_of"] - WINDOW
    by_date = {}
    for r in rows:
        if changes.series_key(r) == key and start <= r["as_of"] <= result["as_of"]:
            by_date[r["as_of"]] = r["price"]
    return sorted(by_date.items())


def compute(results: list[dict], rows: list[dict]) -> list[dict]:
    """One trend per fertilizer result that has 2+ saved dates in the window."""
    out = []
    for res in results:
        if res["item"] not in FERTILIZERS:
            continue
        points = series_points(rows, res)
        if len(points) < 2:
            continue
        low = min(points, key=lambda p: (p[1], p[0]))    # ties: earliest date
        high = max(points, key=lambda p: (p[1], -p[0].toordinal()))
        out.append({"item": res["item"], "region": res["region"], "unit": res["unit"],
                    "source_name": res["source_name"], "source_url": res["source_url"],
                    "points": points, "low": low, "high": high})
    return out


def svg(points: list[tuple], label: str) -> str:
    """Inline SVG line chart. Flat prices draw a flat line across the middle."""
    prices = [p for _, p in points]
    lo, hi = min(prices), max(prices)
    first_day = points[0][0].toordinal()
    span_days = max(points[-1][0].toordinal() - first_day, 1)
    inner_w, inner_h = WIDTH - 2 * PAD, HEIGHT - 2 * PAD
    coords = []
    for d, p in points:
        x = PAD + (d.toordinal() - first_day) / span_days * inner_w
        y = PAD + inner_h / 2 if hi == lo else PAD + (hi - p) / (hi - lo) * inner_h
        coords.append((round(x, 1), round(y, 1)))
    line = " ".join(f"{x},{y}" for x, y in coords)
    last_x, last_y = coords[-1]
    e = html.escape
    return (f'<svg class="trend" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{e(label)}">'
            f'<title>{e(label)}</title>'
            f'<polyline points="{line}" fill="none" stroke="#2b6a3f" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="#2b6a3f"/></svg>')
