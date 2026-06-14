# AI Benchmark Map

Mapa mundial interactivo que muestra labs de IA por ciudad sede, con su modelo
principal y score de benchmark. Sitio estático, datos refrescados a diario.

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

Editar `data/orgs.json`: añadir una entrada con `city`, `country`, `lat`, `lon`,
`logo`, `license` (`open`|`proprietary`) y `aliases` (substrings del nombre de modelo
en el leaderboard). Volver a correr `python scripts/build_data.py`.

Los modelos que el script no logre mapear se imprimen como `UNMATCHED:` en stderr;
añadir sus alias a la org correspondiente.

## Despliegue (GitHub Pages)

1. Push del repo a GitHub.
2. Settings → Pages → Source: "GitHub Actions".
3. El workflow `.github/workflows/update.yml` refresca los datos a diario y despliega.
