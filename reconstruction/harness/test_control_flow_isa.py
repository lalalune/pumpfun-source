import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from test_elf_symbols import fixture
from test_control_flow import ControlFlowTests
from score_admission import sections


class ControlFlowISATests(unittest.TestCase):
    def cli(self,path,start,size,output):
        return subprocess.run([sys.executable,str(Path(__file__).with_name('control_flow.py')),str(path),'--start',hex(start),'--size',str(size),'--json',str(output)],capture_output=True)

    def test_other_instruction_versions_are_not_silently_decoded_as_legacy(self):
        for version in (2,3,4,32):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                image = fixture()
                struct.pack_into('<I',image,0x30,version)
                # SBPFv2 LMUL32_IMM (0x86) is misclassified as a call by a
                # decoder that treats every class-6 opcode as a jump/call.
                image[424:440] = struct.pack('<BBhi',0x86,0,0,2)+struct.pack('<BBhi',0x95,0,0,0)
                candidate,output = root/'candidate.so',root/'cfg.json'
                candidate.write_bytes(image)
                result = self.cli(candidate,0x1000,16,output)
                self.assertEqual(result.returncode,2,result.stderr.decode('utf-8',errors='replace'))
                self.assertIn(b'legacy SBPFv0/v1',result.stderr)
                self.assertFalse(output.exists())
                self.assertEqual(candidate.read_bytes(),image)

    def test_legacy_versions_still_decode(self):
        for version in (0,1):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                image = fixture();struct.pack_into('<I',image,0x30,version)
                image[424:440] = struct.pack('<BBhi',0xb7,0,0,0)+struct.pack('<BBhi',0x95,0,0,0)
                candidate,output = root/'candidate.so',root/'cfg.json'
                candidate.write_bytes(image)
                result = self.cli(candidate,0x1000,16,output)
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['calls'],[])

    def test_all_nine_retained_images_remain_accepted_for_a_complete_instruction(self):
        repo = Path(__file__).resolve().parents[2]
        paths = list((repo/'evidence').glob('*/*/deployed.so'))
        self.assertEqual(len(paths),9)
        with tempfile.TemporaryDirectory() as temporary:
            for index,path in enumerate(paths):
                with self.subTest(program=path.parent.name):
                    image = path.read_bytes();text = sections(image)['.text']
                    size = 16 if image[text['offset']] == 0x18 else 8
                    output = Path(temporary)/f'{index}.json'
                    result = self.cli(path,text['addr'],size,output)
                    self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                    self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['bytes'],size)

    def test_cli_reports_incomplete_branch_ranges(self):
        cases = ((0x05, 2, 'branch target outside function'),
                 (0x15, -1, 'conditional fallthrough outside function'))
        for opcode, displacement, message in cases:
            with self.subTest(opcode=opcode), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                image = fixture()
                image[424:440] = struct.pack('<BBhi', opcode, 0, displacement, 0) + struct.pack('<BBhi', 0x95, 0, 0, 0)
                candidate, output = root / 'candidate.so', root / 'cfg.json'
                candidate.write_bytes(image)
                result = self.cli(candidate, 0x1000, 8, output)
                self.assertEqual(result.returncode, 1, result.stderr.decode('utf-8', errors='replace'))
                self.assertIn(message, output.read_text(encoding='utf-8'))


if __name__ == '__main__': unittest.main()
