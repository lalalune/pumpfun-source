#!/usr/bin/env python3
"""Recompute the stale-baseline regression witness with the maintained comparator."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "reconstruction/harness"))

import compare_scores  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def admitted(document: dict) -> dict:
    # Do not write admission scratch data: mirror load_report's accepted form
    # after the checked fixture has itself been parsed with duplicate-key checks.
    windows = document["windows"]
    return {
        int(start): {
            "bytes": row["bytes"],
            "normalized": row["normalized"],
            "raw": row["raw"],
        }
        for start, row in windows.items()
    }


def reproduce() -> dict:
    fixture_path = HERE / "fixture.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    historical = admitted(fixture["historical_baseline"])
    current = admitted(fixture["current_base"])
    candidate = admitted(fixture["candidate"])
    before = compare_scores.compare(historical, candidate)
    after = compare_scores.compare(current, candidate)
    return {
        "base_revision": "638fce2a34c8433177f5b778f39cf79e70c971d4",
        "fixture_sha256": digest(fixture_path),
        "fresh_control": {
            "accepted": after["accepted"],
            "comparison": after,
            "decision": "reject",
        },
        "historical_control": {
            "accepted": before["accepted"],
            "builds_observed": ["candidate"],
            "comparison": before,
            "decision": "appears_acceptable",
        },
        "maintained_comparator_sha256": digest(ROOT / "reconstruction/harness/compare_scores.py"),
        "schema": "pump-fresh-integration-regression-result-v1",
    }


def canonical(document: dict) -> str:
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    sys.stdout.write(canonical(reproduce()))
