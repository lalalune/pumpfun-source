import json
from pathlib import Path
import struct
import tempfile
import unittest
from score_admission import sections, baseline, same_domain, report_destination

ROOT = Path(__file__).resolve().parents[2]


class AdmissionTests(unittest.TestCase):
    def test_retained_elf_tables_and_rejected_mutations(self):
        paths = sorted((ROOT/'evidence').glob('*/*/deployed.so'))
        self.assertEqual(len(paths), 9)
        for path in paths: self.assertIn('.text', sections(path.read_bytes()))
        original = paths[0].read_bytes()
        edits = [lambda b: b.__setitem__(0, 0), lambda b: b.__setitem__(4, 1),
                 lambda b: struct.pack_into('<Q', b, 40, len(b)),
                 lambda b: struct.pack_into('<H', b, 58, 0)]
        for edit in edits:
            blob = bytearray(original); edit(blob)
            with self.assertRaises(ValueError): sections(blob)

    def test_baseline_flags_duplicates_and_schema(self):
        good = {'windows': {'16': {'normalized': True, 'raw': False, 'bytes': 8}}}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'baseline.json'; p.write_text(json.dumps(good))
            self.assertTrue(baseline(p)[16]['normalized'])
            bad = ['{"windows":{"16":{},"16":{}}}', '{"windows": [1]}', '{}']
            for field, value in [('normalized', 'false'), ('raw', 1), ('bytes', True), ('bytes', -1)]:
                row = dict(good['windows']['16'], **{field:value});bad.append(json.dumps({'windows':{'16':row}}))
            bad.append(json.dumps({'windows':{'16':{'normalized':False,'raw':True,'bytes':8}}}))
            for text in bad:
                p.write_text(text)
                with self.assertRaises((ValueError, TypeError)): baseline(p)

    def test_comparison_domain_and_sizes(self):
        row = {'bytes':8}; same_domain({1:row},{1:row}); same_domain({1:row},{})
        for base in [{2:row}, {1:{'bytes':16}}]:
            with self.assertRaises(ValueError): same_domain({1:row},base)

    def test_report_must_not_alias_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'candidate.so';p.write_bytes(b'evidence')
            alias = Path(d)/'alias';alias.hardlink_to(p)
            link = Path(d)/'link';link.symlink_to(p)
            for out in [p,alias,link]:
                with self.assertRaises(ValueError): report_destination(out,[p])
            report_destination(Path(d)/'new.json',[p])
            self.assertEqual(p.read_bytes(), b'evidence')


if __name__ == '__main__': unittest.main()
