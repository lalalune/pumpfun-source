"""The RPC capture must refuse an intervening deployment change in every
optimization mode.

`python -O` / `-OO` strip `assert`, and every acceptance check in
scripts/capture.py was an assert, so a capture whose program bytes changed
between the first read and the re-read was rejected under plain python but
published evidence (program-account, programdata, deployed payload, and a
capture.json report) under -O/-OO. The driver stubs the module-level rpc()
function with canned finalized accounts -- no network -- and varies only
whether the re-read returns changed program bytes, so the only difference
between the modes is whether the checks run.
"""

import base64
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

DRIVER = """
import base64, json, struct, sys, tempfile
from pathlib import Path
scripts, tmpdir, mode = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, scripts)
import capture as cap

KEY = 'Pump111111111111111111111111111111111111111'
OWNER = 'BPFLoaderUpgradeab1e11111111111111111111111'
p = struct.pack('<I', 2) + bytes(range(32))
pd = cap.b58(p[4:36])
d = struct.pack('<I', 3) + struct.pack('<Q', 4242) + bytes([1]) + bytes(range(32)) + b'\\x7fELF' + b'\\x00' * 100
p2 = struct.pack('<I', 2) + bytes([255] * 32) if mode == 'tampered' else p

def acct(value_data, slot, executable, owner):
    return {'value': {'data': [base64.b64encode(value_data).decode(), 'base64'],
                      'executable': executable, 'owner': owner, 'lamports': 100},
            'context': {'slot': slot}}

calls = {'n': 0}
def fake_rpc(url, method, params):
    if method == 'getGenesisHash':
        return 'genesis-hash'
    key = params[0]
    cfg = params[1] if len(params) > 1 else {}
    if isinstance(cfg, dict) and 'dataSlice' in cfg:
        return acct(d[:45], 99, False, OWNER)
    if key == KEY:
        calls['n'] += 1
        return acct(p if calls['n'] == 1 else p2, 10 if calls['n'] == 1 else 20, True, OWNER)
    if key == pd:
        return acct(d, 15, False, OWNER)
    raise ValueError('unexpected key ' + key)

cap.rpc = fake_rpc
out = tmpdir / 'pump'
try:
    cap.capture('https://example.invalid', 'pump', KEY, out)
except AssertionError as error:
    print('rejected:', error)
else:
    print('published:', json.loads((out / 'capture.json').read_text())['program_sha256'])
"""


class CaptureOptimizationTests(unittest.TestCase):
    def run_driver(self, flags, mode):
        with tempfile.TemporaryDirectory() as directory:
            return subprocess.run(
                [sys.executable, "-B", *flags, "-c", DRIVER,
                 str(SCRIPTS), directory, mode],
                capture_output=True, text=True, timeout=60)

    def test_intervening_upgrade_is_rejected_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags):
                result = self.run_driver(flags, "tampered")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("rejected: deployment changed during capture", result.stdout)
                self.assertNotIn("published:", result.stdout)

    def test_unchanged_deployment_still_publishes_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags):
                result = self.run_driver(flags, "valid")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("published:", result.stdout)


if __name__ == "__main__":
    unittest.main()
