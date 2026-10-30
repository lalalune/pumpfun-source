#!/usr/bin/env python3
"""The zero-creator case must actually send a zero creator.

The payload builder hardcoded the paying user as the creator field, so the
case named zero-creator-is-rejected exercised nothing beyond the base case
while the published receipt advertised that coverage. The builder now reads
the case's creator like every sibling create harness.
"""
import struct
import sys
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_create_mayhem_differential as harness  # noqa: E402


def creator_field(payload):
    offset = 8  # discriminator
    for _ in range(3):  # name, symbol, uri
        length = struct.unpack_from('<I', payload, offset)[0]
        offset += 4 + length
    return payload[offset:offset + 32]


class MayhemZeroCreatorTests(unittest.TestCase):
    def run_case_capturing_payload(self, case):
        payloads = []
        original = harness.Transaction.new_signed_with_payer

        def spy(instructions, payer, signers, blockhash):
            for instruction in instructions:
                if instruction.program_id == harness.PROGRAM:
                    payloads.append(bytes(instruction.data))
            return original(instructions, payer, signers, blockhash)

        with mock.patch.object(harness.Transaction, 'new_signed_with_payer', side_effect=spy):
            result = harness.run(case)
        self.assertEqual(len(payloads), 1)
        return payloads[0], result

    def test_zero_creator_case_transmits_the_zero_key(self):
        case = {'case': 'zero-creator-is-rejected',
                'creator': '11111111111111111111111111111111',
                'is_mayhem_mode': True}
        payload, result = self.run_case_capturing_payload(case)
        self.assertEqual(creator_field(payload), bytes(32))
        self.assertIn('InstructionErrorCustom(6030)', result['error'])
        # A rejected signed transaction still charges the fee payer.
        payer = str(harness.USER.pubkey())
        for key, before in result['before'].items():
            after = result['after'][key]
            if key == payer:
                self.assertLess(after['lamports'], before['lamports'])
                self.assertEqual({k: v for k, v in before.items() if k != 'lamports'},
                                 {k: v for k, v in after.items() if k != 'lamports'})
            else:
                self.assertEqual(before, after)

    def test_default_case_still_transmits_the_paying_user(self):
        payload, result = self.run_case_capturing_payload({'case': 'probe'})
        self.assertIsNone(result['error'])
        self.assertNotEqual(creator_field(payload), bytes(32))
        self.assertEqual(creator_field(payload), bytes(harness.USER.pubkey()))


    def test_nonzero_case_creator_is_transmitted(self):
        creator = harness.OTHER.pubkey()
        payload, result = self.run_case_capturing_payload({
            'case': 'custom-creator', 'creator': str(creator),
        })
        self.assertEqual(creator_field(payload), bytes(creator))
        self.assertIsNone(result['error'])


if __name__ == '__main__':
    unittest.main()
