"""Regression checks for admin token-incentives verification under optimized Python.

main() in scripts/pump_admin_token_incentives_verify.py replays a signed
differential receipt: header hashes bind the receipt to the target, candidate,
build comparison, IDL and snapshot, and the case loop replays all 98 cases
(43 successes) against the stored outcomes. Before this fix every one of those
48 checks was a bare assert, so under -O/-OO a receipt with a tampered baseline
commit, a tampered candidate hash, or a success event minted to the wrong mint
was still printed as verified. The differential module is stubbed here (its
real implementation needs the solders package and the on-chain binaries), so
the driver exercises the verifier's own admission logic, not the replay engine.
"""

from pathlib import Path
import base64
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
EXPECTED_BASELINE = "4ffe8bd88761059693e481ae972443c10204f7af"
REGRESSION_BASELINE = "80990317bd9c0363e071646b892490886d7bf946"
QUOTE_INPUT = "evidence/quote/input.json"
MINT = b"\x07" * 32
SOURCE = "programs/pump/src/incentives.rs"
DISC = bytes([1, 2, 3, 4, 5, 6, 7, 8])
FINANCIAL_ACCOUNTS = (
    "global", "global_volume_accumulator", "mint",
    "global_incentive_token_account", "canonical_global",
    "canonical_volume", "canonical_vault",
)

DRIVER = (
    "import sys, json, hashlib, types\n"
    "from pathlib import Path\n"
    "root = Path(sys.argv[2])\n"
    "def fsha(p):\n"
    "    if isinstance(p, (bytes, bytearray)):\n"
    "        return hashlib.sha256(bytes(p)).hexdigest()\n"
    "    return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"
    "receipt = json.loads(Path(sys.argv[3]).read_text())\n"
    "by_variant = {c['variant']: c['target'] for c in receipt['cases']}\n"
    "fake = types.ModuleType('pump_admin_token_incentives_differential')\n"
    "fake.ROOT = root\n"
    "fake.TARGET = root / 'target.so'\n"
    "fake.IDL = root / 'idl.json'\n"
    "fake.SNAPSHOT = root / 'snap.json'\n"
    "fake.MINT = b'\\x07' * 32\n"
    "fake.OUTPUT = Path(sys.argv[3])\n"
    "fake.CANDIDATE = Path(sys.argv[4])\n"
    "fake.BUILD = Path(sys.argv[5])\n"
    "fake.sha = fsha\n"
    "fake.variants = lambda: [(c['case'], c['variant']) for c in receipt['cases']]\n"
    "fake.run = lambda binary, item, variant, fixture: by_variant[variant]\n"
    "sys.modules['pump_admin_token_incentives_differential'] = fake\n"
    "import pump_admin_token_incentives_verify as v\n"
    "baseline = sys.argv[6] if len(sys.argv) > 6 else '4ffe8bd88761059693e481ae972443c10204f7af'\n"
    "v.main(Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]), baseline)\n"
    "print('OK')\n"
)

MODES = ([], ["-O"], ["-OO"])


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class AdminTokenIncentivesOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.target = self.root / "target.so"
        self.target.write_bytes(b"target-bytes")
        self.candidate = self.root / "candidate.so"
        self.candidate.write_bytes(b"candidate-bytes")
        build_dir = self.root / "build"
        build_dir.mkdir()
        (build_dir / "build.log.gz").write_bytes(gzip.compress(b"log"))
        source = self.root / SOURCE
        source.parent.mkdir(parents=True)
        source.write_bytes(b"source-bytes")
        self.source_sha256 = {SOURCE: file_sha(source)}
        self.build = build_dir / "build.json"
        self.write_build(self.source_sha256)
        self.idl = self.root / "idl.json"
        self.idl.write_text(json.dumps({
            "instructions": [{"name": "admin_update_token_incentives"}],
            "events": [{"name": "AdminUpdateTokenIncentivesEvent",
                        "discriminator": list(DISC)}],
        }))
        self.snapshot = self.root / "snap.json"
        self.snapshot.write_text(json.dumps({
            "accounts": [{"program_name": "pump", "data_sha256": "snaphash"}]}))
        self.receipt_path = self.root / "receipt.json"

    def write_build(self, source_sha256):
        self.build.write_text(json.dumps({
            "selected_toolchain": "v1.44",
            "comparison": {"candidate_sha256": file_sha(self.candidate)},
            "source_sha256": source_sha256,
            "build_log_sha256": hashlib.sha256(b"log").hexdigest(),
        }))

    def event_bytes(self, mint):
        return DISC + b"\x00" * 32 + mint + b"\x00" * 16

    def write_regression_package(self, bound_inputs, quote_rows=None, curve_rows=None):
        """Package files read only under the 80990317 baseline."""
        package = self.build.parent
        candidate = file_sha(self.candidate)
        (package / "build-reproducibility.json").write_text(json.dumps({
            "source_base_commit": REGRESSION_BASELINE, "candidate_sha256": candidate,
            "builds_identical": True, "deployed_byte_match": False,
            "source_sha256": self.source_sha256}))
        for name in ("build-attempt.json", "second-build-attempt.json"):
            (package / name).write_text(json.dumps({
                "returncode": 0, "source_unchanged": True,
                "source_sha256": self.source_sha256}))
        quote = gzip.compress(json.dumps({
            "cases": 507, "mismatches": 0,
            "results": quote_rows if quote_rows is not None
            else [{"matches": True} for _ in range(507)],
            "bound_inputs_sha256": bound_inputs}).encode())
        curve = gzip.compress(json.dumps({
            "case_count": 56, "passed": 56, "candidate_sha256": candidate,
            "cases": curve_rows if curve_rows is not None
            else [{"mismatches": []} for _ in range(56)]}).encode())
        (package / "quote-control-regression.json.gz").write_bytes(quote)
        (package / "multi-hop-regression.json.gz").write_bytes(curve)
        (package / "regression-summary.json").write_text(json.dumps({
            "candidate_sha256": candidate,
            "quote_control": {"receipt_sha256": hashlib.sha256(quote).hexdigest()},
            "multi_hop_curve": {"receipt_sha256": hashlib.sha256(curve).hexdigest()}}))

    def stub_quote_input(self):
        path = self.root / QUOTE_INPUT
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub-quote-input")
        return {QUOTE_INPUT: file_sha(path)}

    def write_receipt(self, tamper, baseline=EXPECTED_BASELINE):
        event = self.event_bytes(MINT)
        cases = []
        for i in range(98):
            if i < 43:
                row = {
                    "error": None, "error_code": None, "before": {}, "after": {},
                    "signed_transaction_base64": "", "signature": "",
                    "events": [base64.b64encode(event).decode()],
                    "state_debug_logs": ["log"],
                    "inner_instructions": [{"data_hex": "00" * 8 + event.hex()}],
                    "return_data_hex": "", "args": {}, "keys": {},
                    "signature_verified": True,
                }
            else:
                row = {
                    "error": "SomeError", "error_code": 6000,
                    "before": {a: 0 for a in FINANCIAL_ACCOUNTS},
                    "after": {a: 0 for a in FINANCIAL_ACCOUNTS},
                    "signed_transaction_base64": "", "signature": "",
                    "events": [], "state_debug_logs": [],
                    "inner_instructions": [], "return_data_hex": "",
                    "args": {}, "keys": {}, "signature_verified": True,
                }
            target = json.loads(json.dumps(row))
            candidate = json.loads(json.dumps(row))
            if tamper == "event_mint" and i == 0:
                bad = self.event_bytes(b"\x09" * 32)
                for copy in (target, candidate):
                    copy["events"] = [base64.b64encode(bad).decode()]
            cases.append({
                "case": f"case{i}", "variant": f"v{i}", "match": True,
                "differing_fields": [], "target": target, "candidate": candidate,
            })
        receipt = {
            "baseline_commit": "TAMPERED" if tamper == "baseline" else baseline,
            "target_sha256": file_sha(self.target),
            "candidate_sha256": "0" * 64 if tamper == "candidate" else file_sha(self.candidate),
            "build_comparison_sha256": file_sha(self.build),
            "idl_sha256": file_sha(self.idl),
            "global_snapshot_sha256": file_sha(self.snapshot),
            "global_snapshot_account_data_sha256": "snaphash",
            "source_sha256": {} if tamper == "receipt_sources" else self.source_sha256,
            "dependency_sha256": {},
            "cases": cases,
            "summary": {"cases": 98, "target_successes": 43, "matched": 98},
        }
        self.receipt_path.write_text(json.dumps(receipt))

    def run_driver(self, optimization, *baseline):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, "case",
             str(self.root), str(self.receipt_path), str(self.candidate), str(self.build), *baseline],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_header_tampers_rejected_in_all_modes(self):
        for tamper in ("baseline", "candidate"):
            with self.subTest(tamper=tamper):
                self.write_receipt(tamper)
                for optimization in MODES:
                    with self.subTest(optimization=optimization or "normal"):
                        completed = self.run_driver(optimization)
                        self.assertNotEqual(completed.returncode, 0, completed.stdout)
                        self.assertNotIn("OK", completed.stdout)

    def test_event_tamper_rejected_in_all_modes(self):
        self.write_receipt("event_mint")
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)

    def test_build_comparison_without_sources_rejected_in_all_modes(self):
        # An empty map made the per-file source check vacuously true, so a
        # build comparison that binds no source at all was printed as verified.
        self.write_build({})
        self.write_receipt("none")
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)
                self.assertIn("build comparison binds no source", completed.stderr)

    def test_receipt_without_sources_rejected_in_all_modes(self):
        self.write_receipt("receipt_sources")
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)
                self.assertIn("receipt binds no source", completed.stderr)

    def test_valid_receipt_accepted_in_all_modes(self):
        self.write_receipt("none")
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK", completed.stdout)

    def run_regression_baseline(self, bound_inputs, **rows):
        self.write_regression_package(bound_inputs, **rows)
        self.write_receipt("none", REGRESSION_BASELINE)
        return [self.run_driver(optimization, REGRESSION_BASELINE) for optimization in MODES]

    def test_regression_baseline_bound_quote_inputs_accepted_in_all_modes(self):
        for completed in self.run_regression_baseline(self.stub_quote_input()):
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("OK", completed.stdout)

    def test_regression_baseline_quote_without_inputs_rejected_in_all_modes(self):
        # The quote receipt is bound only by its hash in the package's own
        # regression summary, so an empty map was printed as verified.
        for completed in self.run_regression_baseline({}):
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
            self.assertNotIn("OK", completed.stdout)
            self.assertIn("quote regression binds no input", completed.stderr)

    def test_regression_baseline_wrong_quote_input_hash_rejected_in_all_modes(self):
        self.stub_quote_input()
        for completed in self.run_regression_baseline({QUOTE_INPUT: "0" * 64}):
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
            self.assertNotIn("OK", completed.stdout)
            self.assertIn("quote bound input hash differs", completed.stderr)

    def test_regression_baseline_quote_rows_disagreeing_with_header_rejected_in_all_modes(self):
        # The header is trusted only when the retained result rows agree with it.
        rows = [{"matches": True} for _ in range(506)] + [{"matches": False}]
        for completed in self.run_regression_baseline(self.stub_quote_input(), quote_rows=rows):
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
            self.assertNotIn("OK", completed.stdout)
            self.assertIn("quote regression cases/mismatches differ", completed.stderr)

    def test_regression_baseline_curve_rows_disagreeing_with_header_rejected_in_all_modes(self):
        rows = [{"mismatches": []} for _ in range(55)] + [{"mismatches": ["hop-3"]}]
        for completed in self.run_regression_baseline(self.stub_quote_input(), curve_rows=rows):
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
            self.assertNotIn("OK", completed.stdout)
            self.assertIn("curve regression case count differs", completed.stderr)


if __name__ == "__main__":
    unittest.main()
