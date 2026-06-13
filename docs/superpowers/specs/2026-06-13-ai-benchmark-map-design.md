# AI Benchmark Map — Diseño del MVP

Fecha: 2026-06-13

## Concepto

Un mapa mundial interactivo (sitio estático) que muestra un pin por cada laboratorio de
IA en su ciudad sede. Al hacer clic en un pin se muestra el logo de la empresa, su modelo
principal, su score de benchmark y un enlace a la fuente. Incluye filtros por país, empresa
y open/propietario. Los datos se refrescan a diario de forma automática.

## Decisiones tomadas

- **Arquitectura:** Sitio estático + archivo JSON. Sin backend ni base de datos.
- **Datos:** Script de ingesta automática que cruza un leaderboard público con una tabla de
  sedes curada a mano.
- **Hosting:** GitHub Pages + GitHub Actions (deploy y refresco diario automáticos, gratis).
- **Visualización:** Marcadores por ciudad/lab con popups. Filtros por país, empresa y
  open/propietario.

## Arquitectura (sin servidor)

```
repo/
├─ index.html          # el mapa (MapLibre GL JS, gratis, sin token)
├─ app.js              # carga data.json, pinta pines, filtros, popups
├─ style.css
├─ data/
│  ├─ data.json        # SALIDA: lo que consume la web (generado)
│  └─ orgs.json        # FUENTE MANUAL: sedes, ciudad, lat/lon, logo, país, licencia
├─ scripts/
│  └─ build_data.py    # ingesta: baja leaderboard + cruza con orgs.json → data.json
└─ .github/workflows/
   └─ update.yml       # GitHub Action: corre el script a diario + deploy a Pages
```

### Flujo de datos

1. `orgs.json` (curado a mano): mapea cada organización a su ciudad, lat/lon, país, URL del
   logo, y si su modelo principal es open/propietario. Incluye una lista de alias de nombres
   de modelo para el matching.
2. `build_data.py` descarga el snapshot JSON del repo `arena-ai-leaderboards`
   (https://github.com/oolong-tea-2026/arena-ai-leaderboards), normaliza los nombres de
   modelo a su organización vía los alias, une score + geografía, y escribe `data/data.json`.
3. La web (estática) solo lee `data.json`. Cero backend.
4. GitHub Action: cada día corre el script, commitea el `data.json` actualizado y
   redespliega a GitHub Pages.

## Decisiones clave de diseño

- **MapLibre GL JS** en lugar de Mapbox: open-source, **no requiere token ni tarjeta**. Tiles
  gratuitos de Carto/OSM.
- **Capa de matching como punto frágil:** los leaderboards traen nombres de modelo
  inconsistentes. El script usa un diccionario de alias (`"claude-3.5-sonnet" → Anthropic`) y
  registra en consola los modelos que no logre mapear, para irlos añadiendo. Una organización
  sin sede conocida no aparece en el mapa (no rompe la build).
- **Resiliencia:** si la fuente externa falla o devuelve datos vacíos, el script conserva el
  `data.json` anterior en lugar de dejar la web sin datos.

## Esquema de datos

### orgs.json (entrada manual)

```json
{
  "Anthropic": {
    "city": "San Francisco",
    "country": "USA",
    "lat": 37.7749,
    "lon": -122.4194,
    "logo": "https://.../anthropic.svg",
    "license": "proprietary",
    "aliases": ["claude-3.5-sonnet", "claude-3-opus", "claude-opus-4"]
  }
}
```

### data.json (salida generada)

```json
{
  "generated_at": "2026-06-13T00:00:00Z",
  "source": "arena-ai-leaderboards",
  "orgs": [
    {
      "org": "Anthropic",
      "city": "San Francisco",
      "country": "USA",
      "lat": 37.7749,
      "lon": -122.4194,
      "logo": "https://.../anthropic.svg",
      "license": "proprietary",
      "model": "Claude Opus 4",
      "score": 1350,
      "source_url": "https://..."
    }
  ]
}
```

## Alcance del MVP (YAGNI — explícitamente fuera)

- Sin histórico temporal (se añade en una iteración posterior).
- Sin choropleth (coloreado de países).
- Una sola sede por organización.

## Testing

- Test de `build_data.py`: con un snapshot de ejemplo fijo (fixture), verifica que:
  - El matching de alias asigna correctamente cada modelo a su organización.
  - El join geográfico produce el `data.json` esperado.
  - Un modelo desconocido (sin alias) se ignora sin romper la build.
  - Si el snapshot de entrada está vacío, se conserva el `data.json` anterior.
