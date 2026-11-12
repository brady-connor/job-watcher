"""Daily pipeline: fetch sources -> raw files -> history -> status -> issue body.

    python -m watcher.pipeline            full run (what the daily workflow does)
    python -m watcher.pipeline --check    test every source, write nothing
"""
import argparse
import datetime as dt
import gzip
import json
import shutil
import time
from pathlib import Path

import requests

from . import convert, history, issue, status as status_mod

ROOT = Path(__file__).resolve().parent.parent

URLS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{token}/jobs",
    "lever": "https://api.lever.co/v0/postings/{token}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{token}",
}
HEADERS = {"User-Agent": "job-watcher-class-project"}
BIG_BOARD = 5000


def fetch(src, session, tries=3):
    url = URLS[src["ats"]].format(token=src["token"])
    last = None
    for attempt in range(tries):
        try:
            r = session.get(url, timeout=60, headers=HEADERS)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # network error, HTTP error, bad JSON
            last = e
            time.sleep(2 * (attempt + 1))
    raise last


def run(date=None, root=ROOT, session=None, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    date = date or now.strftime("%Y-%m-%d")
    session = session or requests.Session()
    root = Path(root)
    sources = convert.load_sources(root / "sources.json")
    raw_dir = root / "data" / "raw"
    day_dir = raw_dir / date
    if day_dir.exists():                      # a second run replaces the day
        shutil.rmtree(day_dir)
    day_dir.mkdir(parents=True)

    results = []
    for name, src in sources.items():
        try:
            raw = fetch(src, session)
            count = len(convert.convert(src, raw))   # validates the response
            data = json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
            (day_dir / f"{name}.json.gz").write_bytes(gzip.compress(data.encode(), mtime=0))
            results.append({"name": name, "ok": True, "count": count})
            if count > BIG_BOARD:
                print(f"WARNING {name}: {count} postings; request it with a search term")
        except Exception as e:                 # one failing source must not stop the run
            results.append({"name": name, "ok": False, "count": 0,
                            "error": str(e)[:200]})
    (day_dir / "_results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")

    rows = history.build_history(raw_dir, sources)
    history.write_history(rows, root / "data" / "history.csv")
    st = status_mod.build_status(rows, results, now, date, raw_dir)
    (root / "data" / "status.json").write_text(json.dumps(st, indent=2) + "\n")
    (root / "issue_body.md").write_text(issue.build_body(rows, date), encoding="utf-8")
    return st, results


def check(root=ROOT):
    sources = convert.load_sources(Path(root) / "sources.json")
    session = requests.Session()
    bad = 0
    for name, src in sources.items():
        try:
            n = len(convert.convert(src, fetch(src, session, tries=1)))
            print(f"ok    {name:<14} {src['ats']:<11} {n} postings")
        except Exception as e:
            bad += 1
            print(f"FAIL  {name:<14} {src['ats']:<11} {str(e)[:80]}")
    print(f"{len(sources) - bad} of {len(sources)} sources work")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="test sources, write nothing")
    args = ap.parse_args()
    if args.check:
        check()
        return
    st, results = run()
    for s in results:
        print(("ok    " if s["ok"] else "FAIL  ") + f"{s['name']:<14} {s['count']} {s.get('error', '')}")
    print(json.dumps({k: v for k, v in st.items() if k != "sources"}))


if __name__ == "__main__":
    main()
