/* ============================================================
   AI Benchmark Map — frontend
   ============================================================ */

const LICENSE_LABEL = { open: "Open source", proprietary: "Propietario" };

const state = {
  all: [],          // todos los orgs (ordenados por score desc)
  rankByOrg: {},    // org -> ranking global (1-based)
  filtered: [],     // resultado de aplicar filtros
  markers: {},      // org -> { marker, el }
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

/* ----------------------- MARKERS (creados una vez) ----------------------- */
function buildMarkers() {
  state.all.forEach((o) => {
    const rank = state.rankByOrg[o.org];
    const el = document.createElement("div");
    el.className = "marker";

    const dot = document.createElement("div");
    dot.className = "marker-dot " + o.license;
    if (rank <= 3) {
      dot.classList.add("top");
      dot.dataset.rank = rank;
    }
    dot.innerHTML = `<img src="${escapeHtml(o.logo)}" alt="" />`;
    el.appendChild(dot);

    const popup = new maplibregl.Popup({ offset: 20, closeButton: true }).setHTML(popupHtml(o));
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

/* ----------------------- KPIs ----------------------- */
function renderKPIs(orgs) {
  const top = orgs.reduce((a, b) => (b.score > a.score ? b : a), orgs[0] || { score: 0, org: "—" });
  const countries = new Set(orgs.map((o) => o.country)).size;
  const openCount = orgs.filter((o) => o.license === "open").length;
  const openPct = orgs.length ? Math.round((openCount / orgs.length) * 100) : 0;

  const cards = [
    { label: "Modelos", value: orgs.length, sub: `${countries} países` },
    { label: "Top score", value: top.score || "—", sub: escapeHtml(top.org || "—") },
    { label: "Open source", value: openPct + "%", sub: `${openCount} de ${orgs.length}` },
    { label: "Países", value: countries, sub: "representados" },
  ];
  document.getElementById("kpis").innerHTML = cards
    .map(
      (c) => `<div class="kpi">
        <div class="k-label">${c.label}</div>
        <div class="k-value">${c.value}</div>
        <div class="k-sub">${c.sub}</div>
      </div>`
    )
    .join("");
}

/* ----------------------- LEADERBOARD ----------------------- */
function renderLeaderboard(orgs) {
  const lb = document.getElementById("leaderboard");
  const empty = document.getElementById("empty-state");
  empty.hidden = orgs.length > 0;

  lb.innerHTML = orgs
    .map((o) => {
      const rank = state.rankByOrg[o.org];
      return `<li class="lb-row r${rank}" data-org="${escapeHtml(o.org)}">
        <span class="lb-rank">${rank <= 3 ? ["🥇", "🥈", "🥉"][rank - 1] : rank}</span>
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

/* ----------------------- CHART (ECharts) ----------------------- */
let chart = null;
function renderChart(orgs) {
  const el = document.getElementById("chart");
  if (!chart) chart = echarts.init(el, null, { renderer: "canvas" });
  const data = [...orgs].sort((a, b) => a.score - b.score); // asc para barras horizontales
  const min = Math.min(...orgs.map((o) => o.score), 1200) - 20;

  chart.setOption({
    grid: { left: 8, right: 46, top: 8, bottom: 8, containLabel: true },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "#121830",
      borderColor: "rgba(255,255,255,0.14)",
      textStyle: { color: "#e8ecf6" },
      formatter: (p) => {
        const d = p[0];
        return `<b>${d.name}</b><br/>Score: <b>${d.value}</b>`;
      },
    },
    xAxis: {
      type: "value",
      min,
      axisLabel: { color: "#5f6b8a", fontSize: 10 },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
      axisLine: { show: false },
    },
    yAxis: {
      type: "category",
      data: data.map((o) => o.org),
      axisLabel: { color: "#9aa6c4", fontSize: 11 },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } },
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: data.map((o) => ({
          value: o.score,
          itemStyle: {
            borderRadius: [0, 5, 5, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: o.license === "open" ? "#0d9488" : "#4f46e5" },
              { offset: 1, color: o.license === "open" ? "#10b981" : "#a855f7" },
            ]),
          },
        })),
        barWidth: "58%",
        label: { show: true, position: "right", color: "#e8ecf6", fontSize: 11, fontWeight: 600 },
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

  renderKPIs(state.filtered);
  renderLeaderboard(state.filtered);
  renderChart(state.filtered);
  syncMarkerVisibility();
}

function populateCountryFilter(orgs) {
  const sel = document.getElementById("filter-country");
  [...new Set(orgs.map((o) => o.country))].sort().forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
  });
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
    state.all = (data.orgs || []).slice().sort((a, b) => b.score - a.score);
    state.all.forEach((o, i) => (state.rankByOrg[o.org] = i + 1));

    const date = (data.generated_at || "").slice(0, 10) || "?";
    document.getElementById("updated").textContent =
      `${state.all.length} modelos · ${date}`;

    populateCountryFilter(state.all);
    wireFilters();
    buildMarkers();
    applyFilters();
  })
  .catch((e) => {
    document.getElementById("updated").textContent = "Error cargando datos";
    console.error(e);
  });
