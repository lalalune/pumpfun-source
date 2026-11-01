"""Regression checks for 8099 claim verification under optimized Python.

main() in scripts/pump_claim_token_incentives_8099_verify.py verifies the
8099031-source claim build and signed offline differential: header hashes bind
the receipt to the candidate and both builds, the regression files bind the
quote/curve outcomes, and the case loop replays all 60 cases (48 successes,
31 payout events) against the stored outcomes. Before this fix every one of
those 38 checks was a bare assert, so under -O/-OO a receipt with a tampered
baseline commit, a tampered candidate hash, or a tampered summary was still
printed as verified. The differential and historical modules are stubbed here
(the real ones need the solders package and the on-chain binaries), and the
package directory is pointed at a synthetic tree, so the driver exercises the
verifier's own admission logic, not the replay engine.
"""

from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SOURCE_BASE = "80990317bd9c0363e071646b892490886d7bf946"

DRIVER = (
    "import sys, json, gzip, hashlib, types\n"
    "from pathlib import Path\n"
    "root = Path(sys.argv[1])\n"
    "pkg = Path(sys.argv[2])\n"
    "def fsha(p):\n"
    "    if isinstance(p, (bytes, bytearray)):\n"
    "        return hashlib.sha256(bytes(p)).hexdigest()\n"
    "    return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"
    "receipt = json.loads(gzip.decompress((pkg / 'differential.json.gz').read_bytes()))\n"
    "by_name = {row['case']['name']: row['target'] for row in receipt['cases']}\n"
    "fake = types.ModuleType('pump_claim_token_incentives_differential')\n"
    "fake.ROOT = root\n"
    "fake.ORIGINAL = root / 'original.so'\n"
    "fake.IDL = root / 'idl.json'\n"
    "fake.FIXTURE = root / 'fixture.bin'\n"
    "fake.__file__ = str(root / 'scripts' / 'pump_claim_token_incentives_differential.py')\n"
    "fake.CASES = [row['case'] for row in receipt['cases']]\n"
    "fake.fixture_data = lambda: (None, {'user_base': 'ub', 'volume': 1234}, None, 1234, 'ga')\n"
    "fake.run_case = lambda binary, case: by_name[case['name']]\n"
    "sys.modules['pump_claim_token_incentives_differential'] = fake\n"
    "hist = types.ModuleType('pump_claim_token_incentives_verify')\n"
    "hist.EXPECTED_ERRORS = {}\n"
    "hist.assert_signature = lambda row: None\n"
    "hist.assert_event_and_cpis = lambda *args: None\n"
    "sys.modules['pump_claim_token_incentives_verify'] = hist\n"
    "import pump_claim_token_incentives_8099_verify as v\n"
    "v.ROOT = root\n"
    "v.PACKAGE = pkg\n"
    "v.main()\n"
    "print('OK')\n"
)

MODES = ([], ["-O"], ["-OO"])


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Claim8099OptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.pkg = self.root / "pkg"
        self.pkg.mkdir()
        (self.root / "scripts").mkdir()
        diff_file = self.root / "scripts" / "pump_claim_token_incentives_differential.py"
        diff_file.write_bytes(b"diff-stub")
        self.original = self.root / "original.so"
        self.original.write_bytes(b"original-bytes")
        self.idl = self.root / "idl.json"
        self.idl.write_text(json.dumps({
            "instructions": [],
            "events": [{"name": "ClaimTokenIncentivesEvent", "discriminator": [1, 2, 3]}],
        }))
        self.fixture = self.root / "fixture.bin"
        self.fixture.write_bytes(b"fixture-bytes")
        for name in ("spl_token_2022", "associated_token"):
            dep_dir = self.root / "evidence" / "dependencies" / name
            dep_dir.mkdir(parents=True)
            (dep_dir / "deployed.so").write_bytes(f"{name}-bytes".encode())
        self.candidate = self.pkg / "candidate.so"
        self.candidate.write_bytes(b"candidate-bytes")
        self.first = {
            "source_sha256": {}, "selected_toolchain": "v1.44",
            "comparison": {"candidate_sha256": file_sha(self.candidate),
                           "full_byte_equality": False},
            "build_log_sha256": hashlib.sha256(b"log").hexdigest(),
        }
        self.second = {
            "source_sha256": {}, "selected_toolchain": "v1.44",
            "comparison": {"candidate_sha256": file_sha(self.candidate),
                           "full_byte_equality": False},
            "build_log_sha256": hashlib.sha256(b"log2").hexdigest(),
        }
        (self.pkg / "build-comparison.json").write_text(json.dumps(self.first))
        (self.pkg / "second-build-comparison.json").write_text(json.dumps(self.second))
        (self.pkg / "build.log.gz").write_bytes(gzip.compress(b"log"))
        (self.pkg / "second-build.log.gz").write_bytes(gzip.compress(b"log2"))
        for name in ("build-attempt.json", "second-build-attempt.json"):
            (self.pkg / name).write_text(json.dumps(
                {"returncode": 0, "source_unchanged": True, "source_sha256": {}}))
        quote = {"cases": 507, "mismatches": 0,
                 "results": [{"matches": True} for _ in range(507)],
                 "bound_inputs_sha256": {"fixture.bin": file_sha(self.fixture)}}
        curve = {"case_count": 56, "passed": 56,
                 "candidate_sha256": file_sha(self.candidate),
                 "cases": [{"mismatches": []} for _ in range(56)]}
        (self.pkg / "quote-control-regression.json.gz").write_bytes(
            gzip.compress(json.dumps(quote).encode()))
        (self.pkg / "multi-hop-regression.json.gz").write_bytes(
            gzip.compress(json.dumps(curve).encode()))
        (self.pkg / "regression-summary.json").write_text(json.dumps({
            "candidate_sha256": file_sha(self.candidate),
            "quote_control": {"receipt_sha256": file_sha(
                self.pkg / "quote-control-regression.json.gz")},
            "multi_hop_curve": {"receipt_sha256": file_sha(
                self.pkg / "multi-hop-regression.json.gz")},
        }))
        (self.pkg / "build-reproducibility.json").write_text(json.dumps({
            "source_base_commit": SOURCE_BASE,
            "candidate_sha256": file_sha(self.candidate),
            "build_comparison_sha256": [
                file_sha(self.pkg / "build-comparison.json"),
                file_sha(self.pkg / "second-build-comparison.json")],
            "source_sha256": {}, "builds_identical": True,
        }))

    def write_receipt(self, tamper):
        cases = []
        for i in range(60):
            if i < 48:
                target = {
                    "error": None, "error_code": None, "before": {}, "after": {},
                    "event_data_base64": ["e"] if i < 31 else [],
                    "inner": [], "signature": "s", "transaction_base64": "t",
                    "success": True,
                }
            else:
                target = {
                    "error": "SomeError", "error_code": None,
                    "before": {"user_volume": 5}, "after": {"user_volume": 5},
                    "event_data_base64": [], "inner": [], "signature": "s",
                    "transaction_base64": "t", "success": False,
                }
            cases.append({
                "case": {"name": f"case{i}"}, "target": target,
                "candidate": json.loads(json.dumps(target)), "differences": [],
            })
        receipt = {
            "baseline_commit": "TAMPERED" if tamper == "baseline" else SOURCE_BASE,
            "candidate_sha256": "0" * 64 if tamper == "candidate" else file_sha(self.candidate),
            "candidate_path": "pkg/candidate.so",
            "build_receipt_sha256": file_sha(self.pkg / "build-comparison.json"),
            "second_build_comparison_sha256": file_sha(self.pkg / "second-build-comparison.json"),
            "source_sha256": {
                "scripts/pump_claim_token_incentives_differential.py": file_sha(
                    self.root / "scripts" / "pump_claim_token_incentives_differential.py")},
            "script_sha256": file_sha(
                self.root / "scripts" / "pump_claim_token_incentives_differential.py"),
            "target_sha256": file_sha(self.original),
            "idl_sha256": file_sha(self.idl),
            "fixture_sha256": file_sha(self.fixture),
            "dependency_sha256": {
                name: file_sha(self.root / "evidence" / "dependencies" / name / "deployed.so")
                for name in ("spl_token_2022", "associated_token")},
            "cases": cases,
            "summary": {"cases": 60, "matched": 60,
                        "target_successes": 47 if tamper == "summary" else 48},
        }
        (self.pkg / "differential.json.gz").write_bytes(
            gzip.compress(json.dumps(receipt).encode()))

    def rewrite_regressions(self, quote=None, curve=None):
        """Replace a regression receipt and keep the summary's hash in step with it."""
        for name, document in (("quote-control-regression.json.gz", quote),
                               ("multi-hop-regression.json.gz", curve)):
            if document is not None:
                (self.pkg / name).write_bytes(gzip.compress(json.dumps(document).encode()))
        summary_path = self.pkg / "regression-summary.json"
        summary = json.loads(summary_path.read_text())
        summary["quote_control"]["receipt_sha256"] = file_sha(
            self.pkg / "quote-control-regression.json.gz")
        summary["multi_hop_curve"]["receipt_sha256"] = file_sha(
            self.pkg / "multi-hop-regression.json.gz")
        summary_path.write_text(json.dumps(summary))

    def run_driver(self, optimization):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, str(self.root), str(self.pkg)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_receipt_tampers_rejected_in_all_modes(self):
        for tamper in ("baseline", "candidate", "summary"):
            with self.subTest(tamper=tamper):
                self.write_receipt(tamper)
                for optimization in MODES:
                    with self.subTest(optimization=optimization or "normal"):
                        completed = self.run_driver(optimization)
                        self.assertNotEqual(completed.returncode, 0, completed.stdout)
                        self.assertNotIn("OK", completed.stdout)

    def test_valid_receipt_accepted_in_all_modes(self):
        self.write_receipt("none")
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK", completed.stdout)

    def test_quote_rows_disagreeing_with_header_rejected_in_all_modes(self):
        self.write_receipt("none")
        self.rewrite_regressions(quote={
            "cases": 507, "mismatches": 0,
            "results": [{"matches": True} for _ in range(506)] + [{"matches": False}],
            "bound_inputs_sha256": {"fixture.bin": file_sha(self.fixture)}})
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)
                self.assertIn("quote['cases'] == 507 and quote['mismatches'] == 0",
                              completed.stderr)

    def test_quote_without_bound_input_rejected_in_all_modes(self):
        self.write_receipt("none")
        self.rewrite_regressions(quote={
            "cases": 507, "mismatches": 0,
            "results": [{"matches": True} for _ in range(507)],
            "bound_inputs_sha256": {}})
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)
                self.assertIn("quote-control receipt binds no input", completed.stderr)

    def test_curve_rows_disagreeing_with_header_rejected_in_all_modes(self):
        self.write_receipt("none")
        self.rewrite_regressions(curve={
            "case_count": 56, "passed": 56,
            "candidate_sha256": file_sha(self.candidate),
            "cases": [{"mismatches": []} for _ in range(55)] + [{"mismatches": [3]}]})
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)
                self.assertIn("curve['case_count'] == curve['passed'] == 56",
                              completed.stderr)


if __name__ == "__main__":
    unittest.main()
