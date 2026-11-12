// Small SVG charts (no external libraries, so they work offline).
function niceMax(v) {
  if (v <= 5) return 5;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * p >= v) return m * p;
  return 10 * p;
}

// Vertical bars. series = [{name, values}], labels = x labels. dates: show MM-DD.
function barChart(el, { labels, series, dates }) {
  if (!labels.length) { el.innerHTML = '<p class="muted">No data yet.</p>'; return; }
  const W = 720, H = 300, L = 44, R = 10, T = 12, B = 40, pw = W - L - R, ph = H - T - B;
  const max = niceMax(Math.max(1, ...series.flatMap(s => s.values)));
  const n = labels.length, gw = pw / n, bw = Math.max(1, gw * 0.8 / series.length);
  let g = "";
  for (let i = 0; i <= 4; i++) {
    const y = T + ph - ph * i / 4;
    g += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" class="grid"/><text x="${L - 6}" y="${y + 4}" class="ax" text-anchor="end">${+(max * i / 4).toFixed(1)}</text>`;
  }
  series.forEach((s, si) => s.values.forEach((v, i) => {
    const h = ph * v / max, x = L + i * gw + gw * 0.1 + si * bw;
    g += `<rect x="${x}" y="${T + ph - h}" width="${bw}" height="${h}" class="bar c${si + 1}"><title>${esc(labels[i])}: ${v}${series.length > 1 ? " (" + esc(s.name) + ")" : ""}</title></rect>`;
  }));
  const step = Math.ceil(n / 12);
  labels.forEach((lb, i) => {
    if (i % step === 0) g += `<text x="${L + i * gw + gw / 2}" y="${H - B + 16}" class="ax" text-anchor="middle">${esc(dates ? String(lb).slice(5) : lb)}</text>`;
  });
  const legend = series.length > 1
    ? '<div class="legend">' + series.map((s, i) => `<span><i style="background:var(--c${i + 1})"></i>${esc(s.name)}</span>`).join("") + "</div>" : "";
  el.innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Bar chart">${g}</svg>${legend}`;
}

// Horizontal bars for ranked lists (employers, locations).
function hBarChart(el, { labels, values }) {
  if (!labels.length) { el.innerHTML = '<p class="muted">No data yet.</p>'; return; }
  const W = 720, rowH = 26, L = 200, R = 50, H = labels.length * rowH + 8, pw = W - L - R;
  const max = Math.max(1, ...values);
  let g = "";
  labels.forEach((lb, i) => {
    const y = 4 + i * rowH, w = pw * values[i] / max;
    const text = lb.length > 30 ? lb.slice(0, 29) + "…" : lb;
    g += `<text x="${L - 8}" y="${y + 16}" class="lbl" text-anchor="end">${esc(text)}</text>` +
         `<rect x="${L}" y="${y + 3}" width="${w}" height="${rowH - 8}" class="bar c1"><title>${esc(lb)}: ${values[i]}</title></rect>` +
         `<text x="${L + w + 6}" y="${y + 16}" class="ax">${values[i]}</text>`;
  });
  el.innerHTML = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Bar chart">${g}</svg>`;
}
