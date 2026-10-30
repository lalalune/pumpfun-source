"""Allowed crate-name trials must publish Cargo's selected library artifact.

Exercise staging, stale-output cleanup and publication. Compiler and stripping
boundaries are controlled; no SDK, program build or VM is run.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fastbuild


@unittest.skipUnless(shutil.which('rsync'), 'fastbuild staging requires rsync')
class LibraryArtifactTests(unittest.TestCase):
    def test_selected_library_is_rebuilt_and_published(self):
        for package, lib_table, artifact in [
            ('pump-recovered', '', 'pump_recovered'),
            ('pump-recovered', 'name = "pump_identity"\n', 'pump_identity'),
            ('pump-identity', '', 'pump_identity'),
        ]:
            with self.subTest(package=package, library=lib_table), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source, work, out = (root / name for name in ('source', 'work', 'out'))
                (source / 'src').mkdir(parents=True)
                (source / 'Cargo.toml').write_text(
                    f'[package]\nname = "{package}"\nversion = "0.1.0"\n'
                    f'[lib]\n{lib_table}crate-type = ["cdylib"]\n'
                    '[profile.release]\nopt-level = 3\n[workspace]\n')
                (source / 'Cargo.lock').write_text('version = 3\n')
                (source / 'src/lib.rs').write_text('// Controlled compiler boundary.\n')
                built = work / 'target-identity/sbpf-solana-solana/release' / f'{artifact}.so'
                built.parent.mkdir(parents=True)
                built.write_bytes(b'previous trial')
                real_run = subprocess.run

                def compiler(command, **kwargs):
                    self.assertFalse(built.exists(), 'the selected library must not survive from a prior trial')
                    built.write_bytes(b'current compiler output')
                    return subprocess.CompletedProcess(command, 0, 'Finished release\n'), False

                def run(command, **kwargs):
                    if command[0] == 'rsync':
                        return real_run(command, **kwargs)
                    self.assertEqual(command[1], '--strip-all')
                    self.assertEqual(Path(command[2]), built)
                    Path(command[3]).write_bytes(b'current stripped output')
                    return subprocess.CompletedProcess(command, 0)

                recipe = {'triple': 'sbpf-solana-solana', 'rustc': root / 'rustc', 'template': root / 'absent-template'}
                with patch.object(fastbuild, 'RECIPES', {'identity': recipe}), \
                     patch.object(fastbuild, 'LOCKDIR', root / 'locks'), \
                     patch.object(fastbuild, 'run_compiler', side_effect=compiler), \
                     patch.object(fastbuild.subprocess, 'run', side_effect=run):
                    result = fastbuild.build(source, work, out, quiet=True)
                self.assertTrue(result['ok'])
                self.assertEqual((out / 'unstripped.so').read_bytes(), b'current compiler output')
                self.assertEqual((out / 'candidate.so').read_bytes(), b'current stripped output')


if __name__ == '__main__':
    unittest.main()
