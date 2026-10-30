import hashlib
from pathlib import Path
import unittest
import score
from instruction_stream import instruction_offsets

ROOT = Path(__file__).resolve().parents[2]
HEADER = 'program\tvariant\toriginal_start\toriginal_end\n'


class InventoryInstructionBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT/'evidence/original/pump/deployed.so').read_bytes()
        cls.section = score.sections(cls.original)['.text']
        cls.text = score.body(cls.original, {'.text':cls.section}, cls.section['addr'], cls.section['size'])
        cls.lddw = next(offset for offset in instruction_offsets(cls.text) if cls.text[offset] == 0x18)

    def inventory(self, start, end):
        return HEADER + f'pump\tselected\t{start}\t{end}\n'

    def test_lddw_continuation_is_not_a_selected_original_function(self):
        start = self.section['addr'] + self.lddw + 8
        # These eight bytes exist in the retained deployed capture, but they
        # are immediate data, not a logical instruction/function boundary.
        with self.assertRaisesRegex(ValueError, 'logical instruction boundar'):
            score._window_rows(self.original, self.inventory(start,start+8))

    def test_complete_lddw_range_remains_admitted(self):
        start = self.section['addr'] + self.lddw
        rows = score._window_rows(self.original, self.inventory(start,start+16))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][2],self.text[self.lddw:self.lddw+16])

    def test_all_retained_selected_windows_keep_exact_bytes(self):
        inventory = (ROOT/'reconstruction/base/functions.tsv').read_text(encoding='utf-8')
        rows = score._window_rows(self.original,inventory)
        self.assertEqual(len(rows),1035)
        self.assertEqual(sum(row[1] for row in rows),1792208)
        self.assertEqual(hashlib.sha256(b''.join(row[2] for row in rows)).hexdigest(), '37cc788bba53d0d90446ea0795463dae60713f14af11902bccd678281f36ec6a')
        self.assertEqual(hashlib.sha256(b''.join(row[3] for row in rows)).hexdigest(), '048af8f1ce897cb8528f721680903b35af2685cfdc0a7811414344b20c2d9f48')


if __name__ == '__main__': unittest.main()
