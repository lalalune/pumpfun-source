import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('retained_snapshot', ROOT / 'reconstruction/verification/retained_multihop_outcomes.py')
successor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(successor)


class RetainedSourceSnapshotTests(unittest.TestCase):
    def copy_packet(self, root):
        packet = root / 'packet'
        shutil.copytree(ROOT / successor.PACKET, packet)
        return packet

    def test_gate_replacement_after_admission_cannot_execute(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = self.copy_packet(Path(temporary))
            read = Path.read_bytes
            last = packet / list(successor.SOURCE_PINS)[-1]
            def replace_after_last_pin(path):
                raw = read(path)
                if path == last:
                    (packet / 'verify.py').write_bytes(b"raise RuntimeError('unreviewed gate executed')\n")
                return raw
            with patch.object(Path, 'read_bytes', replace_after_last_pin):
                # The admitted gate detects changed packet membership/hashes;
                # the replacement module must never get to execute first.
                with self.assertRaisesRegex(AssertionError, 'MANIFEST hash/membership differs'):
                    successor.retained_runtime(packet, ROOT)

    def test_correspondence_replacement_cannot_replace_admitted_checker(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = self.copy_packet(Path(temporary))
            load = successor.load_module
            def replace_after_manifest(name, path, *args):
                module = load(name, path, *args)
                if name == 'retained_multihop_gate':
                    manifest = module.manifest
                    def checked_manifest(packet):
                        result = manifest(packet)
                        (packet / 'correspondence.py').write_bytes(b"raise RuntimeError('unreviewed correspondence executed')\n")
                        return result
                    module.manifest = checked_manifest
                return module
            with patch.object(successor, 'load_module', replace_after_manifest):
                result = successor.retained_runtime(packet, ROOT)
            self.assertEqual(result['case_triples'], 16)
            self.assertEqual(result['verified_signatures'], 48)


if __name__ == '__main__':
    unittest.main()
