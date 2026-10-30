import hashlib
from pathlib import Path
import tempfile
import unittest
from source_manifest_guard import strict_manifest


class IterableInputsTests(unittest.TestCase):
    def test_single_use_inputs_are_checked_and_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            crate = root / 'programs/pump'
            crate.mkdir(parents=True)
            extra = root / 'compiler-input.bin'
            extra.write_bytes(b'synthetic compiler input')
            expected = {'compiler-input.bin': hashlib.sha256(extra.read_bytes()).hexdigest()}
            self.assertEqual(strict_manifest(crate, root, root, iter([extra])), expected)
            self.assertEqual(strict_manifest(crate, root, root, [extra]), expected)
            self.assertEqual(strict_manifest(crate, root, root), {})

    def test_single_use_directory_input_records_nested_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            crate = root / 'programs/pump'
            crate.mkdir(parents=True)
            assets = root / 'assets'
            assets.mkdir()
            (assets / 'input.bin').write_bytes(b'asset')
            self.assertEqual(strict_manifest(crate, root, root, (p for p in [assets])),
                             strict_manifest(crate, root, root, [assets]))


if __name__ == '__main__':
    unittest.main()
