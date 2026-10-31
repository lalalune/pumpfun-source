"""Captured argument setup must stop at every call, including indirect/extern.

The real repository decoder fills Image's normal text cache from retained bytes;
arg_setup, body, normalization and the producer's internal-call selection run
unchanged. This qualifies the API without claiming a full SDK/objdump CLI run.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'reconstruction/pump-main/lanes/callgraph-census'))
import census
from deep_disassembly import decode_instruction
from window_elf_reader import Elf


def captured_setup(start):
    path = ROOT / 'evidence/original/pump/deployed.so'
    elf = Elf(path)
    window = next(row for row in census.original_windows() if row['start'] == start)
    image = census.Image(path, {start: (window['bytes'], [])})
    text = {}
    cursor = start
    while cursor < start + window['bytes']:
        instruction, width = decode_instruction(elf.b, cursor, elf)
        text[cursor] = instruction['mnemonic']
        cursor += width
    image._txt[start] = text
    # This is the same filtering used by census.main before calling arg_setup.
    internal_sites = [site for site, target in image.calls(start) if not isinstance(target, tuple)]
    return elf, text, census.arg_setup(image, start, internal_sites)


class CensusCallBarrierTests(unittest.TestCase):
    def test_indirect_call_does_not_leak_earlier_argument_writes(self):
        elf, text, setup = captured_setup(0x1ab918)
        self.assertEqual(elf.b[0x1ab970:0x1ab978], bytes.fromhex('8d00000004000000'))
        self.assertEqual(text[0x1ab970], 'callx r4')
        self.assertEqual(setup[0x1ab998], ['mov64 r1, rS', 'mov64 r2, rS'])

    def test_relocated_external_call_does_not_leak_earlier_argument_writes(self):
        elf, text, setup = captured_setup(0x19b548)
        self.assertEqual(elf.relocations[0x19b5e8], {'type': 10, 'symbol': 'sol_memcpy_'})
        self.assertEqual(text[0x19b5e8], 'call_extern sol_memcpy_')
        self.assertEqual(setup[0x19b640], ['add64 r1, rS', 'ldxdw r3, [r10-8]'])
        # The later internal call still starts its own setup and masks a pointer.
        self.assertEqual(setup[0x19b660], ['lddw r1, ADDR'])

    def test_current_call_setup_remains_visible(self):
        _elf, _text, setup = captured_setup(0x1afaf0)
        self.assertIn('mov64 r3, 65537', setup[0x1afd78])


if __name__ == '__main__':
    unittest.main()
