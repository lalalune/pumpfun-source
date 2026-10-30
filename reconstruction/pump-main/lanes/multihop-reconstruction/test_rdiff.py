"""rdiff.py must locate a candidate's swap_hop through the harness's current symbol reader."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
# dis.py in this folder would otherwise shadow the standard library module unittest imports.
sys.path[:] = [entry for entry in sys.path if Path(entry or '.').resolve() != HERE]

import gzip
import hashlib
import os
import subprocess
import tempfile
import contextlib  # noqa: E402
import io  # noqa: E402
import runpy  # noqa: E402
import unittest  # noqa: E402
from unittest import mock  # noqa: E402

ROOT = HERE.parents[3]
HARNESS = ROOT / 'reconstruction/harness'
sys.path.insert(0, str(HARNESS))
import score  # noqa: E402
import win  # noqa: E402
from llvm_tools import objdump  # noqa: E402

try:
    OBJDUMP = objdump()
except FileNotFoundError:
    OBJDUMP = None

ORIGINAL_START = 0x5b3b0


class RangeDiffTests(unittest.TestCase):
    def test_candidate_range_diffs_against_the_original_swap_hop(self):
        start = 0x1000
        functions = [(start, 16, 'pump8swap_hop17h0123456789abcdefE')]
        listings = [{start: 'mov64 r1, r2', start + 8: 'exit'},
                    {ORIGINAL_START: 'mov64 r1, r2', ORIGINAL_START + 8: 'mov64 r3, r4'}]
        stdout = io.StringIO()
        argv = ['rdiff.py', str(HARNESS), 'candidate.so', '0', '10', '0', '10']
        with (mock.patch.object(sys, 'argv', argv), mock.patch.object(sys, 'path', list(sys.path)),
              mock.patch.object(score, 'candidate_functions', return_value=functions),
              mock.patch.object(win, 'objdump_text', side_effect=listings),
              contextlib.redirect_stdout(stdout)):
            try:
                runpy.run_path(str(HERE / 'rdiff.py'), run_name='__main__')
            except AttributeError as error:
                self.fail(str(error))
        rows = stdout.getvalue().splitlines()
        self.assertEqual([row[0] for row in rows], [' ', 'r'])
        self.assertIn('mov64 r3, r4', rows[1])
        self.assertIn('exit', rows[1])


class RetainedRangeDiffTests(unittest.TestCase):
    @unittest.skipUnless(OBJDUMP, 'an LLVM objdump is required for retained ELF disassembly')
    def test_actual_retained_candidate_and_invalid_image(self):
        archive=ROOT/'research/pump-multihop-sell-fees-20261029/build/candidate/symbols.so.gz'
        raw=gzip.decompress(archive.read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'b79428215bac7c4cb487681ea3a5cdad84197fcaa04142a0e68f4a4706008898')
        with tempfile.TemporaryDirectory(prefix='rdiff-retained-') as temporary:
            root=Path(temporary);candidate=root/'candidate.so';candidate.write_bytes(raw)
            outputs=[]
            for flags in (['-I','-B'],['-B']):
                result=subprocess.run([sys.executable,*flags,str(HERE/'rdiff.py'),str(HARNESS),
                                       str(candidate),'0','20','0','20'],cwd=root,
                                      env=dict(os.environ,PUMP_OBJDUMP=OBJDUMP),capture_output=True,text=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                rows=result.stdout.splitlines()
                self.assertEqual(len(rows),4)
                self.assertTrue(any(row.startswith('r') for row in rows),rows)
                self.assertTrue(any(row.startswith(' ') for row in rows),rows)
                outputs.append(result.stdout)
            self.assertEqual(outputs[0],outputs[1])
            self.assertEqual(candidate.read_bytes(),raw)
            candidate.write_bytes(b'not an ELF image')
            failed=subprocess.run([sys.executable,'-I','-B',str(HERE/'rdiff.py'),str(HARNESS),
                                   str(candidate),'0','20','0','20'],cwd=root,
                                  capture_output=True,text=True,timeout=60)
            self.assertNotEqual(failed.returncode,0)
            self.assertEqual(failed.stdout,'')
            self.assertEqual(candidate.read_bytes(),b'not an ELF image')


if __name__ == '__main__':
    unittest.main()
