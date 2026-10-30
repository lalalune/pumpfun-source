"""Real matrix CLI admission must reject case-only output-directory collisions."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('experiment_runner.py')


class MatrixNameCaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='experiment-name-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root/'source';self.source.mkdir()
        (self.source/'input.txt').write_text('source bytes')
        self.output = self.root/'out'

    def matrix(self, names):
        rows=[]
        for index,name in enumerate(names):
            marker=self.root/('executed-'+str(index))
            code=('from pathlib import Path;import sys;'
                  f'Path({str(marker)!r}).write_text("executed");'
                  f'Path(sys.argv[1],"result.txt").write_text({name!r})')
            rows.append({'name':name,'source':str(self.source),
                         'command':[sys.executable,'-c',code,'{out}']})
        path=self.root/'matrix.json';path.write_text(json.dumps(rows),encoding='utf-8')
        return path

    def invoke(self, names):
        return subprocess.run([sys.executable,'-I','-B',str(SCRIPT),str(self.matrix(names)),
                               '--out',str(self.output)],cwd=self.root,capture_output=True,
                              text=True,timeout=15)

    def test_names_differing_only_by_case_execute_no_command(self):
        for names in (['Trial','trial'],['A_B','a_b'],['A-b','a-B']):
            with self.subTest(names=names):
                result=self.invoke(names)
                self.assertEqual(result.returncode,2,result.stdout+result.stderr)
                self.assertIn('invalid experiment matrix',result.stderr)
                self.assertFalse(self.output.exists())
                self.assertEqual(list(self.root.glob('executed-*')),[])

    def test_collision_preserves_existing_output_tree(self):
        self.output.mkdir();prior=self.output/'prior-receipt.json';prior.write_bytes(b'prior bytes')
        result=self.invoke(['Trial','trial'])
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        self.assertEqual(list(self.output.iterdir()),[prior])
        self.assertEqual(prior.read_bytes(),b'prior bytes')
        self.assertEqual(list(self.root.glob('executed-*')),[])

    def test_distinct_names_keep_original_case_and_run_both_real_commands(self):
        names=['Trial-a','trial-b'];result=self.invoke(names)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(set(report),set(names))
        self.assertTrue(all(value['status']=='pass' for value in report.values()))
        self.assertEqual(len(list(self.root.glob('executed-*'))),2)
        for name in names:
            receipt=json.loads((self.output/name/'latest.json').read_bytes())
            self.assertEqual(receipt,report[name])
            self.assertEqual((self.output/name/receipt['attempt']/'output/result.txt').read_text(),name)
        self.assertEqual((self.source/'input.txt').read_text(),'source bytes')


if __name__=='__main__':unittest.main()
