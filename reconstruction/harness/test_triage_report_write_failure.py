"""A triage report that cannot be fully written must leave the prior report intact."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

try:
    import resource
except ImportError:  # Not available on Windows.
    resource = None

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
SPEC = importlib.util.spec_from_file_location('window_triage_write_failure', H / 'triage.py')
triage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(triage)


@unittest.skipIf(resource is None, 'requires POSIX file size limits')
class TriageReportWriteFailureTests(unittest.TestCase):
    def test_failed_replacement_keeps_the_prior_report(self):
        prior = b'[{"start": "0x120", "category": "coord"}]'
        rows = [{'start': hex(index), 'category': 'equal-len'} for index in range(2000)]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'triage.json'
            output.write_bytes(prior)
            soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
            # Python ignores SIGXFSZ, so the oversized write raises EFBIG.
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024, hard))
            try:
                with self.assertRaises(OSError):
                    triage.write_report(output, rows)
            finally:
                resource.setrlimit(resource.RLIMIT_FSIZE, (soft, hard))
            self.assertEqual(output.read_bytes(), prior)
            self.assertEqual(os.listdir(temporary), ['triage.json'])


if __name__ == '__main__':
    unittest.main()
