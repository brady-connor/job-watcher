import gzip
import json

SOURCES = {
    "gh": {"name": "gh", "employer": "GH Co", "ats": "greenhouse", "token": "gh"},
    "lv": {"name": "lv", "employer": "LV Co", "ats": "lever", "token": "lv"},
}


def gh_raw(*ids, title="Data Analyst"):
    return {"jobs": [{"id": i, "title": f"{title} {i}", "location": {"name": "Remote"},
                      "absolute_url": f"https://example.com/gh/{i}"} for i in ids]}


def lv_raw(*ids, title="Engineer"):
    return [{"id": i, "text": f"{title} {i}", "hostedUrl": f"https://example.com/lv/{i}",
             "categories": {"location": "NYC"}} for i in ids]


def write_raw(raw_dir, date, source, raw):
    d = raw_dir / date
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{source}.json.gz").write_bytes(gzip.compress(json.dumps(raw).encode()))
