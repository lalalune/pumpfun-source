"""A cache path at the filesystem's name limit must not fail on its staging name."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('prepare_locked_cargo_home.py')
CRATES_IO = 'registry+https://github.com/rust-lang/crates.io-index'
NAMESPACE = 'index.crates.io-1949cf8c6b5b557f'


class LockedCacheLongOutputTests(unittest.TestCase):
    def prepare(self, root, name):
        home = root / 'cargo-home'
        archive = home / 'registry/cache' / NAMESPACE / 'cache-probe-1.0.0.crate'
        archive.parent.mkdir(parents=True)
        archive.write_bytes(b'isolated archive')
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        index = home / 'registry/index' / NAMESPACE / '.cache/ca/ch/cache-probe'
        index.parent.mkdir(parents=True)
        record = json.dumps({'name': 'cache-probe', 'vers': '1.0.0', 'cksum': digest},
                            separators=(',', ':')).encode()
        index.write_bytes(b'\x03\x02\x00\x00\x00offline-fixture\x00' + b'1.0.0\0' + record + b'\0')
        (home / 'registry/index' / NAMESPACE / 'config.json').write_text('{}', encoding='utf-8')
        (root / 'Cargo.lock').write_text(
            f'[[package]]\nname="cache-probe"\nversion="1.0.0"\nsource="{CRATES_IO}"\nchecksum="{digest}"\n',
            encoding='utf-8')
        output = root / 'out' / name
        output.parent.mkdir()
        result = subprocess.run([sys.executable, str(SCRIPT), '--lockfile', str(root / 'Cargo.lock'),
                                 '--output', str(output)],
                                env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
        return result, output

    def test_output_name_at_the_component_limit_is_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, output = self.prepare(Path(tmp), 'c' * 250)
            self.assertEqual(result.returncode, 0, result.stderr[-300:])
            self.assertTrue((output / 'cache-manifest.json').is_file())
            self.assertEqual([path.name for path in output.parent.iterdir()], [output.name])

    def test_short_output_name_keeps_the_readable_staging_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, output = self.prepare(Path(tmp), 'output')
            self.assertEqual(result.returncode, 0, result.stderr[-300:])
            self.assertEqual(list(output.parent.glob('.output.*')), [])


if __name__ == '__main__':
    unittest.main()
