import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import unittest
import tempfile
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('progress',pathlib.Path(__file__).resolve().parents[1]/'scripts/progress.py')
progress=importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)
class ProgressTests(unittest.TestCase):
    def test_empty_frontend_inventory_generates_an_unqualified_report(self):
        app=pathlib.Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)/'app'
            for directory in ['scripts','contracts','evidence/web','evidence/sdk','recovered','packages/sdk']:
                (root/directory).mkdir(parents=True)
            shutil.copyfile(app/'scripts/progress.py',root/'scripts/progress.py')
            shutil.copyfile(app/'evidence/sdk/pump-sdk-4.3.1.tgz',root/'evidence/sdk/pump-sdk-4.3.1.tgz')
            shutil.copyfile(app/'evidence/sdk/registry.json',root/'evidence/sdk/registry.json')
            shutil.copytree(app/'packages/sdk/src',root/'packages/sdk/src')
            for name in ['developer.openapi.json','internal-operations.json']:
                shutil.copyfile(app/'contracts'/name,root/'contracts'/name)
            ledger=progress.read('contracts/feature-progress.json')
            ledger.update(frontend=[],backend=[])
            for path,value in [('contracts/feature-progress.json',ledger),('evidence/web/manifest.json',{'records':[]}),('recovered/modules.json',{'modules':[],'failures':[]})]:
                (root/path).write_text(json.dumps(value),encoding='utf-8')
            (root.parent/'README.md').write_text('## License\n',encoding='utf-8')
            for flags in [[],['-O']]:
                result=subprocess.run([sys.executable,*flags,str(root/'scripts/progress.py')],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                report=(root/'PROGRESS.md').read_text(encoding='utf-8')
                self.assertIn('| Frontend JavaScript capture | 0 / 0 scripts | N/A |',report)
                self.assertIn('| Frontend factory extraction | 0 / 0 inventoried variants | N/A |',report)
                checked=subprocess.run([sys.executable,*flags,str(root/'scripts/progress.py'),'--check'],capture_output=True,text=True)
                self.assertEqual(checked.returncode,0,checked.stderr)
    def test_generated_reports_use_canonical_lf_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)/'app';root.mkdir()
            readme=root.parent/'README.md';readme.write_bytes(b'## Remaining work\n')
            with patch.object(progress,'ROOT',root),patch.object(progress,'render',return_value='Current report'),patch('sys.argv',['progress.py']):
                progress.main()
            self.assertEqual((root/'PROGRESS.md').read_bytes(),b'# Application progress report\n\nCurrent report\n')
            self.assertEqual(readme.read_bytes(),progress.replace_readme('## Remaining work\n','Current report').encode('utf-8'))
    def test_pending_does_not_earn_credit(self):
        self.assertEqual(progress.score({'one':{'status':'pending','evidence':[]}}),'0/1 (0%)')
    def test_acceptance_requires_evidence(self):
        with self.assertRaises(ValueError):progress.score({'one':{'status':'accepted','evidence':[]}})
    def test_not_applicable_requires_a_recorded_decision(self):
        with self.assertRaises(ValueError):progress.score({'one':{'status':'not-applicable','evidence':[]}})
    def test_completion_source_gate_cannot_be_waived_while_source_is_pending(self):
        ledger=progress.read('contracts/feature-progress.json')
        row=next(r for r in ledger['frontend'] if r['completion']['source']['status']=='accepted')
        evidence=row['completion']['source']['evidence']
        row['source']={gate:{'status':'pending','evidence':[]} for gate in row['source']}
        # Marking the completion source gate N/A drops it from the denominator; it must not skip the source check.
        row['completion']['source']={'status':'not-applicable','evidence':evidence}
        real=progress.read
        with patch.object(progress,'read',lambda path:ledger if path=='contracts/feature-progress.json' else real(path)):
            with self.assertRaisesRegex(ValueError,'Source completion requires all source gates'):progress.render()
    def test_check_rejects_stale_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)/'app';root.mkdir()
            (root/'PROGRESS.md').write_text('stale',encoding='utf-8')
            (root.parent/'README.md').write_text('## Remaining work\n',encoding='utf-8')
            with patch.object(progress,'ROOT',root),patch.object(progress,'render',return_value='Current report'),patch('sys.argv',['progress.py','--check']):
                with self.assertRaisesRegex(ValueError,'stale'):progress.main()
    def test_generated_region_preserves_unrelated_readme_content(self):
        old='Existing contract table\n\n## Remaining work\n\nExisting tasks\n'
        updated=progress.replace_readme(old,'App table')
        self.assertTrue(updated.startswith('Existing contract table\n\n'))
        self.assertTrue(updated.endswith('## Remaining work\n\nExisting tasks\n'))
        self.assertEqual(progress.replace_readme(updated,'App table'),updated)
        refreshed=progress.replace_readme(updated,'Updated app table')
        self.assertEqual(refreshed,updated.replace('App table','Updated app table'))
    def test_malformed_regions_are_rejected_before_reports_are_written(self):
        malformed={
            'missing start':progress.END,
            'missing end':progress.BEGIN,
            'reversed':progress.END+'\nstale table\n'+progress.BEGIN,
            'duplicate start':progress.BEGIN+'\n'+progress.BEGIN+'\n'+progress.END,
            'duplicate end':progress.BEGIN+'\n'+progress.END+'\n'+progress.END,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)/'app';root.mkdir()
            report=root/'PROGRESS.md';readme=root.parent/'README.md'
            for name,region in malformed.items():
                for mode in [[],['--check']]:
                    with self.subTest(region=name,mode=mode):
                        original=('Contract table\n\n'+region+'\n\n## Remaining work\n\nExisting tasks\n').encode('utf-8')
                        readme.write_bytes(original)
                        # Keep the standalone report fresh, so --check must validate the README.
                        report.write_bytes(b'# Application progress report\n\nCurrent report\n')
                        with patch.object(progress,'ROOT',root),patch.object(progress,'render',return_value='Current report'),patch('sys.argv',['progress.py',*mode]):
                            with self.assertRaisesRegex(ValueError,'marker'):progress.main()
                        self.assertEqual(readme.read_bytes(),original)
                        self.assertEqual(report.read_bytes(),b'# Application progress report\n\nCurrent report\n')
if __name__=='__main__':unittest.main()
