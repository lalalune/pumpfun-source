import contextlib
import io
import json
import os
import shlex
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import integrate as I

class CompositionBoundaryTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        self.base=self.root/'base';self.part=self.root/'part'
        for path in [self.base,self.part]:
            (path/'src').mkdir(parents=True);(path/'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n');(path/'Cargo.lock').write_text('version=3\n');(path/'src/lib.rs').write_text('old\n')
        (self.part/'src/lib.rs').write_text('new\n')
    def run_main(self,name='case'):
        args=['integrate','--name',name,'--base-src',str(self.base),'--part','p='+str(self.part),'--no-build']
        with patch.object(I,'SC',self.root),patch.object(sys,'argv',args),contextlib.redirect_stdout(io.StringIO()):result=I.main()
        return result,json.loads((self.root/'integ'/name/'report.json').read_text())
    def test_operational_and_post_dry_run_failures_retain_diagnostics(self):
        actual=subprocess.run
        for phase in ['dry','apply']:
            def run(command,**kw):
                if command[0]=='patch' and (('--dry-run' in command)==(phase=='dry')):
                    if kw.get('check'):raise subprocess.CalledProcessError(2,command,output='stdout evidence',stderr='patch tool failed')
                    return subprocess.CompletedProcess(command,2,'stdout evidence','patch tool failed')
                return actual(command,**kw)
            with self.subTest(phase=phase),patch.object(I.subprocess,'run',side_effect=run):
                code,report=self.run_main(phase)
                self.assertNotEqual(code,0);self.assertEqual(report['parts'][0]['status'],'error')
                self.assertIn('patch tool failed',(self.root/'integ'/phase/'rejects/p.txt').read_text())
    def test_real_patch_executable_failure_is_not_a_conflict(self):
        bindir=self.root/'bin';bindir.mkdir();tool=bindir/'patch'
        real=shutil.which('patch')
        tool.write_text('#!/bin/sh\ncase " $* " in *" --dry-run "*) exec '+shlex.quote(real)+' "$@";; esac\necho operational-failure >&2\nexit 2\n')
        tool.chmod(0o755)
        with patch.dict(os.environ,{'PATH':str(bindir)+os.pathsep+os.environ['PATH']}):
            code,report=self.run_main('real-tool')
        self.assertNotEqual(code,0);self.assertEqual(report['parts'][0]['status'],'error')
        self.assertIn('operational-failure',(self.root/'integ/real-tool/rejects/p.txt').read_text())

    def test_source_mutation_during_snapshot_is_rejected(self):
        copy=shutil.copytree;mutated=False
        def copying(src,dst,*args,**kw):
            nonlocal mutated
            result=copy(src,dst,*args,**kw)
            if not mutated:
                mutated=True;(self.base/'src/lib.rs').write_text('changed while composing\n')
            return result
        with patch.object(I.shutil,'copytree',side_effect=copying):
            code,report=self.run_main('mutation')
        self.assertNotEqual(code,0);self.assertIn('source inputs changed',report.get('error',''))
    def test_valid_control_and_real_conflict_policy(self):
        code,report=self.run_main('valid');self.assertEqual(code,0);self.assertEqual(report['parts'][0]['status'],'applied')
        self.assertEqual((self.root/'integ/valid/src/src/lib.rs').read_text(),'new\n')
        other=self.root/'other';shutil.copytree(self.base,other);(other/'src/lib.rs').write_text('third\n')
        args=['integrate','--name','conflict','--base-src',str(other),'--part','p='+str(self.part),'--base-of','p='+str(self.base),'--no-build']
        with patch.object(I,'SC',self.root),patch.object(sys,'argv',args),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(I.main(),0)
        r=json.loads((self.root/'integ/conflict/report.json').read_text());self.assertEqual(r['parts'][0]['status'],'conflict')
if __name__=='__main__':unittest.main()
