import csv
from datetime import datetime, timezone

from watcher import history, status
from tests.helpers import SOURCES, gh_raw, lv_raw, write_raw

D1, D2, D3 = "2026-01-01", "2026-01-02", "2026-01-03"


def build(raw_dir):
    return {r["posting_id"]: r for r in history.build_history(raw_dir, SOURCES)}


def test_first_seen_last_seen_and_first_run(tmp_path):
    write_raw(tmp_path, D1, "gh", gh_raw(1, 2))
    write_raw(tmp_path, D2, "gh", gh_raw(1, 3))
    rows = build(tmp_path)
    assert rows["gh:1"]["first_seen"] == D1 and rows["gh:1"]["last_seen"] == D2
    assert rows["gh:1"]["first_run"] is True and rows["gh:1"]["status"] == "open"
    assert rows["gh:3"]["first_seen"] == D2 and rows["gh:3"]["first_run"] is False


def test_removed_when_source_has_file_and_posting_gone(tmp_path):
    write_raw(tmp_path, D1, "gh", gh_raw(1, 2))
    write_raw(tmp_path, D2, "gh", gh_raw(1))
    rows = build(tmp_path)
    assert rows["gh:2"]["status"] == "removed" and rows["gh:2"]["removed_date"] == D2
    assert rows["gh:2"]["last_seen"] == D1
    assert rows["gh:1"]["status"] == "open" and rows["gh:1"]["removed_date"] == ""


def test_no_raw_file_means_no_removal(tmp_path):
    write_raw(tmp_path, D1, "gh", gh_raw(1))
    write_raw(tmp_path, D1, "lv", lv_raw("a"))
    write_raw(tmp_path, D2, "gh", gh_raw(1))      # lv failed on D2: no file
    rows = build(tmp_path)
    assert rows["lv:a"]["status"] == "open" and rows["lv:a"]["last_seen"] == D1


def test_reopened_posting_clears_removed_date_and_keeps_first_seen(tmp_path):
    write_raw(tmp_path, D1, "gh", gh_raw(1, 2))
    write_raw(tmp_path, D2, "gh", gh_raw(1))
    write_raw(tmp_path, D3, "gh", gh_raw(1, 2))
    row = build(tmp_path)["gh:2"]
    assert row["status"] == "open" and row["removed_date"] == ""
    assert row["first_seen"] == D1 and row["last_seen"] == D3


def test_first_run_is_per_source(tmp_path):
    write_raw(tmp_path, D1, "gh", gh_raw(1))
    write_raw(tmp_path, D2, "gh", gh_raw(1))
    write_raw(tmp_path, D2, "lv", lv_raw("a"))     # lv's first file is D2
    rows = build(tmp_path)
    assert rows["lv:a"]["first_run"] is True


def test_keeps_postings_outside_role_and_marks_in_role(tmp_path):
    write_raw(tmp_path, D1, "gh", gh_raw(1))
    write_raw(tmp_path, D1, "lv", lv_raw("a"))
    rows = build(tmp_path)
    assert rows["gh:1"]["in_role"] is True and rows["lv:a"]["in_role"] is False


def test_rows_sorted_and_build_is_reproducible(tmp_path):
    write_raw(tmp_path, D1, "lv", lv_raw("b", "a"))
    write_raw(tmp_path, D1, "gh", gh_raw(2, 1))
    write_raw(tmp_path, D2, "gh", gh_raw(1))
    rows = history.build_history(tmp_path, SOURCES)
    ids = [r["posting_id"] for r in rows]
    assert ids == sorted(ids)
    history.write_history(rows, tmp_path / "a.csv")
    history.write_history(history.build_history(tmp_path, SOURCES), tmp_path / "b.csv")
    assert (tmp_path / "a.csv").read_bytes() == (tmp_path / "b.csv").read_bytes()
    with open(tmp_path / "a.csv", newline="") as f:
        assert next(csv.reader(f)) == history.HISTORY_COLUMNS


def test_status_counts(tmp_path):
    write_raw(tmp_path, D1, "gh", gh_raw(1, 2))
    write_raw(tmp_path, D2, "gh", gh_raw(1, 3))
    rows = history.build_history(tmp_path, SOURCES)
    results = [{"name": "gh", "ok": True, "count": 2}, {"name": "lv", "ok": False, "count": 0}]
    now = datetime(2026, 1, 2, 6, 0, tzinfo=timezone.utc)
    st = status.build_status(rows, results, now, D2, tmp_path)
    assert st["first_run_date"] == D1 and st["days_with_success"] == 2
    assert (st["open"], st["new_today"], st["removed_today"]) == (2, 1, 1)
    assert st["run_time"] == "2026-01-02T06:00:00Z"
    assert st["sources"][1] == {"name": "lv", "ok": False, "count": 0}
