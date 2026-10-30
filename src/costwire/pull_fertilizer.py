"""Pull every state's fertilizer + fuel report into data/fertilizer.csv.

One state failing (site down, format changed) doesn't stop the others.
Exit code is 1 only if every state failed.

Run it:  python -m costwire.pull_fertilizer
"""

import sys

from . import illinois_cost, iowa_cost

PULLERS = [
    ("Iowa", iowa_cost.pull),
    ("Illinois", illinois_cost.pull),
]


def pull_all(pullers=None) -> dict:
    """Run each puller. Returns {state: list of records, or the error}."""
    results = {}
    for state, pull in pullers or PULLERS:
        try:
            results[state] = pull()
        except Exception as exc:
            print(f"{state} pull failed: {exc}", file=sys.stderr)
            results[state] = exc
    return results


def main(pullers=None) -> int:
    results = pull_all(pullers)
    worked = [s for s, r in results.items() if not isinstance(r, Exception)]
    return 0 if worked else 1


if __name__ == "__main__":
    sys.exit(main())
