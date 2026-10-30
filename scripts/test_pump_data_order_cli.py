"""CLI admission checks for pump_data_order certificates."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pump_data_order


class DataOrderCliTests(unittest.TestCase):
    def test_existing_output_is_rejected_before_derivation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'certificate.json'
            original = b'prior evidence\n'
            output.write_bytes(original)

            argv = [
                str(Path(pump_data_order.__file__)),
                '--baseline-build',
                str(root / 'missing-build'),
                '--text-section-order',
                str(root / 'missing-order.ld'),
                '--output',
                str(output),
            ]
            stderr = io.StringIO()
            with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    pump_data_order.main()

            self.assertEqual(raised.exception.code, 2)
            self.assertIn('use a new certificate output', stderr.getvalue())
            self.assertEqual(output.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
