"""Run the real analyzer CLI on isolated retained ELF/IDL evidence."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORTS = ('binary-analysis.json', 'interface-inventory.json')


class AnalyzeInputAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='analyze-admission-')
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        scripts = self.root / 'scripts'
        scripts.mkdir()
        shutil.copyfile(ROOT / 'scripts/analyze.py', scripts / 'analyze.py')
        self.evidence = self.root / 'evidence'
        capture = self.evidence / 'original/mayhem'
        capture.mkdir(parents=True)
        shutil.copyfile(ROOT / 'evidence/original/mayhem/deployed.so', capture / 'deployed.so')
        upstream = self.evidence / 'upstream'
        upstream.mkdir()
        for source in (ROOT / 'evidence/upstream').glob('pump*.json'):
            shutil.copyfile(source, upstream / source.name)

    def run_analyzer(self):
        # Isolated subprocess roots arise naturally from the copied script path;
        # there is no module/global patching or replacement ELF/IDL parser.
        return subprocess.run(
            [sys.executable, '-I', '-B', '-X', 'utf8', *(['-O'] if sys.flags.optimize else []),
             str(self.root / 'scripts/analyze.py')],
            cwd=self.root, capture_output=True, text=True, encoding='utf-8',
        )

    def test_all_idls_are_admitted_before_either_report_is_replaced(self):
        for invalid in ('{', '{}'):
            with self.subTest(invalid=invalid):
                saved = {}
                for name in REPORTS:
                    saved[name] = (ROOT / 'evidence' / name).read_bytes()
                    (self.evidence / name).write_bytes(saved[name])
                (self.evidence / 'upstream/pump_fees.json').write_text(invalid, encoding='utf-8')
                result = self.run_analyzer()
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue('JSONDecodeError' in result.stderr or 'KeyError' in result.stderr)
                for name in REPORTS:
                    self.assertEqual((self.evidence / name).read_bytes(), saved[name], name)

    def test_failed_first_analysis_publishes_neither_report(self):
        (self.evidence / 'upstream/pump_fees.json').write_text('{', encoding='utf-8')
        result = self.run_analyzer()
        self.assertNotEqual(result.returncode, 0)
        for name in REPORTS:
            self.assertFalse((self.evidence / name).exists(), name)

    def test_invalid_second_report_destination_publishes_neither_report(self):
        prior = self.evidence / 'binary-analysis.json'
        prior.write_text('prior binary report\n', encoding='utf-8')
        (self.evidence / 'interface-inventory.json').mkdir()
        result = self.run_analyzer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('report destination is not a regular file', result.stderr)
        self.assertEqual(prior.read_text(encoding='utf-8'), 'prior binary report\n')
        self.assertTrue((self.evidence / 'interface-inventory.json').is_dir())

    def test_linked_second_report_destination_is_rejected_before_publication(self):
        outside = self.root / 'outside.json'
        outside.write_text('sentinel\n', encoding='utf-8')
        try:
            os.symlink(outside, self.evidence / 'interface-inventory.json')
        except (OSError, NotImplementedError, AttributeError) as error:
            self.skipTest(f'creating links is not permitted: {error}')

        result = self.run_analyzer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('report destination is not a regular file', result.stderr)
        self.assertEqual(outside.read_text(encoding='utf-8'), 'sentinel\n')
        self.assertFalse((self.evidence / 'binary-analysis.json').exists())

    def test_valid_retained_evidence_generates_both_reports(self):
        result = self.run_analyzer()
        self.assertEqual(result.returncode, 0, result.stderr)
        binary = json.loads((self.evidence / REPORTS[0]).read_bytes())
        self.assertEqual(set(binary), {'mayhem'})
        payload = (self.evidence / 'original/mayhem/deployed.so').read_bytes()
        self.assertEqual(hashlib.sha256(payload).hexdigest(),
                         'a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb')
        layout = binary['mayhem']
        self.assertEqual(layout['allocation_bytes'], len(payload))
        self.assertEqual(layout['elf_sha256'], hashlib.sha256(payload[:layout['elf_extent']]).hexdigest())
        interfaces = json.loads((self.evidence / REPORTS[1]).read_bytes())
        for name, inventory in interfaces.items():
            idl = json.loads((self.evidence / 'upstream' / (name + '.json')).read_bytes())
            self.assertEqual(inventory['address'], idl['address'])
            self.assertEqual(inventory['instructions'], len(idl['instructions']))
        self.assertEqual(set(interfaces), {'pump', 'pump_amm', 'pump_fees'})


if __name__ == '__main__':
    unittest.main()
