import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_data

ORGS = {
    "Anthropic": {"aliases": ["claude"], "city": "SF"},
    "OpenAI": {"aliases": ["gpt", "o1"], "city": "SF"},
    "Mistral AI": {"aliases": ["mistral", "mixtral"], "city": "Paris"},
}


def test_match_org_finds_by_alias_substring():
    assert build_data.match_org("claude-3.5-sonnet-20241022", ORGS) == "Anthropic"
    assert build_data.match_org("gpt-4o-2024-11-20", ORGS) == "OpenAI"
    assert build_data.match_org("mixtral-8x7b", ORGS) == "Mistral AI"


def test_match_org_returns_none_for_unknown():
    assert build_data.match_org("some-random-model-xyz", ORGS) is None


def test_match_org_is_case_insensitive():
    assert build_data.match_org("Claude-3-Opus", ORGS) == "Anthropic"


def test_build_orgs_joins_geo_and_keeps_best_score():
    orgs = {
        "Anthropic": {"aliases": ["claude"], "city": "San Francisco",
                      "country": "USA", "lat": 37.77, "lon": -122.41,
                      "logo": "a.png", "license": "proprietary"},
    }
    snapshot = {"models": [
        {"model": "claude-3-opus", "score": 1290, "url": "u1"},
        {"model": "claude-3.5-sonnet", "score": 1350, "url": "u2"},
    ]}
    result = build_data.build_orgs(snapshot, orgs)
    assert len(result) == 1
    row = result[0]
    assert row["org"] == "Anthropic"
    assert row["model"] == "claude-3.5-sonnet"
    assert row["score"] == 1350
    assert row["city"] == "San Francisco"
    assert row["lat"] == 37.77
    assert row["license"] == "proprietary"
    assert row["source_url"] == "u2"


def test_build_orgs_ignores_unknown_models():
    orgs = {"Anthropic": {"aliases": ["claude"], "city": "SF", "country": "USA",
                          "lat": 1.0, "lon": 2.0, "logo": "a.png", "license": "proprietary"}}
    snapshot = {"models": [{"model": "unknown-xyz", "score": 9999, "url": "u"}]}
    result = build_data.build_orgs(snapshot, orgs)
    assert result == []


def test_build_payload_uses_new_data_when_present():
    orgs = {"Anthropic": {"aliases": ["claude"], "city": "SF", "country": "USA",
                          "lat": 1.0, "lon": 2.0, "logo": "a.png", "license": "proprietary"}}
    snapshot = {"models": [{"model": "claude-x", "score": 1300, "url": "u"}]}
    payload = build_data.build_payload(snapshot, orgs, previous=None)
    assert len(payload["orgs"]) == 1
    assert "generated_at" in payload


def test_build_payload_falls_back_to_previous_when_empty():
    orgs = {"Anthropic": {"aliases": ["claude"], "city": "SF", "country": "USA",
                          "lat": 1.0, "lon": 2.0, "logo": "a.png", "license": "proprietary"}}
    empty_snapshot = {"models": []}
    previous = {"generated_at": "2020-01-01T00:00:00Z", "source": "x",
                "orgs": [{"org": "Anthropic"}]}
    payload = build_data.build_payload(empty_snapshot, orgs, previous=previous)
    assert payload == previous


def test_normalize_snapshot_handles_list_and_alt_keys():
    raw = [{"Model": "claude-x", "Arena Score": "1300", "url": "u"}]
    norm = build_data.normalize_snapshot(raw)
    assert norm["models"] == [{"model": "claude-x", "score": 1300.0, "url": "u"}]
