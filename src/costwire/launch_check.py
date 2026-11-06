"""Launch check: what is ready and what is still missing before The Cost Wire goes live.

Run:  python -m costwire.launch_check          (prints a checklist, always exits 0)
      python -m costwire.launch_check --strict (exits 1 if anything is missing)

It only looks at things it can see on this computer (saved data, the newest
brief, the built site, settings in the environment). It cannot see GitHub
secrets or Pages settings; docs/launch-checklist.md covers those.
"""

import argparse
import csv
import os
import sys

from . import accuracy
from .paths import BRIEFS_DIR, DATA_DIR, SITE_DIR


def _rows(path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_checks(data_dir=None, briefs_dir=None, site_dir=None, env=None) -> list[tuple[str, bool, str]]:
    """Return (name, ok, what-to-do-if-not) for each launch item."""
    data_dir = data_dir or DATA_DIR
    briefs_dir = briefs_dir or BRIEFS_DIR
    site_dir = site_dir or SITE_DIR
    env = os.environ if env is None else env

    prices = _rows(data_dir / "fertilizer.csv")
    items = {r["item"] for r in prices}
    regions = {r.get("region", "") for r in prices}
    briefs = sorted(briefs_dir.glob("*.md")) if briefs_dir.exists() else []

    checks = []

    def add(name, ok, todo):
        checks.append((name, bool(ok), todo))

    add("Fertilizer prices saved (Iowa)", "IA" in regions or any(
        r["source_url"].endswith("ams_2863.pdf") for r in prices),
        "Run python -m costwire.pull_fertilizer")
    add("Fertilizer prices saved (Illinois)", "IL" in regions or any(
        r["source_url"].endswith("ams_3195.pdf") for r in prices),
        "Run python -m costwire.pull_fertilizer")
    add("Midwest diesel + propane from EIA", bool({r["source_url"] for r in prices if "eia.gov" in r["source_url"]}),
        "Add the EIA_API_KEY secret (see docs/launch-checklist.md)")
    add("Feed line (DDGS) has real prices", "ddgs" in items,
        "Step 10b: upload tests/samples/ams_3618.pdf")
    add("Cash rent + land values saved", bool(_rows(data_dir / "land.csv")),
        "Add the NASS_API_KEY secret (see docs/launch-checklist.md)")
    add("A weekly brief exists", bool(briefs), "Run python -m costwire.weekly")

    ok_acc = False
    if briefs:
        try:
            ok_acc = accuracy.main(["--brief", str(briefs[-1])]) == 0
        except Exception:  # an unreadable brief counts as a fail, not a crash
            ok_acc = False
    add("Accuracy check passes on the newest brief", ok_acc, "Run python -m costwire.accuracy and fix what it lists")

    add("Website built (home, archive, cash rent)",
        all((site_dir / p).exists() for p in ("index.html", "archive.html", "cash-rent.html")),
        "Run python -m costwire.site")
    add("Test email key set (RESEND_API_KEY + BRIEF_TEST_EMAIL)",
        env.get("RESEND_API_KEY") and env.get("BRIEF_TEST_EMAIL"),
        "Only needed on the computer you send the test from")
    add("Signup form is live (SIGNUP_FORM_URL + SIGNUP_LIVE=yes)",
        (env.get("SIGNUP_FORM_URL") or "").startswith("https://")
        and (env.get("SIGNUP_LIVE") or "").strip().lower() == "yes",
        "Andy's go-ahead step: docs/signup-google-sheet.md")
    return checks


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--strict", action="store_true", help="exit 1 if anything is missing")
    args = p.parse_args(argv)
    checks = run_checks()
    for name, ok, todo in checks:
        print(f"[{'x' if ok else ' '}] {name}" + ("" if ok else f"  ->  {todo}"))
    missing = sum(1 for _, ok, _ in checks if not ok)
    print(f"\n{len(checks) - missing} of {len(checks)} ready.")
    return 1 if (args.strict and missing) else 0


if __name__ == "__main__":
    sys.exit(main())
