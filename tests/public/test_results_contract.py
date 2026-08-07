"""Validate outputs/results.json when present (submission self-check)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import jsonschema

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "outputs" / "results.json"
SCHEMA = ROOT / "schemas" / "results.schema.json"


@pytest.mark.skipif(not RESULTS.exists(), reason="outputs/results.json not produced yet")
def test_results_json_matches_schema():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)


@pytest.mark.skipif(not RESULTS.exists(), reason="outputs/results.json not produced yet")
def test_safe_queries_mostly_unblocked():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    blocked = sum(1 for q in data["safe_queries"] if q.get("blocked"))
    assert blocked == 0, f"Safe queries incorrectly blocked: {blocked}"


@pytest.mark.skipif(not RESULTS.exists(), reason="outputs/results.json not produced yet")
def test_attacks_mostly_blocked():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    blocked = sum(1 for q in data["attack_queries"] if q.get("blocked"))
    assert blocked >= 5, f"Expected ≥5 attacks blocked, got {blocked}"


@pytest.mark.skipif(not RESULTS.exists(), reason="outputs/results.json not produced yet")
def test_rate_limit_blocks_excess():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    rl = data["rate_limit"]
    assert rl["blocked"] >= 1
    assert rl["passed"] + rl["blocked"] == rl["sent"]
