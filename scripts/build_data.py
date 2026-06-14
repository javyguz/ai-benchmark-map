"""Genera data/data.json cruzando un snapshot de leaderboard con orgs.json."""


def match_org(model_name, orgs):
    """Devuelve el nombre de la organización cuyo alias aparece en model_name, o None."""
    name = model_name.lower()
    for org, meta in orgs.items():
        for alias in meta.get("aliases", []):
            if alias.lower() in name:
                return org
    return None
