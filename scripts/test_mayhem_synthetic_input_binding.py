#!/usr/bin/env python3
"""Build inputs must bind at least one file.

verify_pump_set_mayhem_params_synthetic.py checks the build provenance with
``all(sha(ROOT / name) == expected for name, expected in build["input_sha256"].items())``.
``all()`` over an empty map is true, so a provenance file that binds no input
(the synthetic caller crate, the IDL excerpt, the saved receipts) passed and
the verifier printed ``"result": "pass"``. These tests drive the real main()
on a complete hand-built package in a temporary root, with only the
transaction parser and the source-manifest builder replaced by stubs.
"""

import base64
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
VERIFIER = SCRIPTS / "verify_pump_set_mayhem_params_synthetic.py"
MINT = "DKsuJCZ3d3mLcNR3vPCb83qhDzS1YxR6XMvd8GWmpump"
DISCRIMINATOR = bytes.fromhex("757be4b6a1a8dcd6")
COMPARED = ("error", "before", "after", "events", "inner", "return_data")

DRIVER = r'''
import importlib.util, json, sys
from pathlib import Path
scripts, root = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location("stub_synthetic_verifier", scripts / "verify_pump_set_mayhem_params_synthetic.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
stub = json.loads((root / "stub-constants.json").read_text())

class StubInstruction:
    program_id_index = 0

class StubMessage:
    account_keys = [module.MAYHEM]
    instructions = [StubInstruction()]

class StubTransaction:
    message = StubMessage()
    @staticmethod
    def from_bytes(raw):
        return StubTransaction()
    def verify_with_results(self):
        return [True]

module.ROOT = root
module.DIRECTORY = root / "repro/pump/mayhem-synthetic"
module.TARGET_HASH = stub["target_sha256"]
module.VersionedTransaction = StubTransaction
module.source_manifest = lambda *args, **kwargs: stub["program_source_sha256"]
module.main()
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def account(value):
    return {"data_hex": value.hex()}


def case(index, error, binary):
    before = [{}] * 4 + [account(struct.pack("<QQQQQ", 0, 10 + index, 20 + index, 0, 0))]
    if error is None:
        after = [{}] * 4 + [account(struct.pack("<QQQQQ", 0, 30 + index, 40 + index, 50 + index, 60 + index))]
        event = (DISCRIMINATOR + bytes(8) + base58_mint() +
                 struct.pack("<QQQQQQ", 10 + index, 20 + index, 30 + index, 40 + index, 50 + index, 60 + index))
        events = ["Program data: " + base64.b64encode(event).decode()]
        cpi = list(b"\x00" + bytes.fromhex("e445a52e51cb9a1d") + event)
        inner = [[{}, {"instruction": {"data": cpi}}]]
    else:
        after, events, inner = before, [], []
    tx = ("stub-transaction-%d" % index).encode()
    return {"case": "stub_case_%d" % index, "binary_sha256": binary, "error": error,
            "before": before, "after": after, "events": events, "inner": inner,
            "return_data": None, "pump_instruction_reached": True,
            "signed_transaction_base64": base64.b64encode(tx).decode(),
            "signed_transaction_sha256": sha(tx), "signatures_valid": True}


def base58_mint():
    from solders.pubkey import Pubkey
    return bytes(Pubkey.from_string(MINT))


def errors():
    rows = [None] * 13
    rows += ["InstructionErrorCustom(6024)"] * 4 + ["InstructionErrorCustom(4102)"]
    rows += ["InstructionErrorCustom(6000)"] * 7
    return rows


def build_package(root, input_sha256=None):
    directory = root / "repro/pump/mayhem-synthetic"
    target = write(root / "evidence/original/pump/deployed.so", b"stub-target-image")
    candidate = write(directory / "candidate.so", b"stub-candidate-image")
    caller = write(directory / "synthetic-caller.so", b"stub-caller-image")
    caller_source = write(root / "research/synthetic-mayhem-cpi/src/lib.rs", b"// stub caller source\n")
    snapshot = write(directory / "account-snapshot.json.gz", gzip.compress(json.dumps(
        {"context_slot": 7, "accounts": [{}, {}, {"address": MINT}]}).encode(), mtime=0))
    target_hash, candidate_hash = sha(target), sha(candidate)
    write(root / "stub-constants.json", json.dumps(
        {"target_sha256": target_hash, "program_source_sha256": {"programs/pump/src/lib.rs": "stub"}}).encode())
    write(directory / "direct-signer-boundary.json", json.dumps({
        "target_sha256": target_hash, "snapshot_sha256": sha(snapshot),
        "error": "InstructionErrorCustom(2002)", "outer_sol_vault_signer": False,
        "watched_accounts_unchanged": True}).encode())
    builds = []
    for run in (1, 2):
        log = write(directory / ("clean-build-%d.log" % run), b"Finished `release` profile [optimized]\n")
        builds.append({"run": run, "artifact_sha256": candidate_hash, "normalized_build_log_sha256": sha(log)})
    if input_sha256 is None:
        input_sha256 = {"research/synthetic-mayhem-cpi/src/lib.rs": sha(caller_source)}
    write(directory / "build-provenance.json", json.dumps({
        "input_sha256": input_sha256,
        "program_source_sha256": {"programs/pump/src/lib.rs": "stub"},
        "full_byte_equality": False, "first_difference": 24, "candidate_sha256": candidate_hash,
        "clean_build_equality": True, "builds": builds}).encode())
    rows = []
    for count in (7957, 507, 649, 48):
        name = "repro/pump/mayhem-synthetic/regression/stub-%d.json.gz" % count
        raw = write(root / name, gzip.compress(json.dumps({"case_count": count, "mismatches": []}).encode(), mtime=0))
        rows.append({"cases": count, "receipt_file": name, "receipt_sha256": sha(raw), "receipt_bytes": len(raw)})
    write(directory / "regression/summary.json", json.dumps({
        "candidate_sha256": candidate_hash, "original_sha256": target_hash,
        "total_cases": 9161, "total_mismatches": 0, "rows": rows}).encode())
    targets = [case(i, error, target_hash) for i, error in enumerate(errors())]
    candidates = [case(i, error, candidate_hash) for i, error in enumerate(errors())]
    report = {"target_sha256": target_hash, "candidate_sha256": candidate_hash,
              "synthetic_caller_sha256": sha(caller), "fixture_sha256": sha(snapshot), "fixture_slot": 7,
              "cases": targets, "candidate_cases": candidates,
              "comparison": [{"case": row["case"], "equal": {key: True for key in COMPARED}} for row in targets]}
    write(directory / "differential.json.gz", gzip.compress(json.dumps(report).encode(), mtime=0))


def run_main(root):
    return subprocess.run([sys.executable, "-B", "-c", DRIVER, str(SCRIPTS), str(root)],
                          capture_output=True, text=True)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


class SyntheticInputBindingTests(unittest.TestCase):
    def outcome(self, input_sha256=None):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            build_package(root, input_sha256)
            return run_main(root)

    def test_complete_package_verifies(self):
        completed = self.outcome()
        check(completed.returncode == 0 and '"result": "pass"' in completed.stdout,
              completed.stdout + completed.stderr)

    def test_empty_input_map_rejected(self):
        completed = self.outcome({})
        check(completed.returncode != 0, "empty input_sha256 verified: " + completed.stdout)
        check("AssertionError" in completed.stderr, completed.stderr)

    def test_non_mapping_input_map_rejected(self):
        completed = self.outcome([])
        check(completed.returncode != 0, "list input_sha256 verified: " + completed.stdout)

    def test_tampered_input_rejected(self):
        completed = self.outcome({"research/synthetic-mayhem-cpi/src/lib.rs": "0" * 64})
        check(completed.returncode != 0 and "AssertionError" in completed.stderr,
              completed.stdout + completed.stderr)

    def test_optimized_python_refused(self):
        completed = subprocess.run([sys.executable, "-B", "-O", str(VERIFIER)],
                                   capture_output=True, text=True, cwd=SCRIPTS)
        check(completed.returncode != 0 and "Normal Python is required" in completed.stderr,
              completed.stderr)


if __name__ == "__main__":
    unittest.main()
