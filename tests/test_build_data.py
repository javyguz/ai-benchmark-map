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
