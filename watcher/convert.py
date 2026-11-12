"""Convert raw job-board responses to the common columns, and the title rule."""
import json
import re
from datetime import datetime, timezone

COLUMNS = [
    "posting_id", "source", "source_id", "employer", "title", "location",
    "department", "posted_date", "url", "in_role",
]

# Title rule: a title is "in role" when it contains the word "analyst"
# AND one of: data, financial, finance, FP&A, business intelligence, BI.
# Matching is case-insensitive and on whole words (except "FP&A").
_ANALYST = re.compile(r"\banalysts?\b", re.I)
_FOCUS = re.compile(
    r"\bdata\b|\bfinancial\b|\bfinance\b|fp&a|business intelligence|\bbi\b", re.I
)


def in_role(title):
    title = title or ""
    return bool(_ANALYST.search(title) and _FOCUS.search(title))


def load_sources(path):
    """Return {source name: source dict} from sources.json, in file order."""
    with open(path, encoding="utf-8") as f:
        return {s["name"]: s for s in json.load(f)}


def _text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _iso_date(value):
    """UTC date (YYYY-MM-DD) from an ISO string or epoch milliseconds, else ''."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, timezone.utc).strftime("%Y-%m-%d")
    m = re.match(r"\d{4}-\d{2}-\d{2}", str(value))
    return m.group(0) if m else ""


def _row(src, source_id, title, location, department, posted, url):
    source_id = _text(source_id)
    title = _text(title)
    return {
        "posting_id": f"{src['name']}:{source_id}",
        "source": src["name"],
        "source_id": source_id,
        "employer": src["employer"],
        "title": title,
        "location": _text(location),
        "department": _text(department),
        "posted_date": _iso_date(posted),
        "url": _text(url),
        "in_role": in_role(title),
    }


def convert_greenhouse(src, raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("jobs"), list):
        raise ValueError("unexpected Greenhouse response")
    rows = []
    for j in raw["jobs"]:
        loc = j.get("location")
        loc = loc.get("name") if isinstance(loc, dict) else loc
        depts = j.get("departments") or [{}]
        rows.append(_row(src, j["id"], j.get("title"), loc, depts[0].get("name"),
                         j.get("first_published"), j.get("absolute_url")))
    return rows


def convert_lever(src, raw):
    if not isinstance(raw, list):
        raise ValueError("unexpected Lever response")
    rows = []
    for j in raw:
        cat = j.get("categories") or {}
        rows.append(_row(src, j["id"], j.get("text"), cat.get("location"),
                         cat.get("department") or cat.get("team"),
                         j.get("createdAt"), j.get("hostedUrl")))
    return rows


def convert_ashby(src, raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("jobs"), list):
        raise ValueError("unexpected Ashby response")
    rows = []
    for j in raw["jobs"]:
        if j.get("isListed") is False:
            continue
        rows.append(_row(src, j["id"], j.get("title"), j.get("location"),
                         j.get("department") or j.get("team"),
                         j.get("publishedAt"), j.get("jobUrl") or j.get("applyUrl")))
    return rows


CONVERTERS = {
    "greenhouse": convert_greenhouse,
    "lever": convert_lever,
    "ashby": convert_ashby,
}


def convert(src, raw):
    return CONVERTERS[src["ats"]](src, raw)
