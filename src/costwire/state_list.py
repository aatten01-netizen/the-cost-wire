"""State choice on the free signup, and the per-state reader list.

Two parts:

1. The choice. The free signup box (site.py) has an optional "Your state"
   dropdown: Iowa, Illinois, Minnesota, Wisconsin (the states that have a
   state edition, see state_brief.py), or "Other / skip". It posts a `state`
   field to the same Google Sheet web app (docs/signup-google-sheet.md).

2. The export. Andy downloads the Sheet as CSV to a folder OUTSIDE this repo,
   then runs:
       python -m costwire.state_list /path/signups.csv /path/readers.csv
   That writes `email,state` with one row per reader (their newest signup
   wins). A reader with no state, or a state we don't publish, gets a blank
   state, which means "send the main brief". Bad emails are skipped. The
   export refuses to write inside the repo, because the file holds emails.

Nothing here sends email. It only prepares the list for a later send of each
reader's state edition.
"""

import csv
import html
import sys
from pathlib import Path

from .alert_signup import _inside_repo
from .brief import region_name
from .state_brief import STATES

READER_COLUMNS = ["email", "state"]


def options_html() -> str:
    """<option> tags for the signup dropdown. First one = no state (the default)."""
    out = ['<option value="">Your state (optional)</option>']
    for st in STATES:
        out.append(f'<option value="{st}">{html.escape(region_name(st))}</option>')
    out.append('<option value="">Other / skip</option>')
    return "\n".join(out)


def clean_state(raw) -> str:
    """'ia ' -> 'IA'. Anything not in STATES -> '' (main brief)."""
    st = (raw or "").strip().upper()
    return st if st in STATES else ""


def _email_ok(email: str) -> bool:
    return ("@" in email and "." in email.split("@")[-1] and "," not in email
            and " " not in email and email.count("@") == 1)


def parse_readers(sheet_rows) -> list[dict]:
    """Sheet rows -> one {email, state} per reader, newest row wins.

    An alert-only row with no state keeps the state the reader picked before,
    so setting an alert later never wipes their state choice.
    """
    readers = {}
    for row in sheet_rows:
        email = (row.get("email") or "").strip().lower()
        if not _email_ok(email):
            if email:
                print("WARNING: skipped a signup row with a bad email", file=sys.stderr)
            continue
        state = clean_state(row.get("state"))
        if not state and email in readers:
            state = readers[email]["state"]
        readers.pop(email, None)  # re-insert so the newest signup keeps its place at the end
        readers[email] = {"email": email, "state": state}
    return list(readers.values())


def counts(readers: list[dict]) -> dict:
    """How many readers per state ('' = main brief). For the printout only."""
    out = {}
    for r in readers:
        out[r["state"]] = out.get(r["state"], 0) + 1
    return out


def export(sheet_csv, out_csv) -> list[dict]:
    out_csv = Path(out_csv)
    if _inside_repo(out_csv):
        raise ValueError("Refusing to write reader emails inside the repo. Pick a folder outside it.")
    with open(sheet_csv, newline="", encoding="utf-8-sig") as f:
        readers = parse_readers(csv.DictReader(f))
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=READER_COLUMNS)
        w.writeheader()
        w.writerows(readers)
    return readers


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("Usage: python -m costwire.state_list <sheet.csv> <readers.csv (outside the repo)>")
        return 2
    try:
        readers = export(argv[0], argv[1])
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    c = counts(readers)
    parts = [f"{region_name(st)} {c[st]}" for st in STATES if st in c]
    if "" in c:
        parts.append(f"no state {c['']}")
    print(f"Wrote {len(readers)} reader(s) to {argv[1]}: " + (", ".join(parts) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
