"""Call-sequence reports preserve inputs and decode captured indirect calls."""
import gzip
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).with_name('callseq.py')
ROOT = TOOL.resolve().parents[4]
sys.path.insert(0, str(TOOL.parent))
import callseq

class ReportAdmission(unittest.TestCase):
    def test_existing_report_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary)/'report.json'
            report.write_bytes(b'prior report\n')
            result = subprocess.run([sys.executable, '-B', str(TOOL), '--cand', 'missing.so',
                                     '--orig-names', 'missing.so', '--json', str(report)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('report already exists', result.stderr)
            self.assertEqual(report.read_bytes(), b'prior report\n')

    def test_dangling_output_link_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary)/'report.json'; target = Path(temporary)/'missing'
            report.symlink_to(target)
            result = subprocess.run([sys.executable, '-B', str(TOOL), '--cand', 'missing.so',
                                     '--orig-names', 'missing.so', '--json', str(report)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('report already exists', result.stderr)
            self.assertTrue(report.is_symlink())
            self.assertFalse(target.exists())


class IndirectCalls(unittest.TestCase):
    def test_retained_range_formatter_cli(self):
        # Both genuine V0 artifacts encode CALLX r4 as 8d00000004000000.
        # SDK v1.44 llvm-objdump independently reports r4 at these two sites.
        original = ROOT/'evidence/original/pump/deployed.so'
        retained = ROOT/'research/pump-multihop-sell-fees-20261029/build/candidate/symbols.so.gz'
        symbol = ('_ZN71_$LT$core..ops..range..Range$LT$Idx$GT$$u20$as$u20$core..fmt..Debug$GT$'
                  '3fmt17hb4d8325772f511feE')
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary)/'candidate.so'
            candidate.write_bytes(gzip.decompress(retained.read_bytes()))
            report = Path(temporary)/'report.json'
            result = subprocess.run(
                [sys.executable, '-B', str(TOOL), '--cand', str(candidate),
                 '--orig-names', str(original), '--window', '0x1ab918', '--size', '160',
                 '--sym', '^'+re.escape(symbol)+'$', '--table', '--json', str(report)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(report.read_text())
            self.assertEqual((data['orig_calls'], data['cand_calls']), (3, 3))
            indirect = [row for row in data['rows'] if row['opc'] == 0x58]
            self.assertEqual(len(indirect), 1)
            self.assertEqual((indirect[0]['orig'], indirect[0]['cand']), ('callx r4', 'callx r4'))
            self.assertIn('callx r4', result.stdout)

    def test_version_selects_the_operand_field(self):
        raw = struct.pack('<BBhi', 0x8d, 0x32, 0, 4)
        for version, expected in ((0, 4), (1, 4), (2, 3), (3, 2), (4, 2)):
            with self.subTest(version=version):
                blob = bytearray(52)
                struct.pack_into('<I', blob, 48, version)
                self.assertEqual(callseq.calls(raw, 0, {}, {}, blob)[0][3], f'callx r{expected}')

    def test_unknown_version_does_not_invent_a_register(self):
        raw = bytes.fromhex('8d00000004000000')
        blob = bytearray(52)
        struct.pack_into('<I', blob, 48, 99)
        for image in (None, blob):
            self.assertEqual(callseq.calls(raw, 0, {}, {}, image)[0][3], 'callx raw 8d00000004000000')

if __name__ == '__main__':
    unittest.main()
