import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import experiment_runner as E

H=Path(__file__).resolve().parent

class ReceiptIntegrityTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        self.source=self.root/'source';self.source.mkdir();(self.source/'value').write_text('one')
        self.out=self.root/'out'
        self.command=[sys.executable,'-c',"from pathlib import Path;import sys;Path(sys.argv[2],'result').write_bytes(Path(sys.argv[1],'value').read_bytes())",'{source}','{out}']

    def test_real_matrix_retries_contradictory_saved_results(self):
        path = H.parents[1] / 'research/experiment-cache-receipts-20261101/probe.py'
        spec = importlib.util.spec_from_file_location('experiment_receipt_probe', path)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        # Four real matrix CLIs create, reuse, corrupt and resume owned receipts.
        # Actual child commands copy source bytes and return explicit predicates.
        probe.validate(probe.run(H.parents[1]), 'fixed')

    def test_input_changes_during_lock_wait_do_not_reuse_stale_pass(self):
        for kind in ['source','declared']:
            with self.subTest(kind=kind):
                self.source.mkdir(exist_ok=True)
                declared=self.root/'declared';declared.write_text('one')
                out=self.root/('wait-'+kind)
                initial=E.run_trial(self.source,self.command,out,inputs=[declared])
                entered=threading.Event();answer=[];errors=[]
                original=E.identity
                def identity(*args,**kw):
                    value=original(*args,**kw);entered.set();return value
                def run():
                    try:answer.append(E.run_trial(self.source,self.command,out,inputs=[declared]))
                    except BaseException as exc:errors.append(exc)
                with (out/'.lock').open('a') as lock:
                    fcntl.flock(lock,fcntl.LOCK_EX)
                    with patch.object(E,'identity',side_effect=identity):
                        thread=threading.Thread(target=run);thread.start()
                        self.assertTrue(entered.wait(5))
                        (self.source/'value' if kind=='source' else declared).write_text('two')
                        fcntl.flock(lock,fcntl.LOCK_UN);thread.join(5)
                self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
                self.assertFalse(answer[0]['reused']);self.assertNotEqual(answer[0]['attempt'],initial['attempt'])

    def test_nonexecutable_retained_helper_invalidates_reuse(self):
        command=[sys.executable,'-c',"from pathlib import Path;import sys; p=Path(sys.argv[1],'helper');p.write_text('#!/bin/sh\\nexit 0\\n');p.chmod(0o755)",'{out}']
        first=E.run_trial(self.source,command,self.out);self.assertTrue(E.run_trial(self.source,command,self.out)['reused'])
        helper=self.out/first['attempt']/'output/helper';subprocess.run([str(helper)],check=True)
        helper.chmod(0o644)
        with self.assertRaises(PermissionError):subprocess.run([str(helper)],check=True)
        self.assertFalse(E.run_trial(self.source,command,self.out)['reused'])

    def test_matrix_preflights_own_and_cross_source_overlap(self):
        for cross in [False,True]:
            with self.subTest(cross=cross):
                out=self.root/('matrix-'+str(cross));marker=self.root/('marker-'+str(cross))
                second=out/'first'/'second-source' if cross else out/'second';second.mkdir(parents=True)
                (second/'value').write_text('two')
                rows=[{'name':'first','source':str(self.source),'command':[sys.executable,'-c',f'from pathlib import Path;Path({str(marker)!r}).touch()']}, {'name':'second','source':str(second),'command':self.command}]
                matrix=self.root/'matrix.json';matrix.write_text(json.dumps(rows))
                result=subprocess.run([sys.executable,str(H/'experiment_runner.py'),str(matrix),'--out',str(out)],capture_output=True)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse(marker.exists(),'invalid later row executed the earlier command')
        matrix=self.root/'control.json';matrix.write_text(json.dumps([{'name':'valid','source':str(self.source),'command':self.command}]))
        result=subprocess.run([sys.executable,str(H/'experiment_runner.py'),str(matrix),'--out',str(self.root/'control')],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_utf8_patch_list_under_ascii_locale(self):
        patchfile=self.root/'unicodé.patch';patchfile.write_bytes(b'diff --git a/value b/value\n--- a/value\n+++ b/value\n@@ -1 +1 @@\n-one\n+two\n')
        (self.source/'value').write_bytes(b'one\n')
        listing=self.root/'patches.json';listing.write_text(json.dumps([str(patchfile)],ensure_ascii=False),encoding='utf-8')
        oracle=self.root/'oracle.json';oracle.write_text(json.dumps({'command':[sys.executable,'-c','raise SystemExit(0)']}))
        env=dict(os.environ,LC_ALL='C',LANG='C',PYTHONUTF8='0',PYTHONCOERCECLOCALE='0')
        filesystem=subprocess.check_output([sys.executable,'-c','import sys;print(sys.getfilesystemencoding())'],env=env).decode().strip()
        if filesystem.lower().replace('-', '')!='utf8':
            self.skipTest('non-UTF-8 text locale with a UTF-8 filesystem is required for this filename control')
        result=subprocess.run([sys.executable,str(H/'minimize_experiment.py'),'--source',str(self.source),'--patches',str(listing),'--oracle',str(oracle),'--out',str(self.root/'reduction')],env=env,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads((self.root/'reduction/minimized.json').read_text())
        self.assertEqual(report['patches'][0]['sha256'],hashlib.sha256(patchfile.read_bytes()).hexdigest())
        self.assertEqual((self.source/'value').read_bytes(),b'one\n')

if __name__=='__main__':unittest.main()
