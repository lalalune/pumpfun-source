import io
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from build_process import run_compiler
import fastbuild


class CompilerDeadlineTests(unittest.TestCase):
    def run_python(self, code, **kwargs):
        return run_compiler([sys.executable, '-u', '-c', code], **kwargs)

    def test_success_and_nonzero_exit_retain_output(self):
        for status in (0, 7):
            result, expired = self.run_python(f'import sys; print("diagnostic"); sys.exit({status})', timeout=2)
            self.assertFalse(expired);self.assertEqual(result.returncode,status)
            self.assertEqual(result.stdout,'diagnostic\n')

    def test_optional_timeout_preserves_unbounded_mode(self):
        result,expired=self.run_python('print("done")')
        self.assertFalse(expired);self.assertEqual(result.stdout,'done\n')

    def test_timeout_preserves_partial_output(self):
        result,expired=self.run_python('import time; print("started"); time.sleep(30)',timeout=1)
        self.assertTrue(expired);self.assertNotEqual(result.returncode,0)
        self.assertEqual(result.stdout,'started\n')

    def test_compiler_descendants_are_stopped(self):
        with tempfile.TemporaryDirectory() as temp:
            marker=Path(temp)/'orphan'
            child=f'import time; from pathlib import Path; time.sleep(1.5); Path({str(marker)!r}).write_text("survived")'
            parent=f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{child!r}]); print("child launched"); time.sleep(30)'
            result,expired=self.run_python(parent,timeout=1)
            self.assertTrue(expired);self.assertIn('child launched',result.stdout)
            time.sleep(0.8)
            self.assertFalse(marker.exists())

    def test_invalid_timeout_does_not_start_process(self):
        with patch('build_process.subprocess.Popen') as popen:
            for timeout in (0,-1,float('inf'),float('nan'),True,'1'):
                with self.assertRaises(ValueError):self.run_python('',timeout=timeout)
            popen.assert_not_called()

    def test_builder_releases_slot_and_retains_log_without_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);slot=io.StringIO();out=root/'out';(root/'src').mkdir()
            out.mkdir()
            (out/'candidate.so').write_bytes(b'prior candidate')
            (out/'unstripped.so').write_bytes(b'prior unstripped')
            (out/'build.log').write_text('prior log')
            original_archive = fastbuild.archive_previous_outputs
            def archive(path):
                with self.assertRaisesRegex(RuntimeError, 'already in use'):
                    with fastbuild.workspace_lock(root/'work'):
                        pass
                original_archive(path)
            def compiler(command, **kwargs):
                self.assertFalse((out/'candidate.so').exists())
                self.assertFalse((out/'unstripped.so').exists())
                self.assertFalse((out/'build.log').exists())
                self.assertEqual(len(list((out/'previous').glob('build-*'))), 1)
                self.assertEqual(kwargs['timeout'], 1)
                with self.assertRaisesRegex(RuntimeError, 'already in use'):
                    with fastbuild.workspace_lock(root/'work'):
                        pass
                return self.run_python('import time; print("partial compiler log"); time.sleep(30)', timeout=kwargs['timeout'])
            with patch.object(fastbuild,'archive_previous_outputs',side_effect=archive),patch.object(fastbuild,'stage',return_value=root/'crate'),patch.object(fastbuild,'acquire_slot',return_value=slot),patch.object(fastbuild,'run_compiler',side_effect=compiler),patch.object(fastbuild,'RECIPES',{'test':{'triple':'test','rustc':root/'rustc','template':root/'missing'}}),patch.object(fastbuild.subprocess,'run') as publish:
                report=fastbuild.build(root/'src',root/'work',out,quiet=True,recipe='test',timeout=1)
                publish.assert_not_called()
            self.assertFalse(report['ok']);self.assertTrue(report['timed_out']);self.assertTrue(slot.closed)
            self.assertEqual((out/'build.log').read_text(),'partial compiler log\n')
            self.assertFalse((out/'candidate.so').exists())
            self.assertFalse((out/'unstripped.so').exists())
            archive, = (out/'previous').glob('build-*')
            self.assertEqual((archive/'candidate.so').read_bytes(), b'prior candidate')
            self.assertEqual((archive/'unstripped.so').read_bytes(), b'prior unstripped')
            self.assertEqual((archive/'build.log').read_text(), 'prior log')
            with fastbuild.workspace_lock(root/'work'):
                pass

    def test_invalid_timeout_precedes_workspace_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaises(ValueError):
                fastbuild.build(root/'src',root/'work',root/'out',timeout=0)
            self.assertEqual(list(root.iterdir()), [])


if __name__ == '__main__':unittest.main()
