#!/usr/bin/env python3
"""Verify the saved local-only signed Pump Mayhem CPI differential receipt."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O.")

import base64
import gzip
import hashlib
import json
import struct
from pathlib import Path

from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from build_source_manifest import source_manifest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "repro/pump/mayhem-synthetic"
PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
MAYHEM = "MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e"
MINT = "DKsuJCZ3d3mLcNR3vPCb83qhDzS1YxR6XMvd8GWmpump"
TARGET_HASH = "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
EVENT_DISCRIMINATOR = bytes.fromhex("757be4b6a1a8dcd6")
COMPARED = ("error", "before", "after", "events", "inner", "return_data")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def assert_account_event(case):
    assert case["pump_instruction_reached"]
    if case["error"] is not None:
        assert case["events"] == []
        assert case["before"] == case["after"]
        return
    assert len(case["events"]) == 1
    event = base64.b64decode(case["events"][0].split("Program data: ", 1)[1], validate=True)
    assert len(event) == 96 and event[:8] == EVENT_DISCRIMINATOR
    assert event[16:48] == bytes(Pubkey.from_string(MINT))
    before = bytes.fromhex(case["before"][4]["data_hex"])
    after = bytes.fromhex(case["after"][4]["data_hex"])
    values = struct.unpack_from("<QQQQQQ", event, 48)
    assert values == (struct.unpack_from("<Q", before, 8)[0],
                      struct.unpack_from("<Q", before, 16)[0],
                      struct.unpack_from("<Q", after, 8)[0],
                      struct.unpack_from("<Q", after, 16)[0],
                      struct.unpack_from("<Q", after, 24)[0],
                      struct.unpack_from("<Q", after, 32)[0])
    assert len(case["inner"]) == 1 and len(case["inner"][0]) == 2
    event_cpi = case["inner"][0][1]["instruction"]["data"]
    assert bytes(event_cpi[1:]) == bytes.fromhex("e445a52e51cb9a1d") + event


def assert_regression_receipt(receipt, expected_cases):
    """Recount a regression receipt's case list instead of trusting its header.

    When a receipt includes a case list, its header must agree with that list.
    Historical aggregate receipts and count-only shapes keep their existing
    claimed-count check; this does not validate their nested case contents.
    """
    assert type(expected_cases) is int and expected_cases >= 0
    cases = receipt.get("cases")
    if isinstance(cases, list):
        assert len(cases) == expected_cases
        # A default of len(cases) compares that list with itself, so a receipt
        # that stopped declaring its header still passed the agreement check.
        assert "case_count" in receipt, "a case list requires a declared case_count"
        assert type(receipt["case_count"]) is int
        assert receipt["case_count"] == len(cases)
    else:
        count = receipt.get("case_count", cases)
        assert type(count) is int and count == expected_cases
    assert receipt["mismatches"] in ([], 0)


def main():
    report = json.loads(gzip.decompress((DIRECTORY / "differential.json.gz").read_bytes()))
    build = json.loads((DIRECTORY / "build-provenance.json").read_text())
    assert report["target_sha256"] == TARGET_HASH
    assert sha((ROOT / "evidence/original/pump/deployed.so").read_bytes()) == TARGET_HASH
    assert sha((DIRECTORY / "candidate.so").read_bytes()) == report["candidate_sha256"]
    assert sha((DIRECTORY / "synthetic-caller.so").read_bytes()) == report["synthetic_caller_sha256"]
    assert sha((DIRECTORY / "account-snapshot.json.gz").read_bytes()) == report["fixture_sha256"]
    boundary = json.loads((DIRECTORY / "direct-signer-boundary.json").read_text())
    assert boundary["target_sha256"] == TARGET_HASH
    assert boundary["snapshot_sha256"] == report["fixture_sha256"]
    assert "InstructionErrorCustom(2002)" in boundary["error"]
    assert boundary["outer_sol_vault_signer"] is False
    assert boundary["watched_accounts_unchanged"]
    # all() over an empty map is true; provenance must name the inputs it binds.
    assert isinstance(build.get("input_sha256"), dict) and build["input_sha256"]
    assert all(sha((ROOT / name).read_bytes()) == expected
               for name, expected in build["input_sha256"].items())
    assert source_manifest(ROOT / "programs/pump", ROOT / "programs/pump", ROOT, cwd=ROOT) == build["program_source_sha256"]
    assert build["full_byte_equality"] is False and build["first_difference"] == 24
    assert build["candidate_sha256"] == report["candidate_sha256"]
    assert build["clean_build_equality"] and len(build["builds"]) == 2
    for row in build["builds"]:
        assert row["artifact_sha256"] == report["candidate_sha256"]
        log = (DIRECTORY / f'clean-build-{row["run"]}.log').read_bytes()
        assert sha(log) == row["normalized_build_log_sha256"]
        assert b"Finished `release` profile" in log
    regression = json.loads((DIRECTORY / "regression/summary.json").read_text())
    assert regression["candidate_sha256"] == report["candidate_sha256"]
    assert regression["original_sha256"] == TARGET_HASH
    assert regression["total_cases"] == 9161 and regression["total_mismatches"] == 0
    assert [row["cases"] for row in regression["rows"]] == [7957, 507, 649, 48]
    for row in regression["rows"]:
        raw = (ROOT / row["receipt_file"]).read_bytes()
        assert sha(raw) == row["receipt_sha256"] and len(raw) == row["receipt_bytes"]
        receipt = json.loads(gzip.decompress(raw))
        assert_regression_receipt(receipt, row["cases"])
    fixture = json.loads(gzip.decompress((DIRECTORY / "account-snapshot.json.gz").read_bytes()))
    assert fixture["context_slot"] == report["fixture_slot"]
    assert fixture["accounts"][2]["address"] == MINT
    assert len(report["cases"]) == len(report["candidate_cases"]) == len(report["comparison"]) == 25
    assert sum(case["error"] is None for case in report["cases"]) == 13
    for target, candidate, compared in zip(report["cases"], report["candidate_cases"], report["comparison"]):
        assert target["case"] == candidate["case"] == compared["case"]
        assert target["binary_sha256"] == TARGET_HASH
        assert candidate["binary_sha256"] == report["candidate_sha256"]
        for case in (target, candidate):
            tx_bytes = base64.b64decode(case["signed_transaction_base64"], validate=True)
            assert sha(tx_bytes) == case["signed_transaction_sha256"]
            tx = VersionedTransaction.from_bytes(tx_bytes)
            assert (tx.signatures and all(tx.verify_with_results())) and case["signatures_valid"]
            message = tx.message
            assert str(message.account_keys[message.instructions[0].program_id_index]) == MAYHEM
            assert_account_event(case)
        assert target["signed_transaction_base64"] == candidate["signed_transaction_base64"]
        assert set(compared["equal"]) == set(COMPARED)
        assert all(compared["equal"].values())
        assert all(target[key] == candidate[key] for key in COMPARED)
    assert len([c for c in report["cases"] if c["error"] and "6024" in c["error"]]) == 4
    assert len([c for c in report["cases"] if c["error"] and "4102" in c["error"]]) == 1
    print(json.dumps({"result": "pass", "scope": "synthetic local Mayhem-ID caller, no live route",
                      "signed_cases": 25, "bounded_matches": 25, "successes": 13,
                      "target_sha256": TARGET_HASH,
                      "candidate_sha256": report["candidate_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
