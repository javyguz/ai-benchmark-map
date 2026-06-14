"""Genera data/data.json cruzando un snapshot de leaderboard con orgs.json."""

import datetime
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


def match_org(model_name, orgs):
    """Devuelve el nombre de la organización cuyo alias aparece en model_name, o None."""
    name = model_name.lower()
    for org, meta in orgs.items():
        for alias in meta.get("aliases", []):
            if alias.lower() in name:
                return org
    return None


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
        if not isinstance(r, dict):
            continue
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
