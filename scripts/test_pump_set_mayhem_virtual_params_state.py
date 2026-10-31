"""The set_mayhem_virtual_params differential compares the whole written state."""
import contextlib
import gzip
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_set_mayhem_virtual_params_differential as differential

from solders.account import Account
from solders.hash import Hash

CANDIDATE_IMAGE = b'candidate image'
REAL_QUOTE_RESERVES = 32


class FakeVm:
    """Stand in for LiteSVM; the candidate image also changes one unrelated curve field."""

    def __init__(self):
        self.accounts = {}
        self.image = None

    def with_transaction_history(self, _):
        return self

    def add_program_from_file(self, key, path):
        if key == differential.PUMP:
            self.image = Path(path).read_bytes()

    def airdrop(self, *_):
        pass

    def latest_blockhash(self):
        return Hash.default()

    def set_account(self, key, account):
        self.accounts[key] = account

    def get_account(self, key):
        return self.accounts[key]

    def send_transaction(self, _):
        if self.image == CANDIDATE_IMAGE:
            old = self.accounts[differential.CURVE]
            data = bytearray(old.data)
            data[REAL_QUOTE_RESERVES] ^= 1
            self.accounts[differential.CURVE] = Account(old.lamports, bytes(data), old.owner)
        return SimpleNamespace(logs=lambda: [])


class WrittenStateTests(unittest.TestCase):
    def run_main(self, root):
        candidate, output = root / 'candidate.so', root / 'report.json'
        candidate.write_bytes(CANDIDATE_IMAGE)
        arguments = ['differential', '--candidate', str(candidate), '--output', str(output)]
        with mock.patch.object(sys, 'argv', arguments), mock.patch.object(differential, 'LiteSVM', FakeVm), \
                mock.patch.object(differential, 'cases', lambda: differential_cases[:1]), \
                contextlib.redirect_stdout(io.StringIO()):
            differential.main()
        return output

    def test_candidate_changing_another_curve_field_is_a_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exit_code = 0
            try:
                output = self.run_main(root)
            except SystemExit as stopped:
                exit_code = stopped.code
                output = root / 'report.json'
            report = json.loads(gzip.decompress(output.read_bytes()))
            self.assertEqual(report['mismatches'], [0])
            self.assertEqual(report['cases'][0]['diff'], ['writable_accounts'])
            self.assertEqual(exit_code, 1)


differential_cases = differential.cases()

if __name__ == '__main__':
    unittest.main()
