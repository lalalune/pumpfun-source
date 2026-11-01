#!/usr/bin/env python3
"""Produce paired persistent Mayhem V2/PumpSwap execution receipts."""
from __future__ import annotations

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

namespace = {"__file__": str(HERE / "runtime.py"), "__name__": "mayhem_v2_pumpswap_runtime"}
runtime_raw = (HERE / "runtime.py").read_bytes()
exec(compile(runtime_raw, str(HERE / "runtime.py"), "exec", dont_inherit=True), namespace)
plan = namespace["plan"]
run_image = namespace["run_image"]
sha256_bytes = namespace["sha256_bytes"]

ORIGINAL = ROOT / "evidence/original/mayhem/deployed.so"
ORIGINAL_SHA256 = "a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb"
CANDIDATE_SHA256 = "9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d"


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def input_paths() -> list[Path]:
    package = [path for path in HERE.iterdir() if path.is_file() and path.suffix in {".py", ".json"}]
    fixture_inputs = [
        ROOT / "scripts/mayhem_buy_v2_fixture.py",
        ROOT / "scripts/mayhem_sell_v2_fixture.py",
        ROOT / "scripts/mayhem_pump_swap_fixture.py",
        ROOT / "scripts/pump_trade_fixture.py",
        ROOT / "research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json",
        ROOT / "research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json",
        ROOT / "research/imported-lab/analysis/pump_fun/config-snapshot.json",
        ROOT / "reconstruction/mayhem/native-linux-qualification/QUALIFICATION.json",
    ]
    programs = [
        ROOT / "evidence/original/mayhem/deployed.so",
        ROOT / "evidence/original/pump/deployed.so",
        ROOT / "evidence/original/pump_amm/deployed.so",
        ROOT / "evidence/original/pump_fees/deployed.so",
    ]
    for name in ("spl_token", "spl_token_2022", "associated_token"):
        programs.extend(
            (ROOT / f"evidence/dependencies/{name}/capture.json", ROOT / f"evidence/dependencies/{name}/deployed.so")
        )
    sources = [path for path in (ROOT / "programs/mayhem").rglob("*") if path.is_file()]
    return sorted(set(package + fixture_inputs + programs + sources))


def inventory() -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in input_paths()}


def source_tree_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def require_outside_repository(path: Path) -> None:
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError("output must be outside the repository")


def canonical_line(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


def produce(candidate: Path, output: Path, original_control: bool = False) -> dict:
    require_outside_repository(output)
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise ValueError("candidate is not a regular file")
    if sha256_file(ORIGINAL) != ORIGINAL_SHA256:
        raise ValueError("captured Mayhem hash mismatch")
    expected = ORIGINAL_SHA256 if original_control else CANDIDATE_SHA256
    if sha256_file(candidate) != expected:
        raise ValueError("candidate is not admitted for the requested mode")
    initial_inventory = inventory()
    output.mkdir(parents=True, exist_ok=False)

    original_rows = run_image(ORIGINAL)
    candidate_rows = run_image(candidate)
    if inventory() != initial_inventory:
        raise ValueError("declared source or dependency input changed during execution")
    if sha256_file(candidate) != expected:
        raise ValueError("candidate changed during execution")
    if len(original_rows) != len(candidate_rows):
        raise AssertionError("paired execution count differs")
    paired = []
    for original, rebuilt in zip(original_rows, candidate_rows, strict=True):
        case_id = f"{original['lifecycle']}/{original['step']}"
        if case_id != f"{rebuilt['lifecycle']}/{rebuilt['step']}":
            raise AssertionError("paired case order differs")
        paired.append({"case_id": case_id, "original": original, "candidate": rebuilt})

    receipt_path = output / "receipts.jsonl"
    receipt_path.write_text("".join(canonical_line(row) for row in paired), encoding="utf-8", newline="\n")
    mayhem_sources = [path for path in input_paths() if path.is_relative_to(ROOT / "programs/mayhem")]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    report = {
        "schema": "mayhem-v2-pumpswap-lifecycle-report-v1",
        "scope": "Persistent signed Mayhem V2 and PumpSwap execution with synthetic preinitialized canonical state and captured dependency CPIs.",
        "source_commit": commit,
        "mode": "original_vs_original" if original_control else "original_vs_candidate",
        "fixture_classification": "synthetic_preinitialized",
        "original": {
            "path": str(ORIGINAL.relative_to(ROOT)),
            "bytes": ORIGINAL.stat().st_size,
            "sha256": ORIGINAL_SHA256,
        },
        "candidate": {
            "path": str(candidate),
            "bytes": candidate.stat().st_size,
            "sha256": sha256_file(candidate),
        },
        "plan": plan(),
        "input_sha256": initial_inventory,
        "mayhem_source_files": len(mayhem_sources),
        "mayhem_source_tree_sha256": source_tree_sha256(mayhem_sources),
        "receipt_file": receipt_path.name,
        "receipt_sha256": sha256_file(receipt_path),
        "observed_case_count": len(paired),
        "observed_signed_transactions": len(paired) * 2,
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if inventory() != initial_inventory or sha256_file(candidate) != expected:
        raise ValueError("input changed during publication")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--original-control", action="store_true")
    args = parser.parse_args()
    report = produce(args.candidate, args.output, args.original_control)
    print(json.dumps({key: report[key] for key in ("mode", "observed_case_count", "observed_signed_transactions", "receipt_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
