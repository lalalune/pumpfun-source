"""The real Fees withdraw CLI must not publish reports over its inputs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'scripts/fees_withdraw_differential.py',
    'scripts/fees_admin_differential.py',
    'scripts/pump_differential_output.py',
    'evidence/upstream/pump_fees.json',
    'evidence/original/pump_fees/deployed.so',
    'evidence/dependencies/spl_token/deployed.so',
    'evidence/dependencies/spl_token_2022/deployed.so',
    'evidence/dependencies/associated_token/deployed.so',
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FeesWithdrawOutputInputTests(unittest.TestCase):
    def test_real_cli_refuses_candidate_and_runtime_input_aliases(self):
        # Every file is an independent test-owned copy. A regressed CLI can
        # destroy only this temporary copy, never a captured repository input.
        with tempfile.TemporaryDirectory(prefix='fees-withdraw-output-') as temporary:
            root = Path(temporary) / 'private runtime root'
            for name in FILES:
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, destination)
            candidate = root / 'candidate.so'
            shutil.copyfile(root / 'evidence/original/pump_fees/deployed.so', candidate)
            sources = [candidate, *(root / name for name in FILES)]
            before = {path: sha(path) for path in sources}
            aliases = root / 'aliases'
            aliases.mkdir()
            executed = {'same-path': 0, 'hardlink': 0, 'symlink': 0}
            skipped_symlinks = []
            for index, source in enumerate(sources):
                outputs = [('same-path', source)]
                hard = aliases / f'{index}-hardlink'
                os.link(source, hard)
                outputs.append(('hardlink', hard))
                symbolic = aliases / f'{index}-symlink'
                try:
                    symbolic.symlink_to(source)
                except OSError as error:
                    if os.name != 'nt' or getattr(error, 'winerror', None) != 1314:
                        raise
                    skipped_symlinks.append(str(source.relative_to(root)))
                else:
                    outputs.append(('symlink', symbolic))
                for kind, output in outputs:
                    with self.subTest(input=str(source.relative_to(root)), alias=kind):
                        child = subprocess.run(
                            [sys.executable, '-B', str(root / FILES[0]),
                             '--candidate', str(candidate), '--output', str(output)],
                            cwd=root, capture_output=True, text=True, timeout=45)
                        self.assertNotEqual(child.returncode, 0, child.stdout)
                        self.assertIn('report output aliases an input', child.stderr)
                        self.assertEqual({path: sha(path) for path in sources}, before)
                        self.assertFalse(list(output.parent.glob('.' + output.name[:32] + '.*')))
                        executed[kind] += 1
            self.assertEqual(executed['same-path'], len(sources))
            self.assertEqual(executed['hardlink'], len(sources))
            self.assertEqual(executed['symlink'] + len(skipped_symlinks), len(sources))
            print(json.dumps({'executed_alias_checks': executed,
                              'windows_symlink_privilege_skips': skipped_symlinks}))

    def test_late_alias_and_publication_failure_preserve_inputs(self):
        driver = r'''
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,sys.argv.pop(1))
mode=sys.argv.pop(1)
import fees_withdraw_differential as module
import pump_differential_output as publication
candidate=Path(sys.argv[sys.argv.index('--candidate')+1]);output=Path(sys.argv[sys.argv.index('--output')+1])
seen=[]
def hook(frame,event,arg):
 if event=='return' and frame.f_code is module.run.__code__ and not seen:
  seen.append(True);sys.setprofile(None)
  if mode=='late-alias':output.symlink_to(candidate)
if mode=='late-alias':sys.setprofile(hook)
try:
 if mode=='publish-failure':
  with patch.object(publication.os,'replace',side_effect=OSError('controlled publication failure')):module.main()
 else:module.main()
finally:sys.setprofile(None)
'''
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);candidate=root/'candidate.so'
            data=(ROOT/'evidence/original/pump_fees/deployed.so').read_bytes();candidate.write_bytes(data)
            for mode in ('late-alias','publish-failure'):
                output=root/(mode+'.json')
                if mode=='publish-failure':output.write_bytes(b'prior receipt')
                result=subprocess.run([sys.executable,'-B','-c',driver,str(ROOT/'scripts'),mode,
                    '--candidate',str(candidate),'--output',str(output)],capture_output=True,text=True,timeout=60)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('aliases an input' if mode=='late-alias' else 'controlled publication failure',result.stderr)
                self.assertEqual(candidate.read_bytes(),data)
                if mode=='late-alias':self.assertTrue(output.is_symlink())
                else:self.assertEqual(output.read_bytes(),b'prior receipt')
                self.assertEqual(list(root.glob('.'+output.name+'.*')),[])

    def test_full_runtime_receipt_and_original_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            for candidate in (True,False):
                output=Path(temporary)/('paired.json' if candidate else 'original.json')
                command=[sys.executable,'-B',str(ROOT/FILES[0]),'--output',str(output)]
                if candidate:command.extend(['--candidate',str(ROOT/'evidence/original/pump_fees/deployed.so')])
                result=subprocess.run(command,capture_output=True,text=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report=json.loads(output.read_bytes())
                self.assertEqual(len(report['cases']),113)
                self.assertEqual(report['mismatches'],[])
                self.assertTrue(all(row['match'] is True if candidate else row['match'] is None for row in report['cases']))


if __name__ == '__main__':
    unittest.main()
