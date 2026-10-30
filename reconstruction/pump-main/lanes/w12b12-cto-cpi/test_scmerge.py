import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('scmerge',Path(__file__).with_name('tools')/'scmerge.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class TraceTests(unittest.TestCase):
    def test_transitive_merges_have_one_final_representative(self):
        log='slot #0 with allocation: a\nslot #1 with allocation: b\nslot #2 with allocation: c\nSlot #0 - 16 bytes.\nSlot #1 - 8 bytes.\nSlot #2 - 4 bytes.\nMerging #1 and slots #2 together\nMerging #0 and slots #1 together\n'
        groups=m.parse_trace(log)
        self.assertEqual(len(groups),1)
        self.assertEqual(groups[0]['representative'],0)
        self.assertEqual([x['name'] for x in groups[0]['members']],['a','b','c'])
    def test_empty_trace_is_not_success(self):
        with self.assertRaises(ValueError): m.parse_trace('')
    def test_unknown_merge_is_rejected(self):
        with self.assertRaises(ValueError): m.parse_trace('slot #0 with allocation: a\nSlot #0 - 16 bytes.\nMerging #0 and slots #1 together\n')
if __name__=='__main__':unittest.main()
