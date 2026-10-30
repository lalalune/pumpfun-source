"""The verified-build receipt publisher must reject a tampered data-order build
in every optimization mode.

`python -O` / `-OO` strip `assert`, and every acceptance check in
scripts/pump_build_verified.py finish_report() was an assert, so a data-order
build on a cache miss (with changed staged source, primary source, and
certificate) was rejected under plain python but published a receipt claiming
data_order status "passed" under -O/-OO. The driver exercises finish_report()
directly: the full cargo build behind main() needs an admitted v1.44 SDK that
is not present here, and finish_report() is the last gate before the receipt
is published. The stub cache stands in for a cache whose finish() already ran
without enforcing the "hit" requirement -- finish() itself never checks it --
and pump_data_order is stubbed because its import requires
evidence/original/pump/deployed.so, which the sparse checkout excludes;
finish_report() never touches it.
"""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

DRIVER = """
import hashlib, json, sys, types
from pathlib import Path
scripts, tmpdir, mode = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, scripts)
sys.modules['pump_data_order'] = types.ModuleType('pump_data_order')
import pump_build_verified as bv

class StubCache:
    def __init__(self, status):
        self.record = {'status': status}
    def finish(self, target, log, report):
        pass

cert = tmpdir / 'cert.json'
cert.write_text('tampered certificate\\n')
real_source = bv.ROOT / 'scripts' / 'pump_build_verified.py'
real_hash = hashlib.sha256(real_source.read_bytes()).hexdigest()
cert_hash = hashlib.sha256(cert.read_bytes()).hexdigest()
if mode == 'tampered':
    status, source_hash, cert_recorded = 'miss', '0' * 64, '0' * 64
else:
    status, source_hash, cert_recorded = 'hit', real_hash, cert_hash
record = {
    'source_sha256': {'scripts/pump_build_verified.py': source_hash},
    'primary_source_sha256': {'scripts/pump_build_verified.py': source_hash},
    'text_layout': {'data_order_certificate': {'path': str(cert), 'sha256': cert_recorded}},
    'data_order': {},
}
report, receipt = tmpdir / 'report.json', tmpdir / 'receipt.json'
try:
    bv.finish_report(record, report, receipt, StubCache(status),
                     tmpdir / 'target', tmpdir / 'build.log', data_order=True)
except AssertionError as error:
    print('rejected:', error)
else:
    print('published:', json.loads(receipt.read_text())['data_order']['status'])
"""


class BuildVerifiedOptimizationTests(unittest.TestCase):
    def run_driver(self, flags, mode):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-B", *flags, "-c", DRIVER,
                 str(SCRIPTS), directory, mode],
                capture_output=True, text=True, timeout=60)
            return result

    def test_tampered_data_order_receipt_is_rejected_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags):
                result = self.run_driver(flags, "tampered")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("rejected:", result.stdout)
                self.assertNotIn("published:", result.stdout)

    def test_valid_data_order_receipt_still_passes_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags):
                result = self.run_driver(flags, "valid")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("published: passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
