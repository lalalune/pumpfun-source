import json,os,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'reconstruction/harness')]
import pump_compare_function_bytes as comparison

class ReportStagingTests(unittest.TestCase):
    def test_report_with_valid_long_basename(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/('x'*250+'.json')
            path.write_text('old')
            comparison.write_report(path,{'new':True})
            self.assertEqual(json.loads(path.read_text()),{'new':True})

    def test_stale_pid_temporary_does_not_block_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path=root/'report.json';path.write_text('old')
            stale=root/('.report.json.'+str(os.getpid()));stale.write_text('interrupted')
            comparison.write_report(path,{'new':True})
            self.assertEqual(json.loads(path.read_text()),{'new':True})
            self.assertEqual(stale.read_text(),'interrupted')

if __name__=='__main__':unittest.main(verbosity=2)
