"""Reject zero-exit compiler stack failures without running a compiler or VM."""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fastbuild
import integrate


STACK = 'Error: Function example Stack offset of 4104 exceeded max offset of 4096 by 8 bytes.'


class BuildDiagnosticTests(unittest.TestCase):
    def run_build(self, log, returncode=0, quiet=True, prior=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            src, work, out = (root / name for name in ('src', 'work', 'out'))
            src.mkdir()
            crate = work / 'ws/programs/pump'
            crate.mkdir(parents=True)
            (crate / 'Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\n')
            out.mkdir()
            if prior:
                (out / 'candidate.so').write_bytes(b'prior stripped')
                (out / 'unstripped.so').write_bytes(b'prior unstripped')
                (out / 'build.log').write_bytes(b'prior compiler log')
            recipe = {'triple': 'sbpf-solana-solana', 'rustc': root / 'rustc',
                      'template': root / 'absent-template'}
            commands = []

            def run(command, **kwargs):
                commands.append(command)
                if command[1] == 'build':
                    self.assertFalse((out / 'candidate.so').exists())
                    self.assertFalse((out / 'unstripped.so').exists())
                    self.assertFalse((out / 'build.log').exists())
                    with self.assertRaisesRegex(RuntimeError, 'already in use'):
                        with fastbuild.workspace_lock(work):
                            pass
                    built = work / 'target-identity' / recipe['triple'] / 'release/pump_recovered.so'
                    built.parent.mkdir(parents=True)
                    built.write_bytes(b'synthetic compiler output')
                    return subprocess.CompletedProcess(command, returncode, stdout=log)
                self.assertEqual(command[1], '--strip-all')
                Path(command[-1]).write_bytes(b'synthetic stripped output')
                return subprocess.CompletedProcess(command, 0)

            stderr = io.StringIO()
            with patch.object(fastbuild, 'RECIPES', {'identity': recipe}), \
                 patch.object(fastbuild, 'stage', return_value=work / 'ws/programs/pump'), \
                 patch.object(fastbuild, 'acquire_slot', side_effect=lambda: io.StringIO()), \
                 patch.object(fastbuild.subprocess, 'run', side_effect=run), \
                 patch.object(fastbuild, 'run_compiler', side_effect=lambda command, **kw: (run(command), False)), \
                 contextlib.redirect_stderr(stderr):
                result = fastbuild.build(src, work, out, quiet=quiet, recipe='identity')
            with fastbuild.workspace_lock(work):
                pass
            files = {p.relative_to(out).as_posix(): p.read_bytes()
                     for p in out.rglob('*') if p.is_file()}
            return result, files, commands, stderr.getvalue()

    def test_zero_exit_stack_error_rejects_before_publishing(self):
        log = STACK + '\nFinished release\n'
        result, files, commands, _ = self.run_build(log)
        self.assertFalse(result['ok'])
        self.assertFalse(result['runtime_valid'])
        self.assertEqual(result['stack_warnings'], [STACK])
        self.assertEqual(set(files), {'build.log', 'source-inputs.json'})
        self.assertEqual(files['build.log'], log.encode())
        self.assertEqual(json.loads(files['source-inputs.json'])['schema'], 'pump-source-inputs-v1')
        self.assertEqual(len(commands), 1)
        self.assertNotIn('unstripped', result)

    def test_rejected_build_preserves_prior_artifacts(self):
        result, files, commands, diagnostic = self.run_build(STACK, quiet=False, prior=True)
        self.assertFalse(result['ok'])
        self.assert_archived(files)
        self.assertEqual(files['build.log'], STACK.encode())
        self.assertEqual(len(commands), 1)
        self.assertIn('STACK OVERFLOW RISK', diagnostic)

    def assert_archived(self, files):
        self.assertNotIn('candidate.so', files)
        self.assertNotIn('unstripped.so', files)
        archived = {Path(name).name: value for name, value in files.items()
                    if name.startswith('previous/build-')}
        self.assertEqual(archived, {'candidate.so': b'prior stripped',
                                    'unstripped.so': b'prior unstripped',
                                    'build.log': b'prior compiler log'})
        self.assertEqual(len({str(Path(name).parent) for name in files
                              if name.startswith('previous/')}), 1)

    def test_nonzero_exit_archives_prior_outputs(self):
        result, files, commands, _ = self.run_build('compiler failed', returncode=1, prior=True)
        self.assertFalse(result['ok'])
        self.assert_archived(files)
        self.assertEqual(files['build.log'], b'compiler failed')
        self.assertEqual(len(commands), 1)

    def test_success_replaces_current_outputs_and_preserves_evidence(self):
        result, files, _, _ = self.run_build('Finished release', prior=True)
        self.assertTrue(result['ok'])
        self.assertEqual(files.pop('candidate.so'), b'synthetic stripped output')
        self.assertEqual(files.pop('unstripped.so'), b'synthetic compiler output')
        self.assert_archived(files)
        self.assertEqual(files['build.log'], b'Finished release')

    def test_repeated_archives_keep_distinct_evidence_and_dangling_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            for content in (b'first', b'second'):
                (out / 'unstripped.so').write_bytes(content)
                (out / 'candidate.so').symlink_to('missing.so')
                fastbuild.archive_previous_outputs(out)
                self.assertFalse((out / 'candidate.so').is_symlink())
                self.assertFalse((out / 'unstripped.so').exists())
            archives = list((out / 'previous').iterdir())
            self.assertEqual(len(archives), 2)
            self.assertEqual({(p / 'unstripped.so').read_bytes() for p in archives},
                             {b'first', b'second'})
            self.assertTrue(all((p / 'candidate.so').is_symlink() for p in archives))

    def test_clean_build_still_publishes_both_outputs(self):
        result, files, commands, _ = self.run_build('Finished release\n')
        self.assertTrue(result['ok'])
        self.assertEqual(result['stack_warnings'], [])
        self.assertEqual(files['unstripped.so'], b'synthetic compiler output')
        self.assertEqual(files['candidate.so'], b'synthetic stripped output')
        self.assertEqual(len(commands), 2)

    def test_nonzero_compiler_exit_still_rejects(self):
        result, files, commands, _ = self.run_build('compiler failed\n', returncode=1)
        self.assertFalse(result['ok'])
        self.assertEqual(set(files), {'build.log', 'source-inputs.json'})
        self.assertEqual(len(commands), 1)

    def test_integration_does_not_score_rejected_build(self):
        result, _, _, _ = self.run_build(STACK)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            (source / 'src').mkdir()
            (source / 'Cargo.toml').write_text('[package]\nname="synthetic"\nversion="0.0.0"\n')
            (source / 'Cargo.lock').write_text('version = 3\n')
            (source / 'src/lib.rs').write_text('// synthetic input\n')
            baseline = root / 'pump-main/baseline'
            baseline.mkdir(parents=True)
            (baseline / 'score.json').write_text('{}')
            argv = ['integrate.py', '--name', 'stack-check', '--base-src', str(source)]
            with patch.object(integrate, 'SC', root), patch.object(sys, 'argv', argv), \
                 patch.object(integrate, 'build_source', return_value=result), \
                 patch.object(integrate.subprocess, 'run',
                              return_value=subprocess.CompletedProcess([], 0, stdout='{}')) as command, \
                 contextlib.redirect_stdout(io.StringIO()):
                integrate.main()
            command.assert_not_called()
            report = json.loads((root / 'integ/stack-check/report.json').read_text())
            self.assertFalse(report['build']['ok'])
            self.assertNotIn('score', report)


if __name__ == '__main__':
    unittest.main()
