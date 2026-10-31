from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parent
TOOL=ROOT/'scripts/framebound.py'
MOV=bytes.fromhex('bf10000000000000')
EXIT=bytes.fromhex('9500000000000000')
LDDW_LOW=bytes.fromhex('1801000001000000')
LDDW_HIGH=bytes(8)
class RawInputTests(unittest.TestCase):
    def run_tool(self,raw):
        with tempfile.TemporaryDirectory() as scratch:
            path=Path(scratch)/'fn.bin'
            path.write_bytes(raw)
            return subprocess.run([sys.executable,'-B',str(TOOL),str(path)],capture_output=True,text=True)
    def test_whole_instructions_are_scored(self):
        result=self.run_tool(MOV+LDDW_LOW+LDDW_HIGH+EXIT)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('perfect-frame ratio',result.stdout)
    def test_empty_input_is_refused(self):
        self.assertEqual(self.refused(b''),'raw input must contain whole SBF instructions')
    def test_partial_instruction_is_refused(self):
        self.assertEqual(self.refused(MOV+EXIT[:5]),'raw input must contain whole SBF instructions')
    def test_lddw_without_its_second_slot_is_refused(self):
        self.assertEqual(self.refused(MOV+LDDW_LOW),'truncated SBF instruction')
    def refused(self,raw):
        result=self.run_tool(raw)
        self.assertEqual(result.returncode,1,result.stdout)
        self.assertEqual(result.stdout,'')
        return result.stderr.strip()
if __name__=='__main__':unittest.main()
