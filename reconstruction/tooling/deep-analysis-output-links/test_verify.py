"""Exercise both deep-analysis CLIs with captured Mayhem bytes and real links."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ('deep_disassembly.py', 'deep_section_analysis.py')
RUNS = []


def snapshot(folder):
    return {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()}


class DeepAnalysisOutputLinkTests(unittest.TestCase):
    def create_link(self, link, target, *, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f'symlinks are unavailable: {error}')

    def run_analysis(self, script, output, case):
        completed = subprocess.run(
            [sys.executable, '-B', str(ROOT / 'scripts' / script),
             '--program', 'mayhem', '--output', str(output)],
            capture_output=True, text=True, timeout=60,
        )
        RUNS.append({'script': script, 'case': case, 'returncode': completed.returncode,
                     'diagnostic': completed.stderr.strip().splitlines()[-1:]})
        return completed

    def test_member_links_reject_before_any_output_changes(self):
        for script in SCRIPTS:
            for member in ('summary.json', 'verify.py', 'manifest.json'):
                for existing in (True, False):
                    with self.subTest(script=script, member=member, existing=existing), tempfile.TemporaryDirectory() as temporary:
                        root = Path(temporary)
                        output = root / 'packet'
                        output.mkdir()
                        target = root / 'retained-evidence'
                        sentinel = b'retain this evidence\n'
                        if existing:
                            target.write_bytes(sentinel)
                        link = output / member
                        self.create_link(link, target)
                        result = self.run_analysis(script, output, f'{member}:existing={existing}')
                        self.assertNotEqual(result.returncode, 0, result.stdout)
                        self.assertIn('packet entry is not a regular file', result.stderr)
                        self.assertEqual([p.name for p in output.iterdir()], [member])
                        self.assertTrue(link.is_symlink())
                        if existing:
                            self.assertEqual(target.read_bytes(), sentinel)
                        else:
                            self.assertFalse(target.exists())

    def test_output_directory_links_reject_before_publication(self):
        for script in SCRIPTS:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                target = root / 'retained-directory'
                target.mkdir()
                output = root / 'packet'
                self.create_link(output, target, directory=True)
                result = self.run_analysis(script, output, 'directory-symlink')
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('output directory is a link', result.stderr)
                self.assertEqual(list(target.iterdir()), [])

    @unittest.skipUnless(os.name == 'nt', 'Windows junction behavior')
    def test_windows_directory_junctions_reject_before_publication(self):
        import _winapi
        for script in SCRIPTS:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                target = root / 'retained-directory'
                target.mkdir()
                output = root / 'packet'
                _winapi.CreateJunction(str(target), str(output))
                result = self.run_analysis(script, output, 'directory-junction')
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('output directory is a link', result.stderr)
                self.assertEqual(list(target.iterdir()), [])

    def test_regular_packets_regenerate_unchanged_and_verify(self):
        for script in SCRIPTS:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'packet'
                first = self.run_analysis(script, output, 'regular-first')
                self.assertEqual(first.returncode, 0, first.stderr)
                before = snapshot(output)
                second = self.run_analysis(script, output, 'regular-repeat')
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual(snapshot(output), before)
                verified = subprocess.run([sys.executable, '-I', '-B', str(output / 'verify.py')],
                                          capture_output=True, text=True, timeout=30)
                self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--report', type=Path)
    options, remaining = parser.parse_known_args()
    ROOT = options.repo.resolve()
    run = unittest.main(argv=[sys.argv[0], *remaining], exit=False)
    # Four cases, one of them Windows-only; a renamed, emptied or skipped case
    # still exits 0 through wasSuccessful(), so the count and the skip set are
    # checked here.
    skipped = {case.id().rsplit('.', 1)[-1] for case, _ in run.result.skipped}
    allowed_skips = ({'test_windows_directory_junctions_reject_before_publication'}
                     if os.name != 'nt' else set())
    passed = (run.result.wasSuccessful() and run.result.testsRun == 4
              and skipped <= allowed_skips)
    if options.report:
        inputs = [*(f'scripts/{name}' for name in SCRIPTS),
                  'scripts/analyze_program.py', 'scripts/window_elf_reader.py',
                  'evidence/original/mayhem/deployed.so']
        report = {'python': sys.version, 'platform': sys.platform,
                  'passed': passed, 'runs': RUNS,
                  'tests_run': run.result.testsRun,
                  'skipped': [case.id() for case, _ in run.result.skipped],
                  'inputs': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                             for name in inputs}}
        with options.report.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
    sys.exit(0 if passed else 1)
