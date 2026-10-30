"""Path crates staged inside the Pump crate must recompile; no compiler, SDK or VM is run.

fastbuild keeps a persistent target directory, and `rsync -a` stages sources with
their original mtimes. Cargo trusts mtimes for local packages, so any local
package whose fingerprint survives can be linked from an earlier trial.
"""
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fastbuild

ROOT = Path(__file__).resolve().parents[2]
TRIPLE = 'sbpf-solana-solana'
HASH = '0123456789abcdef'


class PathCrateInvalidationTests(unittest.TestCase):
    def fingerprints_at_compile(self, crate, packages):
        """Build `crate` on a target holding fingerprints for `packages`; return those left for cargo."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, out = root / 'work', root / 'out'
            fingerprints = work / 'target-identity' / TRIPLE / 'release/.fingerprint'
            for package in packages:
                (fingerprints / f'{package}-{HASH}').mkdir(parents=True)
                (fingerprints / f'{package}-{HASH}' / 'lib-synthetic').write_text('synthetic\n')
            recipe = {'triple': TRIPLE, 'rustc': root / 'rustc', 'template': root / 'absent-template'}
            seen = []

            def cargo(command, **kwargs):
                # fastbuild starts cargo through build_process.run_compiler.
                self.assertEqual(command[1], 'build')
                seen.extend(sorted(p.name[:-len(HASH) - 1] for p in fingerprints.iterdir()))
                built = work / 'target-identity' / TRIPLE / 'release/pump_recovered.so'
                built.write_bytes(b'synthetic compiler output')
                return subprocess.CompletedProcess(command, 0, 'Finished release\n'), False

            def strip(command, **kwargs):
                self.assertEqual(command[1], '--strip-all')
                Path(command[-1]).write_bytes(b'synthetic stripped output')
                return subprocess.CompletedProcess(command, 0)

            with patch.object(fastbuild, 'RECIPES', {'identity': recipe}), \
                 patch.object(fastbuild, 'stage', return_value=crate), \
                 patch.object(fastbuild, 'snapshot', return_value={'sha256': '0' * 64}), \
                 patch.object(fastbuild, 'assert_unchanged'), \
                 patch.object(fastbuild.link_order, 'configure', return_value=({}, None)), \
                 patch.object(fastbuild, 'acquire_slot', side_effect=lambda: io.StringIO()), \
                 patch.object(fastbuild, 'run_compiler', side_effect=cargo), \
                 patch.object(fastbuild.subprocess, 'run', side_effect=strip):
                result = fastbuild.build(root / 'src', work, out, quiet=True, recipe='identity')
            self.assertTrue(result['ok'])
            return seen

    def test_tracked_pump_token_ext_recompiles(self):
        # The tracked crate nests pump-token-ext, whose functions are scored windows.
        crate = ROOT / 'programs/pump'
        self.assertTrue((crate / 'pump-token-ext/Cargo.toml').is_file())
        seen = self.fingerprints_at_compile(crate, ('anchor-lang', 'pump-recovered', 'pump-token-ext'))
        # Registry dependencies stay cached; both local packages are rebuilt.
        self.assertEqual(seen, ['anchor-lang'])

    def test_any_nested_path_crate_recompiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            crate = Path(temporary) / 'ws/programs/pump'
            (crate / 'crates/helper').mkdir(parents=True)
            (crate / 'Cargo.toml').write_text('[package]\nname = "pump-recovered"\nversion = "0.1.0"\n')
            (crate / 'crates/helper/Cargo.toml').write_text('[package]\nname = "helper-ext"\nversion = "0.1.0"\n')
            seen = self.fingerprints_at_compile(crate, ('helper-ext', 'pump-recovered', 'spl-token'))
        self.assertEqual(seen, ['spl-token'])


if __name__ == '__main__':
    unittest.main()
