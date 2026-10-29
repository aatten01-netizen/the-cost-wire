"""Where things live in the project. Everything else imports from here."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"    # clean CSV/JSON from the weekly pulls
SITE_DIR = ROOT / "site"    # the static website we publish
TESTS_DIR = ROOT / "tests"
