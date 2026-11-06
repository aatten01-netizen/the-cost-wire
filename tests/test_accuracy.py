from datetime import date

from costwire import accuracy, brief, changes

HEADER = "item,region,unit,price,as_of,source_name,source_url\n"
GOOD = "urea,IL,$/ton,770.0,2026-10-30,USDA AMS Illinois Production Cost Report,https://www.ams.usda.gov/mnreports/ams_3195.pdf\n"
TODAY = date(2026, 11, 6)


def write(tmp_path, body):
    p = tmp_path / "f.csv"
    p.write_text(HEADER + body)
    return p


def make_brief(path):
    results = changes.compute(changes.read_rows(path))
    return brief.to_markdown(brief.build(results, date(2026, 11, 2))), results


def test_good_data_passes(tmp_path):
    assert accuracy.check_data(write(tmp_path, GOOD), TODAY) == []


def test_data_problems_are_flagged(tmp_path):
    bad = (",IL,$/ton,abc,2026-13-01,,http://x\n"
           "urea,IA,,-5,2027-01-01,Name,https://x.gov\n")
    text = " ".join(accuracy.check_data(write(tmp_path, bad), TODAY))
    for word in ("no item", "not a number", "not YYYY-MM-DD", "no source name",
                 "not https", "no unit", "not above zero", "future"):
        assert word in text


def test_missing_data_file(tmp_path):
    assert accuracy.check_data(tmp_path / "nope.csv", TODAY)


def test_matching_brief_passes(tmp_path):
    md, results = make_brief(write(tmp_path, GOOD))
    assert accuracy.check_brief(md, results) == []


def test_wrong_price_in_brief_is_caught(tmp_path):
    md, results = make_brief(write(tmp_path, GOOD))
    problems = accuracy.check_brief(md.replace("$770.00/ton", "$707.00/ton"), results)
    assert any("price says '$707.00/ton'" in p for p in problems)


def test_changed_source_and_date_caught(tmp_path):
    md, results = make_brief(write(tmp_path, GOOD))
    md2 = md.replace("Oct 30, 2026", "Oct 31, 2026", 1)
    assert any("date says" in p for p in accuracy.check_brief(md2, results))


def test_row_missing_or_invented(tmp_path):
    md, results = make_brief(write(tmp_path, GOOD))
    lines = [l for l in md.splitlines() if not l.startswith("| Urea")]
    assert any("missing from the brief" in p for p in accuracy.check_brief("\n".join(lines), results))
    extra = md.replace("\n\nn/a =", "\n| DAP | Illinois | $1.00/ton | n/a | n/a | Oct 30, 2026 | [x](https://x.gov) |\n\nn/a =")
    assert any("not in the saved data" in p for p in accuracy.check_brief(extra, results))


def test_missing_sources_and_disclaimer(tmp_path):
    md, results = make_brief(write(tmp_path, GOOD))
    problems = accuracy.check_brief(md.split("## Sources")[0], results)
    assert any("Sources section" in p for p in problems)
    assert any("disclaimer" in p for p in problems)


def test_change_needs_earlier_source(tmp_path):
    md, results = make_brief(write(tmp_path, GOOD))
    results[0]["change_2w"], results[0]["source_url_2w"] = 5.0, ""
    results[0]["as_of_2w"] = None
    assert any("earlier price" in p for p in accuracy.check_brief(md, results))


def test_run_checks_end_to_end_and_main_exit_code(tmp_path, capsys):
    data = write(tmp_path, GOOD)
    md, _ = make_brief(data)
    b = tmp_path / "2026-11-02.md"
    b.write_text(md)
    assert accuracy.run_checks(b, data, TODAY) == []
    b.write_text(md.replace("$770.00", "$1.00"))
    assert accuracy.run_checks(b, data, TODAY)
    assert accuracy.main(["--brief", str(tmp_path / "missing.md")]) == 1
    assert "FAILED" in capsys.readouterr().err
