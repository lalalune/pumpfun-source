"""Bind saved Mayhem trade checks to real signed, locally executed instructions."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from solders.account import Account
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
BINARY = ROOT / 'evidence/original/mayhem/deployed.so'
FAMILIES = (('verify_mayhem_buy.py', 'buy'), ('verify_mayhem_sell.py', 'sell'),
            ('verify_mayhem_buy_v2.py', 'buy_v2'), ('verify_mayhem_sell_v2.py', 'sell_v2'),
            ('verify_mayhem_pump_swap.py', 'buy_pump_swap'),
            ('verify_mayhem_pump_swap.py', 'sell_pump_swap'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(account):
    if account is None:
        return None
    return {'lamports': account.lamports, 'owner': str(account.owner),
            'executable': account.executable, 'rent_epoch': account.rent_epoch,
            'data_base64': None if account.executable else base64.b64encode(account.data).decode(),
            'data_sha256': sha(account.data)}


def execute_rejection(name):
    """Use a real selector with missing arguments; the captured SBF rejects it."""
    vm = LiteSVM().with_sigverify(True).with_blockhash_check(True).with_transaction_history(0)
    vm.add_program_from_file(PROGRAM, BINARY)
    payer = Keypair.from_seed(hashlib.sha256(b'mayhem-receipt-owned-test-payer').digest())
    vm.set_account(payer.pubkey(), Account(10**9, b'', Pubkey.default()))
    payload = hashlib.sha256(('global:' + name).encode()).digest()[:8]
    tx = Transaction.new_signed_with_payer([Instruction(PROGRAM, payload, [])],
                                         payer.pubkey(), [payer], vm.latest_blockhash())
    before = {str(key): snapshot(vm.get_account(key)) for key in tx.message.account_keys}
    result = vm.send_transaction(tx)
    if not isinstance(result, FailedTransactionMetadata):
        raise RuntimeError('short trade payload unexpectedly succeeded')
    return {'error': str(result.err()), 'signature': str(tx.signatures[0]),
            'signature_verified': all(tx.verify_with_results()),
            'transaction_base64': base64.b64encode(bytes(tx)).decode(), 'before': before,
            'after': {str(key): snapshot(vm.get_account(key)) for key in tx.message.account_keys},
            'metadata': json.loads(result.meta().to_json())}


class MayhemReceiptAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='mayhem-receipt-admission-')
        cls.addClassCleanup(temporary.cleanup)
        cls.work = Path(temporary.name)
        cls.receipts = {}
        for _, name in FAMILIES:
            original, candidate = execute_rejection(name), execute_rejection(name)
            if original['transaction_base64'] != candidate['transaction_base64']:
                raise RuntimeError('original/candidate signed transactions differ')
            cls.receipts[name] = {
                'original_sha256': sha(BINARY.read_bytes()), 'candidate_sha256': sha(BINARY.read_bytes()),
                'harness_sha256': {str(Path(__file__).relative_to(ROOT)): sha(Path(__file__).read_bytes())},
                'case_count': 1, 'mismatches': [], 'cases': [{
                    'case': {'name': 'short-payload', 'instruction': name},
                    'original': original, 'candidate': candidate, 'different_fields': []}]}

    def verify(self, script, document, flags=(), optimize=None):
        receipt = self.work / 'receipt.json'
        output = self.work / 'verified.json'
        receipt.write_text(json.dumps(document), encoding='utf-8')
        output.unlink(missing_ok=True)
        environment = dict(os.environ)
        environment.pop('PYTHONOPTIMIZE', None)
        if optimize is not None:
            environment['PYTHONOPTIMIZE'] = optimize
        result = subprocess.run(
            [sys.executable, '-B', *flags, str(ROOT / 'scripts' / script),
             '--candidate', str(BINARY), '--receipts', str(receipt), '--output', str(output)],
            cwd=ROOT, env=environment, text=True, capture_output=True, timeout=30)
        return result, output

    def test_matching_instruction_rejections_keep_signature_and_rollback_checks(self):
        for script, name in FAMILIES:
            with self.subTest(script=script, instruction=name):
                result, output = self.verify(script, self.receipts[name])
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(output.read_bytes())
                self.assertEqual(report['verified_signed_transactions'], 2)
                self.assertEqual(report['rejection_cases'], 1)
                self.assertEqual(report['complete_failed_transaction_rollback_checks'], 2)

    def test_other_signed_trade_failures_cannot_count_as_this_instruction(self):
        for script, expected in FAMILIES:
            for actual in self.receipts:
                if actual == expected:
                    continue
                with self.subTest(script=script, expected=expected, actual=actual):
                    document = copy.deepcopy(self.receipts[actual])
                    document['cases'][0]['case']['instruction'] = expected
                    result, output = self.verify(script, document)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertFalse(output.exists())

    def test_empty_or_noninteger_case_counts_cannot_publish_success(self):
        for script, name in FAMILIES:
            for count in (0, True, 1.0):
                with self.subTest(script=script, count=count):
                    document = copy.deepcopy(self.receipts[name])
                    document['case_count'] = count
                    if count == 0:
                        document['cases'] = []
                    result, output = self.verify(script, document)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertFalse(output.exists())

    def test_a_changed_signature_still_fails_cryptographic_verification(self):
        for script, name in FAMILIES:
            with self.subTest(script=script, instruction=name):
                document = copy.deepcopy(self.receipts[name])
                for side in ('original', 'candidate'):
                    record = document['cases'][0][side]
                    wire = bytearray(base64.b64decode(record['transaction_base64']))
                    wire[1] ^= 1  # first signature byte, after the one-signature count
                    tx = Transaction.from_bytes(bytes(wire))
                    self.assertFalse(all(tx.verify_with_results()))
                    record['transaction_base64'] = base64.b64encode(wire).decode()
                    record['signature'] = str(tx.signatures[0])
                    record['metadata']['signature'] = str(tx.signatures[0])
                result, output = self.verify(script, document)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertFalse(output.exists())

    def test_optimized_modes_refuse_before_checks_can_be_stripped(self):
        for script, expected in FAMILIES:
            actual = next(name for name in self.receipts if name != expected)
            document = copy.deepcopy(self.receipts[actual])
            document['cases'][0]['case']['instruction'] = expected
            for flags, optimize in ((('-O',), None), (('-OO',), None), ((), '1'), ((), '2')):
                with self.subTest(script=script, flags=flags, optimize=optimize):
                    result, output = self.verify(script, document, flags, optimize)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn('Normal Python is required', result.stderr)
                    self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
