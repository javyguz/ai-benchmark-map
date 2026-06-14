const map = new maplibregl.Map({
  container: "map",
  style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
  center: [10, 30],
  zoom: 1.5,
});

let allOrgs = [];
let markers = [];

function clearMarkers() {
  markers.forEach((m) => m.remove());
  markers = [];
}

function popupHtml(o) {
  return `<div class="popup-card">
    <img src="${o.logo}" alt="${o.org}" />
    <div>
      <div>${o.org} · ${o.city}, ${o.country}</div>
      <div class="model">${o.model}</div>
      <div><span class="score">${o.score}</span> · ${o.license}</div>
      <a href="${o.source_url}" target="_blank" rel="noopener">fuente</a>
    </div>
  </div>`;
}

function render(orgs) {
  clearMarkers();
  orgs.forEach((o) => {
    const popup = new maplibregl.Popup({ offset: 18 }).setHTML(popupHtml(o));
    const marker = new maplibregl.Marker({ color: o.license === "open" ? "#16a34a" : "#2563eb" })
      .setLngLat([o.lon, o.lat])
      .setPopup(popup)
      .addTo(map);
    markers.push(marker);
  });
}

function applyFilters() {
  const country = document.getElementById("filter-country").value;
  const license = document.getElementById("filter-license").value;
  render(
    allOrgs.filter(
      (o) => (!country || o.country === country) && (!license || o.license === license)
    )
  );
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

fetch("data/data.json")
  .then((r) => r.json())
  .then((data) => {
    allOrgs = data.orgs || [];
    document.getElementById("updated").textContent =
      `${allOrgs.length} organizaciones · actualizado ${data.generated_at || "?"}`;
    populateCountryFilter(allOrgs);
    render(allOrgs);
  })
  .catch((e) => {
    document.getElementById("updated").textContent = "Error cargando datos";
    console.error(e);
  });

document.getElementById("filter-country").addEventListener("change", applyFilters);
document.getElementById("filter-license").addEventListener("change", applyFilters);
