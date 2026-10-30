from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parent
class AdmissionTests(unittest.TestCase):
    def test_ranker_failure_is_not_success(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/pfboard.py'),'missing-candidate.so'],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertIn('error',result.stdout)
    def test_empty_ranker_is_usage_error(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/pfboard.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
    def test_segment_size_is_checked_before_candidate_read(self):
        for value in ['0','-1']:
            result=subprocess.run([sys.executable,str(ROOT/'scripts/regionmap.py'),'missing-candidate.so',value],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn('segment size must be positive',result.stderr)
if __name__=='__main__':unittest.main()
