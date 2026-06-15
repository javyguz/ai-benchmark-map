/* ============================================================
   AI Benchmark Map — frontend (Johns Hopkins CSSE-inspired)
   ============================================================ */

const LICENSE_LABEL = { open: "Open source", proprietary: "Propietario" };

const state = {
  byCategory: {},   // cid -> [orgs]
  category: null,   // categoría activa
  all: [],          // orgs de la categoría activa (ordenados por score desc)
  rankByOrg: {},    // org -> ranking dentro de la categoría (1-based)
  filtered: [],     // resultado de aplicar filtros
  markers: {},      // org -> { marker, el }
  scoreRange: [0, 1],
  filters: { search: "", country: "", license: "" },
  tab: "ranking",
};

/* ----------------------- MAP ----------------------- */
const map = new maplibregl.Map({
  container: "map",
  style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
  center: [12, 28],
  zoom: 1.55,
  attributionControl: false,
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

/* ----------------------- HELPERS ----------------------- */
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

// Diámetro de la burbuja proporcional al score (símbolo proporcional, estilo JHU).
function bubbleSize(score) {
  const [min, max] = state.scoreRange;
  const t = max > min ? (score - min) / (max - min) : 0.5;
  return Math.round(16 + t * 40); // 16px..56px de diámetro
}

function popupHtml(o) {
  return `<div class="popup-card">
    <img src="${escapeHtml(o.logo)}" alt="${escapeHtml(o.org)}" />
    <div>
      <div class="popup-org">${escapeHtml(o.org)}</div>
      <div class="popup-loc">${escapeHtml(o.city)}, ${escapeHtml(o.country)}</div>
      <div class="popup-model">${escapeHtml(o.model)}</div>
      <div class="popup-stats">
        <span class="popup-score">${o.score}</span>
        <span class="lb-pill ${o.license}">${escapeHtml(LICENSE_LABEL[o.license] || o.license)}</span>
      </div>
      <a href="${escapeHtml(o.source_url)}" target="_blank" rel="noopener">Ver fuente ↗</a>
    </div>
  </div>`;
}

/* ----------------------- MARKERS (proportional bubbles) ----------------------- */
function buildMarkers() {
  Object.values(state.markers).forEach((m) => m.marker.remove());
  state.markers = {};
  state.all.forEach((o) => {
    const d = bubbleSize(o.score);
    const el = document.createElement("div");
    el.className = "marker";

    const bubble = document.createElement("div");
    bubble.className = "bubble " + o.license;
    bubble.style.width = d + "px";
    bubble.style.height = d + "px";
    el.appendChild(bubble);

    const popup = new maplibregl.Popup({ offset: d / 2, closeButton: true }).setHTML(popupHtml(o));
    const marker = new maplibregl.Marker({ element: el }).setLngLat([o.lon, o.lat]).setPopup(popup).addTo(map);

    el.addEventListener("mouseenter", () => highlightRow(o.org, true));
    el.addEventListener("mouseleave", () => highlightRow(o.org, false));

    state.markers[o.org] = { marker, el };
  });
}

function syncMarkerVisibility() {
  const shown = new Set(state.filtered.map((o) => o.org));
  Object.entries(state.markers).forEach(([org, m]) => {
    m.el.style.display = shown.has(org) ? "" : "none";
  });
}

/* ----------------------- LEFT: TOTALS ----------------------- */
function renderTotals(orgs) {
  const top = orgs.reduce((a, b) => (b.score > a.score ? b : a), orgs[0] || { score: 0, org: "—" });
  const countries = new Set(orgs.map((o) => o.country)).size;
  const openCount = orgs.filter((o) => o.license === "open").length;
  const openPct = orgs.length ? Math.round((openCount / orgs.length) * 100) : 0;

  document.getElementById("totals").innerHTML = `
    <div class="total-block">
      <div class="t-label">Modelos trackeados</div>
      <div class="t-value">${orgs.length}</div>
      <div class="t-sub">en ${countries} países</div>
    </div>
    <div class="total-block alt">
      <div class="t-label">Top score</div>
      <div class="t-value">${top.score || "—"}</div>
      <div class="t-sub">${escapeHtml(top.org || "—")}</div>
    </div>
    <div class="total-block">
      <div class="t-label">Open source</div>
      <div class="t-value">${openPct}%</div>
      <div class="t-sub">${openCount} de ${orgs.length} modelos</div>
    </div>`;
}

/* ----------------------- LEFT: COUNTRY BREAKDOWN ----------------------- */
function renderBreakdown(orgs) {
  const byCountry = {};
  orgs.forEach((o) => {
    if (!byCountry[o.country]) byCountry[o.country] = { count: 0, best: 0 };
    byCountry[o.country].count++;
    byCountry[o.country].best = Math.max(byCountry[o.country].best, o.score);
  });
  const rows = Object.entries(byCountry).sort((a, b) =>
    b[1].count - a[1].count || b[1].best - a[1].best
  );
  const maxCount = rows.length ? rows[0][1].count : 1;

  document.getElementById("country-list").innerHTML = rows
    .map(
      ([country, d]) => `<li class="country-row">
        <span class="c-name">${escapeHtml(country)}</span>
        <span class="c-meta">
          <span class="c-count">${d.count}</span>
          <span class="c-best">top ${d.best}</span>
        </span>
        <span class="country-bar" style="width:${(d.count / maxCount) * 100}%"></span>
      </li>`
    )
    .join("");
}

/* ----------------------- RIGHT: LEADERBOARD ----------------------- */
function renderLeaderboard(orgs) {
  const lb = document.getElementById("leaderboard");
  document.getElementById("empty-state").hidden = orgs.length > 0;

  lb.innerHTML = orgs
    .map((o) => {
      const rank = state.rankByOrg[o.org];
      return `<li class="lb-row r${rank}" data-org="${escapeHtml(o.org)}">
        <span class="lb-rank">${rank}</span>
        <span class="lb-logo"><img src="${escapeHtml(o.logo)}" alt="" /></span>
        <span class="lb-main">
          <span class="lb-org">${escapeHtml(o.org)}
            <span class="lb-pill ${o.license}">${o.license === "open" ? "OPEN" : "PROP"}</span>
          </span>
          <span class="lb-model">${escapeHtml(o.model)}</span>
        </span>
        <span class="lb-meta">
          <span class="lb-score">${o.score}</span>
          <span class="lb-city">${escapeHtml(o.city)}</span>
        </span>
      </li>`;
    })
    .join("");

  lb.querySelectorAll(".lb-row").forEach((row) => {
    const org = row.dataset.org;
    row.addEventListener("click", () => focusOrg(org));
    row.addEventListener("mouseenter", () => state.markers[org]?.el.classList.add("hot"));
    row.addEventListener("mouseleave", () => state.markers[org]?.el.classList.remove("hot"));
  });
}

function highlightRow(org, on) {
  const row = document.querySelector(`.lb-row[data-org="${CSS.escape(org)}"]`);
  if (row) row.classList.toggle("hot", on);
}

function focusOrg(org) {
  const o = state.all.find((x) => x.org === org);
  if (!o) return;
  map.flyTo({ center: [o.lon, o.lat], zoom: 4.2, speed: 1.4 });
  const m = state.markers[org];
  if (m && !m.marker.getPopup().isOpen()) m.marker.togglePopup();
}

/* ----------------------- RIGHT: CHART (ECharts) ----------------------- */
let chart = null;
function renderChart(orgs) {
  const el = document.getElementById("chart");
  el.style.height = Math.max(360, orgs.length * 30) + "px";
  if (!chart) chart = echarts.init(el, null, { renderer: "canvas" });
  const data = [...orgs].sort((a, b) => a.score - b.score);
  const min = Math.min(...orgs.map((o) => o.score), 1200) - 20;

  chart.setOption({
    grid: { left: 8, right: 46, top: 8, bottom: 8, containLabel: true },
    tooltip: {
      trigger: "axis", axisPointer: { type: "shadow" },
      backgroundColor: "#000", borderColor: "#d62728", textStyle: { color: "#e9e9e9" },
      formatter: (p) => `<b>${p[0].name}</b><br/>Score: <b>${p[0].value}</b>`,
    },
    xAxis: {
      type: "value", min,
      axisLabel: { color: "#6a6a6a", fontSize: 10, fontFamily: "DM Mono" },
      splitLine: { lineStyle: { color: "#1f1f1f" } },
      axisLine: { show: false },
    },
    yAxis: {
      type: "category", data: data.map((o) => o.org),
      axisLabel: { color: "#9a9a9a", fontSize: 11, fontFamily: "DM Mono" },
      axisLine: { lineStyle: { color: "#2a2a2a" } },
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: data.map((o) => ({
          value: o.score,
          itemStyle: {
            borderRadius: [0, 3, 3, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0,
              o.license === "open"
                ? [{ offset: 0, color: "#2a6f9e" }, { offset: 1, color: "#4aa3df" }]
                : [{ offset: 0, color: "#8a1a1b" }, { offset: 1, color: "#ff4136" }]
            ),
          },
        })),
        barWidth: "58%",
        label: { show: true, position: "right", color: "#e9e9e9", fontSize: 11, fontFamily: "Oswald", fontWeight: 600 },
      },
    ],
  });
  chart.resize();
}
window.addEventListener("resize", () => chart && chart.resize());

/* ----------------------- FILTERS / PIPELINE ----------------------- */
function applyFilters() {
  const { search, country, license } = state.filters;
  const q = search.trim().toLowerCase();
  state.filtered = state.all.filter((o) => {
    if (country && o.country !== country) return false;
    if (license && o.license !== license) return false;
    if (q && !(`${o.org} ${o.model} ${o.city}`.toLowerCase().includes(q))) return false;
    return true;
  });

  renderTotals(state.filtered);
  renderBreakdown(state.filtered);
  renderLeaderboard(state.filtered);
  renderChart(state.filtered);
  syncMarkerVisibility();
}

function populateCountryFilter(orgs) {
  const sel = document.getElementById("filter-country");
  sel.innerHTML = '<option value="">Todos los países</option>';
  [...new Set(orgs.map((o) => o.country))].sort().forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
  });
}

/* ----------------------- CATEGORY SWITCHING ----------------------- */
function setCategory(cid) {
  state.category = cid;
  state.all = (state.byCategory[cid] || []).slice().sort((a, b) => b.score - a.score);
  state.rankByOrg = {};
  state.all.forEach((o, i) => (state.rankByOrg[o.org] = i + 1));
  const scores = state.all.map((o) => o.score);
  state.scoreRange = scores.length ? [Math.min(...scores), Math.max(...scores)] : [0, 1];

  // Resetea filtros dependientes de la categoría (los países cambian).
  state.filters.country = "";
  populateCountryFilter(state.all);
  buildMarkers();
  applyFilters();
}

function populateCategorySelect(categories) {
  const sel = document.getElementById("category-select");
  sel.innerHTML = categories
    .map((c) => `<option value="${c.id}">${c.label} (${c.count})</option>`)
    .join("");
  sel.addEventListener("change", (e) => setCategory(e.target.value));
}

function wireFilters() {
  document.getElementById("filter-search").addEventListener("input", (e) => {
    state.filters.search = e.target.value;
    applyFilters();
  });
  document.getElementById("filter-country").addEventListener("change", (e) => {
    state.filters.country = e.target.value;
    applyFilters();
  });
  document.querySelectorAll("#filter-license .seg").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#filter-license .seg").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.filters.license = btn.dataset.val;
      applyFilters();
    });
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      document.querySelector(`.tab-panel[data-panel="${tab.dataset.tab}"]`).classList.add("active");
      state.tab = tab.dataset.tab;
      if (state.tab === "chart" && chart) chart.resize();
    });
  });
}

/* ----------------------- BOOT ----------------------- */
fetch("data/data.json")
  .then((r) => r.json())
  .then((data) => {
    state.byCategory = data.data || {};
    const categories = data.categories || [];

    const date = data.snapshot_date || (data.generated_at || "").slice(0, 10) || "?";
    document.getElementById("updated").textContent = `Arena AI · ${date}`;

    wireFilters();
    populateCategorySelect(categories);
    setCategory(categories[0] ? categories[0].id : Object.keys(state.byCategory)[0]);
  })
  .catch((e) => {
    document.getElementById("updated").textContent = "Error cargando datos";
    console.error(e);
  });
