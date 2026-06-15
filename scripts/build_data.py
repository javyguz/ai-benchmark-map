"""Genera data/data.json a partir del leaderboard real de Arena AI.

Fuente: https://github.com/oolong-tea-2026/arena-ai-leaderboards
Los snapshots viven en data/<YYYY-MM-DD>/text.json con la forma:
    { "meta": { "source_url", "last_updated", ... },
      "models": [ { "rank", "model", "vendor", "license", "score", ... } ] }

El leaderboard ya trae vendor + license + score, así que el match con la
tabla de sedes (data/orgs.json) es directo por nombre de vendor.
"""

import datetime
import json
import os
import sys
import urllib.request

REPO = "oolong-tea-2026/arena-ai-leaderboards"
API_DATA_URL = f"https://api.github.com/repos/{REPO}/contents/data"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main/data"

# Categorías de leaderboard a publicar (id en el repo, etiqueta para la UI).
# El orden define el orden del selector.
# Nota: la categoría "agent" se excluye a propósito — su leaderboard trae score=null
# (no usa puntajes Elo) y todo el dashboard es score-based.
CATEGORIES = [
    ("text", "Texto"),
    ("code", "Código"),
    ("vision", "Visión"),
    ("document", "Documentos"),
    ("search", "Búsqueda"),
    ("text-to-image", "Texto → Imagen"),
    ("image-edit", "Edición de imagen"),
    ("text-to-video", "Texto → Video"),
    ("image-to-video", "Imagen → Video"),
    ("video-edit", "Edición de video"),
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORGS_PATH = os.path.join(ROOT, "data", "orgs.json")
DATA_PATH = os.path.join(ROOT, "data", "data.json")


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _http_get_json(url):
    headers = {"User-Agent": "ai-benchmark-map", "Accept": "application/json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --------------------------------------------------------------------------- #
# Pure transforms (testeables sin red)
# --------------------------------------------------------------------------- #
def latest_date(listing):
    """Dado el listado de contents/data de GitHub, devuelve el dir de fecha más reciente."""
    dates = sorted(x["name"] for x in listing if x.get("type") == "dir")
    return dates[-1] if dates else None


def normalize_snapshot(raw):
    """Adapta el text.json crudo a {'models': [{model, vendor, license, score, url}]}."""
    meta = raw.get("meta", {}) if isinstance(raw, dict) else {}
    source_url = meta.get("source_url", "")
    out = []
    for r in (raw.get("models", []) if isinstance(raw, dict) else []):
        if not isinstance(r, dict):
            continue
        if r.get("model") is None or r.get("score") is None or r.get("vendor") is None:
            continue
        out.append(
            {
                "model": r["model"],
                "vendor": r["vendor"],
                "license": r.get("license", "proprietary"),
                "score": float(r["score"]),
                "url": source_url,
            }
        )
    return {"models": out}


def unmatched_vendors(snapshot, orgs):
    """Vendors del snapshot que no tienen sede en la tabla orgs (únicos, en orden)."""
    seen, out = set(), []
    for e in snapshot.get("models", []):
        v = e["vendor"]
        if v not in orgs and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def build_orgs(snapshot, orgs):
    """Una fila por vendor conocido, con su modelo de mayor score y su geo."""
    best = {}  # vendor -> entrada con mayor score
    for e in snapshot.get("models", []):
        v = e["vendor"]
        if v not in orgs:
            continue
        if v not in best or e["score"] > best[v]["score"]:
            best[v] = e

    rows = []
    for vendor, e in best.items():
        geo = orgs[vendor]
        rows.append(
            {
                "org": vendor,
                "city": geo["city"],
                "country": geo["country"],
                "lat": geo["lat"],
                "lon": geo["lon"],
                "logo": geo["logo"],
                "license": e["license"],
                "model": e["model"],
                "score": int(e["score"]),
                "source_url": e.get("url", ""),
            }
        )
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


def build_payload(rows_by_cat, date, previous=None):
    """Payload multi-categoría. Si todas las categorías quedan vacías y hay previo,
    conserva el previo (resiliencia). Solo incluye categorías con al menos una fila."""
    total = sum(len(rows) for rows in rows_by_cat.values())
    if total == 0 and previous is not None:
        return previous

    categories = [
        {"id": cid, "label": label, "count": len(rows_by_cat.get(cid, []))}
        for cid, label in CATEGORIES
        if rows_by_cat.get(cid)
    ]
    data = {cid: rows_by_cat[cid] for cid, _ in CATEGORIES if rows_by_cat.get(cid)}
    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "source": "arena-ai-leaderboards",
        "snapshot_date": date,
        "categories": categories,
        "data": data,
    }


# --------------------------------------------------------------------------- #
# Network
# --------------------------------------------------------------------------- #
def fetch_snapshots():
    """Descarga todas las categorías del snapshot más reciente.

    Devuelve ({cid: {'models': [...]}}, date). Ante fallo de red total: ({}, None).
    Las categorías que fallen individualmente quedan como {'models': []}.
    """
    try:
        listing = _http_get_json(API_DATA_URL)
        date = latest_date(listing)
    except Exception as exc:  # noqa: BLE001 - degradar con gracia
        print(f"WARN: no se pudo listar el snapshot: {exc}", file=sys.stderr)
        return {}, None
    if not date:
        return {}, None

    snapshots = {}
    for cid, _ in CATEGORIES:
        try:
            raw = _http_get_json(f"{RAW_BASE}/{date}/{cid}.json")
            snapshots[cid] = normalize_snapshot(raw)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: categoría '{cid}' no disponible: {exc}", file=sys.stderr)
            snapshots[cid] = {"models": []}
    return snapshots, date


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
def main():
    orgs = load_json(ORGS_PATH, default={})
    previous = load_json(DATA_PATH, default=None)
    snapshots, date = fetch_snapshots()

    # Reporta vendors sin sede (únicos en todas las categorías) para mantener orgs.json.
    seen = set()
    for snap in snapshots.values():
        for v in unmatched_vendors(snap, orgs):
            if v not in seen:
                seen.add(v)
                print(f"UNMATCHED VENDOR (sin sede en orgs.json): {v}", file=sys.stderr)

    rows_by_cat = {cid: build_orgs(snap, orgs) for cid, snap in snapshots.items()}
    payload = build_payload(rows_by_cat, date, previous=previous)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    counts = ", ".join(f"{c['id']}={c['count']}" for c in payload.get("categories", []))
    print(f"Escrito {DATA_PATH} (snapshot {date}): {counts}")


if __name__ == "__main__":
    main()
