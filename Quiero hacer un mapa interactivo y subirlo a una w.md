<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Quiero hacer un mapa interactivo y subirlo a una web que este en tiempo real entre comillas trackeando los benchmarks de modelos de inteligencia artificial, es decir que puedas ver el mapa mundi, y por pais salga el modelo y por ciudad en donde fue creado y el logo de la empresa junto con su benchmark, existe alguna tecnologica o pagina web similar? Tendria que utilizar los datos publicos de benchmarks existentes

Sí, **sí existe espacio real** para esa web, y de hecho tu idea tiene bastante sentido porque hoy hay leaderboards y dashboards de benchmarks, pero no es común verlos geolocalizados en un mapa mundi con país, ciudad de origen, logo de empresa y benchmark consolidado en una sola experiencia.[^1][^2]

## Qué ya existe

Hay varias referencias parciales, pero ninguna parece resolver exactamente tu concepto de “mapa + benchmark + procedencia geográfica”. Epoch AI tiene un dashboard de benchmarks para explorar rendimiento por modelo y benchmark, pero no está centrado en geolocalización de labs o ciudades.[^3][^2]

También existen sitios como Artificial Analysis, OpenRouter Rankings, Scale Labs, LiveBench y agregadores tipo ALL-Bench o LLM Stats, que comparan modelos por calidad, precio, velocidad o benchmarks compuestos; aun así, su foco es ranking y análisis, no visualización geográfica por país/ciudad.[^4][^5][^6][^7][^8]

## Referencias útiles

Una fuente interesante para datos “casi en tiempo real” es el repo `arena-ai-leaderboards`, que publica snapshots diarios estructurados en JSON de leaderboards de Arena AI y además expone un endpoint REST no oficial con histórico.[^9][^1]

Para benchmarks agregados, Epoch AI ofrece una base de resultados de benchmarks y Artificial Analysis muestra índices compuestos y comparativas entre modelos; eso te serviría como capa de performance.[^7][^10][^8][^3]

## Viabilidad técnica

Tu idea es perfectamente viable como web app: un frontend con mapa interactivo, capas de filtros y tarjetas por modelo; y un backend pequeño que haga ETL diario desde fuentes públicas, normalice nombres de modelos/empresas y añada metadatos geográficos manuales o semi-manuales.[^3][^1]

La parte difícil no es el mapa, sino la **unificación de datos**: muchos leaderboards públicos sí traen modelo, vendor y score, pero normalmente no incluyen ciudad exacta de creación, así que esa dimensión tendrías que enriquecerla con una tabla propia de empresas/labs y sus sedes principales.[^2][^1]

## Stack recomendado

Para el mapa, usaría Mapbox GL JS, Leaflet o deck.gl; para una experiencia moderna, filtros y tarjetas, React/Next.js encaja muy bien. Como ya trabajas con Python y FastAPI, un backend con FastAPI + Postgres te vendría natural para ingestión, cache y API pública.[^1]

La arquitectura mínima sería:

- Frontend: Next.js + Mapbox/Leaflet.
- Backend: FastAPI.
- Base de datos: PostgreSQL con tablas `models`, `organizations`, `benchmarks`, `benchmark_results`, `locations`.
- Jobs programados: GitHub Actions o cron para refrescar snapshots diarios.[^1]


## Fuentes de datos públicas

Las más útiles para arrancar serían estas:

- Arena AI snapshots no oficiales, porque ya vienen en JSON y con histórico diario.[^9][^1]
- Epoch AI, para resultados de benchmarks y tendencias de capacidades.[^2][^3]
- Artificial Analysis, para índices compuestos y comparaciones amplias.[^8][^7]
- LiveBench / ALL-Bench / otros agregadores públicos, como capa complementaria o para contrastar.[^11][^6][^3]


## Qué haría yo primero

Empezaría con un MVP simple: un mapa con 20–40 organizaciones, una sola localización por empresa, y 2 o 3 métricas por modelo, por ejemplo Arena score, benchmark compuesto y tipo de licencia.[^7][^9][^1]

Luego añadiría:

- Filtros por país, empresa, benchmark y open/proprietary.
- Popups con logo, modelo principal, score y enlace a la fuente.
- Historial temporal para ver cómo cambia el liderazgo por región.[^9][^1]

Un ejemplo de registro sería: “Anthropic → San Francisco, USA → Claude X → score Arena / índice compuesto / licencia / última actualización”. El mapa no te diría necesariamente dónde se entrenó físicamente el modelo, sino la ciudad/lab de origen de la organización, que es una definición mucho más mantenible.[^1]

Hoy no veo una página claramente igual a la que propones; lo más parecido son leaderboards, dashboards de benchmarks y repos con snapshots diarios, pero no una interfaz geográfica consolidada.[^2][^7][^9]

Si quieres, te puedo proponer en el siguiente mensaje un diseño concreto del MVP: esquema de base de datos, fuentes exactas, endpoints de FastAPI y cómo montar el mapa interactivo en Next.js.
<span style="display:none">[^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29]</span>

<div align="center">⁂</div>

[^1]: https://gptbased.com

[^2]: https://epoch.ai/benchmarks

[^3]: https://lmmarketcap.com/benchmarks/livebench

[^4]: https://labs.scale.com/leaderboard

[^5]: https://openrouter.ai/rankings

[^6]: https://magichour.ai/model-leaderboard

[^7]: https://artificialanalysis.ai/models

[^8]: https://artificialanalysis.ai

[^9]: https://github.com/oolong-tea-2026/arena-ai-leaderboards

[^10]: https://artificialanalysis.ai/evaluations

[^11]: https://github.com/final-bench/ALL-Bench-Leaderboard

[^12]: https://www.reddit.com/r/LLMDevs/comments/1mwt4fq/i_built_this_ai_performance_vs_price_comparison/

[^13]: https://llm-stats.com

[^14]: https://enterprisedna.co/directories/apps/openrouter-llm-rankings/

[^15]: https://typethink.ai/leaderboard

[^16]: https://github.com/topics/lmarena

[^17]: https://en.wikipedia.org/wiki/Hugging_Face

[^18]: https://huggingface.co/docs/hub/index

[^19]: https://github.com/fboulnois/llm-leaderboard-csv

[^20]: https://github.com/BenchGecko/awesome-llm-benchmarks

[^21]: https://huggingface.co/docs/hub/datasets-usage

[^22]: https://github.com/lmarena/arena-rank

[^23]: https://runbenchhub.com

[^24]: https://huggingface.co

[^25]: https://github.com/nakasyou/lmarena-history

[^26]: https://github.com/brandonhimpfen/awesome-ai-benchmarks-evaluation

[^27]: https://docs.alliancecan.ca/wiki/Huggingface

[^28]: https://github.com/lmarena

[^29]: https://github.com/fixie-ai/ai-benchmarks

