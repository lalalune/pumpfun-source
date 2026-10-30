import sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'reconstruction/harness')]
import experiment_runner as runner

class PlaceholderExpansionTests(unittest.TestCase):
    def test_placeholder_text_inside_destination_is_not_expanded(self):
        for label in ('normal','{out}','{work}'):
            with self.subTest(label=label),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);source=root/'source';source.mkdir();(source/'value').write_text('input')
                command=[sys.executable,'-c',
                         'from pathlib import Path;import sys;assert Path(sys.argv[1],"value").read_text()=="input";'
                         'Path(sys.argv[2],"result").write_text("ok")','{source}','{out}']
                result=runner.run_trial(source,command,root/label/'trial')
                self.assertEqual(result['status'],'pass')
                self.assertTrue(runner.run_trial(source,command,root/label/'trial')['reused'])

if __name__=='__main__':unittest.main(verbosity=2)
