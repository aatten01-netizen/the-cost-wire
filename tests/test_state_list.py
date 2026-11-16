import csv

import pytest

from costwire import site, state_list


def test_dropdown_has_states_and_blank_default():
    opts = state_list.options_html()
    assert opts.startswith('<option value="">')  # nothing picked by default
    for st in ["IA", "IL", "MN", "WI"]:
        assert f'value="{st}"' in opts
    assert "Iowa" in opts and "Wisconsin" in opts and "Other / skip" in opts


def test_placeholder_box_has_disabled_state_choice():
    box = site.signup_box({})
    assert "<select" in box and 'name="state"' not in box  # placeholder sends nothing
    assert box.count("disabled") >= 3


def test_live_box_posts_state():
    env = {"SIGNUP_FORM_URL": "https://script.google.com/macros/s/ABC/exec", "SIGNUP_LIVE": "yes"}
    box = site.signup_box(env)
    assert '<select name="state"' in box and "disabled" not in box
    assert "required" not in box.split('<select name="state"')[1].split(">")[0]  # optional
    assert "{state_options}" not in box


def test_clean_state():
    assert state_list.clean_state(" ia ") == "IA"
    assert state_list.clean_state("NE") == ""
    assert state_list.clean_state(None) == ""


def test_parse_readers_newest_wins_and_alert_row_keeps_state():
    rows = [
        {"email": "A@farm.com", "state": "IA"},
        {"email": "b@farm.com", "state": ""},
        {"email": "bad-email", "state": "IL"},
        {"email": "c@farm.com", "state": "TX"},
        {"email": "a@farm.com", "state": "", "alert_item": "anhydrous", "alert_region": "IA"},
        {"email": "b@farm.com", "state": "wi"},
    ]
    readers = state_list.parse_readers(rows)
    assert readers == [
        {"email": "c@farm.com", "state": ""},
        {"email": "a@farm.com", "state": "IA"},
        {"email": "b@farm.com", "state": "WI"},
    ]
    assert state_list.counts(readers) == {"IA": 1, "": 1, "WI": 1}


def test_export_writes_outside_repo(tmp_path):
    sheet = tmp_path / "sheet.csv"
    sheet.write_text("time,email,alert_item,alert_region,alert_threshold,state\n"
                     "2026-11-16,x@farm.com,,,,MN\n")
    out = tmp_path / "readers.csv"
    assert state_list.main([str(sheet), str(out)]) == 0
    with open(out) as f:
        assert list(csv.DictReader(f)) == [{"email": "x@farm.com", "state": "MN"}]


def test_old_sheet_without_state_column(tmp_path):
    sheet = tmp_path / "sheet.csv"
    sheet.write_text("time,email\n2026-11-16,y@farm.com\n")
    out = tmp_path / "readers.csv"
    readers = state_list.export(sheet, out)
    assert readers == [{"email": "y@farm.com", "state": ""}]


def test_export_refuses_inside_repo(tmp_path):
    sheet = tmp_path / "sheet.csv"
    sheet.write_text("email,state\nz@farm.com,IA\n")
    from costwire.paths import ROOT
    with pytest.raises(ValueError):
        state_list.export(sheet, ROOT / "readers.csv")
    assert not (ROOT / "readers.csv").exists()
