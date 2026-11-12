import pytest

from watcher import convert
from tests.helpers import SOURCES


def test_greenhouse_to_common_columns():
    raw = {"jobs": [{"id": 123, "title": "  Data   Analyst ", "location": {"name": "Remote"},
                     "absolute_url": "https://x.test/1",
                     "first_published": "2026-01-02T10:00:00-05:00",
                     "departments": [{"name": "Finance"}]}]}
    rows = convert.convert(SOURCES["gh"], raw)
    assert rows == [{
        "posting_id": "gh:123", "source": "gh", "source_id": "123", "employer": "GH Co",
        "title": "Data Analyst", "location": "Remote", "department": "Finance",
        "posted_date": "2026-01-02", "url": "https://x.test/1", "in_role": True,
    }]
    assert list(rows[0]) == convert.COLUMNS


def test_greenhouse_missing_optional_columns_are_empty():
    rows = convert.convert(SOURCES["gh"], {"jobs": [{"id": 5, "title": "Cook"}]})
    assert rows[0]["department"] == "" and rows[0]["posted_date"] == ""
    assert rows[0]["location"] == "" and rows[0]["in_role"] is False


def test_lever_to_common_columns():
    raw = [{"id": "abc", "text": "Financial Analyst", "hostedUrl": "https://l.test/abc",
            "createdAt": 1767225600000,
            "categories": {"location": "NYC", "department": "Finance"}}]
    rows = convert.convert(SOURCES["lv"], raw)
    assert rows == [{
        "posting_id": "lv:abc", "source": "lv", "source_id": "abc", "employer": "LV Co",
        "title": "Financial Analyst", "location": "NYC", "department": "Finance",
        "posted_date": "2026-01-01", "url": "https://l.test/abc", "in_role": True,
    }]


def test_ashby_to_common_columns_skips_unlisted():
    src = {"name": "ab", "employer": "AB Co", "ats": "ashby", "token": "ab"}
    raw = {"jobs": [
        {"id": "u1", "title": "BI Analyst", "location": "Austin", "department": "Data",
         "publishedAt": "2026-02-03T12:00:00.000+00:00", "jobUrl": "https://a.test/u1",
         "isListed": True},
        {"id": "u2", "title": "Hidden", "isListed": False},
    ]}
    rows = convert.convert(src, raw)
    assert [r["posting_id"] for r in rows] == ["ab:u1"]
    assert rows[0]["posted_date"] == "2026-02-03" and rows[0]["in_role"] is True


@pytest.mark.parametrize("ats,raw", [("greenhouse", []), ("lever", {}), ("ashby", [])])
def test_unexpected_shape_raises(ats, raw):
    src = {"name": "x", "employer": "X", "ats": ats, "token": "x"}
    with pytest.raises(ValueError):
        convert.convert(src, raw)


@pytest.mark.parametrize("title,expected", [
    ("Data Analyst", True),
    ("Senior Financial Analyst, FP&A", True),
    ("FP&A Analyst", True),
    ("business intelligence analyst", True),
    ("BI Analyst II", True),
    ("Finance Analysts", True),
    ("Data Engineer", False),            # no "analyst"
    ("Security Analyst", False),         # analyst but no focus word
    ("Metadata Analyst", False),         # "data" only inside a word
    ("Bias Analyst", False),             # "bi" only inside a word
    ("", False),
])
def test_title_rule(title, expected):
    assert convert.in_role(title) is expected
