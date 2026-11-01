"""The 8099 Mayhem verifier must refuse evidence whose hash maps bind nothing.

The real ``main()`` runs end to end against a hand-built package, with the
differential replay, the historical event check and the transaction parser
replaced by stub_* modules. A complete valid package prints ``verified``.
"""

import gzip
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SOURCE = "programs/pump/src/mayhem.rs"
QUOTE_INPUT = "evidence/quote/input.json"
EQUAL_KEYS = ("error", "before", "after", "events", "inner", "return_data")
STUB_ROWS = [{"case": None, "equal": {key: True for key in EQUAL_KEYS}}] * 25

DRIVER = r"""
import gzip, json, sys, types
from pathlib import Path
root = Path(sys.argv[1])
receipt_path = root / 'repro/pump/mayhem-synthetic-8099/differential.json.gz'

stub_differential = types.ModuleType('pump_set_mayhem_params_synthetic_cpi')
stub_differential.__file__ = str(root / 'differential.py')
stub_shaped = root / 'stub_shaped_replay.json.gz'
def stub_replay():
    output = Path(sys.argv[sys.argv.index('--output') + 1])
    source = stub_shaped if stub_shaped.exists() else receipt_path
    output.write_bytes(source.read_bytes())
stub_differential.main = stub_replay
stub_historical = types.ModuleType('verify_pump_set_mayhem_params_synthetic')
stub_historical.assert_account_event = lambda case: None
class StubTransaction:
    @classmethod
    def from_bytes(cls, data):
        return cls()
    @property
    def signatures(self):
        return [bytes(64)]
    def verify_with_results(self):
        return [True]
stub_solders = types.ModuleType('solders')
stub_transaction = types.ModuleType('solders.transaction')
stub_transaction.VersionedTransaction = StubTransaction
sys.modules.update({
    'pump_set_mayhem_params_synthetic_cpi': stub_differential,
    'verify_pump_set_mayhem_params_synthetic': stub_historical,
    'solders': stub_solders, 'solders.transaction': stub_transaction})
import verify_pump_set_mayhem_params_8099 as v
v.ROOT = root
v.PACKAGE = root / 'repro/pump/mayhem-synthetic-8099'
v.main()
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Mayhem8099EmptyMapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.package = self.root / "repro/pump/mayhem-synthetic-8099"
        self.package.mkdir(parents=True)
        for rel, data in {
            SOURCE: b"source-bytes", QUOTE_INPUT: b"quote-input",
            "differential.py": b"",
            "evidence/original/pump/deployed.so": b"original",
        }.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.sources = {SOURCE: sha(b"source-bytes")}
        self.bound_inputs = {QUOTE_INPUT: sha(b"quote-input")}

    def write_package(self, sources, bound_inputs, comparison=None, shaped_replay=False):
        package = self.package
        for name, data in {"candidate.so": b"candidate",
                           "synthetic-caller.so": b"caller",
                           "account-snapshot.json.gz": gzip.compress(b"{}")}.items():
            (package / name).write_bytes(data)
        candidate = sha(b"candidate")
        snapshot = sha((package / "account-snapshot.json.gz").read_bytes())
        logs = {}
        for name in ("build.log.gz", "second-build.log.gz"):
            (package / name).write_bytes(gzip.compress(name.encode()))
            logs[name] = sha(name.encode())
        for name, log in (("build-comparison.json", "build.log.gz"),
                          ("second-build-comparison.json", "second-build.log.gz")):
            (package / name).write_text(json.dumps({
                "source_sha256": sources, "selected_toolchain": "v1.44",
                "comparison": {"candidate_sha256": candidate,
                               "full_byte_equality": False},
                "build_log_sha256": logs[log]}))
        (package / "build-reproducibility.json").write_text(json.dumps({
            "source_base_commit": "80990317bd9c0363e071646b892490886d7bf946",
            "candidate_sha256": candidate, "source_sha256": sources,
            "builds_identical": True,
            "differential_script_sha256": sha(b"")}))
        for name in ("build-attempt.json", "second-build-attempt.json"):
            (package / name).write_text(json.dumps({
                "returncode": 0, "source_unchanged": True,
                "source_sha256": sources}))
        case = {"error": None, "signed_transaction_base64": "",
                "signatures_valid": True}
        cases = [dict(case, error=None if i < 13 else "Err") for i in range(25)]
        receipt = {
            "candidate_sha256": candidate, "target_sha256": sha(b"original"),
            "synthetic_caller_sha256": sha(b"caller"), "fixture_sha256": snapshot,
            "cases": cases, "candidate_cases": cases, "comparison": STUB_ROWS}
        if shaped_replay:
            # Stands in for the real differential, which always emits 25 rows
            # with all six keys; the package receipt must match it exactly.
            (self.root / "stub_shaped_replay.json.gz").write_bytes(
                gzip.compress(json.dumps(receipt).encode()))
        if comparison is not None:
            receipt["comparison"] = comparison
        (package / "differential.json.gz").write_bytes(
            gzip.compress(json.dumps(receipt).encode()))
        (package / "direct-signer-boundary.json").write_text(json.dumps({
            "snapshot_sha256": snapshot, "outer_sol_vault_signer": False,
            "watched_accounts_unchanged": True}))
        quote = gzip.compress(json.dumps({
            "cases": 507, "mismatches": 0,
            "results": [{"matches": True} for _ in range(507)],
            "bound_inputs_sha256": bound_inputs}).encode())
        curve = gzip.compress(json.dumps({
            "case_count": 56, "passed": 56, "candidate_sha256": candidate,
            "cases": [{"mismatches": []} for _ in range(56)]}).encode())
        (package / "quote-control-regression.json.gz").write_bytes(quote)
        (package / "multi-hop-regression.json.gz").write_bytes(curve)
        (package / "regression-summary.json").write_text(json.dumps({
            "candidate_sha256": candidate,
            "quote_control": {"receipt_sha256": sha(quote)},
            "multi_hop_curve": {"receipt_sha256": sha(curve)}}))

    def run_verifier(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run([sys.executable, "-c", DRIVER, str(self.root)],
                              text=True, capture_output=True, env=env, check=False)

    def assert_rejected(self, message):
        completed = self.run_verifier()
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertNotIn('"verified": true', completed.stdout)
        self.assertIn(message, completed.stderr)

    def test_valid_package_verifies(self):
        self.write_package(self.sources, self.bound_inputs)
        completed = self.run_verifier()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"verified": true', completed.stdout)

    def test_empty_build_source_map_rejected(self):
        self.write_package({}, self.bound_inputs)
        self.assert_rejected("build reproducibility binds no source")

    def test_empty_quote_bound_inputs_rejected(self):
        self.write_package(self.sources, {})
        self.assert_rejected("quote-control regression binds no input")

    def test_tampered_source_hash_rejected(self):
        self.write_package({SOURCE: "0" * 64}, self.bound_inputs)
        self.assert_rejected("AssertionError")

    def test_tampered_quote_input_hash_rejected(self):
        self.write_package(self.sources, {QUOTE_INPUT: "0" * 64})
        self.assert_rejected("AssertionError")

    def stub_rows(self, **equal):
        row = {key: True for key in EQUAL_KEYS}
        row.update(equal)
        return [{"case": None, "equal": {k: v for k, v in row.items() if v is not None}}] * 25

    def write_comparison(self, comparison, shaped_replay=False):
        self.write_package(self.sources, self.bound_inputs, comparison, shaped_replay)

    def test_complete_comparison_verifies_under_both_replays(self):
        for shaped in (False, True):
            with self.subTest(shaped_replay=shaped):
                self.write_comparison(STUB_ROWS, shaped)
                completed = self.run_verifier()
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn('"verified": true', completed.stdout)

    def test_empty_comparison_rejected(self):
        self.write_comparison([])
        self.assert_rejected("comparison must cover every case")

    def test_short_comparison_rejected(self):
        self.write_comparison(STUB_ROWS[:24])
        self.assert_rejected("comparison must cover every case")

    def test_empty_equal_map_rejected(self):
        self.write_comparison([{"case": None, "equal": {}}] * 25)
        self.assert_rejected("comparison must check every field")

    def test_equal_map_missing_key_rejected(self):
        self.write_comparison(self.stub_rows(return_data=None))
        self.assert_rejected("comparison must check every field")

    def test_equal_map_extra_key_rejected(self):
        self.write_comparison(self.stub_rows(stub_extra=True))
        self.assert_rejected("comparison must check every field")

    def test_divergent_field_still_rejected(self):
        self.write_comparison(self.stub_rows(events=False))
        self.assert_rejected("AssertionError")

    def test_shaped_replay_rejects_incomplete_comparisons(self):
        # The exact replay-equality check already refuses these against
        # output shaped like the real differential's.
        for comparison in ([], STUB_ROWS[:24], [{"case": None, "equal": {}}] * 25,
                           self.stub_rows(return_data=None), self.stub_rows(stub_extra=True)):
            with self.subTest(rows=len(comparison)):
                self.write_comparison(comparison, shaped_replay=True)
                self.assert_rejected("AssertionError")


if __name__ == "__main__":
    unittest.main()
