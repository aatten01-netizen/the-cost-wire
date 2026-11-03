from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from costwire import weekly

ROOT = Path(__file__).resolve().parents[1]


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


# ---------- schedule check ----------

def test_winter_noon_utc_is_6am_central_monday():
    # Mon Jan 5 2026, 12:00 UTC = 6:00 AM CST
    assert weekly.should_run(utc(2026, 1, 5, 12, 0))


def test_winter_11_utc_is_5am_so_skip():
    assert not weekly.should_run(utc(2026, 1, 5, 11, 0))


def test_summer_11_utc_is_6am_central_monday():
    # Mon Jul 6 2026, 11:00 UTC = 6:00 AM CDT
    assert weekly.should_run(utc(2026, 7, 6, 11, 0))


def test_late_github_start_still_runs():
    # GitHub sometimes starts scheduled jobs late; 7:40 AM CST is still fine
    assert weekly.should_run(utc(2026, 1, 5, 13, 40))


def test_not_monday_in_central():
    # Tue Jan 6 2026 12:00 UTC
    assert not weekly.should_run(utc(2026, 1, 6, 12, 0))
    # Mon 03:00 UTC is still Sunday evening in Chicago
    assert not weekly.should_run(utc(2026, 1, 5, 3, 0))


def test_check_time_prints_flag(capsys):
    assert weekly.main(["--check-time"]) == 0
    assert capsys.readouterr().out.strip() in ("run=true", "run=false")


# ---------- running the steps ----------

def fake_steps(codes, calls):
    def make(name):
        def step():
            calls.append(name)
            return codes.get(name, 0)
        return step
    return {n: make(n) for n in ("pull", "changes", "brief", "site")}


def test_runs_all_steps_in_order():
    calls = []
    assert weekly.run(date(2026, 11, 9), fake_steps({}, calls)) == 0
    assert calls == ["pull", "changes", "brief", "site"]


def test_failed_pull_still_builds_from_saved_prices():
    calls = []
    assert weekly.run(date(2026, 11, 9), fake_steps({"pull": 1}, calls)) == 0
    assert calls == ["pull", "changes", "brief", "site"]


def test_stops_when_no_saved_prices():
    calls = []
    assert weekly.run(date(2026, 11, 9), fake_steps({"changes": 1}, calls)) == 1
    assert calls == ["pull", "changes"]


# ---------- the workflow file ----------

def load_workflow():
    return yaml.safe_load((ROOT / ".github/workflows/weekly.yml").read_text())


def test_workflow_schedule_covers_both_central_offsets():
    wf = load_workflow()
    on = wf.get("on", wf.get(True))  # PyYAML reads bare `on:` as True
    crons = {s["cron"] for s in on["schedule"]}
    assert crons == {"0 11 * * 1", "0 12 * * 1"}
    assert "workflow_dispatch" in on


def test_workflow_uses_secret_not_a_key():
    text = (ROOT / ".github/workflows/weekly.yml").read_text()
    assert "${{ secrets.EIA_API_KEY }}" in text
    assert "python -m costwire.weekly" in text
    assert "python -m pytest" in text


def test_deploy_waits_for_andy_to_turn_pages_on():
    wf = load_workflow()
    deploy = wf["jobs"]["deploy"]
    assert "PAGES_ENABLED" in deploy["if"]
    assert deploy["needs"] == "build"
