import json

from watcher import pipeline
from tests.helpers import SOURCES, gh_raw, lv_raw


class Resp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class FakeSession:
    def __init__(self, by_token):
        self.by_token = by_token

    def get(self, url, **kw):
        for token, data in self.by_token.items():
            if f"/{token}" in url:
                if isinstance(data, Exception):
                    raise data
                return Resp(data)
        raise RuntimeError("unknown url " + url)


def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline.time, "sleep", lambda s: None)
    (tmp_path / "sources.json").write_text(json.dumps(list(SOURCES.values())))


def test_failed_source_writes_no_file_and_run_continues(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    session = FakeSession({"gh": gh_raw(1, 2), "lv": RuntimeError("boom")})
    st, results = pipeline.run("2026-01-01", root=tmp_path, session=session)
    day = tmp_path / "data" / "raw" / "2026-01-01"
    assert (day / "gh.json.gz").exists() and not (day / "lv.json.gz").exists()
    assert [(r["name"], r["ok"], r["count"]) for r in results] == [("gh", True, 2), ("lv", False, 0)]
    assert st["sources"] == [{"name": "gh", "ok": True, "count": 2},
                             {"name": "lv", "ok": False, "count": 0}]
    assert (tmp_path / "data" / "history.csv").exists()
    assert (tmp_path / "data" / "status.json").exists()


def test_second_run_same_day_replaces_the_day(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    pipeline.run("2026-01-01", root=tmp_path,
                 session=FakeSession({"gh": gh_raw(1), "lv": lv_raw("a")}))
    st, _ = pipeline.run("2026-01-01", root=tmp_path,
                         session=FakeSession({"gh": gh_raw(1, 2), "lv": RuntimeError("x")}))
    day = tmp_path / "data" / "raw" / "2026-01-01"
    assert sorted(p.name for p in day.glob("*.json.gz")) == ["gh.json.gz"]
    assert st["days_with_success"] == 1
    lines = (tmp_path / "data" / "history.csv").read_text().splitlines()
    assert len(lines) == 1 + 2          # header + gh:1 + gh:2, one day counted once


def test_day_two_reports_new_and_removed(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    pipeline.run("2026-01-01", root=tmp_path,
                 session=FakeSession({"gh": gh_raw(1, 2), "lv": lv_raw("a")}))
    st, _ = pipeline.run("2026-01-02", root=tmp_path,
                         session=FakeSession({"gh": gh_raw(1, 3), "lv": lv_raw("a")}))
    assert (st["new_today"], st["removed_today"], st["open"]) == (1, 1, 3)
    assert st["days_with_success"] == 2 and st["first_run_date"] == "2026-01-01"
    body = (tmp_path / "issue_body.md").read_text()
    assert "New postings (1)" in body and "Removed postings (1)" in body
