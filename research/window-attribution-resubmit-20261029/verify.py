#!/usr/bin/env python3
"""Verify the resubmission packet from the committed bytes (stdlib only).

Checks every file against manifest.json and SHA256SUMS, then re-checks the key
content claims distilled in this packet. Run from a fresh checkout so the
hashes cover the committed bytes, not a pre-commit working copy.
"""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise SystemExit(f"FAIL: {message}")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest():
    manifest = json.loads((P / "manifest.json").read_text(encoding="utf-8"))
    require(isinstance(manifest, dict) and manifest, "manifest.json empty")
    for rel, meta in manifest.items():
        f = P / rel
        require(f.is_file(), f"missing file {rel}")
        require(f.stat().st_size == meta["bytes"], f"size mismatch {rel}")
        require(sha(f) == meta["sha256"], f"sha256 mismatch {rel}")


def check_sums():
    for line in (P / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        rel = rel.lstrip("*").strip()
        f = P / rel
        require(f.is_file(), f"missing file {rel}")
        require(sha(f) == digest.lower(), f"sha256 mismatch {rel}")


def check_content():
    readme = (P / "README.md").read_text(encoding="utf-8")
    require("resubmission" in readme.lower(), "README must state it is a resubmission")
    require("corrections" in readme.lower(), "README must carry the corrections")
    helpers = json.loads((P / "data" / "helpers-classification.json").read_text(encoding="utf-8"))
    windows = {w["target"]: w for w in helpers["windows"]}
    require(set(windows) == {"0x80df8", "0x83c00"}, "helper windows mismatch")
    require(windows["0x80df8"]["deployed_bytes"] == 2120, "0x80df8 deployed size")
    require(windows["0x80df8"]["candidate_bytes"] == 2056, "0x80df8 candidate size")
    require(windows["0x83c00"]["deployed_bytes"] == 3440, "0x83c00 deployed size")
    require(windows["0x83c00"]["candidate_bytes"] == 3408, "0x83c00 candidate size")
    for w in helpers["windows"]:
        require(w["tuples_equal"] is True, f"{w['target']} tuples must be equal")
    experiments = json.loads((P / "data" / "experiments-summary.json").read_text(encoding="utf-8"))
    require(len(experiments["experiments"]) == 15, "experiment count != 15")
    require("superseded_note" in experiments, "experiments must record the supersession")


if __name__ == "__main__":
    check_manifest()
    check_sums()
    check_content()
    print("verify: OK (window-attribution-resubmit-20261029)")
