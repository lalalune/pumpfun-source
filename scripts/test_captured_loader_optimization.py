"""The captured loader must refuse tampered evidence in every optimization
mode.

`python -O` / `-OO` strip `assert`, and the import-time evidence checks in
scripts/pump_captured_loader.py (program-account shape, programdata hash,
payload hash) were asserts, so a capture.json naming a wrong programdata hash
failed to import under plain python but imported fine under -O/-OO and let
the tampered evidence load into LiteSVM. The driver copies the module into
an isolated tree with synthetic evidence and stub solders modules -- the
real solders package and the 10 MB captured binaries are not present here --
so the only difference between the modes is whether the checks run.
"""

import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "pump_captured_loader.py"

DRIVER = """
import hashlib, json, struct, sys, types
from pathlib import Path
tmpdir, mode = Path(sys.argv[1]), sys.argv[2]
scripts = tmpdir / 'scripts'
sys.path.insert(0, str(scripts))

class Pubkey:
    def __init__(self, raw):
        self._raw = raw
    @classmethod
    def from_string(cls, s):
        return cls(hashlib.sha256(s.encode()).digest())
    def __bytes__(self):
        return self._raw
    def __eq__(self, other):
        return isinstance(other, Pubkey) and self._raw == other._raw
    def __hash__(self):
        return hash(self._raw)

class Account:
    def __init__(self, lamports, data, owner, executable):
        self.lamports, self.data, self.owner, self.executable = lamports, data, owner, executable

class LiteSVM:
    pass

class Rent:
    @staticmethod
    def default():
        return Rent()
    def minimum_balance(self, size):
        return 0

class Clock:
    def __init__(self, slot, epoch_start_timestamp, epoch, leader_schedule_epoch, unix_timestamp):
        self.slot = slot

def module(name, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod

module('solders')
module('solders.litesvm', LiteSVM=LiteSVM)
module('solders.account', Account=Account)
module('solders.pubkey', Pubkey=Pubkey)
module('solders.rent', Rent=Rent)
module('solders.clock', Clock=Clock)

try:
    import pump_captured_loader
    print('imported')
except AssertionError as error:
    print('rejected:', error)
"""


def fixture(root, mode):
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    shutil.copyfile(MODULE, scripts / "pump_captured_loader.py")
    evidence = root / "evidence" / "original" / "pump"
    evidence.mkdir(parents=True)
    program_str, programdata_str, owner_str = "program111", "programdata111", "owner111"
    program_bytes = b"PROG" + hashlib.sha256(programdata_str.encode()).digest()
    header = struct.pack("<I", 3) + struct.pack("<Q", 4242) + bytes([1]) + bytes(range(32))
    payload = b"\\x7fELF" + b"\\x00" * 100
    programdata = header + payload
    capture = {
        "program": program_str,
        "programdata": programdata_str,
        "owner": owner_str,
        "lamports": 100,
        "programdata_sha256": "0" * 64 if mode == "tampered" else hashlib.sha256(programdata).hexdigest(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_bytes": len(payload),
    }
    (evidence / "capture.json").write_text(json.dumps(capture))
    (evidence / "program-account.bin").write_bytes(program_bytes)
    (evidence / "programdata-account.bin").write_bytes(programdata)


class CapturedLoaderOptimizationTests(unittest.TestCase):
    def run_driver(self, flags, mode):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root, mode)
            return subprocess.run(
                [sys.executable, "-B", *flags, "-c", DRIVER, str(root), mode],
                capture_output=True, text=True, timeout=60)

    def test_tampered_evidence_is_rejected_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags):
                result = self.run_driver(flags, "tampered")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("rejected:", result.stdout)
                self.assertNotIn("imported", result.stdout)

    def test_valid_evidence_still_imports_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags):
                result = self.run_driver(flags, "valid")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("imported", result.stdout)


if __name__ == "__main__":
    unittest.main()
