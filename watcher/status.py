"""Build the contents of data/status.json for the latest run."""
from . import history


def build_status(rows, results, now, date, raw_dir):
    days = sorted(history.raw_files(raw_dir))
    return {
        "run_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "first_run_date": days[0] if days else "",
        "days_with_success": len(days),
        "open": sum(1 for r in rows if r["status"] == "open"),
        "new_today": sum(1 for r in rows
                         if r["first_seen"] == date and not r["first_run"]),
        "removed_today": sum(1 for r in rows if r["removed_date"] == date),
        "sources": [
            {"name": s["name"], "ok": bool(s["ok"]), "count": int(s["count"])}
            for s in results
        ],
    }
