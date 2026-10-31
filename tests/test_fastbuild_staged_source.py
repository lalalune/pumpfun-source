"""Never publish a successful build attributed to a rewritten staged source."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import fastbuild


@unittest.skipUnless(shutil.which('rsync'), 'requires the staging rsync')
class StagedSourcePublicationTests(unittest.TestCase):
    def test_rewrite_and_addition_stop_publication_and_preserve_previous_outputs(self):
        for operation in ('rewrite', 'add'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source, work, out = (root / name for name in ('source', 'work', 'out'))
                (source / 'src').mkdir(parents=True)
                (source / 'Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\n[profile.release]\npanic="abort"\n[workspace]\n')
                (source / 'Cargo.lock').write_text('version = 3\n')
                (source / 'src/lib.rs').write_text('pub fn value() -> u64 { 1 }\n')
                admitted = fastbuild.snapshot(source)
                out.mkdir()
                for name in ('candidate.so', 'unstripped.so'):
                    (out / name).write_bytes(b'previous complete binary')
                recipe = {'triple': 'sbf-solana-solana', 'rustc': root / 'rustc', 'template': root / 'absent'}

                def compile(command, **_):
                    staged = work / 'ws/programs/pump/src'
                    (staged / ('lib.rs' if operation == 'rewrite' else 'generated.rs')).write_text('pub fn value() -> u64 { 2 }\n')
                    built = work / 'target/sbf-solana-solana/release/pump_recovered.so'
                    built.parent.mkdir(parents=True)
                    built.write_bytes(b'compiler output after changed source')
                    return subprocess.CompletedProcess(command, 0, 'compiler succeeded\n'), False

                with patch.object(fastbuild, 'RECIPES', {'mac': recipe}), \
                     patch.object(fastbuild, 'run_compiler', side_effect=compile), \
                     patch.object(fastbuild, 'acquire_slot', side_effect=lambda: io.StringIO()):
                    with self.assertRaisesRegex(ValueError, 'source inputs changed during compilation: src/'):
                        fastbuild.build(source, work, out, recipe='mac', quiet=True)
                self.assertEqual(fastbuild.snapshot(source), admitted)
                self.assertFalse((out / 'candidate.so').exists())
                self.assertFalse((out / 'unstripped.so').exists())
                self.assertEqual((out / 'build.log').read_text(), 'compiler succeeded\n')
                self.assertEqual(json.loads((out / 'source-inputs.json').read_text()), admitted)
                previous = list((out / 'previous').glob('build-*'))
                self.assertEqual(len(previous), 1)
                for name in ('candidate.so', 'unstripped.so'):
                    self.assertEqual((previous[0] / name).read_bytes(), b'previous complete binary')
                with fastbuild.workspace_lock(work), fastbuild.output_lock(out):
                    pass

    @unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK'), 'requires the explicit v1.44 SDK')
    def test_actual_sbf_codegen_and_standard_out_dir_control(self):
        proof = ROOT / 'research/fastbuild-staged-source-20261101/probe.py'
        result = subprocess.run([sys.executable, '-B', str(proof), str(ROOT), os.environ['PUMP_BUILD_TEST_SDK']],
                                capture_output=True, text=True, check=True)
        rows = {row['case']: row for row in json.loads(result.stdout)}
        for case in ('rewrite_source', 'add_source'):
            self.assertIsNone(rows[case]['result'])
            self.assertIn('changed during compilation: src/generated.rs', rows[case]['error'])
            self.assertFalse(rows[case]['candidate_exists'])
        for case in ('unchanged', 'out_dir', 'pre_generated'):
            self.assertTrue(rows[case]['result']['ok'])
            self.assertTrue(rows[case]['candidate_exists'])
        self.assertTrue(all(row['caller_source_unchanged'] for row in rows.values()))
        self.assertEqual(rows['out_dir']['result']['candidate_sha256'], rows['pre_generated']['result']['candidate_sha256'])
        self.assertNotEqual(rows['unchanged']['result']['candidate_sha256'], rows['pre_generated']['result']['candidate_sha256'])


if __name__ == '__main__':
    unittest.main()
