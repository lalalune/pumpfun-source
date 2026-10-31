"""An invalid slot count must not move the last good build aside.

Compilation is never reached; no SDK, program build or VM is run.
"""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fastbuild


@unittest.skipUnless(shutil.which('rsync'), 'fastbuild staging requires rsync')
class SlotPreflightTests(unittest.TestCase):
    def test_nonpositive_slots_keep_previous_outputs(self):
        for count in (0, -1):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                source, work, out = (root / name for name in ('source', 'work', 'out'))
                (source / 'src').mkdir(parents=True)
                (source / 'Cargo.toml').write_text(
                    '[package]\nname = "pump-recovered"\nversion = "0.1.0"\n'
                    '[lib]\ncrate-type = ["cdylib"]\n'
                    '[profile.release]\nopt-level = 3\n[workspace]\n')
                (source / 'Cargo.lock').write_text('version = 3\n')
                (source / 'src/lib.rs').write_text('// Never compiled.\n')
                out.mkdir()
                (out / 'unstripped.so').write_bytes(b'last good build')
                (out / 'build.log').write_text('last good log\n')
                recipe = {'triple': 'sbpf-solana-solana', 'rustc': root / 'rustc', 'template': root / 'absent-template'}
                with patch.object(fastbuild, 'SLOTS', count), \
                     patch.object(fastbuild, 'RECIPES', {'identity': recipe}), \
                     patch.object(fastbuild, 'LOCKDIR', root / 'locks'):
                    with self.assertRaisesRegex(ValueError, 'PUMP_BUILD_SLOTS'):
                        fastbuild.build(source, work, out, quiet=True, recipe='identity')
                self.assertEqual(sorted(path.name for path in out.iterdir()), ['build.log', 'unstripped.so'])
                self.assertEqual((out / 'unstripped.so').read_bytes(), b'last good build')
                self.assertFalse(work.exists())


if __name__ == '__main__':
    unittest.main()
