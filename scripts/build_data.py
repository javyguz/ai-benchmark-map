"""Genera data/data.json cruzando un snapshot de leaderboard con orgs.json."""

import datetime


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
