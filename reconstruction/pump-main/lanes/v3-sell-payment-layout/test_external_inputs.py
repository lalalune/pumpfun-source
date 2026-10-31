"""Exercise historical input admission with real Git objects."""
import base64
import copy
import gzip
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from solders.transaction import Transaction
from solders.hash import Hash
from solders.keypair import Keypair
from solders.system_program import transfer, TransferParams

import verify


class HistoricalInputsTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((verify.HERE / 'manifest.json').read_text())
        self.git_dir = subprocess.check_output(
            ['git', '-C', str(verify.ROOT), 'rev-parse', '--absolute-git-dir'],
            text=True).strip()

    def test_real_blobs_need_no_working_tree_inputs(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(verify, 'ROOT', Path(temporary)), \
                patch.dict(os.environ, {'GIT_DIR': self.git_dir}):
            blobs = verify.external_inputs(self.manifest)
        self.assertEqual(set(blobs), set(self.manifest['external']))
        for name, data in blobs.items():
            self.assertEqual(verify.digest(data), self.manifest['external'][name])

    def test_revision_must_be_a_full_commit_object(self):
        revision = self.manifest['externalRevision']
        tree = subprocess.check_output(
            ['git', '-C', str(verify.ROOT), 'rev-parse', revision + '^{tree}'],
            text=True).strip()
        for value in (revision[:12], tree, '0' * 40):
            with self.subTest(revision=value):
                changed = copy.deepcopy(self.manifest)
                changed['externalRevision'] = value
                with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                    verify.external_inputs(changed)

    def test_recorded_digest_is_still_required(self):
        changed = copy.deepcopy(self.manifest)
        name = 'reconstruction/base/functions.tsv'
        changed['external'][name] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'external hash:'):
            verify.external_inputs(changed)


class SignatureAdmissionTests(unittest.TestCase):
    def receipts(self):
        runtime = json.loads(gzip.decompress((verify.HERE / 'runtime.json.gz').read_bytes()))
        return [receipt for row in runtime['rows'] for receipt in row['receipts'].values()]

    def test_unsigned_transaction_is_rejected(self):
        # No signatures verifies as an empty result list, which all() accepts.
        receipt = {'transaction_base64': base64.b64encode(bytes(Transaction.default())).decode()}
        with self.assertRaisesRegex(ValueError, 'invalid retained transaction signature'):
            verify.require_signatures(receipt)

    def test_altered_signature_is_rejected(self):
        raw = bytearray(base64.b64decode(self.receipts()[0]['transaction_base64']))
        raw[2] ^= 0xFF  # Inside the first 64-byte signature, after the count prefix.
        altered = {'transaction_base64': base64.b64encode(bytes(raw)).decode()}
        with self.assertRaisesRegex(ValueError, 'invalid retained transaction signature'):
            verify.require_signatures(altered)

    def test_retained_receipts_verify(self):
        receipts = self.receipts()
        self.assertEqual(len(receipts), 351)
        for receipt in receipts:
            verify.require_signatures(receipt)

    def test_required_signature_cardinality_is_enforced(self):
        # These signed message controls are not additional VM executions.
        one = Keypair.from_seed(bytes([31]) * 32)
        two = Keypair.from_seed(bytes([32]) * 32)
        first = transfer(TransferParams(from_pubkey=one.pubkey(), to_pubkey=two.pubkey(), lamports=1))
        second = transfer(TransferParams(from_pubkey=two.pubkey(), to_pubkey=one.pubkey(), lamports=1))
        complete = Transaction.new_signed_with_payer([first, second], one.pubkey(), [one, two], Hash.default())
        partial = Transaction.populate(complete.message, [complete.signatures[0]])
        single = Transaction.new_signed_with_payer([first], one.pubkey(), [one], Hash.default())
        self.assertEqual(single.message.account_keys[1], two.pubkey())
        extra = Transaction.populate(single.message, [single.signatures[0], two.sign_message(bytes(single.message))])
        for transaction in (complete, single):
            verify.require_signatures({'transaction_base64': base64.b64encode(bytes(transaction)).decode()})
        for transaction in (partial, extra):
            # Both weaker all()/nonempty guards admit these valid signature
            # vectors despite the missing or excessive declared signer count.
            self.assertTrue(all(transaction.verify_with_results()))
            with self.assertRaisesRegex(ValueError, 'invalid retained transaction signature'):
                verify.require_signatures({'transaction_base64': base64.b64encode(bytes(transaction)).decode()})


if __name__ == '__main__':
    unittest.main()
