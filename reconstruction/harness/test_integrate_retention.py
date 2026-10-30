"""A repeated integration name must preserve the earlier source and report."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import integrate


class IntegrationRetentionTests(unittest.TestCase):
    def invoke(self, root, base):
        argv = ['integrate.py', '--name', 'trial', '--base-src', str(base), '--no-build']
        with patch.object(integrate, 'SC', root), patch.object(sys, 'argv', argv), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            integrate.main()

    def test_existing_result_survives_repeated_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'integ/trial'
            output.mkdir(parents=True)
            marker = output / 'report.json'
            marker.write_bytes(b'prior evidence')
            base = root / 'base'
            base.mkdir()
            with self.assertRaises(SystemExit) as error:
                self.invoke(root, base)
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(marker.read_bytes(), b'prior evidence')
            self.assertEqual(list(output.iterdir()), [marker])

    def test_dangling_result_link_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'integ').mkdir()
            output = root / 'integ/trial'
            output.symlink_to(root / 'missing', target_is_directory=True)
            with self.assertRaises(SystemExit):
                self.invoke(root, root / 'base')
            self.assertTrue(output.is_symlink())
            self.assertFalse((root / 'missing').exists())

    def test_fresh_name_still_composes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / 'base'
            base.mkdir()
            (base / 'lib.rs').write_bytes(b'// source\n')
            self.invoke(root, base)
            self.assertEqual((root / 'integ/trial/src/lib.rs').read_bytes(), b'// source\n')
            self.assertEqual(json.loads((root / 'integ/trial/report.json').read_text())['parts'], [])


if __name__ == '__main__':
    unittest.main()
