import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import integrate

class CompositionDeadlineTests(unittest.TestCase):
    def test_deadline_reaches_builder_and_timeout_is_a_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=root/'crate';(src/'src').mkdir(parents=True)
            for f in ['Cargo.toml','Cargo.lock','src/lib.rs']:(src/f).write_text('fixture')
            baseline=root/'pump-main/baseline/score.json';baseline.parent.mkdir(parents=True);baseline.write_text('{}')
            args=['integrate','--name','deadline','--base-src',str(src),'--timeout','0.1']
            with patch.object(integrate,'SC',root),patch.object(sys,'argv',args),patch.object(integrate,'build_source',return_value={'ok':False,'timed_out':True}) as builder,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(integrate.main(),1)
            self.assertEqual(builder.call_args.kwargs['timeout'],.1)
            report=json.loads((root/'integ/deadline/report.json').read_text());self.assertTrue(report['build']['timed_out']);self.assertNotIn('score',report)
            for value in ['0','-1','inf','nan']:
                with patch.object(sys,'argv',['integrate','--name','invalid','--base-src',str(src),'--timeout',value,'--no-build']),contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):integrate.main()
            self.assertFalse((root/'integ/invalid').exists())
if __name__=='__main__':unittest.main()
