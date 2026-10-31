"""A sell size change must not count the moved callees and data as edits.

The candidates are in-memory edits of the captured AMM image, so nothing is
compiled or executed: one instruction goes in at the end of the sell window and
everything after it moves eight bytes, as it does in a real longer build.
"""
import importlib.util
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('shifted_sell_score', HERE / 'amm_sell/sell_score.py')
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

CAPTURE = HERE.parent / 'evidence/original/pump_amm/deployed.so'
INSERTED = struct.pack('<BBhi', 0xbf, 0, 0, 0)  # mov64 r0, r0
SHIFT = len(INSERTED)
START, SIZE = score.SELL_START, score.SELL_SIZE
END = START + SIZE


def lengthened(original):
    """Return the captured image with one more sell instruction and all moves applied."""
    image = bytearray(original.b)
    for row in score.listing(original, START, SIZE):
        at = START + row['off']
        if isinstance(row['target'], tuple) and row['target'][1] >= END:
            immediate = struct.unpack_from('<i', image, at + 4)[0]
            struct.pack_into('<i', image, at + 4, immediate + 1)
        if row['fields'][0] == 'lddw' and at in original.relocations:
            struct.pack_into('<I', image, at + 4, row['fields'][2] + SHIFT)
    secs = {name: section[:3] + (section[3] + SHIFT,) + section[4:]
            for name, section in original.secs.items()}
    secs['.text'] = original.secs['.text']
    return SimpleNamespace(
        b=bytes(image[:END]) + INSERTED + bytes(image[END:]),
        normalized=original.normalized[:END] + INSERTED + original.normalized[END:],
        entries=[at + SHIFT if at >= END else at for at in original.entries],
        hi=original.hi + SHIFT, secs=secs, relocations=dict(original.relocations),
        calls={at + SHIFT if at >= END else at: target + SHIFT if target >= END else target
               for at, target in original.calls.items()},
        funcs=[{'name': 'x4sell8cashback', 'start': START, 'size': SIZE + SHIFT}])


def sell_slots(original, kind):
    """Return the offset of the first sell row of one kind."""
    rows = score.listing(original, START, SIZE)
    if kind == 'call':
        return next(START + row['off'] for row in rows
                    if isinstance(row['target'], tuple) and row['target'][1] >= END)
    return next(START + row['off'] for row in rows
                if row['fields'][0] == 'lddw' and START + row['off'] in original.relocations)


class ShiftedCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = score.elf_reader.Elf(CAPTURE)

    def measure(self, candidate):
        original = self.original
        def image(path):
            return original if path == CAPTURE else candidate
        with tempfile.TemporaryDirectory() as out, \
                mock.patch.object(score, 'ORIGINAL', CAPTURE), \
                mock.patch.object(score.elf_reader, 'Elf', side_effect=image):
            return score.score(out)

    def test_one_inserted_instruction_costs_one_edit(self):
        report = self.measure(lengthened(self.original))
        self.assertEqual(report['sell_size'], SIZE + SHIFT)
        self.assertEqual(report['lost_windows_normalized'], [])
        self.assertEqual(report['align_distance'], 1)
        for name in ('sell_raw_equal', 'whole_elf_equal', 'allocation_image_equal', 'unstripped_elf_equal'):
            self.assertFalse(report[name], name)

    def test_equal_size_capture_stays_at_zero(self):
        candidate = SimpleNamespace(**vars(self.original))
        candidate.funcs = [{'name': 'x4sell8cashback', 'start': START, 'size': SIZE}]
        report = self.measure(candidate)
        self.assertEqual(report['align_distance'], 0)
        self.assertTrue(report['sell_raw_equal'])

    def test_wrong_callee_after_the_shift_still_differs(self):
        candidate = lengthened(self.original)
        image = bytearray(candidate.b)
        at = sell_slots(self.original, 'call')
        immediate = struct.unpack_from('<i', image, at + 4)[0]
        target = at + 8 + immediate * 8
        following = candidate.entries[candidate.entries.index(target) + 1]
        struct.pack_into('<i', image, at + 4, (following - at - 8) // 8)
        candidate.b = bytes(image)
        self.assertEqual(self.measure(candidate)['align_distance'], 2)

    def test_wrong_pointer_after_the_shift_still_differs(self):
        candidate = lengthened(self.original)
        image = bytearray(candidate.b)
        at = sell_slots(self.original, 'lddw')
        value = struct.unpack_from('<I', image, at + 4)[0]
        struct.pack_into('<I', image, at + 4, value + 1)
        candidate.b = bytes(image)
        self.assertEqual(self.measure(candidate)['align_distance'], 2)

    def test_unpaired_windows_cannot_collide_with_original_call_addresses(self):
        candidate = lengthened(self.original)
        candidate.entries = candidate.entries[:-1]
        report = self.measure(candidate)
        self.assertIsNone(report['lost_windows_normalized'])
        calls = [row for row in score.listing(self.original, START, SIZE)
                 if isinstance(row['target'], tuple)]
        self.assertEqual(report['align_distance'], 1 + len(calls))


    def test_external_or_unadmitted_call_is_not_rebased(self):
        for relocation in (None, 10):
            candidate = lengthened(self.original)
            at = sell_slots(self.original, 'call')
            candidate.calls.pop(at)
            if relocation is not None:
                candidate.relocations[at] = {'type': relocation, 'symbol': 'external'}
            self.assertEqual(self.measure(candidate)['align_distance'], 2)

    def test_unrelocated_or_other_relocation_pointer_is_not_rebased(self):
        for relocation in (None, 42):
            candidate = lengthened(self.original)
            at = sell_slots(self.original, 'lddw')
            if relocation is None:
                candidate.relocations.pop(at)
            else:
                candidate.relocations[at] = {'type': relocation, 'symbol': ''}
            self.assertEqual(self.measure(candidate)['align_distance'], 2)

    def test_unpaired_old_call_address_cannot_match_original_token(self):
        raw = struct.pack('<BBhi', 0x85, 0x10, 0, (0x200 - 8) // 8)
        rows = score.listing(SimpleNamespace(b=raw), 0, 8)
        candidate = SimpleNamespace(entries=[0x208], calls={0: 0x200},
                                    relocations={}, secs={})
        original = SimpleNamespace(entries=[0x200], secs={})
        rebased = score.rebase_candidate(rows, 0, candidate, original)
        self.assertNotEqual(score.normalized_tokens(rows), score.normalized_tokens(rebased))
        self.assertEqual(rebased[0]['fields'], ('unpaired_call', 0x200))

    def pointer_row(self, value):
        raw = struct.pack('<BBhi', 0x18, 0, 0, value) + bytes(8)
        return score.listing(SimpleNamespace(b=raw), 0, 16)

    def test_unpaired_old_pointer_address_cannot_match_original_token(self):
        rows = self.pointer_row(0x1000)
        original = SimpleNamespace(entries=[], secs={'.rodata': (0, 1, 2, 0x1000, 0, 16)}, b=bytes(16))
        candidate = SimpleNamespace(entries=[], calls={}, relocations={0: {'type': 8}},
                                    secs={'.rodata': (0, 1, 2, 0x1008, 0, 16)}, b=bytes(16))
        rebased = score.rebase_candidate(rows, 0, candidate, original)
        self.assertNotEqual(score.normalized_tokens(rows), score.normalized_tokens(rebased))
        self.assertEqual(rebased[0]['fields'][0], 'unpaired_lddw')

    def test_pointer_offsets_must_fit_both_file_backed_sections(self):
        for kind, old_size, new_size, blob_size in ((1, 8, 16, 16), (8, 16, 16, 16),
                                                   (1, 16, 16, 8)):
            rows = self.pointer_row(0x2008)
            original = SimpleNamespace(entries=[], secs={'.rodata': (0, kind, 2, 0x1000, 0, old_size)},
                                       b=bytes(16))
            candidate = SimpleNamespace(entries=[], calls={}, relocations={0: {'type': 8}},
                                        secs={'.rodata': (0, 1, 2, 0x2000, 0, new_size)},
                                        b=bytes(blob_size))
            rebased = score.rebase_candidate(rows, 0, candidate, original)
            self.assertEqual(rebased[0]['fields'][0], 'unpaired_lddw')


if __name__ == '__main__':
    unittest.main()
