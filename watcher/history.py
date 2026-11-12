"""Build data/history.csv from the raw files alone.

The build is a pure function of data/raw/<date>/<source>.json.gz and
sources.json: running it again gives the same file, and a rule change
applies to every day of the history.

Command:  python -m watcher.history
"""
import csv
import gzip
import json
from pathlib import Path

from . import convert

ROOT = Path(__file__).resolve().parent.parent

HISTORY_COLUMNS = [
    "posting_id", "source", "source_id", "employer", "title", "location",
    "department", "posted_date", "url", "in_role", "first_run", "first_seen",
    "last_seen", "status", "removed_date",
]


def raw_files(raw_dir):
    """Return {date: {source: path}} for every raw file under raw_dir."""
    days = {}
    for path in sorted(Path(raw_dir).glob("*/*.json.gz")):
        source = path.name[: -len(".json.gz")]
        days.setdefault(path.parent.name, {})[source] = path
    return days


def read_raw(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def build_history(raw_dir, sources):
    """Walk the raw files day by day and return the history rows, sorted."""
    days = raw_files(raw_dir)
    postings = {}      # source -> {posting_id: row}
    first_day = {}     # source -> date of its first raw file
    for date in sorted(days):
        for source in sorted(days[date]):
            if source not in sources:
                continue
            first_day.setdefault(source, date)
            known = postings.setdefault(source, {})
            listed = set()
            for r in convert.convert(sources[source], read_raw(days[date][source])):
                pid = r["posting_id"]
                if pid in listed:
                    continue
                listed.add(pid)
                row = known.get(pid)
                if row is None:
                    known[pid] = dict(
                        r, first_run=(first_day[source] == date),
                        first_seen=date, last_seen=date,
                        status="open", removed_date="",
                    )
                else:
                    row.update(r)               # latest details; keeps first_*
                    row["last_seen"] = date
                    row["status"] = "open"      # reopened if it had been removed
                    row["removed_date"] = ""
            for pid, row in known.items():
                if row["status"] == "open" and pid not in listed:
                    row["status"] = "removed"
                    row["removed_date"] = date
    rows = [row for known in postings.values() for row in known.values()]
    return sorted(rows, key=lambda r: r["posting_id"])


def write_history(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(HISTORY_COLUMNS)
        for r in rows:
            out = []
            for c in HISTORY_COLUMNS:
                v = r[c]
                out.append(("true" if v else "false") if isinstance(v, bool) else v)
            w.writerow(out)


def main():
    sources = convert.load_sources(ROOT / "sources.json")
    rows = build_history(ROOT / "data" / "raw", sources)
    write_history(rows, ROOT / "data" / "history.csv")
    print(f"wrote data/history.csv with {len(rows)} postings")


if __name__ == "__main__":
    main()
