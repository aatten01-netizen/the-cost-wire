from datetime import date

import pytest

from costwire.records import PriceRecord

GOOD = dict(
    item="anhydrous",
    price=850.0,
    unit="$/ton",
    as_of=date(2026, 10, 23),
    source_url="https://mymarketnews.ams.usda.gov/viewReport/2863",
    source_name="USDA AMS Iowa Production Cost Report",
)


def test_good_record_and_row():
    row = PriceRecord(**GOOD).to_row()
    assert row["as_of"] == "2026-10-23"
    assert row["price"] == 850.0
    assert row["source_url"].startswith("https://")


@pytest.mark.parametrize(
    "field,bad",
    [
        ("source_url", ""),
        ("source_url", "mymarketnews.ams.usda.gov"),
        ("source_name", "  "),
        ("item", ""),
        ("as_of", "2026-10-23"),
        ("price", None),
        ("price", "850"),
        ("price", True),
        ("price", float("nan")),
        ("price", -1.0),
    ],
)
def test_missing_or_bad_fields_are_refused(field, bad):
    with pytest.raises(ValueError):
        PriceRecord(**{**GOOD, field: bad})
