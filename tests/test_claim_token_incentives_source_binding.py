"""The claim verifier must refuse evidence whose source maps bind nothing.

This drives the real ``main()`` CLI against a hand-built root with the
differential module stubbed. The check of interest runs before the inherited
regression receipts are read, so the fixture omits that file: reaching it
(``inherited-regressions.json`` missing) proves the source checks passed.
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
BASELINE = "4ffe8bd88761059693e481ae972443c10204f7af"
SOURCE = "programs/pump/src/claim.rs"
MODES = ([], ["-O"], ["-OO"])

DRIVER = r"""
import hashlib, sys, types
from pathlib import Path
root = Path(sys.argv[1])
stub_differential = types.ModuleType('pump_claim_token_incentives_differential')
stub_differential.ROOT = root
stub_differential.sha = lambda data: hashlib.sha256(bytes(data)).hexdigest()
for name, rel in (('BUILD', 'build.json'), ('ORIGINAL', 'original.so'),
                  ('IDL', 'idl.json'), ('FIXTURE', 'fixture.json'),
                  ('OUT', 'receipt.json')):
    setattr(stub_differential, name, root / rel)
stub_differential.__file__ = str(root / 'differential.py')
sys.modules['pump_claim_token_incentives_differential'] = stub_differential
txmod = types.ModuleType('solders.transaction')
txmod.Transaction = object
sys.modules['solders'] = types.ModuleType('solders')
sys.modules['solders.transaction'] = txmod
import pump_claim_token_incentives_verify as v
sys.argv = ['verify', '--candidate', str(root / 'candidate.so')]
v.main()
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ClaimSourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        files = {
            "original.so": b"original", "candidate.so": b"candidate",
            "idl.json": b"{}", "fixture.json": b"{}", "differential.py": b"",
            SOURCE: b"source-bytes",
            "evidence/dependencies/spl_token_2022/deployed.so": b"t22",
            "evidence/dependencies/associated_token/deployed.so": b"ata",
        }
        for rel, data in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.sources = {SOURCE: sha(b"source-bytes")}
        self.repro_dir = self.root / "repro/pump/claim-token-incentives"
        self.repro_dir.mkdir(parents=True)
        for name in ("build.log.gz", "build-second.log.gz"):
            (self.repro_dir / name).write_bytes(gzip.compress(b"log"))

    def write(self, report_sources, build_sources):
        build = {"source_sha256": build_sources, "build_log_sha256": sha(b"log")}
        (self.root / "build.json").write_text(json.dumps(build))
        second = self.repro_dir / "build-second-comparison.json"
        second.write_text(json.dumps(build))
        (self.repro_dir / "build-reproducibility.json").write_text(json.dumps({
            "build_receipt_sha256": [sha((self.root / "build.json").read_bytes()),
                                     sha(second.read_bytes())],
            "source_sha256": build_sources,
            "candidate_sha256": [sha(b"candidate")] * 2,
            "builds_identical": True, "deployed_byte_match": False,
        }))
        (self.root / "receipt.json").write_text(json.dumps({
            "baseline_commit": BASELINE,
            "target_sha256": sha(b"original"),
            "candidate_sha256": sha(b"candidate"),
            "build_receipt_sha256": sha((self.root / "build.json").read_bytes()),
            "idl_sha256": sha(b"{}"), "fixture_sha256": sha(b"{}"),
            "script_sha256": sha(b""),
            "dependency_sha256": {"spl_token_2022": sha(b"t22"),
                                  "associated_token": sha(b"ata")},
            "source_sha256": report_sources,
        }))

    def run_modes(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return [(optimization or "normal", subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, str(self.root)],
            text=True, capture_output=True, env=env, check=False))
            for optimization in MODES]

    def assert_rejected(self, message):
        for mode, completed in self.run_modes():
            with self.subTest(optimization=mode):
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(message, completed.stderr)
                self.assertNotIn("inherited-regressions.json", completed.stderr)

    def test_empty_report_and_build_sources_rejected(self):
        self.write({}, {})
        self.assert_rejected("report binds no source")

    def test_empty_build_sources_rejected(self):
        self.write(self.sources, {})
        self.assert_rejected("build comparison binds no source")

    def test_tampered_source_hash_rejected(self):
        self.write({SOURCE: "0" * 64}, self.sources)
        self.assert_rejected("claim verification failed")

    def test_bound_sources_pass_the_source_checks(self):
        self.write(self.sources, self.sources)
        for mode, completed in self.run_modes():
            with self.subTest(optimization=mode):
                self.assertIn("inherited-regressions.json", completed.stderr)
                self.assertNotIn("binds no source", completed.stderr)


FULL_DRIVER = r"""
import hashlib, json, sys, types
from pathlib import Path
root = Path(sys.argv[1])
stub_differential = types.ModuleType('pump_claim_token_incentives_differential')
stub_differential.ROOT = root
stub_differential.sha = lambda data: hashlib.sha256(bytes(data)).hexdigest()
for name, rel in (('BUILD', 'build.json'), ('ORIGINAL', 'original.so'),
                  ('IDL', 'idl.json'), ('FIXTURE', 'fixture.json'),
                  ('OUT', 'receipt.json')):
    setattr(stub_differential, name, root / rel)
stub_differential.__file__ = str(root / 'differential.py')
stub_differential.CASES = json.loads((root / 'cases.json').read_text())
stub_differential.fixture_data = lambda: (
    None, {'user_base': 'user-ata', 'volume': 'volume'}, None, 'volume', 'global-ata')
rows = json.loads((root / 'rows.json').read_text())
stub_differential.run_case = lambda path, case: rows[case['name']]
sys.modules['pump_claim_token_incentives_differential'] = stub_differential
class StubTransaction:
    @classmethod
    def from_bytes(cls, data):
        return cls()
    def verify_with_results(self):
        return [True]
    signatures = ['stub-signature']
stub_transaction = types.ModuleType('solders.transaction')
stub_transaction.Transaction = StubTransaction
sys.modules['solders'] = types.ModuleType('solders')
sys.modules['solders.transaction'] = stub_transaction
import pump_claim_token_incentives_verify as v
sys.argv = ['verify', '--candidate', str(root / 'candidate.so')]
v.main()
"""

CANDIDATE_PATH = "work/claim-pr-candidate/pump_recovered.so"
QUOTE_INPUT = "evidence/quote/input.json"
MAINTAINED_SCRIPT = "stub_regression_script.py"


class ClaimInheritedBindingTests(unittest.TestCase):
    """End to end: a complete hand-built package is printed as verified."""

    setUp = ClaimSourceBindingTests.setUp
    write = ClaimSourceBindingTests.write

    def write_inherited(self, quote_inputs, maintained_scripts, quote_rows=None):
        for rel, data in ((QUOTE_INPUT, b"quote-input"),
                          ("scripts/" + MAINTAINED_SCRIPT, b"regression-script")):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.write(self.sources, self.sources)
        candidate, target = sha(b"candidate"), sha(b"original")
        idl = json.dumps({"events": [{"name": "ClaimTokenIncentivesEvent",
                                      "discriminator": [1] * 8}]}).encode()
        (self.root / "idl.json").write_bytes(idl)
        build_path = self.root / "build.json"
        build = json.loads(build_path.read_text())
        build.update({"selected_toolchain": "v1.44", "comparison": {
            "candidate_sha256": candidate, "original_sha256": target,
            "full_byte_equality": False}})
        build_path.write_text(json.dumps(build))
        second = self.repro_dir / "build-second-comparison.json"
        second.write_text(json.dumps(build))
        repro_path = self.repro_dir / "build-reproducibility.json"
        repro = json.loads(repro_path.read_text())
        repro["build_receipt_sha256"] = [sha(build_path.read_bytes()), sha(second.read_bytes())]
        repro_path.write_text(json.dumps(repro))

        selected = {
            "maintained": {
                "candidate_sha256": candidate, "original_sha256": target,
                "case_count": 7957, "mismatches": [],
                "suites": {f"suite{i}": {"case_count": 7957 - 32 if i == 0 else 1}
                           for i in range(33)},
                "script_sha256": maintained_scripts},
            "holder_distribution": {
                "candidate_sha256": candidate, "original_sha256": target,
                "case_count": 649, "mismatches": [], "cases": [{}] * 649},
            "nested_create": {
                "candidate_sha256": candidate, "original_sha256": target,
                "case_count": 48, "mismatches": [], "cases": [{}] * 48},
            "quote_control": {"cases": 507, "mismatches": 0,
                              "results": [{"matches": True} for _ in range(507)]
                              if quote_rows is None else quote_rows,
                              "bound_inputs_sha256": quote_inputs},
        }
        receipts = []
        for name, cases in (("maintained", 7957), ("holder_distribution", 649),
                            ("nested_create", 48), ("quote_control", 507)):
            raw = json.dumps(selected[name]).encode()
            compressed = gzip.compress(raw)
            (self.repro_dir / f"{name}.json.gz").write_bytes(compressed)
            receipts.append({"name": name, "cases": cases, "file": f"{name}.json.gz",
                             "compressed_sha256": sha(compressed),
                             "json_sha256": sha(raw), "json_bytes": len(raw)})
        (self.repro_dir / "inherited-regressions.json").write_text(json.dumps({
            "baseline_commit": BASELINE, "candidate_sha256": candidate,
            "target_sha256": target, "total_cases": 9161, "suite_count": 36,
            "receipts": receipts}))

        cases, rows, report_rows = [], {}, []
        for i in range(60):
            success = i < 48
            name = f"stub_case_{i}"
            account = {"lamports": 1}
            row = {"error": None if success else "StubError", "error_code": None,
                   "success": success,
                   "before": {"payer": {"lamports": 10_000}, "global_volume": account,
                              "mint": account, "user_ata": account,
                              "global_ata": account, "user_volume": account},
                   "after": {"payer": {"lamports": 5_000}, "global_volume": account,
                             "mint": account, "user_ata": account,
                             "global_ata": account, "user_volume": account},
                   "event_data_base64": [], "inner": [], "signature": "stub-signature",
                   "transaction_base64": "",
                   "relevant_logs": ["Program log: Instruction: ClaimTokenIncentives"]}
            case = {"name": name}
            cases.append(case)
            rows[name] = row
            report_rows.append({"case": case, "target": row, "candidate": row,
                                "differences": []})
        (self.root / "cases.json").write_text(json.dumps(cases))
        (self.root / "rows.json").write_text(json.dumps(rows))
        receipt_path = self.root / "receipt.json"
        receipt = json.loads(receipt_path.read_text())
        receipt.update({"idl_sha256": sha(idl),
                        "build_receipt_sha256": sha(build_path.read_bytes()),
                        "signed_local": True, "offline_only": True,
                        "cases": report_rows,
                        "summary": {"cases": 60, "target_successes": 48, "matched": 60}})
        receipt_path.write_text(json.dumps(receipt))

    def run_full(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return [(optimization or "normal", subprocess.run(
            [sys.executable, *optimization, "-c", FULL_DRIVER, str(self.root)],
            text=True, capture_output=True, env=env, check=False))
            for optimization in MODES]

    def assert_full_rejected(self, message):
        for mode, completed in self.run_full():
            with self.subTest(optimization=mode):
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn('"verified": true', completed.stdout)
                self.assertIn(message, completed.stderr)

    def valid_maps(self):
        return ({QUOTE_INPUT: sha(b"quote-input"), CANDIDATE_PATH: sha(b"candidate")},
                {MAINTAINED_SCRIPT: sha(b"regression-script")})

    def test_complete_package_verifies(self):
        self.write_inherited(*self.valid_maps())
        for mode, completed in self.run_full():
            with self.subTest(optimization=mode):
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn('"verified": true', completed.stdout)

    def test_empty_quote_bound_inputs_rejected(self):
        self.write_inherited({}, self.valid_maps()[1])
        self.assert_full_rejected("quote-control receipt binds no input")

    def test_empty_maintained_script_map_rejected(self):
        self.write_inherited(self.valid_maps()[0], {})
        self.assert_full_rejected("maintained receipt binds no script")

    def test_tampered_quote_input_rejected(self):
        quote, scripts = self.valid_maps()
        self.write_inherited(dict(quote, **{QUOTE_INPUT: "0" * 64}), scripts)
        self.assert_full_rejected("claim verification failed")

    def test_tampered_maintained_script_rejected(self):
        self.write_inherited(self.valid_maps()[0], {MAINTAINED_SCRIPT: "0" * 64})
        self.assert_full_rejected("claim verification failed")

    def test_quote_result_row_disagreeing_with_header_rejected(self):
        # A header that says zero mismatches over rows that say otherwise.
        rows = [{"matches": True} for _ in range(506)] + [{"matches": False}]
        self.write_inherited(*self.valid_maps(), quote_rows=rows)
        self.assert_full_rejected(
            "not any(row.get('matches') is not True for row in selected['results'])")


if __name__ == "__main__":
    unittest.main()
