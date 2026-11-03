"""The weekly job: pull prices, work out changes, write the brief, build the site.

This is what the GitHub Actions weekly job runs (every Monday, 6 AM Central).
You can also run it by hand:  python -m costwire.weekly

Rules:
- A failed pull doesn't stop the build: the brief and site are rebuilt from
  whatever real prices are already saved (never guessed).
- If there are no saved prices at all, it stops with an error (exit code 1).

The schedule check:  python -m costwire.weekly --check-time
GitHub's timer only speaks UTC and doesn't know about daylight saving time, so
the workflow fires at both 11:00 and 12:00 UTC on Mondays. This check says
"go" only when it's Monday, 6 AM or later, in Central time. That gives one run
at 6 AM Central all year (the other firing is either 5 AM, skipped, or a
harmless re-run at 7 AM that finds nothing new).
"""

import argparse
import sys
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from . import brief, changes, pull_fertilizer, site

CENTRAL = ZoneInfo("America/Chicago")
RUN_WEEKDAY = 0  # Monday
RUN_HOUR = 6     # 6 AM Central


def should_run(now_utc: datetime) -> bool:
    """True if it's Monday, 6 AM or later, Central time."""
    local = now_utc.astimezone(CENTRAL)
    return local.weekday() == RUN_WEEKDAY and local.hour >= RUN_HOUR


def run(brief_date: date, steps=None) -> int:
    """Run the weekly steps in order. Returns 0 if the brief and site got built."""
    steps = steps or {
        "pull": pull_fertilizer.main,
        "changes": changes.main,
        "brief": lambda: brief.main(["--date", brief_date.isoformat()]),
        "site": site.main,
    }
    pull_code = steps["pull"]()
    if pull_code != 0:
        print("Every price pull failed this week; building from the prices already saved.",
              file=sys.stderr)
    for name in ("changes", "brief", "site"):
        code = steps[name]()
        if code != 0:
            print(f"Weekly build stopped: the {name} step failed.", file=sys.stderr)
            return code
    print(f"Weekly build done for {brief_date.isoformat()}.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the weekly Cost Wire build.")
    parser.add_argument("--check-time", action="store_true",
                        help="only print 'run=true' or 'run=false' (is it Monday 6 AM+ Central?)")
    parser.add_argument("--date", type=date.fromisoformat, default=None,
                        help="brief date YYYY-MM-DD (default: today, Central time)")
    args = parser.parse_args(argv)
    if args.check_time:
        print(f"run={'true' if should_run(datetime.now(timezone.utc)) else 'false'}")
        return 0
    return run(args.date or brief.today_central())


if __name__ == "__main__":
    sys.exit(main())
