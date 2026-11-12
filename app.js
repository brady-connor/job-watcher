// Shared helpers for all three pages.
const NAV = [["index.html", "Today"], ["browse.html", "Browse"], ["market.html", "Market"]];

function renderNav() {
  const here = location.pathname.split("/").pop() || "index.html";
  document.getElementById("nav").innerHTML =
    '<a class="brand" href="index.html">Job Watcher</a>' +
    NAV.map(([h, t]) => `<a href="${h}"${h === here ? ' class="active"' : ""}>${t}</a>`).join("");
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function parseCSV(text) {
  const rows = []; let row = [], f = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; }
      else f += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(f); f = ""; }
    else if (c === "\n") { row.push(f); rows.push(row); row = []; f = ""; }
    else if (c !== "\r") f += c;
  }
  if (f !== "" || row.length) { row.push(f); rows.push(row); }
  const head = rows.shift() || [];
  return rows.filter(r => r.length === head.length).map(r => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}

function toRows(csvText) {
  return parseCSV(csvText).map(r => ({ ...r, in_role: r.in_role === "true", first_run: r.first_run === "true" }));
}

async function loadData() {
  const get = u => fetch(u, { cache: "no-cache" }).then(r => { if (!r.ok) throw new Error(u + " returned " + r.status); return r; });
  const [csv, status] = await Promise.all([
    get("data/history.csv").then(r => r.text()),
    get("data/status.json").then(r => r.json()),
  ]);
  return { rows: toRows(csv), status };
}

function dayNum(s) { const [y, m, d] = s.split("-").map(Number); return Date.UTC(y, m - 1, d) / 86400000; }
function numToDate(n) { return new Date(n * 86400000).toISOString().slice(0, 10); }

function showError(e) {
  const el = document.getElementById("msg");
  el.hidden = false;
  el.textContent = "Could not load the data files (" + e.message + "). Open the site once while online.";
}

if (typeof navigator !== "undefined" && "serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}
if (typeof module !== "undefined") module.exports = { parseCSV, toRows, dayNum, numToDate };
