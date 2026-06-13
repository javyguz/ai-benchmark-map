# AI Benchmark Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un sitio estático con un mapa mundial interactivo que muestra labs de IA por ciudad sede, con su modelo principal y score de benchmark, refrescado a diario vía GitHub Actions.

**Architecture:** Sitio 100% estático (HTML/CSS/JS con MapLibre GL JS) que lee un `data/data.json` generado. Un script Python (`build_data.py`) descarga un snapshot de leaderboard público, lo cruza con una tabla manual de sedes (`orgs.json`) y produce `data.json`. Una GitHub Action corre el script a diario y despliega a GitHub Pages.

**Tech Stack:** MapLibre GL JS, HTML/CSS/JS vanilla, Python 3 (stdlib + `requests`), pytest, GitHub Actions, GitHub Pages.

---

## File Structure

- `data/orgs.json` — Tabla manual: organizaciones → ciudad, lat/lon, país, logo, licencia, alias de modelos. (entrada)
- `data/data.json` — Salida generada que consume la web. Se commitea un seed inicial.
- `scripts/build_data.py` — Lógica de ingesta: descarga snapshot, normaliza, hace join geo, escribe `data.json`. Funciones puras testeables + un `main()` con I/O.
- `tests/test_build_data.py` — Tests de las funciones puras de matching/join/resiliencia.
- `tests/fixtures/sample_snapshot.json` — Snapshot de leaderboard de ejemplo para tests.
- `index.html` — Estructura de la página y contenedor del mapa.
- `style.css` — Estilos del mapa, panel de filtros y popups.
- `app.js` — Carga `data.json`, pinta marcadores MapLibre, popups y filtros.
- `.github/workflows/update.yml` — Cron diario: corre script + deploy a Pages.
- `requirements.txt` — Dependencias Python (`requests`, `pytest`).
- `README.md` — Cómo correr local, cómo añadir orgs, cómo desplegar.

---

## Task 1: Estructura del proyecto y orgs.json seed

**Files:**
- Create: `data/orgs.json`
- Create: `requirements.txt`

- [ ] **Step 1: Crear `requirements.txt`**

```
requests==2.32.3
pytest==8.3.4
```

- [ ] **Step 2: Crear `data/orgs.json` con seed inicial**

Tabla manual con organizaciones reales. Cada `aliases` es una lista de substrings (lowercase) que aparecen en los nombres de modelo del leaderboard.

```json
{
  "Anthropic": {
    "city": "San Francisco", "country": "USA", "lat": 37.7749, "lon": -122.4194,
    "logo": "https://www.google.com/s2/favicons?domain=anthropic.com&sz=64",
    "license": "proprietary",
    "aliases": ["claude"]
  },
  "OpenAI": {
    "city": "San Francisco", "country": "USA", "lat": 37.7790, "lon": -122.4170,
    "logo": "https://www.google.com/s2/favicons?domain=openai.com&sz=64",
    "license": "proprietary",
    "aliases": ["gpt", "o1", "o3", "o4", "chatgpt"]
  },
  "Google DeepMind": {
    "city": "London", "country": "UK", "lat": 51.5336, "lon": -0.1276,
    "logo": "https://www.google.com/s2/favicons?domain=deepmind.google&sz=64",
    "license": "proprietary",
    "aliases": ["gemini", "gemma", "palm"]
  },
  "Mistral AI": {
    "city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522,
    "logo": "https://www.google.com/s2/favicons?domain=mistral.ai&sz=64",
    "license": "open",
    "aliases": ["mistral", "mixtral", "magistral", "codestral"]
  },
  "Meta AI": {
    "city": "Menlo Park", "country": "USA", "lat": 37.4848, "lon": -122.1484,
    "logo": "https://www.google.com/s2/favicons?domain=ai.meta.com&sz=64",
    "license": "open",
    "aliases": ["llama"]
  },
  "DeepSeek": {
    "city": "Hangzhou", "country": "China", "lat": 30.2741, "lon": 120.1551,
    "logo": "https://www.google.com/s2/favicons?domain=deepseek.com&sz=64",
    "license": "open",
    "aliases": ["deepseek"]
  },
  "Alibaba Qwen": {
    "city": "Hangzhou", "country": "China", "lat": 30.2500, "lon": 120.1600,
    "logo": "https://www.google.com/s2/favicons?domain=qwen.ai&sz=64",
    "license": "open",
    "aliases": ["qwen", "qwq"]
  },
  "xAI": {
    "city": "San Francisco", "country": "USA", "lat": 37.7700, "lon": -122.4000,
    "logo": "https://www.google.com/s2/favicons?domain=x.ai&sz=64",
    "license": "proprietary",
    "aliases": ["grok"]
  },
  "Cohere": {
    "city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832,
    "logo": "https://www.google.com/s2/favicons?domain=cohere.com&sz=64",
    "license": "open",
    "aliases": ["command", "aya"]
  },
  "01.AI": {
    "city": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074,
    "logo": "https://www.google.com/s2/favicons?domain=01.ai&sz=64",
    "license": "open",
    "aliases": ["yi-"]
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add data/orgs.json requirements.txt
git commit -m "feat: add orgs seed table and python deps"
```

---

## Task 2: Fixture de snapshot para tests

**Files:**
- Create: `tests/fixtures/sample_snapshot.json`

- [ ] **Step 1: Crear el fixture**

Estructura representativa de un snapshot de leaderboard: lista de entradas con nombre de modelo y score. Incluye un modelo desconocido (`some-random-model`) para probar que se ignora.

```json
{
  "models": [
    { "model": "claude-3.5-sonnet-20241022", "score": 1350, "url": "https://lmarena.ai" },
    { "model": "gpt-4o-2024-11-20", "score": 1365, "url": "https://lmarena.ai" },
    { "model": "gemini-1.5-pro-002", "score": 1340, "url": "https://lmarena.ai" },
    { "model": "claude-3-opus", "score": 1290, "url": "https://lmarena.ai" },
    { "model": "mistral-large-2407", "score": 1250, "url": "https://lmarena.ai" },
    { "model": "some-random-model-xyz", "score": 1400, "url": "https://lmarena.ai" }
  ]
}
```

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/sample_snapshot.json
git commit -m "test: add sample leaderboard snapshot fixture"
```

---

## Task 3: Función de matching modelo → organización

**Files:**
- Create: `scripts/build_data.py`
- Test: `tests/test_build_data.py`

- [ ] **Step 1: Escribir el test que falla**

```python
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_data

ORGS = {
    "Anthropic": {"aliases": ["claude"], "city": "SF"},
    "OpenAI": {"aliases": ["gpt", "o1"], "city": "SF"},
    "Mistral AI": {"aliases": ["mistral", "mixtral"], "city": "Paris"},
}


def test_match_org_finds_by_alias_substring():
    assert build_data.match_org("claude-3.5-sonnet-20241022", ORGS) == "Anthropic"
    assert build_data.match_org("gpt-4o-2024-11-20", ORGS) == "OpenAI"
    assert build_data.match_org("mixtral-8x7b", ORGS) == "Mistral AI"


def test_match_org_returns_none_for_unknown():
    assert build_data.match_org("some-random-model-xyz", ORGS) is None


def test_match_org_is_case_insensitive():
    assert build_data.match_org("Claude-3-Opus", ORGS) == "Anthropic"
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_build_data.py -v`
Expected: FAIL con `ModuleNotFoundError` o `AttributeError: module 'build_data' has no attribute 'match_org'`

- [ ] **Step 3: Implementación mínima**

Crear `scripts/build_data.py`:

```python
"""Genera data/data.json cruzando un snapshot de leaderboard con orgs.json."""


def match_org(model_name, orgs):
    """Devuelve el nombre de la organización cuyo alias aparece en model_name, o None."""
    name = model_name.lower()
    for org, meta in orgs.items():
        for alias in meta.get("aliases", []):
            if alias.lower() in name:
                return org
    return None
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `pytest tests/test_build_data.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/build_data.py tests/test_build_data.py
git commit -m "feat: add model-to-org matching by alias"
```

---

## Task 4: Construir la lista de orgs (join geo + mejor score por org)

**Files:**
- Modify: `scripts/build_data.py`
- Test: `tests/test_build_data.py`

- [ ] **Step 1: Escribir el test que falla**

Añadir a `tests/test_build_data.py`:

```python
def test_build_orgs_joins_geo_and_keeps_best_score():
    orgs = {
        "Anthropic": {"aliases": ["claude"], "city": "San Francisco",
                      "country": "USA", "lat": 37.77, "lon": -122.41,
                      "logo": "a.png", "license": "proprietary"},
    }
    snapshot = {"models": [
        {"model": "claude-3-opus", "score": 1290, "url": "u1"},
        {"model": "claude-3.5-sonnet", "score": 1350, "url": "u2"},
    ]}
    result = build_data.build_orgs(snapshot, orgs)
    assert len(result) == 1
    row = result[0]
    assert row["org"] == "Anthropic"
    assert row["model"] == "claude-3.5-sonnet"
    assert row["score"] == 1350
    assert row["city"] == "San Francisco"
    assert row["lat"] == 37.77
    assert row["license"] == "proprietary"
    assert row["source_url"] == "u2"


def test_build_orgs_ignores_unknown_models():
    orgs = {"Anthropic": {"aliases": ["claude"], "city": "SF", "country": "USA",
                          "lat": 1.0, "lon": 2.0, "logo": "a.png", "license": "proprietary"}}
    snapshot = {"models": [{"model": "unknown-xyz", "score": 9999, "url": "u"}]}
    result = build_data.build_orgs(snapshot, orgs)
    assert result == []
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_build_data.py::test_build_orgs_joins_geo_and_keeps_best_score -v`
Expected: FAIL con `AttributeError: module 'build_data' has no attribute 'build_orgs'`

- [ ] **Step 3: Implementación mínima**

Añadir a `scripts/build_data.py`:

```python
def build_orgs(snapshot, orgs):
    """Cruza el snapshot con orgs; una fila por org con su modelo de mayor score."""
    best = {}  # org -> entrada del snapshot con mayor score
    for entry in snapshot.get("models", []):
        org = match_org(entry["model"], orgs)
        if org is None:
            continue
        if org not in best or entry["score"] > best[org]["score"]:
            best[org] = entry

    rows = []
    for org, entry in best.items():
        meta = orgs[org]
        rows.append({
            "org": org,
            "city": meta["city"],
            "country": meta["country"],
            "lat": meta["lat"],
            "lon": meta["lon"],
            "logo": meta["logo"],
            "license": meta["license"],
            "model": entry["model"],
            "score": entry["score"],
            "source_url": entry.get("url", ""),
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/test_build_data.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/build_data.py tests/test_build_data.py
git commit -m "feat: build org rows with geo join and best score"
```

---

## Task 5: Resiliencia — conservar data.json previo si el snapshot está vacío

**Files:**
- Modify: `scripts/build_data.py`
- Test: `tests/test_build_data.py`

- [ ] **Step 1: Escribir el test que falla**

Añadir a `tests/test_build_data.py`:

```python
def test_build_payload_uses_new_data_when_present():
    orgs = {"Anthropic": {"aliases": ["claude"], "city": "SF", "country": "USA",
                          "lat": 1.0, "lon": 2.0, "logo": "a.png", "license": "proprietary"}}
    snapshot = {"models": [{"model": "claude-x", "score": 1300, "url": "u"}]}
    payload = build_data.build_payload(snapshot, orgs, previous=None)
    assert len(payload["orgs"]) == 1
    assert "generated_at" in payload


def test_build_payload_falls_back_to_previous_when_empty():
    orgs = {"Anthropic": {"aliases": ["claude"], "city": "SF", "country": "USA",
                          "lat": 1.0, "lon": 2.0, "logo": "a.png", "license": "proprietary"}}
    empty_snapshot = {"models": []}
    previous = {"generated_at": "2020-01-01T00:00:00Z", "source": "x",
                "orgs": [{"org": "Anthropic"}]}
    payload = build_data.build_payload(empty_snapshot, orgs, previous=previous)
    assert payload == previous
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_build_data.py::test_build_payload_falls_back_to_previous_when_empty -v`
Expected: FAIL con `AttributeError: module 'build_data' has no attribute 'build_payload'`

- [ ] **Step 3: Implementación mínima**

Añadir a `scripts/build_data.py` (al principio, los imports):

```python
import datetime
```

Y la función:

```python
def build_payload(snapshot, orgs, previous=None):
    """Construye el payload completo; si no hay filas y hay previo, devuelve el previo."""
    rows = build_orgs(snapshot, orgs)
    if not rows and previous is not None:
        return previous
    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "arena-ai-leaderboards",
        "orgs": rows,
    }
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `pytest tests/test_build_data.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/build_data.py tests/test_build_data.py
git commit -m "feat: keep previous data.json when snapshot is empty"
```

---

## Task 6: main() con descarga, I/O y logging de no-mapeados

**Files:**
- Modify: `scripts/build_data.py`
- Create: `data/data.json` (seed generado al correr)

- [ ] **Step 1: Implementar `fetch_snapshot`, `load_json`, `unmatched_models` y `main`**

Añadir a `scripts/build_data.py`:

```python
import json
import os
import sys
import urllib.request

# URL del snapshot diario más reciente del repo público de Arena AI.
# Si cambia la estructura del repo, actualizar esta constante.
SNAPSHOT_URL = (
    "https://raw.githubusercontent.com/oolong-tea-2026/"
    "arena-ai-leaderboards/main/data/latest.json"
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORGS_PATH = os.path.join(ROOT, "data", "orgs.json")
DATA_PATH = os.path.join(ROOT, "data", "data.json")


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_snapshot(url=SNAPSHOT_URL):
    """Descarga el snapshot; ante cualquier error devuelve {'models': []}."""
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - degradar con gracia
        print(f"WARN: no se pudo descargar el snapshot: {exc}", file=sys.stderr)
        return {"models": []}
    return normalize_snapshot(raw)


def normalize_snapshot(raw):
    """Adapta distintas formas de snapshot a {'models': [{model, score, url}]}.

    Acepta ya sea {'models': [...]} o una lista de filas. Cada fila debe tener
    una clave de nombre ('model'/'name'/'Model') y de score ('score'/'rating'/'Arena Score').
    """
    rows = raw.get("models", raw) if isinstance(raw, dict) else raw
    out = []
    for r in rows or []:
        name = r.get("model") or r.get("name") or r.get("Model")
        score = r.get("score") or r.get("rating") or r.get("Arena Score")
        if name is None or score is None:
            continue
        out.append({"model": name, "score": float(score), "url": r.get("url", "")})
    return {"models": out}


def unmatched_models(snapshot, orgs):
    return [e["model"] for e in snapshot.get("models", [])
            if match_org(e["model"], orgs) is None]


def main():
    orgs = load_json(ORGS_PATH, default={})
    previous = load_json(DATA_PATH, default=None)
    snapshot = fetch_snapshot()

    for m in unmatched_models(snapshot, orgs):
        print(f"UNMATCHED: {m}", file=sys.stderr)

    payload = build_payload(snapshot, orgs, previous=previous)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Escrito {DATA_PATH} con {len(payload['orgs'])} organizaciones")


if __name__ == "__main__":
    main()
```

Nota: mover el `import datetime` de la Task 5 junto a estos imports si quedó duplicado.

- [ ] **Step 2: Test de `normalize_snapshot` con fixture**

Añadir a `tests/test_build_data.py`:

```python
def test_normalize_snapshot_handles_list_and_alt_keys():
    raw = [{"Model": "claude-x", "Arena Score": "1300", "url": "u"}]
    norm = build_data.normalize_snapshot(raw)
    assert norm["models"] == [{"model": "claude-x", "score": 1300.0, "url": "u"}]
```

- [ ] **Step 3: Correr los tests**

Run: `pytest tests/test_build_data.py -v`
Expected: PASS (8 tests)

- [ ] **Step 4: Generar un data.json seed local**

Run: `python scripts/build_data.py`
Expected: imprime "Escrito ... con N organizaciones". Si la URL remota no responde aún, el `data.json` tendrá `orgs: []` — en ese caso, generar un seed manual mínimo editando `data/data.json` con 2-3 orgs reales tomadas de `orgs.json` para que la web tenga algo que mostrar.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_data.py tests/test_build_data.py data/data.json
git commit -m "feat: add fetch, normalize and main entrypoint for build_data"
```

---

## Task 7: La web — index.html y style.css

**Files:**
- Create: `index.html`
- Create: `style.css`

- [ ] **Step 1: Crear `index.html`**

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Benchmark Map</title>
  <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header>
    <h1>AI Benchmark Map</h1>
    <p id="updated">Cargando…</p>
  </header>
  <aside id="filters">
    <label>País <select id="filter-country"><option value="">Todos</option></select></label>
    <label>Licencia
      <select id="filter-license">
        <option value="">Todas</option>
        <option value="open">Open</option>
        <option value="proprietary">Propietario</option>
      </select>
    </label>
  </aside>
  <div id="map"></div>
  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Crear `style.css`**

```css
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; }
header { padding: 12px 16px; background: #0f172a; color: #fff; }
header h1 { margin: 0; font-size: 20px; }
header p { margin: 4px 0 0; font-size: 12px; color: #94a3b8; }
#filters {
  position: absolute; top: 70px; left: 12px; z-index: 1;
  background: #fff; padding: 12px; border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,.2); display: flex; flex-direction: column; gap: 8px;
}
#filters label { font-size: 12px; display: flex; flex-direction: column; gap: 4px; }
#map { position: absolute; top: 58px; bottom: 0; left: 0; right: 0; }
.popup-card { display: flex; gap: 8px; align-items: center; }
.popup-card img { width: 32px; height: 32px; }
.popup-card .model { font-weight: 600; }
.popup-card .score { color: #2563eb; font-weight: 700; }
```

- [ ] **Step 3: Commit**

```bash
git add index.html style.css
git commit -m "feat: add page shell and styles"
```

---

## Task 8: app.js — render de marcadores, popups y filtros

**Files:**
- Create: `app.js`

- [ ] **Step 1: Crear `app.js`**

```javascript
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
```

- [ ] **Step 2: Verificar manualmente en el navegador**

Run: `python -m http.server 8000`
Abrir `http://localhost:8000` en el navegador.
Expected: el mapa carga, aparecen marcadores (azul=propietario, verde=open). Click en un marcador muestra el popup con logo, modelo, score, licencia y enlace. Los dos filtros (país, licencia) reducen los marcadores.

(Si `data/data.json` tiene `orgs: []`, primero poblarlo con el seed manual de la Task 6, Step 4.)

- [ ] **Step 3: Commit**

```bash
git add app.js
git commit -m "feat: render markers, popups and filters from data.json"
```

---

## Task 9: GitHub Action — refresco diario + deploy a Pages

**Files:**
- Create: `.github/workflows/update.yml`

- [ ] **Step 1: Crear el workflow**

```yaml
name: Update data and deploy

on:
  schedule:
    - cron: "0 6 * * *"   # diario 06:00 UTC
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements.txt

      - name: Refrescar data.json
        run: python scripts/build_data.py

      - name: Commitear data.json si cambió
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/data.json
          git diff --staged --quiet || git commit -m "chore: refresh benchmark data"
          git push

      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: "."
      - uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/update.yml
git commit -m "ci: daily data refresh and GitHub Pages deploy"
```

- [ ] **Step 3: Nota de activación manual (no automatizable desde aquí)**

Tras hacer push al repo de GitHub: en Settings → Pages, elegir "GitHub Actions" como source. La primera ejecución del workflow desplegará el sitio. Documentar esto en el README (Task 10).

---

## Task 10: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Crear `README.md`**

```markdown
# AI Benchmark Map

Mapa mundial interactivo que muestra labs de IA por ciudad sede, con su modelo
principal y score de benchmark. Sitio estático, datos refrescados a diario.

## Desarrollo local

```bash
pip install -r requirements.txt
python scripts/build_data.py     # genera data/data.json
python -m http.server 8000       # abrir http://localhost:8000
```

## Tests

```bash
pytest -v
```

## Añadir una organización

Editar `data/orgs.json`: añadir una entrada con `city`, `country`, `lat`, `lon`,
`logo`, `license` (`open`|`proprietary`) y `aliases` (substrings del nombre de modelo
en el leaderboard). Volver a correr `python scripts/build_data.py`.

Los modelos que el script no logre mapear se imprimen como `UNMATCHED:` en stderr;
añadir sus alias a la org correspondiente.

## Despliegue (GitHub Pages)

1. Push del repo a GitHub.
2. Settings → Pages → Source: "GitHub Actions".
3. El workflow `.github/workflows/update.yml` refresca los datos a diario y despliega.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup, dev and deploy instructions"
```

---

## Self-Review Notes

- **Cobertura del spec:** mapa con marcadores por ciudad (Tasks 7-8), popups con logo/modelo/score/fuente (Task 8), filtros país + open/propietario (Task 8), ingesta con matching de alias (Tasks 3-4), logging de no-mapeados (Task 6), resiliencia ante snapshot vacío (Task 5), MapLibre sin token (Task 7), GitHub Pages + Action diaria (Task 9), una sede por org (orgs.json, Task 1). Fuera de alcance confirmado (histórico, choropleth) no se implementa. ✔
- **Consistencia de tipos:** `match_org`, `build_orgs`, `build_payload`, `normalize_snapshot`, `fetch_snapshot`, `load_json`, `unmatched_models`, `main` usados consistentemente. Campos de `data.json` (`org`, `city`, `country`, `lat`, `lon`, `logo`, `license`, `model`, `score`, `source_url`, `generated_at`, `orgs`) coinciden entre build_data.py y app.js. ✔
- **Riesgo conocido:** la `SNAPSHOT_URL` exacta del repo `arena-ai-leaderboards` puede diferir; `normalize_snapshot` + el fallback a previo + el seed manual de la Task 6 mitigan que la web quede vacía mientras se ajusta la URL real.
```
