"""Actual retained diagnostic CLI over the real Pump/CENSUS input layout."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
LANE = Path('reconstruction/pump-main/lanes/callgraph-census')


class CensusPortabilityTests(unittest.TestCase):
    def test_actual_hotness_report_and_all_five_cli_parsers(self):
        with tempfile.TemporaryDirectory(prefix='pump-census-portable-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-census-portable-'))
            for name in ['census.py', 'callid_audit.py', 'dataref_audit.py', 'blocksim.py', 'hotness.py',
                         'CENSUS.json', 'NOTES.md']:
                target = root / LANE / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / LANE / name, target)
            for name in ['score.py', 'win.py', 'coords.py']:
                target = root / 'reconstruction/harness' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / 'reconstruction/harness' / name, target)
            for name in ['original.so', 'functions.tsv']:
                target = root / 'reconstruction/base' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                source = (ROOT / 'evidence/original/pump/deployed.so' if name == 'original.so'
                          else ROOT / 'reconstruction/base/functions.tsv')
                shutil.copyfile(source, target)
            capture = root / 'evidence/original/pump/deployed.so'
            capture.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'evidence/original/pump/deployed.so', capture)
            runner = root / 'reconstruction/diagnostics/census-portability/run.py'
            runner.parent.mkdir(parents=True)
            shutil.copyfile(PACKAGE / 'run.py', runner)
            def invoke(*arguments):
                return subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', *map(str, arguments)],
                                      cwd=root, capture_output=True, text=True, encoding='utf-8')
            common = ['--remarks', root / LANE / 'NOTES.md', '--census', root / LANE / 'CENSUS.json']
            before = invoke(root / LANE / 'hotness.py', *common, '--json', root / 'before.json')
            self.assertNotEqual(before.returncode, 0)
            self.assertIn("No module named 'win'", before.stderr)
            output = root / 'after.json'
            fixed = invoke(runner, 'hotness', *common, '--json', output)
            self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
            actual = json.loads(output.read_text(encoding='utf-8'))
            retained = json.loads((root / LANE / 'CENSUS.json').read_text(encoding='utf-8'))
            self.assertEqual(len(actual), 16)
            for target in retained['targets']:
                self.assertEqual(actual[target['original']]['orig_error_sites'],
                                 target.get('error_format_forms', {}).get('orig', []))
                self.assertEqual(actual[target['original']]['ours'], [])
            # Source notes are an explicit no-remarks control, not an LLVM run.
            for tool in ['census', 'callid', 'dataref', 'blocksim', 'hotness']:
                result = invoke(runner, tool, '--help')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            preserved = output.read_bytes()
            denied = invoke(runner, 'hotness', *common, '--json', output)
            self.assertNotEqual(denied.returncode, 0)
            self.assertEqual(output.read_bytes(), preserved)


if __name__ == '__main__':
    unittest.main()
