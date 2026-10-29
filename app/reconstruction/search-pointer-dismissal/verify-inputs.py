#!/usr/bin/env python3
"""Verify the original pointer-dismissal input list without changing its record."""

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RECORD_SHA256 = "0c49750699794674cc02a4acd9fd65148c84952fac1a1629ed4ccd905388c391"


def verify():
    record_bytes = (PACKET / "work-record.json").read_bytes()
    if hashlib.sha256(record_bytes).hexdigest() != RECORD_SHA256:
        raise ValueError("historical work record changed")
    record = json.loads(record_bytes)
    inputs = []
    for relative, expected in record["actualInputs"].items():
        if re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            raise ValueError(f"not a SHA-256 digest: {relative}")
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            # Installed pnpm dependencies can resolve outside the checkout.
            if relative != "app/packages/frontend/node_modules/@types/react/index.d.ts":
                raise ValueError(f"input outside checkout: {relative}")
        contents = path.read_bytes()
        actual = hashlib.sha256(contents).hexdigest()
        if actual != expected:
            raise ValueError(f"input digest differs: {relative}")
        inputs.append({"path": relative, "bytes": len(contents), "sha256": actual})
    return {
        "historicalPublicCommit": "440a495d4c37625f4f5b321d2d54df83475a62da",
        "historicalWorkRecordSha256": RECORD_SHA256,
        "inputCount": len(inputs),
        "allDigestsValidAndMatched": True,
        "inputs": inputs,
        "limits": [
            "Fresh byte verification of the original declared input list; not a new browser run.",
            "The installed React type file requires the pinned dependencies to be available.",
            "This does not expand the original input list into a complete dependency closure."
        ]
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2) + "\n", end="")
