"""Ambient Cargo overrides must not change the staged release recipe.

Exercise staging and the compiler environment. Compiler and stripping boundaries
are controlled; no SDK, program build or VM is run.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fastbuild

OVERRIDES = {
    'CARGO_PROFILE_RELEASE_OPT_LEVEL': '0',
    'CARGO_PROFILE_RELEASE_LTO': 'off',
    'CARGO_PROFILE_RELEASE_CODEGEN_UNITS': '16',
    'CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_OPT_LEVEL': '0',
    'CARGO_INCREMENTAL': '1',
    'CARGO_BUILD_INCREMENTAL': 'true',
    'RUSTC_WORKSPACE_WRAPPER': '/absent/wrapper',
    'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER': '/absent/wrapper',
}


@unittest.skipUnless(shutil.which('rsync'), 'fastbuild staging requires rsync')
class AmbientOverrideTests(unittest.TestCase):
    def compiler_environment(self, ambient):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source, work, out = (root / name for name in ('source', 'work', 'out'))
            (source / 'src').mkdir(parents=True)
            (source / 'Cargo.toml').write_text(
                '[package]\nname = "pump-recovered"\nversion = "0.1.0"\n'
                '[lib]\ncrate-type = ["cdylib"]\n'
                '[profile.release]\nopt-level = 3\n[workspace]\n')
            (source / 'Cargo.lock').write_text('version = 3\n')
            (source / 'src/lib.rs').write_text('// Controlled compiler boundary.\n')
            built = work / 'target-identity/sbpf-solana-solana/release/pump_recovered.so'
            seen = {}
            real_run = subprocess.run

            def compiler(command, **kwargs):
                seen.update(kwargs['env'])
                built.parent.mkdir(parents=True, exist_ok=True)
                built.write_bytes(b'compiler output')
                return subprocess.CompletedProcess(command, 0, 'Finished release\n'), False

            def run(command, **kwargs):
                if command[0] == 'rsync':
                    return real_run(command, **kwargs)
                Path(command[3]).write_bytes(b'stripped output')
                return subprocess.CompletedProcess(command, 0)

            recipe = {'triple': 'sbpf-solana-solana', 'rustc': root / 'rustc', 'template': root / 'absent-template'}
            with patch.dict(os.environ, ambient), \
                 patch.object(fastbuild, 'RECIPES', {'identity': recipe}), \
                 patch.object(fastbuild, 'LOCKDIR', root / 'locks'), \
                 patch.object(fastbuild, 'run_compiler', side_effect=compiler), \
                 patch.object(fastbuild.subprocess, 'run', side_effect=run):
                result = fastbuild.build(source, work, out, quiet=True, recipe='identity')
            self.assertTrue(result['ok'])
            return seen

    def test_overrides_do_not_reach_cargo(self):
        for name, value in OVERRIDES.items():
            with self.subTest(name=name):
                self.assertFalse(name in self.compiler_environment({name: value}), name + ' reached Cargo')

    def test_build_slot_controls_still_reach_cargo(self):
        environment = self.compiler_environment({'CARGO_BUILD_JOBS': '1', 'CARGO_PROFILE_RELEASE_LTO': 'off'})
        self.assertEqual(environment['CARGO_BUILD_JOBS'], '1')


if __name__ == '__main__':
    unittest.main()
