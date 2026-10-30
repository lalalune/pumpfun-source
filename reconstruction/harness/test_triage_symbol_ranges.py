"""Triage each same-address function symbol using its own byte length."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import coords
from instruction_stream import instruction_offsets
import score

HERE = Path(__file__).resolve().parent


def candidate_elf(text, sizes):
    """Synthetic ELF metadata around unchanged instructions from the Pump capture."""
    names = b'\0.shstrtab\0.text\0.strtab\0.symtab\0'
    strings = b'\0short\0long\0'
    blob = bytearray(544 + len(text))
    blob[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHI', blob, 16, 3, 247, 1)
    struct.pack_into('<H', blob, 52, 64)
    struct.pack_into('<Q', blob, 40, 64)
    struct.pack_into('<HHH', blob, 58, 64, 5, 1)
    blob[384:384 + len(names)] = names
    blob[432:432 + len(strings)] = strings
    headers = [
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 3, 0, 0, 384, len(names), 0, 0, 1, 0),
        (11, 1, 6, 0x1000, 544, len(text), 0, 0, 8, 0),
        (17, 3, 0, 0, 432, len(strings), 0, 0, 1, 0),
        (25, 2, 0, 0, 464, 72, 3, 0, 8, 24),
    ]
    for i, header in enumerate(headers):
        struct.pack_into('<IIQQQQIIQQ', blob, 64 + 64 * i, *header)
    for i, (name, size) in enumerate(zip((1, 7), sizes)):
        struct.pack_into('<IBBHQQ', blob, 488 + i * 24, name, 2, 0, 2, 0x1000, size)
    blob[544:] = text
    return bytes(blob)


class TriageRangeTests(unittest.TestCase):
    def test_different_length_symbols_at_one_address(self):
        windows = {w['start']: w for w in score.original_windows()}
        first, second = windows[0x120], windows[0x1d0]
        text = windows[0x288]['raw'][:second['bytes']]
        self.assertEqual((first['bytes'], second['bytes']), (176, 184))
        for size in (first['bytes'], second['bytes']):
            list(instruction_offsets(text[:size]))

        with tempfile.TemporaryDirectory(prefix='triage-ranges-') as temporary:
            candidate = Path(temporary) / 'candidate.so'
            candidate.write_bytes(candidate_elf(text, (first['bytes'], second['bytes'])))
            output = Path(temporary) / 'triage.json'
            memberships = score.score(candidate)
            self.assertFalse(memberships[first['start']]['normalized'])
            self.assertFalse(memberships[second['start']]['normalized'])
            result = subprocess.run(
                [sys.executable, '-X', 'utf8', '-B', str(HERE / 'triage.py'),
                 '--cand', str(candidate), '--json', str(output)],
                capture_output=True, text=True, encoding='utf-8',
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = {int(row['start'], 16): row for row in json.loads(output.read_text())}
            for window, symbol in ((first, 'short'), (second, 'long')):
                candidate_norm = score.normalize(text[:window['bytes']], 0x1000, score.sections(candidate.read_bytes()))
                original_norm = score.normalize(window['raw'], window['start'], coords.OS)
                sites = coords.sites(coords.ORIG, coords.OS, window['start'], window['raw'])
                expected = coords.non_coordinate_slots(original_norm, candidate_norm, sites)
                self.assertEqual(rows[window['start']]['nearest']['noncoord_slots'], len(expected))
                self.assertEqual(rows[window['start']]['nearest']['addr'], '0x1000')
                self.assertEqual(rows[window['start']]['nearest']['symbol'], symbol)


if __name__ == '__main__':
    unittest.main()
