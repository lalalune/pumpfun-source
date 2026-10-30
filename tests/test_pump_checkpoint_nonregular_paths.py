"""Pump checkpoint readers must reject nonregular inputs without blocking.

Sibling of the nonregular-input admission in verify_current_checkpoint
(and of open #2231 for verify_current_bindings): both Pump checkpoint
bridges read sealed inputs through content(), which opened the path with a
blocking open and no regular-file pre-check, so a FIFO planted at a read
path (for example repro/status.json or a package manifest.json, which is
read before the strict-package walk) blocked the verifier forever instead
of failing. Both readers now reject nonregular paths before opening and
open nonblocking, mirroring verify_current_checkpoint.read_regular.
"""
import os
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_pump_compared_checkpoint as compared
import verify_pump_remaining_checkpoint as remaining

MODULES = {
    'verify_pump_compared_checkpoint': compared,
    'verify_pump_remaining_checkpoint': remaining,
}

FIFO_SCRIPT = r'''
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("pump_checkpoint", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.content(Path(sys.argv[2]) / "fifo")
except AssertionError as error:
    if "Nonregular path" not in str(error):
        raise
else:
    raise SystemExit("a FIFO was accepted")
'''


class PumpCheckpointNonregularPathTests(unittest.TestCase):
    def test_regular_files_are_still_read(self):
        for module in MODULES.values():
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary).resolve() / 'input.txt'
                path.write_bytes(b'sealed-bytes\n')
                self.assertEqual(module.content(path), b'sealed-bytes\n')

    def test_valid_sealed_package_and_tampered_payload(self):
        for module in MODULES.values():
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as temporary:
                package = Path(temporary).resolve()
                payload = package / 'nested' / 'payload.bin'
                payload.parent.mkdir()
                payload.write_bytes(b'validated payload')
                manifest = {'nested/payload.bin': {
                    'sha256': hashlib.sha256(payload.read_bytes()).hexdigest(),
                    'bytes': payload.stat().st_size,
                }}
                raw = json.dumps(manifest, sort_keys=True).encode()
                seal = hashlib.sha256(raw).hexdigest()
                (package / 'manifest.json').write_bytes(raw)
                sidecar = (seal + '  manifest.json\n').encode()
                (package / 'manifest.sha256').write_bytes(sidecar)
                with mock.patch.dict(module.SIDECAR_SHA256, {seal: hashlib.sha256(sidecar).hexdigest()}):
                    self.assertEqual(module.strict_package(package, seal), manifest)
                    payload.write_bytes(b'tampered payload')
                    with self.assertRaises(module.CheckpointError):
                        module.strict_package(package, seal)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFOs need POSIX')
    def test_fifo_inputs_are_rejected_without_blocking(self):
        for name in MODULES:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                os.mkfifo(root / 'fifo')
                try:
                    result = subprocess.run(
                        [sys.executable, '-B', '-c', FIFO_SCRIPT,
                         str(ROOT / 'scripts' / f'{name}.py'), str(root)],
                        capture_output=True, text=True, timeout=5,
                    )
                except subprocess.TimeoutExpired:
                    self.fail(f'{name}.content blocked on a FIFO')
                self.assertEqual(result.returncode, 0,
                                 f'{name}: ' + result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
