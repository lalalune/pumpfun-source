"""Regression checks for signer-boundary trace verification under optimized Python.

verify_traces() in scripts/pump_set_mayhem_params_signer_boundary.py checks
saved Mayhem initializer traces: exactly two records, each with a hash-bound
signed transaction whose signature verifies and matches the recorded one, a
successful meta, a CreateV2 instruction, exactly one InitializeMayhemState
log preceded by the Mayhem invoke, and no SetMayhemVirtualParams CPI. Before
this fix every one of those checks was a bare assert, so under -O/-OO a trace
with a mismatched signature, a SetMayhemVirtualParams CPI, or a single record
was still accepted as a clean signer boundary. The solders modules are stubbed
here (the real ones need the solders package), so the driver exercises the
verifier's own admission logic, not transaction verification itself.
"""

from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
MAYHEM_STR = "MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e"

DRIVER = (
    "import sys, base64, gzip, hashlib, json, types\n"
    "from pathlib import Path\n"
    "class Pubkey:\n"
    "    def __init__(self, s):\n"
    "        self._s = s\n"
    "    @classmethod\n"
    "    def from_string(cls, s):\n"
    "        return cls(s)\n"
    "    @classmethod\n"
    "    def find_program_address(cls, seeds, program):\n"
    "        return (cls('pda'), 255)\n"
    "    def __str__(self):\n"
    "        return self._s\n"
    "    def __bytes__(self):\n"
    "        return hashlib.sha256(self._s.encode()).digest()\n"
    "class VersionedTransaction:\n"
    "    @classmethod\n"
    "    def from_bytes(cls, data):\n"
    "        return cls()\n"
    "    def verify_with_results(self):\n"
    "        return [True]\n"
    "    @property\n"
    "    def signatures(self):\n"
    "        return ['real-sig']\n"
    "solders = types.ModuleType('solders')\n"
    "sys.modules['solders'] = solders\n"
    "for mod_name, attrs in [\n"
    "    ('solders.account', {'Account': object}),\n"
    "    ('solders.instruction', {'AccountMeta': object, 'Instruction': object}),\n"
    "    ('solders.keypair', {'Keypair': object}),\n"
    "    ('solders.litesvm', {'LiteSVM': object}),\n"
    "    ('solders.message', {'Message': object}),\n"
    "    ('solders.pubkey', {'Pubkey': Pubkey}),\n"
    "    ('solders.transaction', {'VersionedTransaction': VersionedTransaction}),\n"
    "]:\n"
    "    mod = types.ModuleType(mod_name)\n"
    "    mod.__dict__.update(attrs)\n"
    "    sys.modules[mod_name] = mod\n"
    "import pump_set_mayhem_params_signer_boundary as v\n"
    "tamper = sys.argv[1]\n"
    "trace_path = Path(sys.argv[2])\n"
    "def make_record(sig, extra_logs):\n"
    "    signed = b'tx-bytes'\n"
    "    logs = [f'Program " + MAYHEM_STR + " invoke [2]',\n"
    "            'Program log: Instruction: InitializeMayhemState',\n"
    "            'Instruction: CreateV2 ok'] + extra_logs\n"
    "    return {'signed_transaction_base64': __import__('base64').b64encode(signed).decode(),\n"
    "            'signed_transaction_sha256': hashlib.sha256(signed).hexdigest(),\n"
    "            'signature': sig,\n"
    "            'transaction': {'transaction': {'signatures': [sig]},\n"
    "                            'meta': {'err': None, 'logMessages': logs},\n"
    "                            'slot': 123}}\n"
    "if tamper == 'count':\n"
    "    records = [make_record('real-sig', [])]\n"
    "elif tamper == 'sig':\n"
    "    records = [make_record('other-sig', []), make_record('real-sig', [])]\n"
    "elif tamper == 'params':\n"
    "    records = [make_record('real-sig', ['Instruction: SetMayhemVirtualParams x']),\n"
    "               make_record('real-sig', [])]\n"
    "else:\n"
    "    records = [make_record('real-sig', []), make_record('real-sig', [])]\n"
    "trace_path.write_bytes(gzip.compress(json.dumps(records).encode()))\n"
    "summary = v.verify_traces(trace_path)\n"
    "print('OK')\n"
)

MODES = ([], ["-O"], ["-OO"])


class MayhemSignerBoundaryOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.trace_path = Path(temporary.name) / "traces.json.gz"

    def run_driver(self, optimization, tamper):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, tamper, str(self.trace_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_trace_tampers_rejected_in_all_modes(self):
        for tamper in ("sig", "params", "count"):
            with self.subTest(tamper=tamper):
                for optimization in MODES:
                    with self.subTest(optimization=optimization or "normal"):
                        completed = self.run_driver(optimization, tamper)
                        self.assertNotEqual(completed.returncode, 0, completed.stdout)
                        self.assertNotIn("OK", completed.stdout)

    def test_valid_traces_accepted_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "none")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
