"""An archived selector must name at least one program with a usable address.

``program_addresses`` returned ``repro/programs.json`` verbatim, so an empty
object made ``main()`` loop over nothing and publish
``audit/local-validation.json`` with ``"programs": {}`` and exit 0 — a
self-consistent receipt for a run that validated no program at all. A
non-string address only failed later, inside ``Pubkey.from_string``.
"""
import json
import hashlib
import io
import os
import shutil
import subprocess
from unittest import mock
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import local_validation


class ArchivedSelectorTests(unittest.TestCase):
    def root_with(self, selector):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / 'repro').mkdir()
        (root / 'repro/programs.json').write_text(json.dumps(selector))
        return root

    def test_empty_selector_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'selects no programs'):
            local_validation.program_addresses(self.root_with({}))

    def test_blank_and_non_string_addresses_are_refused(self):
        for selector in ({'pump': ''}, {'pump': 123}, {'pump': None}, {'': 'address'},
                         {'pump': ' \t\n'}, {' \t': 'address'}, {'pump': '\u2003'}, {'\u2003': 'address'}):
            with self.subTest(selector=selector):
                with self.assertRaises(ValueError):
                    local_validation.program_addresses(self.root_with(selector))

    def test_valid_selector_is_returned_unchanged(self):
        selector = {'pump': 'address-one', 'pump_amm': 'address-two'}
        self.assertEqual(local_validation.program_addresses(self.root_with(selector)),
                         selector)

    def test_capture_fallback_is_unchanged(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / 'evidence/original/pump').mkdir(parents=True)
        (root / 'evidence/original/pump/deployed.so').write_bytes(b'\x7fELF')
        (root / 'evidence/original/pump/capture.json').write_text(
            json.dumps({'program': 'captured-id'}))
        self.assertEqual(local_validation.program_addresses(root),
                         {'pump': 'captured-id'})


    def cli_root(self, selector):
        root = self.root_with(selector)
        (root/'scripts').mkdir()
        shutil.copyfile(Path(local_validation.__file__), root/'scripts/local_validation.py')
        return root

    def invoke(self, root):
        env = dict(os.environ);env.pop('PYTHONOPTIMIZE',None)
        return subprocess.run([sys.executable,'-B',str(root/'scripts/local_validation.py')],
                              cwd=root,env=env,capture_output=True,text=True,timeout=60)

    def test_empty_selector_cli_preserves_prior_report_and_creates_no_output(self):
        for prior in (False,True):
            with self.subTest(prior_report=prior):
                root=self.cli_root({});report=root/'audit/local-validation.json'
                if prior:
                    report.parent.mkdir();report.write_bytes(b'prior smoke receipt')
                result=self.invoke(root)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('selects no programs',result.stderr)
                if prior:self.assertEqual(report.read_bytes(),b'prior smoke receipt')
                else:self.assertFalse(report.parent.exists())

    def test_real_mayhem_only_cli_runs_all_67_malformed_inputs(self):
        repository=Path(local_validation.__file__).resolve().parents[1]
        capture=repository/'evidence/original/mayhem'
        address=json.loads((capture/'capture.json').read_text(encoding='utf-8'))['program']
        root=self.cli_root({'mayhem':address})
        shutil.copytree(capture,root/'evidence/original/mayhem')
        result=self.invoke(root)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        data=json.loads((root/'audit/local-validation.json').read_bytes())
        self.assertEqual(set(data['programs']),{'mayhem'})
        report=data['programs']['mayhem']
        self.assertEqual(len(report['cases']),67)
        self.assertTrue(report['all_rejected'])
        self.assertTrue(all(row['rejected'] for row in report['cases']))
        self.assertEqual(report['binary_sha256'],hashlib.sha256((capture/'deployed.so').read_bytes()).hexdigest())

    def test_actual_utf8_selector_is_independent_of_locale_defaults(self):
        selector={'名':'address'};root=self.root_with(selector)
        (root/'repro/programs.json').write_text(json.dumps(selector,ensure_ascii=False),encoding='utf-8')
        original=io.open
        def locale_open(file,mode='r',buffering=-1,encoding=None,*args,**kwargs):
            if 'b' not in mode and encoding in (None,'locale'):encoding='cp949'
            return original(file,mode,buffering,encoding,*args,**kwargs)
        with mock.patch.object(io,'open',side_effect=locale_open):
            self.assertEqual(local_validation.program_addresses(root),selector)


if __name__ == '__main__':
    unittest.main()
