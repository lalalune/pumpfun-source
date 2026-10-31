import contextlib
import io
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest import mock
ROOT=Path(__file__).resolve().parent
TOOL=ROOT/'scripts/capture.py'
def run_tool(result,root):
    def build(src,work,out,recipe=None):
        return result
    fastbuild=types.SimpleNamespace(run_compiler=lambda *a,**k:None,build=build)
    argv=[str(TOOL),str(root/'crate'),str(root/'work'),str(root/'out')]
    stdout=io.StringIO()
    with mock.patch.dict(sys.modules,{'fastbuild':fastbuild}),mock.patch.object(sys,'argv',argv),mock.patch.object(sys,'path',list(sys.path)),contextlib.redirect_stdout(stdout):
        try:
            runpy.run_path(str(TOOL),run_name='__main__')
        except SystemExit as stop:
            return stop.code,stdout.getvalue()
    return 0,stdout.getvalue()
class BuildStatusTests(unittest.TestCase):
    def test_failed_build_is_not_success(self):
        with tempfile.TemporaryDirectory() as scratch:
            root=Path(scratch)
            out=root/'out';out.mkdir()
            stale=out/'pump_recovered.ll';stale.write_text('stale IR')
            code,stdout=run_tool({'ok':False,'log':'build.log'},root)
            self.assertEqual(code,1)
            self.assertIn('"ok": false',stdout)
            self.assertEqual(stale.read_text(),'stale IR')
    def test_successful_build_copies_the_newest_module(self):
        with tempfile.TemporaryDirectory() as scratch:
            root=Path(scratch)
            out=root/'out';out.mkdir()
            deps=root/'work/target-identity/sbpf-solana-solana/release/deps';deps.mkdir(parents=True)
            (deps/'pump_recovered-1.ll').write_text('fresh IR')
            code,_=run_tool({'ok':True},root)
            self.assertEqual(code,0)
            self.assertEqual((out/'pump_recovered.ll').read_text(),'fresh IR')
if __name__=='__main__':unittest.main()
