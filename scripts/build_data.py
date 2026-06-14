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
LEADERBOARD = "text"  # leaderboard de modelos de texto
API_DATA_URL = f"https://api.github.com/repos/{REPO}/contents/data"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main/data"

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


def build_payload(snapshot, orgs, previous=None, date=None):
    """Payload final; si no hay filas y hay previo, conserva el previo (resiliencia)."""
    rows = build_orgs(snapshot, orgs)
    if not rows and previous is not None:
        return previous
    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "source": f"arena-ai-leaderboards/{LEADERBOARD}",
        "snapshot_date": date,
        "orgs": rows,
    }


# --------------------------------------------------------------------------- #
# Network
# --------------------------------------------------------------------------- #
def fetch_snapshot():
    """Descarga el text.json del snapshot más reciente. Ante error: ({'models': []}, None)."""
    try:
        listing = _http_get_json(API_DATA_URL)
        date = latest_date(listing)
        if not date:
            return {"models": []}, None
        raw = _http_get_json(f"{RAW_BASE}/{date}/{LEADERBOARD}.json")
    except Exception as exc:  # noqa: BLE001 - degradar con gracia
        print(f"WARN: no se pudo descargar el snapshot: {exc}", file=sys.stderr)
        return {"models": []}, None
    return normalize_snapshot(raw), date


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
def main():
    orgs = load_json(ORGS_PATH, default={})
    previous = load_json(DATA_PATH, default=None)
    snapshot, date = fetch_snapshot()

    for v in unmatched_vendors(snapshot, orgs):
        print(f"UNMATCHED VENDOR (sin sede en orgs.json): {v}", file=sys.stderr)

    payload = build_payload(snapshot, orgs, previous=previous, date=date)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Escrito {DATA_PATH} con {len(payload['orgs'])} organizaciones (snapshot {date})")


if __name__ == "__main__":
    main()
