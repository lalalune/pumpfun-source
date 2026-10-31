"""Receipt-integrity and non-destructive failure checks for fees_validate_all.py."""

import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fees_validate_all.py"

VALID_CHILD = """import argparse, hashlib, json, pathlib
p = argparse.ArgumentParser()
p.add_argument('--candidate')
p.add_argument('--output')
a = p.parse_args()
r = pathlib.Path(__file__).resolve().parents[1]
sha = lambda path: hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
report = {
    'original_sha256': sha(r / 'evidence/original/pump_fees/deployed.so'),
    'candidate_sha256': sha(a.candidate),
    'cases': [json.loads(pathlib.Path(__file__).with_suffix('.case.json').read_text())],
    'mismatches': [],
}
pathlib.Path(a.output).write_text(json.dumps(report), encoding='utf-8', newline='\\n')
"""


def custom_child_source(extra_expr: str) -> str:
    return f"""import argparse, hashlib, json, pathlib
p = argparse.ArgumentParser()
p.add_argument('--candidate')
p.add_argument('--output')
a = p.parse_args()
r = pathlib.Path(__file__).resolve().parents[1]
sha = lambda path: hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
report = {{
    'original_sha256': sha(r / 'evidence/original/pump_fees/deployed.so'),
    'candidate_sha256': sha(a.candidate),
    'cases': [json.loads(pathlib.Path(__file__).with_suffix('.case.json').read_text())],
    'mismatches': [],
}}
report.update({extra_expr})
pathlib.Path(a.output).write_text(json.dumps(report, ensure_ascii=False), encoding='utf-8', newline='\\n')
"""


class FeesValidateAllReceiptIntegrityTests(unittest.TestCase):
    def build_fixture(self, root: Path) -> Path:
        scripts = root / "scripts"
        scripts.mkdir()
        for name in (
            "fees_validate_all.py",
            "pump_differential_output.py",
            "pump_amm_reusable_harness.py",
            "serial_suite_process.py",
        ):
            shutil.copyfile(ROOT / "scripts" / name, scripts / name)
        harness = root / "reconstruction/harness"
        harness.mkdir(parents=True)
        shutil.copyfile(
            ROOT / "reconstruction/harness/build_process.py",
            harness / "build_process.py",
        )
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        suites = next(
            ast.literal_eval(node.iter)
            for node in ast.walk(tree)
            if isinstance(node, ast.For) and isinstance(node.iter, ast.List)
        )
        self.assertEqual(len(suites), 18)
        retained = json.loads(gzip.decompress((
            ROOT / 'research/runtime-fees-retained-outcomes-20261101/bounded-receipts.json.gz'
        ).read_bytes()))['suites']
        for suite, name in suites:
            (scripts / name).write_text(VALID_CHILD, encoding="utf-8", newline="\n")
            (scripts / name).with_suffix('.case.json').write_text(
                json.dumps(retained[suite]['cases'][0]), encoding='utf-8', newline='\n')
        for relative in (
            "programs/pump-fees/unused-source-input.rs",
            "evidence/original/pump_fees/deployed.so",
            "evidence/dependencies/donation_relay/deployed.so",
            "research/fees-query-inputs/quote-selector-cases.json.gz",
            "research/fees-query-inputs/fee-selector-cases.json.gz",
            "research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json",
        ):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"retained fixture input")
        candidate = root / "candidate.so"
        candidate.write_bytes(b"retained candidate input")
        return candidate

    def invoke(self, root: Path, candidate: Path, output: Path, env=None):
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(root / "scripts/fees_validate_all.py"),
                "--candidate",
                str(candidate),
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

    def test_child_mismatches_preserve_prior_aggregate_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self.build_fixture(root)
            output = root / "prior.json"
            prior = b"previous valid aggregate\n"
            output.write_bytes(prior)
            (root / "scripts/fees_admin_differential.py").write_text(
                custom_child_source("{'mismatches': ['admin-case-1']}"),
                encoding="utf-8",
                newline="\n",
            )
            result = self.invoke(root, candidate, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), prior)

    def test_empty_or_mismatched_case_count_is_rejected(self):
        invalid_payloads = {
            "empty_cases": "{'cases': []}",
            "count_mismatch": "{'case_count': 5, 'cases': [{'match': True}]}",
            "bool_case_count": "{'case_count': True, 'cases': [{'match': True}]}",
            "non_list_cases": "{'case_count': 1, 'cases': None}",
        }
        for label, payload in invalid_payloads.items():
            with self.subTest(kind=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                candidate = self.build_fixture(root)
                output = root / "prior.json"
                prior = b"previous valid aggregate\n"
                output.write_bytes(prior)
                (root / "scripts/fees_config_differential.py").write_text(
                    custom_child_source(payload),
                    encoding="utf-8",
                    newline="\n",
                )
                result = self.invoke(root, candidate, output)
                self.assertNotEqual(result.returncode, 0, label)
                self.assertEqual(output.read_bytes(), prior)

    def test_masked_failures_and_mismatch_count_are_rejected(self):
        invalid_payloads = {
            "failures_masked_by_empty_mismatches": "{'mismatches': [], 'failures': ['query-0']}",
            "nonzero_mismatch_count": "{'mismatch_count': 2, 'failures': [], 'mismatches': []}",
            "bool_mismatch_count": "{'mismatch_count': False, 'failures': []}",
            "string_mismatches": "{'mismatches': 'unexpected-string'}",
        }
        for label, payload in invalid_payloads.items():
            with self.subTest(kind=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                candidate = self.build_fixture(root)
                output = root / "prior.json"
                prior = b"previous valid aggregate\n"
                output.write_bytes(prior)
                (root / "scripts/validate_fee_handlers.py").write_text(
                    custom_child_source(payload),
                    encoding="utf-8",
                    newline="\n",
                )
                result = self.invoke(root, candidate, output)
                self.assertNotEqual(result.returncode, 0, label)
                self.assertEqual(output.read_bytes(), prior)

    def test_contradictory_case_rows_are_rejected(self):
        invalid_payloads = {
            "match_false": "{'cases': [{'match': False}], 'mismatches': []}",
            "match_none": "{'cases': [{'match': None}], 'mismatches': []}",
            "nonempty_different_fields": "{'cases': [{'different_fields': ['after']}], 'mismatches': []}",
            "query_row_outcome_mismatch": (
                "{'cases': [{'name': 'quote-0', 'original': {'fees': [1, 2, 3]}, "
                "'candidate': {'error': 'InstructionError'}}], 'failures': []}"
            ),
            "missing_candidate_outcome": (
                "{'cases': [{'original': {'ok': 1}, 'candidate': None}], 'mismatches': []}"
            ),
        }
        for label, payload in invalid_payloads.items():
            with self.subTest(kind=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                candidate = self.build_fixture(root)
                output = root / "prior.json"
                prior = b"previous valid aggregate\n"
                output.write_bytes(prior)
                (root / "scripts/fees_withdraw_differential.py").write_text(
                    custom_child_source(payload),
                    encoding="utf-8",
                    newline="\n",
                )
                result = self.invoke(root, candidate, output)
                self.assertNotEqual(result.returncode, 0, label)
                self.assertEqual(output.read_bytes(), prior)

    def test_utf8_child_receipt_decodes_under_c_locale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self.build_fixture(root)
            output = root / "aggregate.json"
            (root / "scripts/validate_fee_handlers.py").write_text(
                custom_child_source(
                    "{'scope': 'Two query handlers \\u2192 verified', "
                    "'cases': [{'name': 'quote-0', 'original': {'fees': [1, 2, 3]}, 'candidate': {'fees': [1, 2, 3]}}]}"
                ),
                encoding="utf-8",
                newline="\n",
            )
            env = dict(
                os.environ,
                LC_ALL="C",
                LANG="C",
                PYTHONUTF8="0",
                PYTHONCOERCECLOCALE="0",
            )
            result = self.invoke(root, candidate, output, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["case_count"], 18)
            self.assertEqual(report["mismatches"], [])


if __name__ == "__main__":
    unittest.main()
