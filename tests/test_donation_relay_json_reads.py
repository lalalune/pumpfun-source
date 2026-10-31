#!/usr/bin/env python3
"""The relay differential must decode its JSON inputs as UTF-8.

donation_relay_differential.py read the relay IDL and the imported AMM fixture
with the platform default encoding. Both files carry documentation text, and on
an ASCII-locale host a non-ASCII byte there aborts the fixture build before any
case runs, the same defect the pump IDL consumers fixed earlier.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

DRIVER = '''
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import donation_relay_differential as differential
differential.IDL = Path(sys.argv[2])
differential.AMM_FIXTURE = Path(sys.argv[3])
accounts, instruction, signers, fee, proof = differential.prepare(json.loads(sys.argv[4]))
print(len(accounts), len(proof["instruction_accounts"]))
'''


class DonationRelayJsonReadTests(unittest.TestCase):
    def inputs(self, root):
        idl = root / 'idl.json'
        idl.write_text(json.dumps({
            'description': 'donation → relay',
            'instructions': [
                {'name': 'donate', 'discriminator': [0] * 8, 'accounts': []},
                {'name': 'donate_native', 'discriminator': [0] * 8, 'accounts': []},
            ],
        }, ensure_ascii=False), encoding='utf-8')
        fixture = root / 'amm.json'
        fixture.write_text(json.dumps({
            'note': 'quote → mint',
            'accounts': {'quote_mint': {'data_base64': '', 'lamports': 0}},
        }, ensure_ascii=False), encoding='utf-8')
        return idl, fixture

    def invoke(self, idl, fixture, case):
        environment = dict(os.environ)
        environment.update(LC_ALL='C', LANG='C', PYTHONUTF8='0', PYTHONCOERCECLOCALE='0')
        return subprocess.run(
            [sys.executable, '-B', '-c', DRIVER, str(ROOT / 'scripts'),
             str(idl), str(fixture), json.dumps(case)],
            capture_output=True, text=True, timeout=120, env=environment)

    def test_non_ascii_idl_decodes(self):
        work = ROOT / 'work'
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='relay-idl-read-', dir=work) as temporary:
            idl, fixture = self.inputs(Path(temporary))
            result = self.invoke(idl, fixture, {'name': 'donate', 'kind': 'donation', 'instruction': 'donate'})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout.strip(), r'^\d+ 0$')

    def test_non_ascii_amm_fixture_decodes(self):
        work = ROOT / 'work'
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='relay-amm-read-', dir=work) as temporary:
            idl, fixture = self.inputs(Path(temporary))
            result = self.invoke(idl, fixture, {'name': 'donate_native', 'kind': 'donation', 'instruction': 'donate_native'})
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
