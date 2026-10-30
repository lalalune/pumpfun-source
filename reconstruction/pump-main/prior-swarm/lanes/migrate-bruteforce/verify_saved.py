#!/usr/bin/env python3
"""Verify saved migrate-bruteforce evidence without rebuilding or editing binaries."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O.")

from pathlib import Path
import fcntl
import hashlib
import json
import subprocess
import sys

LANE = Path(__file__).resolve().parent
SWARM = LANE.parents[1]
SUMMARY_PATH = LANE / "SUMMARY.json"
summary = json.loads(SUMMARY_PATH.read_text())
state = json.loads((LANE / "SEARCH-STATE.json").read_text())
rows = state["results"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root):
    root = Path(root)
    return {str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()}


assert len(rows) == 26
assert len({r["source_sha256"] for r in rows}) == 26
assert len({r["unstripped_sha256"] for r in rows}) == 12
assert sum(r["baseline_memberships_retained"] for r in rows) == 23
assert summary["attempted_keys"] == [r["dedupe_key"] for r in rows]
assert summary["strict_gains"] == []
assert summary["strict_losses"] == ["0x52660"]
assert summary["best_candidate_strict_gains"] == []
assert summary["best_candidate_strict_losses"] == []
assert inventory(LANE / "source") == inventory(SWARM / "baseline/pump")

for row in rows:
    out = SWARM / row["output"]
    assert sha(out / "migrate_v2.rs") == row["source_sha256"]
    assert sha(out / "unstripped.so") == row["unstripped_sha256"]
    assert sha(out / "candidate.so") == row["stripped_sha256"]
    score = json.loads((out / "score.json").read_text())
    assert score["summary"]["candidate_sha256"] == row["unstripped_sha256"]
    assert score["summary"]["normalized"] == row["normalized"]
    assert score["summary"]["raw"] == row["raw"]
    assert score["summary"]["gains"] == row["gains"]
    assert score["summary"]["losses"] == row["losses"]
    assert score["windows"][str(0x4C158)]["normalized"] == row["target_official"]["normalized"]
    assert score["windows"][str(0x4C158)]["raw"] == row["target_official"]["raw"]

best = summary["best_candidate"]
assert best["name"] == "unified-expr-question-lines"
assert best["normalized"] == 1019 and best["raw"] == 188
assert best["target_official"]["normalized"] is False and best["target_official"]["raw"] is False
assert best["machine_blocks"] == [137, 137]
assert best["reduced_blocks"] == [112, 112]
assert best["topology"]["verified"] is True
assert best["physical_order_callees_depth2_equal"] is True
best_out = SWARM / best["output"]
assert sha(best_out / "migrate_v2.rs") == best["source_sha256"] == "7f970c3dcbb9806252369c3a2bd8f2f6849bc5a2bf9d9f2d394427d3227989e3"
assert sha(best_out / "unstripped.so") == best["unstripped_sha256"] == "d4aef468f45c4fcdd10888bb2e77794d4c2cda2ed3f2d343d11717100496c644"
assert sha(best_out / "candidate.so") == best["stripped_sha256"] == "59f5de65a736122297133f8f90631a774d5c53b08890abe3f9b7abd33613db6c"
assert len((best_out / "migrate_v2.rs").read_text().splitlines()) == len((SWARM / "baseline/pump/src/migrate_v2.rs").read_text().splitlines()) == 822
original_score = json.loads((best_out / "score.json").read_text())
verify_score = json.loads((best_out / "score-verify.json").read_text())
assert original_score == verify_score
assert verify_score["summary"]["normalized"] == 1019
assert verify_score["summary"]["raw"] == 188
assert verify_score["summary"]["gains"] == [] and verify_score["summary"]["losses"] == []
assert verify_score["summary"]["raw_gains"] == [] and verify_score["summary"]["raw_losses"] == []

with (SWARM / ".attempts.lock").open("r+") as lock:
    fcntl.flock(lock, fcntl.LOCK_SH)
    ledger = [json.loads(line) for line in (SWARM / "ATTEMPTS.jsonl").read_text().splitlines() if line.strip()]
    fcntl.flock(lock, fcntl.LOCK_UN)
for key in summary["attempted_keys"]:
    assert sum(r["dedupe_key"] == key for r in ledger) == 1, key
for key in summary["analysis_keys"]:
    assert sum(r["dedupe_key"] == key for r in ledger) == 1, key

verification = {
    "status": "incomplete_no_strict_window_gain",
    "targets": [hex(0x4C158)],
    "attempts_verified": 26,
    "distinct_sources": 26,
    "distinct_outputs": 12,
    "baseline_membership_preserving_candidates": 23,
    "membership_rejected_candidates": 3,
    "best_candidate": best["name"],
    "best_source_sha256": best["source_sha256"],
    "best_unstripped_sha256": best["unstripped_sha256"],
    "best_stripped_sha256": best["stripped_sha256"],
    "best_official_normalized": 1019,
    "best_official_raw": 188,
    "best_gains": [],
    "best_losses": [],
    "target_normalized": False,
    "target_raw": False,
    "target_topology_verified_diagnostic_only": True,
    "best_independent_rescore_equal_to_saved_score": True,
    "source_line_count_preserved": 822,
    "source_tree_restored_to_pinned_baseline": True,
    "all_attempt_and_analysis_keys_unique_in_shared_ledger": True,
    "new_runtime_executions": 0,
}
(LANE / "VERIFICATION.json").write_text(json.dumps(verification, indent=2) + "\n")
key = "migrate-bruteforce:0x4c158:e38a8b97a:verification-v1"
check = subprocess.run([sys.executable, str(SWARM / "log_attempt.py"), "check", "--dedupe-key", key], check=True, text=True, stdout=subprocess.PIPE)
if not json.loads(check.stdout)["duplicate"]:
    subprocess.run([
        sys.executable, str(SWARM / "log_attempt.py"), "record", "--lane", "migrate-bruteforce",
        "--approach", "saved-evidence-verification", "--target", hex(0x4C158),
        "--dedupe-key", key, "--hypothesis", "Recompute hashes, ledger uniqueness, source restoration, and official best-candidate rescore",
        "--status", "analyzed", "--data", json.dumps({"verification": verification, "output": "lanes/migrate-bruteforce/VERIFICATION.json"}, sort_keys=True, separators=(",", ":")),
    ], check=True, text=True, stdout=subprocess.PIPE)
if key not in summary["analysis_keys"]:
    summary["analysis_keys"].append(key)
summary["verification"] = "lanes/migrate-bruteforce/VERIFICATION.json"
SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(verification, indent=2))
