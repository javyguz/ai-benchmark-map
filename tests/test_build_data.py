import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_data

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_snapshot.json")

# Tabla geo de prueba (vendor -> sede). NoSuchLab a propósito NO está.
ORGS = {
    "Anthropic": {"city": "San Francisco", "country": "USA", "lat": 37.77, "lon": -122.41,
                  "logo": "a.png"},
    "Z.ai": {"city": "Beijing", "country": "China", "lat": 39.9, "lon": 116.4,
             "logo": "z.png"},
}


def load_fixture():
    with open(FIXTURE, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# latest_date
# --------------------------------------------------------------------------- #
def test_latest_date_picks_max_dir():
    listing = [
        {"name": "2026-06-12", "type": "dir"},
        {"name": "2026-06-14", "type": "dir"},
        {"name": "2026-06-13", "type": "dir"},
        {"name": "README.md", "type": "file"},
    ]
    assert build_data.latest_date(listing) == "2026-06-14"


def test_latest_date_empty():
    assert build_data.latest_date([{"name": "x", "type": "file"}]) is None


# --------------------------------------------------------------------------- #
# normalize_snapshot
# --------------------------------------------------------------------------- #
def test_normalize_snapshot_maps_fields_and_source_url():
    norm = build_data.normalize_snapshot(load_fixture())
    assert len(norm["models"]) == 4
    first = norm["models"][0]
    assert first == {
        "model": "claude-fable-5",
        "vendor": "Anthropic",
        "license": "proprietary",
        "score": 1510.0,
        "url": "https://arena.ai/leaderboard/text",
    }


def test_normalize_snapshot_skips_incomplete_rows():
    raw = {"meta": {}, "models": [
        {"model": "x", "vendor": "V"},           # sin score -> descartado
        {"model": "y", "vendor": "V", "score": 1},  # ok
    ]}
    assert len(build_data.normalize_snapshot(raw)["models"]) == 1


# --------------------------------------------------------------------------- #
# unmatched_vendors
# --------------------------------------------------------------------------- #
def test_unmatched_vendors_lists_unknown_once():
    snapshot = build_data.normalize_snapshot(load_fixture())
    assert build_data.unmatched_vendors(snapshot, ORGS) == ["NoSuchLab"]


# --------------------------------------------------------------------------- #
# build_orgs
# --------------------------------------------------------------------------- #
def test_build_orgs_joins_geo_keeps_best_score_and_uses_snapshot_license():
    snapshot = build_data.normalize_snapshot(load_fixture())
    rows = build_data.build_orgs(snapshot, ORGS)
    # NoSuchLab (1600) se ignora por no tener sede; quedan Anthropic y Z.ai.
    assert [r["org"] for r in rows] == ["Anthropic", "Z.ai"]
    anthropic = rows[0]
    assert anthropic["model"] == "claude-fable-5"   # el de mayor score, no claude-opus-4-6
    assert anthropic["score"] == 1510
    assert anthropic["city"] == "San Francisco"
    assert anthropic["license"] == "proprietary"
    assert anthropic["source_url"] == "https://arena.ai/leaderboard/text"
    assert rows[1]["license"] == "open"             # licencia tomada del snapshot


def test_build_orgs_ignores_unknown_vendors():
    snapshot = {"models": [
        {"model": "m", "vendor": "Ghost", "license": "open", "score": 9999, "url": "u"},
    ]}
    assert build_data.build_orgs(snapshot, ORGS) == []


# --------------------------------------------------------------------------- #
# build_payload (resiliencia)
# --------------------------------------------------------------------------- #
def test_build_payload_uses_new_data_and_includes_date():
    snapshot = build_data.normalize_snapshot(load_fixture())
    payload = build_data.build_payload(snapshot, ORGS, previous=None, date="2026-06-14")
    assert len(payload["orgs"]) == 2
    assert payload["snapshot_date"] == "2026-06-14"
    assert "generated_at" in payload


def test_build_payload_falls_back_to_previous_when_empty():
    previous = {"generated_at": "2020-01-01T00:00:00Z", "source": "x", "orgs": [{"org": "Old"}]}
    payload = build_data.build_payload({"models": []}, ORGS, previous=previous, date="2026-06-14")
    assert payload == previous
