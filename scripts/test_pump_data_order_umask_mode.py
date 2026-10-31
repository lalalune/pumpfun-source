#!/usr/bin/env python3
"""A published data-order certificate keeps the same umask mode as a direct write."""
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_data_order as gate


@unittest.skipIf(os.name == 'nt', 'POSIX permission bits')
class DataOrderUmaskModeTests(unittest.TestCase):
    def publish(self, path, mask):
        path.parent.mkdir(parents=True, exist_ok=True)
        previous = os.umask(mask)
        try:
            gate.publish_certificate(path, {'schema': 1, 'payload': {'roles': ['control']}})
        finally:
            os.umask(previous)
        return stat.S_IMODE(path.stat().st_mode)

    def test_new_certificate_keeps_the_process_umask(self):
        for mask, mode in ((0o022, 0o644), (0o027, 0o640)):
            with self.subTest(mask=oct(mask)):
                with tempfile.TemporaryDirectory(prefix='data-order-umask-') as temporary:
                    path = Path(temporary) / ('certificate-' + oct(mask) + '.json')
                    self.assertEqual(self.publish(path, mask), mode)
                    self.assertEqual(json.loads(path.read_bytes())['payload']['roles'],
                                     ['control'])

    def test_nested_parent_keeps_the_process_umask(self):
        with tempfile.TemporaryDirectory(prefix='data-order-umask-') as temporary:
            path = Path(temporary) / 'new' / 'nested' / 'certificate.json'
            self.assertEqual(self.publish(path, 0o022), 0o644)
            self.assertEqual(list(path.parent.iterdir()), [path])


if __name__ == '__main__':
    unittest.main()
