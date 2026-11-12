(async () => {
  renderNav();
  try {
    const { rows, status } = await loadData();
    const day = status.run_time.slice(0, 10);
    document.getElementById("runtime").textContent = status.run_time.replace("T", " ").replace("Z", " UTC");
    const counts = [["Days with a successful run", status.days_with_success], ["Open postings", status.open],
                    ["New today", status.new_today], ["Removed today", status.removed_today]];
    document.getElementById("counts").innerHTML = counts.map(([l, v]) => `<div class="count"><b>${v}</b>${l}</div>`).join("");
    document.getElementById("sources").innerHTML = status.sources.map(s =>
      `<tr><td>${esc(s.name)}</td><td class="${s.ok ? "ok" : "fail"}">${s.ok ? "OK" : "Failed"}</td><td>${s.count}</td></tr>`).join("");
    const list = (items, el, empty) => {
      items.sort((a, b) => Number(b.in_role) - Number(a.in_role) || a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title));
      document.getElementById(el).innerHTML = items.length
        ? items.map(r => `<li><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a> <span class="muted">${esc(r.employer)}${r.location ? " · " + esc(r.location) : ""}</span></li>`).join("")
        : `<li class="muted">${empty}</li>`;
    };
    list(rows.filter(r => r.first_seen === day && !r.first_run), "new", "No new postings in the latest run.");
    list(rows.filter(r => r.removed_date === day), "removed", "No postings removed in the latest run.");
    document.getElementById("newh").textContent = `New postings in the latest run (${rows.filter(r => r.first_seen === day && !r.first_run).length})`;
    document.getElementById("removedh").textContent = `Removed postings in the latest run (${rows.filter(r => r.removed_date === day).length})`;
  } catch (e) { showError(e); }
})();
