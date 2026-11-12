(async () => {
  renderNav();
  const KEY = "jw-shortlist";
  const getShort = () => { try { return new Set(JSON.parse(localStorage.getItem(KEY) || "[]")); } catch (e) { return new Set(); } };
  const saveShort = s => { try { localStorage.setItem(KEY, JSON.stringify([...s])); } catch (e) {} };
  const st = { role: true, employer: "", loc: "", days: "", q: "", newest: true, short: false, limit: 200 };
  let open = [], today = "";
  const $ = id => document.getElementById(id);

  function draw() {
    const shortlist = getShort(), q = st.q.toLowerCase(), loc = st.loc.toLowerCase();
    let list = open.filter(r =>
      (!st.role || r.in_role) && (!st.employer || r.employer === st.employer) &&
      (!loc || r.location.toLowerCase().includes(loc)) && (!q || r.title.toLowerCase().includes(q)) &&
      (!st.days || r.daysOpen <= Number(st.days)) && (!st.short || shortlist.has(r.posting_id)));
    list.sort((a, b) => (st.newest ? -1 : 1) * (a.first_seen < b.first_seen ? -1 : a.first_seen > b.first_seen ? 1 : 0) || a.title.localeCompare(b.title));
    $("count").textContent = `${list.length} postings`;
    $("shortcount").textContent = shortlist.size;
    $("rows").innerHTML = list.slice(0, st.limit).map(r => `<tr>
      <td><button class="star${shortlist.has(r.posting_id) ? " on" : ""}" data-id="${esc(r.posting_id)}" aria-label="Save to shortlist" aria-pressed="${shortlist.has(r.posting_id)}">${shortlist.has(r.posting_id) ? "★" : "☆"}</button></td>
      <td>${esc(r.title)}</td><td>${esc(r.employer)}</td><td>${esc(r.location)}</td>
      <td>${r.first_seen}</td><td>${r.daysOpen}</td>
      <td><a href="${esc(r.url)}" target="_blank" rel="noopener">Apply</a></td></tr>`).join("");
    $("more").hidden = list.length <= st.limit;
    $("more").textContent = `Show more (${list.length - st.limit} left)`;
  }

  try {
    const { rows, status } = await loadData();
    today = status.run_time.slice(0, 10);
    open = rows.filter(r => r.status === "open").map(r => ({ ...r, daysOpen: dayNum(today) - dayNum(r.first_seen) }));
    const employers = [...new Set(open.map(r => r.employer))].sort();
    $("employer").innerHTML = '<option value="">All employers</option>' + employers.map(e => `<option>${esc(e)}</option>`).join("");
    const bind = (id, key, ev = "input") => $(id).addEventListener(ev, e => { st[key] = e.target.value; st.limit = 200; draw(); });
    bind("employer", "employer", "change"); bind("loc", "loc"); bind("days", "days", "change"); bind("q", "q");
    $("sort").addEventListener("change", e => { st.newest = e.target.value === "new"; draw(); });
    $("short").addEventListener("change", e => { st.short = e.target.checked; st.limit = 200; draw(); });
    $("more").addEventListener("click", () => { st.limit += 200; draw(); });
    for (const b of document.querySelectorAll("#role button")) b.addEventListener("click", () => {
      st.role = b.dataset.v === "role"; st.limit = 200;
      document.querySelectorAll("#role button").forEach(x => x.classList.toggle("on", x === b)); draw();
    });
    $("rows").addEventListener("click", e => {
      const b = e.target.closest(".star"); if (!b) return;
      const s = getShort(); s.has(b.dataset.id) ? s.delete(b.dataset.id) : s.add(b.dataset.id);
      saveShort(s); draw();
    });
    draw();
  } catch (e) { showError(e); }
})();
