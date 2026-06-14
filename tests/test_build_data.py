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
