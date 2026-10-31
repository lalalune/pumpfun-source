"""The oracle must refuse overlapping paths before it writes into the source."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import match_oracle as oracle  # noqa: E402


class SourceOverlapTests(unittest.TestCase):
    def setUp(self):
        for module, name in ((oracle.fastbuild, 'SDK'), (oracle.score, 'BASE')):
            self.addCleanup(setattr, module, name, getattr(module, name))
        self.addCleanup(oracle.fastbuild.RECIPES.__setitem__, 'identity', oracle.fastbuild.RECIPES['identity'])
        self.addCleanup(oracle.score.__dict__.pop, 'OBJDUMP', None)

    def attempt(self, root, source, work, out):
        (root / 'base').mkdir()
        for name in ('original.so', 'functions.tsv'):
            (root / 'base' / name).write_bytes(b'input fixture')
        source.mkdir()
        (source / 'lib.rs').write_text('fixture')
        argv = ['match_oracle.py', '--source', str(source), '--work', str(work), '--out', str(out),
                '--sdk', str(root / 'sdk'), '--hybrid', str(root / 'hybrid'), '--window', '8']
        oracle.score.BASE = root / 'base'
        with patch.object(sys, 'argv', argv), \
             patch.object(oracle.score, 'original_windows', return_value=[{'start': 8}]), \
             self.assertRaisesRegex(ValueError, 'overlap'):
            oracle.main()
        return sorted(path.relative_to(source).as_posix() for path in source.rglob('*'))

    def test_work_inside_source_leaves_the_source_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.assertEqual(self.attempt(root, root / 'source', root / 'source/work', root / 'out'), ['lib.rs'])

    def test_output_inside_source_leaves_the_source_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.assertEqual(self.attempt(root, root / 'source', root / 'work', root / 'source/out'), ['lib.rs'])


if __name__ == '__main__':
    unittest.main()
