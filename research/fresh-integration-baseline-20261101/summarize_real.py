#!/usr/bin/env python3
"""Create a compact, path-independent summary of a retained real qualification."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "reconstruction/harness"))

import verify_fresh_control  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(document: dict) -> str:
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def summarize(integration: Path, base_revision: str) -> dict:
    integration = integration.resolve(strict=True)
    fresh = integration / "fresh-control"
    receipt_path = fresh / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    outer = json.loads((integration / "report.json").read_text(encoding="utf-8"))
    verified = verify_fresh_control.verify(fresh)
    scores = {
        side: {key: value for key, value in receipt["scores"][side].items() if key != "ambiguous"}
              | {"ambiguous_count": len(receipt["scores"][side]["ambiguous"])}
        for side in ("base", "candidate")
    }
    return {
        "artifacts": {
            "count": len(receipt["artifacts"]),
            "retained_bytes": sum(row["bytes"] for row in receipt["artifacts"].values()),
        },
        "base_revision": base_revision,
        "builds": receipt["builds"],
        "captured_evidence": receipt["provenance"]["inputs"],
        "comparison": receipt["comparison"],
        "independent_verification": {
            key: verified[key] for key in
            ("accepted", "artifact_count", "comparison", "receipt_sha256", "schema")
        },
        "outer_report_sha256": sha256(integration / "report.json"),
        "parts": outer["parts"],
        "provenance_sha256": canonical_hash(receipt["provenance"]),
        "qualification": outer["qualification"],
        "scores": scores,
        "schema": "pump-fresh-control-real-qualification-v1",
        "toolchain": {
            key: receipt["provenance"][key] for key in
            ("cargo_sha256", "clang_sha256", "compiler_sha256", "objcopy_sha256",
             "objdump_sha256", "sdk_inventory_sha256", "target_library_manifest_sha256")
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("integration", type=Path)
    parser.add_argument("--base-revision", required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(args.integration, args.base_revision), indent=2, sort_keys=True))
