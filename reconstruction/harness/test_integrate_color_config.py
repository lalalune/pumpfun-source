"""A user's Git color setting must not reach the patches a composition applies."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import integrate


def crate(path, files):
    (path / 'src').mkdir(parents=True)
    (path / 'Cargo.toml').write_text('[package]\nname="synthetic"\nversion="0.0.0"\n')
    (path / 'Cargo.lock').write_text('version = 3\n')
    for name, text in files.items():
        (path / name).write_text(text)


class IntegrateColorConfigTests(unittest.TestCase):
    def compose(self, root, setting):
        config = root / 'gitconfig'
        config.write_text(setting)
        base, part = root / 'base', root / 'part'
        crate(base, {'src/lib.rs': 'one\n', 'src/empty.rs': 'gone\n'})
        # Emptying a file selects the Git diff format.
        crate(part, {'src/lib.rs': 'two\n', 'src/empty.rs': ''})
        sc = root / 'reconstruction'
        argv = ['integrate.py', '--name', 'colored', '--base-src', str(base),
                '--part', 'lane=' + str(part), '--no-build']
        environment = dict(os.environ, GIT_CONFIG_GLOBAL=str(config),
                           GIT_CONFIG_NOSYSTEM='1')
        environment.pop('NO_COLOR', None)
        with patch.object(integrate, 'SC', sc), patch.object(sys, 'argv', argv), \
                patch.dict(os.environ, environment, clear=True), \
                contextlib.redirect_stdout(io.StringIO()):
            status = integrate.main()
        out = sc / 'integ/colored'
        return status, json.loads((out / 'report.json').read_text()), out

    def test_forced_color_is_not_written_into_the_part_patch(self):
        for setting in ('[color]\n\tui = always\n', '[color]\n\tdiff = always\n'):
            with self.subTest(setting=setting), tempfile.TemporaryDirectory() as temporary:
                status, report, out = self.compose(Path(temporary), setting)
                self.assertEqual(report['parts'][0]['status'], 'applied', report['parts'])
                self.assertEqual(status, 0)
                self.assertNotIn(b'\x1b[', (out / 'parts/lane.patch').read_bytes())
                self.assertEqual((out / 'src/src/lib.rs').read_text(), 'two\n')
                self.assertEqual((out / 'src/src/empty.rs').read_text(), '')


if __name__ == '__main__':
    unittest.main()
