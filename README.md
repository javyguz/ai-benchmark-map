# AI Benchmark Map

Mapa mundial interactivo que muestra labs de IA por ciudad sede, con su modelo
principal y score de benchmark. Sitio estático, datos refrescados a diario.

## Fuente de datos

Los scores vienen del leaderboard público **Arena AI** vía el repo
[`oolong-tea-2026/arena-ai-leaderboards`](https://github.com/oolong-tea-2026/arena-ai-leaderboards),
que publica un snapshot diario en `data/<YYYY-MM-DD>/text.json` (categoría de modelos
de texto). Cada entrada trae `model`, `vendor`, `license` y `score`.

`scripts/build_data.py` busca el snapshot más reciente, y para **cada categoría**
(texto, código, visión, documentos, búsqueda, texto→imagen, edición de imagen,
texto→video, imagen→video, edición de video) toma el modelo de mayor score por vendor
y lo cruza con la tabla de sedes `data/orgs.json` (geografía + logo). El resultado es
`data/data.json` con la forma `{ categories: [...], data: { <cat>: [orgs] } }`, que la
web consume con un selector de categoría. La categoría `agent` se excluye porque su
leaderboard no expone scores Elo (`score: null`).

## Desarrollo local

```bash
pip install -r requirements.txt
python scripts/build_data.py     # genera data/data.json
python -m http.server 8080       # abrir http://localhost:8080
```

## Tests

```bash
pytest -v
```

## Añadir una organización

El matching es por **nombre de vendor** (el campo `vendor` del leaderboard). Para que
un vendor aparezca en el mapa, añade una entrada en `data/orgs.json` cuya **clave sea
exactamente el nombre del vendor** (p. ej. `"Google"`, `"Z.ai"`, `"Bytedance"`) con
`city`, `country`, `lat`, `lon` y `logo`. La licencia y el score se toman del
leaderboard, no de aquí. Vuelve a correr `python scripts/build_data.py`.

Los vendors del leaderboard que no tengan sede en `orgs.json` se imprimen como
`UNMATCHED VENDOR:` en stderr al correr el script — añade su entrada para incluirlos.

## Despliegue (GitHub Pages)

1. Push del repo a GitHub (rama `master`).
2. Settings → Pages → Source: "GitHub Actions".
3. El workflow `.github/workflows/update.yml` baja el snapshot más reciente, refresca
   `data/data.json` a diario (06:00 UTC) y despliega a Pages.
