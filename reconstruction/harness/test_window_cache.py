import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import score

HEADER = 'program\tvariant\toriginal_start\toriginal_end\n'


class WindowCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.blob=struct.pack('<BBhi',0xb7,0,0,1)*2
        (self.root/'original.so').write_bytes(self.blob)
        self.inventory=HEADER+'pump\tselected\t0\t8\n'
        (self.root/'functions.tsv').write_text(self.inventory)
        self.addCleanup(patch.stopall)
        patch.object(score,'BASE',self.root).start()
        self.sections=patch.object(score,'sections',return_value={'.text':{'addr':0,'offset':0,'size':16}}).start()
        score._window_rows.cache_clear()

    def test_input_bytes_invalidate_cache_even_when_length_unchanged(self):
        first=score.original_windows()
        (self.root/'original.so').write_bytes(struct.pack('<BBhi',0xb7,0,0,2)*2)
        self.assertNotEqual(score.original_windows()[0]['raw'],first[0]['raw'])
        self.assertEqual(self.sections.call_count,2)

    def test_inventory_edits_are_not_hidden_by_cache(self):
        score.original_windows()
        (self.root/'functions.tsv').write_text(HEADER+'pump\tselected\t8\t16\n')
        self.assertEqual(score.original_windows()[0]['start'],8)

    def test_repeat_uses_cache_but_returns_isolated_rows(self):
        rows=score.original_windows();rows[0]['raw']=b'poison';rows.clear()
        self.assertEqual(score.original_windows()[0]['raw'],self.blob[:8])
        self.assertEqual(self.sections.call_count,1)

    def test_legacy_pickle_is_neither_loaded_nor_rewritten(self):
        legacy=self.root/'original-windows.pkl';legacy.write_bytes(b'not a pickle')
        self.assertEqual(len(score.original_windows()),1)
        self.assertEqual(legacy.read_bytes(),b'not a pickle')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),['functions.tsv','original-windows.pkl','original.so'])

    def test_bad_inventory_is_rejected(self):
        for inventory in [HEADER, 'bad\n', HEADER+'pump\tselected\t0\t24\n',
                          HEADER+'pump\tselected\t0\t0\n',HEADER+'pump\tselected\t1\t8\n',
                          self.inventory+'pump\tselected\t0\t8\n']:
            with self.subTest(inventory=inventory):
                (self.root/'functions.tsv').write_text(inventory)
                with self.assertRaises(ValueError):score.original_windows()

    def test_unselected_windows_are_not_admitted(self):
        (self.root/'functions.tsv').write_text(self.inventory+'other\tselected\t8\t16\n'+'pump\tother\t8\t16\n')
        self.assertEqual(len(score.original_windows()),1)


if __name__ == '__main__':unittest.main()
