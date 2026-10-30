#!/usr/bin/env python3
"""Actual source-admission CLI checks; captured ELF controls claim no rebuild."""
import concurrent.futures
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
CANDIDATE = ROOT / 'evidence/original/pump/deployed.so'
COUNTS = {'buy': 334, 'quote': 130, 'sell': 301, 'config_admin': 351, 'authority': 59}
SUITES = tuple('pump_validate_' + name + '.py' for name in COUNTS)
DELETE_DRIVER = r'''
import runpy,sys
from pathlib import Path
script,source,*args=sys.argv[1:];source=Path(source);count=0
sys.path.insert(0,str(Path(script).parent));sys.argv=[script,*args]
def profile(frame,event,arg):
 global count
 if event=='return' and frame.f_code.co_filename==script and frame.f_code.co_name in ('run','execute'):
  count+=1
  if count==1:source.unlink()
sys.setprofile(profile)
try:runpy.run_path(script,run_name='__main__')
finally:sys.setprofile(None)
'''


class EmptySourceBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='source-binding-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def invoke(self, script, source, output, *, candidate=None, delete=None):
        args = ['--candidate', str(candidate or CANDIDATE), '--source-directory', str(source),
                '--output', str(output)]
        command = [sys.executable, '-B', str(SCRIPTS / script), *args]
        if delete:
            command = [sys.executable, '-B', '-c', DELETE_DRIVER,
                       str(SCRIPTS / script), str(delete), *args]
        env = dict(os.environ)
        env.pop('PYTHONOPTIMIZE', None)
        return subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                              text=True, timeout=120)

    def source(self, base):
        source = base / 'target' / 'input-crate'
        source.mkdir(parents=True)
        (source / 'lib.rs').write_text('// test-only admitted source input\n')
        # The root target/ directory is generated output, not a source input.
        (source / 'target').mkdir()
        (source / 'target/generated.rs').write_text('// generated\n')
        return source

    def test_all_entrypoints_refuse_empty_non_source_and_target_only_trees(self):
        for kind in ('missing', 'empty', 'unrelated', 'target-only'):
            source = self.root / kind
            if kind != 'missing':source.mkdir()
            if kind == 'unrelated':(source / 'README.md').write_text('not compiler input')
            if kind == 'target-only':
                (source / 'target').mkdir();(source / 'target/generated.rs').write_text('// generated')
            for script in (*SUITES, 'pump_validate_all.py'):
                with self.subTest(kind=kind, script=script):
                    output = self.root / (kind + '-' + script) / 'report.json.gz'
                    result = self.invoke(script, source, output, candidate=self.root/'missing.so')
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn('no Rust/Cargo inputs under ' + str(source), result.stderr)
                    self.assertNotIn('FileNotFoundError', result.stderr)
                    self.assertFalse(output.parent.exists())

    def test_all_five_real_corpora_bind_admitted_sources_under_target_ancestor(self):
        def check(script):
            base = self.root / script;base.mkdir()
            source = self.source(base);output = base/'report.json.gz'
            result = self.invoke(script, source, output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(gzip.decompress(output.read_bytes()))
            key = script.removeprefix('pump_validate_').removesuffix('.py')
            self.assertEqual(report['case_count'], COUNTS[key])
            self.assertEqual(len(report['cases']), COUNTS[key])
            self.assertEqual(report['mismatches'], [])
            self.assertEqual(report['source_sha256'], {
                'lib.rs': hashlib.sha256((source/'lib.rs').read_bytes()).hexdigest()})
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(check, SUITES))

    def test_late_source_removal_cannot_publish_an_empty_binding(self):
        for script in ('pump_validate_authority.py', 'pump_validate_buy.py'):
            with self.subTest(script=script):
                base = self.root/script;base.mkdir();source = self.source(base)
                output = base/'report.json.gz';output.write_bytes(b'prior receipt')
                result = self.invoke(script, source, output, delete=source/'lib.rs')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('FileNotFoundError', result.stderr)
                self.assertFalse((source/'lib.rs').exists())
                self.assertEqual(output.read_bytes(), b'prior receipt')

    def test_admitted_source_output_alias_is_still_refused(self):
        source = self.source(self.root)
        original = (source/'lib.rs').read_bytes()
        for script in SUITES:
            with self.subTest(script=script):
                result = self.invoke(script, source, source/'lib.rs')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('report output aliases an input', result.stderr)
                self.assertEqual((source/'lib.rs').read_bytes(), original)

    def test_aggregate_valid_source_reaches_real_candidate_loader(self):
        source = self.source(self.root);output = self.root/'reports/report.json.gz'
        result = self.invoke('pump_validate_all.py', source, output, candidate=self.root/'missing.so')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FileNotFoundError', result.stderr)
        self.assertNotIn('no Rust/Cargo inputs', result.stderr)
        self.assertFalse(output.parent.exists())


if __name__ == '__main__':unittest.main()
