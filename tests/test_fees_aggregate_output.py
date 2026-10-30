"""Exercise the real aggregate CLI's output boundary with small child receipts.

The child programs only isolate publication; they do not simulate SBF execution.
The recorded manual reproduction additionally runs all 18 real LiteSVM suites.
"""
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/fees_validate_all.py'
CHILD = '''import argparse,hashlib,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--candidate');p.add_argument('--output');a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
pathlib.Path(a.output).write_text(json.dumps({'original_sha256':sha(r/'evidence/original/pump_fees/deployed.so'),'candidate_sha256':sha(a.candidate),'cases':[{}],'mismatches':[]}))
'''


class FeesAggregateOutputTests(unittest.TestCase):
    def fixture(self, root):
        scripts = root / 'scripts'
        scripts.mkdir()
        for name in ('fees_validate_all.py', 'pump_differential_output.py', 'pump_amm_reusable_harness.py'):
            shutil.copyfile(ROOT / 'scripts' / name, scripts / name)
        tree = ast.parse(SCRIPT.read_text())
        suites = next(ast.literal_eval(node.iter) for node in ast.walk(tree)
                      if isinstance(node, ast.For) and isinstance(node.iter, ast.List))
        self.assertEqual(len(suites), 18)
        for _, name in suites:
            (scripts / name).write_text(CHILD)
        for relative in (
            'programs/pump-fees/unused-source-input.rs',
            'evidence/original/pump_fees/deployed.so',
            'evidence/dependencies/donation_relay/deployed.so',
            'research/fees-query-inputs/quote-selector-cases.json.gz',
            'research/fees-query-inputs/fee-selector-cases.json.gz',
            'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
        ):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'retained fixture input')
        candidate = root / 'candidate.so'
        candidate.write_bytes(b'retained candidate input')
        return candidate

    def invoke(self, root, candidate, output, *, limited=False):
        command = [sys.executable, '-B', str(root / 'scripts/fees_validate_all.py'),
                   '--candidate', str(candidate), '--output', str(output)]
        if limited:
            # Each small child receipt fits; the complete aggregate exceeds it.
            command = [sys.executable, '-c',
                       'import os,resource,signal,sys;'
                       'signal.signal(signal.SIGXFSZ,signal.SIG_IGN);'
                       'resource.setrlimit(resource.RLIMIT_FSIZE,(512,512));'
                       'os.execv(sys.argv[1],sys.argv[1:])', *command]
        return subprocess.run(command, capture_output=True, text=True, timeout=30)

    def test_candidate_aliases_are_rejected_before_any_suite(self):
        for kind in ('direct', 'symlink', 'hardlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                candidate = self.fixture(root)
                before = candidate.read_bytes()
                output = candidate if kind == 'direct' else root / 'report.json'
                if kind == 'symlink':
                    output.symlink_to(candidate)
                elif kind == 'hardlink':
                    os.link(candidate, output)
                result = self.invoke(root, candidate, output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('report output aliases an input', result.stderr)
                self.assertEqual(candidate.read_bytes(), before)

    def test_child_inputs_and_sources_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self.fixture(root)
            for relative in (
                'programs/pump-fees/unused-source-input.rs',
            'evidence/original/pump_fees/deployed.so',
                'evidence/dependencies/donation_relay/deployed.so',
                'scripts/fees_admin_differential.py',
                'research/fees-query-inputs/quote-selector-cases.json.gz',
                'research/fees-query-inputs/fee-selector-cases.json.gz',
                'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
            ):
                with self.subTest(input=relative):
                    path = root / relative
                    before = path.read_bytes()
                    result = self.invoke(root, candidate, path)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('report output aliases an input', result.stderr)
                    self.assertEqual(path.read_bytes(), before)

    def test_normal_nested_output_can_be_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self.fixture(root)
            output = root / 'reports/aggregate.json'
            for _ in range(2):
                result = self.invoke(root, candidate, output)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(output.read_bytes())
                self.assertEqual(report['case_count'], 18)
                self.assertEqual(len(report['suites']), 18)
                self.assertEqual(report['mismatches'], [])
                self.assertEqual(candidate.read_bytes(), b'retained candidate input')

    @unittest.skipUnless(sys.platform in ('darwin', 'linux'), 'requires POSIX file-size limits')
    def test_failed_aggregate_write_preserves_previous_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self.fixture(root)
            output = root / 'report.json'
            output.write_bytes(b'previous complete report\n')
            result = self.invoke(root, candidate, output, limited=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('File too large', result.stderr)
            self.assertEqual(output.read_bytes(), b'previous complete report\n')
            self.assertEqual(list(root.glob('.report.json.*')), [])

    def test_late_candidate_alias_is_rejected_after_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);candidate=self.fixture(root);output=root/'late.json'
            script=root/'scripts/validate_fee_handlers.py'
            script.write_text(script.read_text()+
                '\npathlib.Path('+repr(str(output))+').symlink_to('+repr(str(candidate))+')\n')
            result=self.invoke(root,candidate,output)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('report output aliases an input',result.stderr)
            self.assertTrue(output.is_symlink())
            self.assertEqual(candidate.read_bytes(),b'retained candidate input')
            self.assertEqual(list(root.glob('.late.json.*')),[])

    def test_child_failure_preserves_previous_aggregate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);candidate=self.fixture(root);output=root/'prior.json'
            output.write_bytes(b'previous complete aggregate')
            (root/'scripts/fees_admin_differential.py').write_text('raise SystemExit(9)\n')
            result=self.invoke(root,candidate,output)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(output.read_bytes(),b'previous complete aggregate')
            self.assertEqual(candidate.read_bytes(),b'retained candidate input')


if __name__ == '__main__':
    unittest.main()
