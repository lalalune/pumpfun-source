#!/usr/bin/env python3
"""Independently verify the retained stale-baseline correction receipt."""
from __future__ import annotations

import json
from pathlib import Path

from reproduce import canonical, reproduce


HERE = Path(__file__).resolve().parent


def main() -> int:
    expected = canonical(reproduce()).encode()
    retained = (HERE / "results.json").read_bytes()
    if retained != expected:
        raise SystemExit("results.json does not match a fresh recomputation")
    result = json.loads(retained)
    historical = result["historical_control"]
    fresh = result["fresh_control"]
    if not historical["accepted"] or historical["comparison"]["normalized_losses"]:
        raise SystemExit("historical witness no longer demonstrates the gap")
    if fresh["accepted"] or fresh["decision"] != "reject":
        raise SystemExit("fresh control did not reject the regression")
    if fresh["comparison"]["normalized_losses"] != ["0x100"]:
        raise SystemExit("fresh control did not identify normalized loss 0x100")
    if fresh["comparison"]["raw_losses"] != ["0x100"]:
        raise SystemExit("fresh control did not identify raw loss 0x100")
    real = json.loads((HERE / "real-qualification.json").read_text(encoding="utf-8"))
    if real.get("schema") != "pump-fresh-control-real-qualification-v1":
        raise SystemExit("real qualification has the wrong schema")
    if not real["qualification"]["accepted"] or not real["independent_verification"]["accepted"]:
        raise SystemExit("real qualification was not accepted twice")
    if real["comparison"] != real["independent_verification"]["comparison"]:
        raise SystemExit("real producer and independent comparisons differ")
    if any(real["comparison"][field] for field in
           ("missing", "added", "resized", "normalized_losses", "raw_losses")):
        raise SystemExit("real qualification contains a regression")
    if real["builds"]["base"]["unstripped_sha256"] \
            != real["builds"]["candidate"]["unstripped_sha256"]:
        raise SystemExit("real unstripped binaries unexpectedly differ")
    if real["builds"]["base"]["candidate_sha256"] \
            != real["builds"]["candidate"]["candidate_sha256"]:
        raise SystemExit("real stripped binaries unexpectedly differ")
    if real["scores"]["base"] != real["scores"]["candidate"]:
        raise SystemExit("real fresh scores unexpectedly differ")
    if real["artifacts"]["count"] != real["independent_verification"]["artifact_count"]:
        raise SystemExit("real artifact counts differ")
    print("verified fresh-integration stale-baseline correction")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
