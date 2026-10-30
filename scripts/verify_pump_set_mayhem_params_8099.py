"""Verify the merged-source synthetic Mayhem CPI receipt and builds."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O.")

import base64
import contextlib
import gzip
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path

from solders.transaction import VersionedTransaction

import pump_set_mayhem_params_synthetic_cpi as differential
import verify_pump_set_mayhem_params_synthetic as historical


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "repro/pump/mayhem-synthetic-8099"
SOURCE_BASE = "80990317bd9c0363e071646b892490886d7bf946"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    first = json.loads((PACKAGE / "build-comparison.json").read_text())
    second = json.loads((PACKAGE / "second-build-comparison.json").read_text())
    repro = json.loads((PACKAGE / "build-reproducibility.json").read_text())
    receipt = json.loads(gzip.decompress((PACKAGE / "differential.json.gz").read_bytes()))
    candidate = PACKAGE / "candidate.so"
    caller = PACKAGE / "synthetic-caller.so"
    fixture = PACKAGE / "account-snapshot.json.gz"
    assert repro["source_base_commit"] == SOURCE_BASE
    assert repro["candidate_sha256"] == receipt["candidate_sha256"] == sha(candidate)
    assert first["source_sha256"] == second["source_sha256"] == repro["source_sha256"]
    assert first["selected_toolchain"] == second["selected_toolchain"] == "v1.44"
    assert first["comparison"]["candidate_sha256"] == second["comparison"]["candidate_sha256"] == sha(candidate)
    assert not first["comparison"]["full_byte_equality"] and repro["builds_identical"]
    assert all(sha(ROOT / name) == digest for name, digest in repro["source_sha256"].items())
    assert repro["differential_script_sha256"] == sha(Path(differential.__file__))
    for attempt_name in ("build-attempt.json", "second-build-attempt.json"):
        attempt = json.loads((PACKAGE / attempt_name).read_text())
        assert attempt["returncode"] == 0 and attempt["source_unchanged"]
        assert attempt["source_sha256"] == repro["source_sha256"]
    for build, log_name in ((first, "build.log.gz"), (second, "second-build.log.gz")):
        assert hashlib.sha256(gzip.decompress((PACKAGE / log_name).read_bytes())).hexdigest() == build["build_log_sha256"]
    assert receipt["target_sha256"] == sha(ROOT / "evidence/original/pump/deployed.so")
    assert receipt["synthetic_caller_sha256"] == sha(caller)
    assert receipt["fixture_sha256"] == sha(fixture)
    boundary = json.loads((PACKAGE / "direct-signer-boundary.json").read_text())
    assert boundary["snapshot_sha256"] == sha(fixture)
    assert boundary["outer_sol_vault_signer"] is False and boundary["watched_accounts_unchanged"]

    regression = json.loads((PACKAGE / "regression-summary.json").read_text())
    quote_file = PACKAGE / "quote-control-regression.json.gz"
    curve_file = PACKAGE / "multi-hop-regression.json.gz"
    quote = json.loads(gzip.decompress(quote_file.read_bytes()))
    curve = json.loads(gzip.decompress(curve_file.read_bytes()))
    assert regression["candidate_sha256"] == sha(candidate)
    assert regression["quote_control"]["receipt_sha256"] == sha(quote_file)
    assert regression["multi_hop_curve"]["receipt_sha256"] == sha(curve_file)
    assert quote["cases"] == 507 and quote["mismatches"] == 0
    assert all(sha(ROOT / path) == digest for path, digest in quote["bound_inputs_sha256"].items())
    assert curve["case_count"] == curve["passed"] == 56
    assert curve["candidate_sha256"] == sha(candidate)

    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "replay.json.gz"
        prior_argv = sys.argv
        try:
            sys.argv = [differential.__file__, "--candidate", str(candidate),
                        "--caller", str(caller), "--output", str(output)]
            with contextlib.redirect_stdout(io.StringIO()):
                differential.main()
        finally:
            sys.argv = prior_argv
        assert json.loads(gzip.decompress(output.read_bytes())) == receipt

    assert len(receipt["cases"]) == len(receipt["candidate_cases"]) == 25
    assert sum(case["error"] is None for case in receipt["cases"]) == 13
    for original, current, comparison in zip(
            receipt["cases"], receipt["candidate_cases"], receipt["comparison"]):
        assert all(comparison["equal"].values())
        for case in (original, current):
            tx = VersionedTransaction.from_bytes(
                base64.b64decode(case["signed_transaction_base64"]))
            assert all(tx.verify_with_results()) and case["signatures_valid"]
            historical.assert_account_event(case)
    print(json.dumps({"verified": True, "synthetic_signed_cases": 25,
                      "bounded_matches": 25, "successes": 13,
                      "candidate_sha256": sha(candidate)}))


if __name__ == "__main__":
    main()
