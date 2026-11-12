// Market report: every number is computed here from data/history.csv.
function median(a) {
  if (!a.length) return null;
  const s = [...a].sort((x, y) => x - y), m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
function countBy(rows, f) {
  const m = new Map();
  for (const r of rows) { const k = f(r); if (k !== "" && k != null) m.set(k, (m.get(k) || 0) + 1); }
  return m;
}
function ranked(map, n) {
  return [...map.entries()].sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0]))).slice(0, n);
}

function compute(rows) {
  const dn = s => { const [y, m, d] = s.split("-").map(Number); return Date.UTC(y, m - 1, d) / 86400000; };
  const toDate = n => new Date(n * 86400000).toISOString().slice(0, 10);
  const out = { empty: rows.length === 0 };
  if (out.empty) return out;
  const first = Math.min(...rows.map(r => dn(r.first_seen)));
  const last = Math.max(...rows.map(r => dn(r.last_seen)));
  out.lastRun = toDate(last);
  out.days = []; for (let d = first; d <= last; d++) out.days.push(toDate(d));

  // 1. New postings per day (first-run postings left out)
  const fresh = rows.filter(r => !r.first_run);
  const newAll = countBy(fresh, r => r.first_seen), newRole = countBy(fresh.filter(r => r.in_role), r => r.first_seen);
  out.newAll = out.days.map(d => newAll.get(d) || 0);
  out.newRole = out.days.map(d => newRole.get(d) || 0);

  // 2. Removed postings per day
  const rem = countBy(rows.filter(r => r.removed_date), r => r.removed_date);
  out.removed = out.days.map(d => rem.get(d) || 0);

  // 3. Open postings per employer as of the last run
  const open = rows.filter(r => r.status === "open");
  out.openTotal = open.length;
  out.employers = ranked(countBy(open, r => r.employer), 100);

  // 4. Days open: removed, not first-run
  const spans = fresh.filter(r => r.removed_date).map(r => dn(r.removed_date) - dn(r.first_seen));
  out.spans = spans; out.median = median(spans);

  // 5. Share removed within seven days
  const cohort = fresh.filter(r => dn(r.first_seen) <= last - 7);
  const quick = cohort.filter(r => r.removed_date && dn(r.removed_date) - dn(r.first_seen) <= 7);
  out.cohort = cohort.length; out.quick = quick.length;
  out.share = cohort.length ? quick.length / cohort.length : null;

  // 6. Top locations among open postings
  out.locations = ranked(countBy(open, r => r.location), 10);
  return out;
}

function render(m) {
  const sections = [];
  const add = (title, text, id) => sections.push(`<section class="report"><h2>${title}</h2><p>${text}</p><div id="${id}"></div></section>`);
  const sum = a => a.reduce((x, y) => x + y, 0);
  const nDays = m.days.length;
  add(`${sum(m.newAll)} new postings since tracking began, ${sum(m.newRole)} in the role`,
    `Postings first seen on each day, leaving out first-run postings (those already open when a source was first watched, so their start date is unknown). Over ${nDays} day${nDays === 1 ? "" : "s"} of history, ${sum(m.newAll)} postings appeared (${sum(m.newRole)} in the role).`, "c1");
  add(`${sum(m.removed)} postings have been removed so far`,
    `Postings with a removed date on each day. A posting is marked removed on the first day its source has a raw file and no longer lists it. The latest day shows ${m.removed[m.removed.length - 1]} removals.`, "c2");
  add(m.employers.length ? `${esc(m.employers[0][0])} has the most open postings (${m.employers[0][1]})` : "No open postings yet",
    `Open postings per employer as of the last run (${esc(m.lastRun)}), ${m.openTotal} open in total.`, "c3");
  add(m.median === null ? "Not enough data yet for days open" : `Removed postings were open for a median of ${m.median} day${m.median === 1 ? "" : "s"}`,
    m.median === null ? "No removed posting has a known start date yet. This fills in as the history grows."
      : `Days open is the removed date minus the first-seen date, for ${m.spans.length} removed postings that are not first-run postings. The median is ${m.median}.`, "c4");
  add(m.share === null ? "Not enough data yet for the seven-day share" : `${(m.share * 100).toFixed(1)}% of postings were removed within seven days`,
    m.share === null ? "This needs postings that are not first-run postings and were first seen at least seven days before the last run."
      : `Among ${m.cohort} postings that are not first-run postings and were first seen at least seven days before the last run, ${m.quick} were removed within seven days of first being seen.`, "c5");
  add(m.locations.length ? `${esc(m.locations[0][0])} is the top location (${m.locations[0][1]} open postings)` : "No locations yet",
    "The ten locations with the most open postings as of the last run. Postings with no location are left out.", "c6");
  document.getElementById("sections").innerHTML = sections.join("");

  barChart(document.getElementById("c1"), { labels: m.days, dates: true, series: [{ name: "All postings", values: m.newAll }, { name: "In role", values: m.newRole }] });
  barChart(document.getElementById("c2"), { labels: m.days, dates: true, series: [{ name: "Removed", values: m.removed }] });
  hBarChart(document.getElementById("c3"), { labels: m.employers.map(e => e[0]), values: m.employers.map(e => e[1]) });
  const bins = [["0", 0, 0], ["1", 1, 1], ["2", 2, 2], ["3", 3, 3], ["4", 4, 4], ["5", 5, 5], ["6", 6, 6], ["7", 7, 7], ["8-14", 8, 14], ["15-30", 15, 30], ["31+", 31, 1e9]];
  barChart(document.getElementById("c4"), { labels: bins.map(b => b[0]), series: [{ name: "Removed postings", values: bins.map(b => m.spans.filter(s => s >= b[1] && s <= b[2]).length) }] });
  barChart(document.getElementById("c5"), { labels: ["Within 7 days", "Later or still open"], series: [{ name: "Postings", values: [m.quick, m.cohort - m.quick] }] });
  hBarChart(document.getElementById("c6"), { labels: m.locations.map(e => e[0]), values: m.locations.map(e => e[1]) });
}

if (typeof document !== "undefined") {
  (async () => {
    renderNav();
    try {
      const { rows } = await loadData();
      const m = compute(rows);
      if (m.empty) { document.getElementById("sections").innerHTML = '<p class="muted">The history file has no postings yet.</p>'; return; }
      render(m);
    } catch (e) { showError(e); }
  })();
}
if (typeof module !== "undefined") module.exports = { compute };
