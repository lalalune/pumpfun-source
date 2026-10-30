#!/usr/bin/env python3
"""Each external-codec boolean case must corrupt a bool field, not the discriminator.

The real harness needs the removed Pump Global capture, so this test replaces
only its runner. It records the cases main() builds and checks each boolean
patch against the field layout in the checked-in upstream IDLs.
"""
import base64
import collections
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'evidence/original/pump_fees/deployed.so'
SIZES = {'bool': 1, 'u8': 1, 'i8': 1, 'u16': 2, 'i16': 2, 'u32': 4, 'i32': 4,
         'u64': 8, 'i64': 8, 'u128': 16, 'i128': 16, 'pubkey': 32}
# The external account type each case family corrupts.
TYPES = {'global': ('pump', 'Global'), 'curve': ('pump', 'BondingCurve'),
         'pool': ('pump_amm', 'Pool')}


def bool_offsets(program, name):
    """Return {offset: field} for bools in the fixed-size prefix after the discriminator."""
    idl = json.loads((ROOT / f'evidence/upstream/{program}.json').read_text(encoding='utf-8'))
    fields = next(t for t in idl['types'] if t['name'] == name)['type']['fields']
    offset, found = 8, {}
    for field in fields:
        kind = field['type']
        if kind == 'bool':
            found[offset] = field['name']
        if not isinstance(kind, str) or kind not in SIZES:
            break
        offset += SIZES[kind]
    return found


def signed_transaction():
    from solders.hash import Hash
    from solders.keypair import Keypair
    from solders.system_program import TransferParams, transfer
    from solders.transaction import Transaction
    payer = Keypair.from_seed(bytes([7]) * 32)
    instruction = transfer(TransferParams(from_pubkey=payer.pubkey(), to_pubkey=payer.pubkey(), lamports=1))
    transaction = Transaction.new_signed_with_payer([instruction], payer.pubkey(), [payer], Hash.default())
    return base64.b64encode(bytes(transaction)).decode()


def recorded_cases():
    cases = {}
    transaction = signed_transaction()

    def run(case, binary):
        cases.setdefault(case['name'], case)
        return collections.defaultdict(lambda: None, error='rejected', transaction_base64=transaction,
                                       logs=['Program log: AnchorError caused by account: test.'])

    runner = types.ModuleType('fees_sharing_create_differential')
    runner.run = run
    with mock.patch.dict(sys.modules, {'fees_sharing_create_differential': runner}):
        sys.modules.pop('fees_external_codec_differential', None)
        import fees_external_codec_differential as codec
        with tempfile.TemporaryDirectory() as temp:
            argv = ['codec', '--candidate', str(ORIGINAL), '--output', str(pathlib.Path(temp) / 'report.json')]
            with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                codec.main()
    return cases


class ExternalCodecBooleanCases(unittest.TestCase):
    def test_boolean_cases_corrupt_a_bool_field(self):
        cases = recorded_cases()
        for family, (program, name) in TYPES.items():
            with self.subTest(family=family):
                patches = cases[family + '-boolean'][family + '_patches']
                self.assertEqual(len(patches), 1)
                offset, value = patches[0]
                self.assertNotIn(bytes.fromhex(value)[0], (0, 1))
                fields = bool_offsets(program, name)
                self.assertIn(offset, fields, f'{family}-boolean patches offset {offset}, '
                                              f'which is not a {name} bool field {fields}')


if __name__ == '__main__':
    unittest.main()
