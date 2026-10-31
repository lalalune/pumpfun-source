"""A checkpoint seal that is not pinned must fail closed, not self-check.

strict_package() in verify_pump_compared_checkpoint and
verify_pump_remaining_checkpoint both compare the manifest sidecar against
the pinned SIDECAR_SHA256 entry for the seal. The remaining bridge indexes
the pin table directly (KeyError for an unknown seal). The compared bridge
fell back to hashlib.sha256(sidecar).hexdigest() -- the hash of the very
bytes compared on the previous line -- so the "Known seal" pin degraded to
a self-comparison and any unpinned seal was accepted as long as the package
was internally consistent with itself.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_pump_compared_checkpoint as compared
import verify_pump_remaining_checkpoint as remaining

MODULES = (compared, remaining)


def sealed_package(root):
    raw = json.dumps({}, sort_keys=True).encode()
    seal = hashlib.sha256(raw).hexdigest()
    (root / 'manifest.json').write_bytes(raw)
    (root / 'manifest.sha256').write_bytes((seal + '  manifest.json\n').encode())
    return seal


class UnpinnedSealTests(unittest.TestCase):
    def test_unpinned_seal_is_rejected_by_every_bridge(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary).resolve()
            seal = sealed_package(package)
            for module in MODULES:
                with self.subTest(module=module.__name__):
                    self.assertNotIn(seal, module.SIDECAR_SHA256)
                    with self.assertRaises(KeyError) as caught:
                        module.strict_package(package, seal)
                    self.assertIn(seal, str(caught.exception))

    def test_pinned_seal_is_still_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary).resolve()
            seal = sealed_package(package)
            sidecar = (package / 'manifest.sha256').read_bytes()
            for module in MODULES:
                with self.subTest(module=module.__name__):
                    module.SIDECAR_SHA256[seal] = hashlib.sha256(sidecar).hexdigest()
                    try:
                        self.assertEqual(module.strict_package(package, seal), {})
                    finally:
                        del module.SIDECAR_SHA256[seal]


if __name__ == '__main__':
    unittest.main()
