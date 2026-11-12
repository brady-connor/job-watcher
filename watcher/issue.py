"""Daily GitHub Issue: build the body, then open/update today's and close old ones.

Run by the workflow after the pipeline:  python -m watcher.issue
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIMIT = 60000  # GitHub allows 65,536 characters in an issue body


def _line(r):
    title = r["title"].replace("[", "(").replace("]", ")")
    where = f" ({r['location']})" if r["location"] else ""
    return f"- [{title}]({r['url']}) - {r['employer']}{where}"


def _section(heading, rows, budget):
    rows = sorted(rows, key=lambda r: (not r["in_role"], r["employer"], r["title"]))
    out = [f"## {heading} ({len(rows)})", ""]
    if not rows:
        out += ["None.", ""]
        return out
    used = 0
    for i, r in enumerate(rows):
        line = _line(r)
        if used + len(line) > budget:
            out += [f"- ... and {len(rows) - i} more (see data/history.csv)"]
            break
        out.append(line)
        used += len(line) + 1
    out.append("")
    return out


def build_body(rows, date):
    new = [r for r in rows if r["first_seen"] == date and not r["first_run"]]
    removed = [r for r in rows if r["removed_date"] == date]
    lines = [f"Job postings for {date} (UTC). Postings in the role are listed first.", ""]
    lines += _section("New postings", new, LIMIT // 2)
    lines += _section("Removed postings", removed, LIMIT // 2)
    return "\n".join(lines)


def _gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def publish(date, body_path):
    _gh("label", "create", "job-watcher", "--color", "0f766e", "--force")
    existing = json.loads(_gh("issue", "list", "--state", "all", "--label", "job-watcher",
                              "--limit", "300", "--json", "number,title,state"))
    today = [i for i in existing if i["title"] == date]
    if today:
        number = str(today[0]["number"])
        _gh("issue", "edit", number, "--body-file", str(body_path))
        if today[0]["state"] != "OPEN":
            _gh("issue", "reopen", number)
    else:
        _gh("issue", "create", "--title", date, "--body-file", str(body_path),
            "--label", "job-watcher")
    for i in existing:
        if i["state"] == "OPEN" and i["title"] != date:
            _gh("issue", "close", str(i["number"]))


def main():
    status = json.loads((ROOT / "data" / "status.json").read_text())
    publish(status["run_time"][:10], ROOT / "issue_body.md")


if __name__ == "__main__":
    main()
