"""Exact token-program loads reach the maintained signature CLI and its consumers."""
import importlib.util
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import bytecode_signatures as signatures


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = load('default_token_probe', ROOT / 'research/default-token-constants-20261101/probe.py')


def lddw(chunk):
    return struct.pack('<BBh', 0x18, 1, 0) + chunk[:4] + bytes(4) + chunk[4:]


def loads(value):
    store = struct.pack('<BBhi', 0x7b, 0x1a, -8, 0)
    return b''.join(lddw(value[offset:offset + 8]) + store for offset in range(0, len(value), 8))


class TokenConstantTests(unittest.TestCase):
    def detect(self, blob, end=None, relocations=None):
        return signatures.detect_token_transfer_patterns(
            SimpleNamespace(b=blob, relocations=relocations or {}), 0,
            len(blob) if end is None else end)

    def test_exact_addresses_keep_the_legacy_callable(self):
        for name, value in probe.PROGRAM_IDS.items():
            with self.subTest(program=name):
                rows = self.detect(loads(bytes.fromhex(value)))
                self.assertEqual(rows, [{'offset': 0, 'type': 'token_program_constant',
                    'token_program': name, 'program_id_hex': value, 'lddw_slots': 4}])

    def test_partial_different_and_scalar_values_are_not_token_programs(self):
        value = bytes.fromhex(probe.PROGRAM_IDS['Tokenkeg'])
        for data in (value[:24], value[:-1] + bytes([value[-1] ^ 1]),
                     (3).to_bytes(8, 'little') * 4):
            with self.subTest(data=data.hex()):
                self.assertEqual(self.detect(loads(data)), [])

    def test_full_constant_cannot_cross_the_window_end(self):
        blob = loads(bytes.fromhex(probe.PROGRAM_IDS['Tokenkeg']))
        # The final load is present in the image, but half is in another window.
        self.assertEqual(self.detect(blob, end=len(blob) - 16), [])
        self.assertEqual(self.detect(blob[:len(blob) - 16]), [])

    def test_relocated_loads_are_not_literal_chunks_or_skipped_bridges(self):
        value = bytes.fromhex(probe.PROGRAM_IDS['Tokenkeg'])
        blob = loads(value)
        self.assertEqual(self.detect(blob, relocations={24: {'type': 8}}), [])
        # Inserting an extra relocated LDDW between chunks must break the sequence.
        extra = lddw((99).to_bytes(8, 'little'))
        interrupted = blob[:24] + extra + blob[24:]
        self.assertEqual(self.detect(interrupted, relocations={24: {'type': 8}}), [])

    def test_complete_default_cli_agrees_with_retained_bytes_and_accepted_detector(self):
        report = probe.collect(ROOT, expected='fixed')
        self.assertTrue(report['all_input_bytes_preserved'])
        self.assertEqual(report['generated_verifier_exit'], 0)
        self.assertEqual({name: row['reported_constants'] for name, row in report['programs'].items()},
                         {'pump': 4, 'pump_amm': 2, 'mayhem': 20})


if __name__ == '__main__':
    unittest.main()
