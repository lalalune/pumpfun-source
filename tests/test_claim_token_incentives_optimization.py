"""Regression checks for claim token-incentives verification under optimized Python.

account_bytes(), assert_signature() and assert_event_and_cpis() in
scripts/pump_claim_token_incentives_verify.py are the per-case admission checks
of the signed claim differential: an account row is bound to its hash, a replayed
transaction to its signature, and a payout event to its discriminator, mint and
amounts. Before this fix every one of those checks was a bare assert, so under
-O/-OO a row with a mismatched account hash, a transaction whose signature
differs from the recorded one, or a payout event minted to the wrong mint was
accepted silently. The solders and differential modules are stubbed here (the
real ones need the solders package and the on-chain binaries), so the driver
exercises the verifier's own admission logic, not the replay engine.
"""

from pathlib import Path
import hashlib
import os
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

DRIVER = (
    "import sys, base64, hashlib, struct, types\n"
    "from pathlib import Path\n"
    "def fsha(p):\n"
    "    if isinstance(p, (bytes, bytearray)):\n"
    "        return hashlib.sha256(bytes(p)).hexdigest()\n"
    "    return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"
    "fake = types.ModuleType('pump_claim_token_incentives_differential')\n"
    "fake.ROOT = Path('/tmp')\n"
    "fake.sha = fsha\n"
    "fake.TOKEN = 'token-program'\n"
    "fake.PROGRAM = 'pump-program'\n"
    "fake.EVENT_AUTHORITY = 'event-authority'\n"
    "fake.GLOBAL_VOLUME = 'global-volume'\n"
    "sys.modules['pump_claim_token_incentives_differential'] = fake\n"
    "solders = types.ModuleType('solders')\n"
    "txmod = types.ModuleType('solders.transaction')\n"
    "class Transaction:\n"
    "    @classmethod\n"
    "    def from_bytes(cls, data):\n"
    "        return cls()\n"
    "    def verify_with_results(self):\n"
    "        return [True]\n"
    "    @property\n"
    "    def signatures(self):\n"
    "        return ['real-sig']\n"
    "txmod.Transaction = Transaction\n"
    "sys.modules['solders'] = solders\n"
    "sys.modules['solders.transaction'] = txmod\n"
    "import pump_claim_token_incentives_verify as v\n"
    "case = sys.argv[1]\n"
    "tamper = sys.argv[2] == '1'\n"
    "def account_row(value):\n"
    "    data = bytearray(72)\n"
    "    struct.pack_into('<Q', data, 64, value)\n"
    "    return {'data_base64': base64.b64encode(bytes(data)).decode(),\n"
    "            'data_sha256': hashlib.sha256(bytes(data)).hexdigest()}\n"
    "if case == 'account':\n"
    "    row = account_row(1000)\n"
    "    if tamper:\n"
    "        row['data_sha256'] = '0' * 64\n"
    "    v.account_bytes(row)\n"
    "elif case == 'sig':\n"
    "    row = {'transaction_base64': base64.b64encode(b'tx-bytes').decode(),\n"
    "           'signature': 'other-sig' if tamper else 'real-sig'}\n"
    "    v.assert_signature(row)\n"
    "elif case == 'event':\n"
    "    user = b'U' * 32\n"
    "    mint = b'X' * 32 if tamper else b'M' * 32\n"
    "    disc = bytes.fromhex('0102030405060708')\n"
    "    amount, claimed, volume = 5000, 700, 900\n"
    "    event = disc + user + mint + struct.pack('<QqQQ', amount, 10, claimed, volume)\n"
    "    keys = {'user': user, 'mint': b'M' * 32, 'global_ata': 'global-ata',\n"
    "            'user_ata': 'user-ata'}\n"
    "    row = {'before': {'user_ata': account_row(1000), 'global_ata': account_row(9000)},\n"
    "           'after': {'user_ata': account_row(6000), 'global_ata': account_row(4000)},\n"
    "           'event_data_base64': [base64.b64encode(event).decode()],\n"
    "           'case': {'now': 10}, 'user_after': [0, 0, claimed, volume],\n"
    "           'relevant_logs': ['Instruction: TransferChecked ok'],\n"
    "           'inner': [\n"
    "               {'program': 'token-program',\n"
    "                'accounts': [str(keys['global_ata']), str(keys['mint']),\n"
    "                             str(keys['user_ata']), 'global-volume'],\n"
    "                'data_hex': (bytes([12]) + struct.pack('<Q', amount) + bytes([6])).hex()},\n"
    "               {'program': 'pump-program', 'accounts': ['event-authority'],\n"
    "                'data_hex': (v.EVENT_CPI_DISCRIMINATOR + event).hex()}]}\n"
    "    v.assert_event_and_cpis(row, disc, keys)\n"
    "print('OK')\n"
)

MODES = ([], ["-O"], ["-OO"])


class ClaimTokenIncentivesOptimizationTests(unittest.TestCase):
    def run_driver(self, optimization, case, tamper):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, case, "1" if tamper else "0"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_account_hash_tamper_rejected_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "account", True)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)

    def test_signature_tamper_rejected_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "sig", True)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)

    def test_event_mint_tamper_rejected_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "event", True)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)

    def test_valid_helpers_accepted_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                for case in ("account", "sig", "event"):
                    completed = self.run_driver(optimization, case, False)
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertIn("OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
