import io
import json
import os
import signal
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

    def detached_pipe_trial(self, stream='stdout', leader_exits=False, interrupt=False):
        """Run run_compiler behind a watchdog and always reap escaped descendants."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            leader_pid = root / 'leader.pid'
            descendant_pid = root / 'descendant.pid'
            child = (
                'import sys,time; '
                f'print("detached-{stream}",file=sys.{stream},flush=True); time.sleep(30)'
            )
            leader_tail = 'sys.exit(0)' if leader_exits else 'time.sleep(30)'
            leader = (
                'import os,subprocess,sys,time; from pathlib import Path; '
                f'Path({str(leader_pid)!r}).write_text(str(os.getpid())); '
                f'c=subprocess.Popen([sys.executable,"-u","-c",{child!r}],start_new_session=True); '
                f'Path({str(descendant_pid)!r}).write_text(str(c.pid)); '
                f'print("leader-{stream}",file=sys.{stream},flush=True); {leader_tail}'
            )
            harness = str(Path(__file__).resolve().parent)
            if interrupt:
                wrapper = (
                    'import json,os,signal,sys,threading\n'
                    f'sys.path.insert(0,{harness!r})\n'
                    'from build_process import run_compiler\n'
                    f'command=[sys.executable,"-u","-c",{leader!r}]\n'
                    'threading.Timer(0.2,lambda:os.kill(os.getpid(),signal.SIGINT)).start()\n'
                    'try:\n'
                    ' run_compiler(command,timeout=30)\n'
                    'except KeyboardInterrupt:\n'
                    ' print(json.dumps({"interrupted":True}),flush=True)\n'
                )
            else:
                wrapper = (
                    'import json,sys; '
                    f'sys.path.insert(0,{harness!r}); from build_process import run_compiler; '
                    f'command=[sys.executable,"-u","-c",{leader!r}]; '
                    'r,t=run_compiler(command,timeout=0.2); '
                    'print(json.dumps({"timed_out":t,"returncode":r.returncode,"stdout":r.stdout}),flush=True)'
                )
            started = time.monotonic()
            outer = subprocess.Popen(
                [sys.executable, '-u', '-c', wrapper], start_new_session=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            returned = False
            output = ''
            descendant_alive = False
            try:
                output, _ = outer.communicate(timeout=2.5)
                returned = True
            except subprocess.TimeoutExpired as error:
                output = error.output or ''
                os.killpg(outer.pid, signal.SIGKILL)
                tail, _ = outer.communicate(timeout=1)
                output = tail or output
            finally:
                if outer.poll() is None:
                    os.killpg(outer.pid, signal.SIGKILL)
                    outer.communicate(timeout=1)
                pids = []
                for pid_path in (leader_pid, descendant_pid):
                    if pid_path.exists():
                        pid = int(pid_path.read_text())
                        pids.append(pid)
                        if pid_path == descendant_pid:
                            try:
                                os.kill(pid, 0)
                                descendant_alive = True
                            except ProcessLookupError:
                                pass
                        try:
                            os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
            return {
                'returned': returned,
                'elapsed': time.monotonic() - started,
                'outer_returncode': outer.returncode,
                'pids': pids,
                'descendant_alive_before_cleanup': descendant_alive,
                'output': output,
            }

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

    def test_detached_descendant_cannot_hold_stdout_cleanup_open(self):
        trial = self.detached_pipe_trial()
        self.assertTrue(trial['returned'], trial)
        report = json.loads(trial['output'])
        self.assertTrue(report['timed_out'])
        self.assertNotEqual(report['returncode'], 0)
        self.assertCountEqual(report['stdout'].splitlines(), ['leader-stdout', 'detached-stdout'])

    def test_detached_pipes_and_exited_leader_have_bounded_cleanup(self):
        cases = (('stderr', False, -signal.SIGKILL), ('stdout', True, 0))
        for stream, leader_exits, returncode in cases:
            with self.subTest(stream=stream, leader_exits=leader_exits):
                trial = self.detached_pipe_trial(stream, leader_exits)
                self.assertTrue(trial['returned'], trial)
                self.assertLess(trial['elapsed'], 2.5)
                self.assertTrue(trial['descendant_alive_before_cleanup'], trial)
                report = json.loads(trial['output'])
                self.assertTrue(report['timed_out'])
                self.assertEqual(report['returncode'], returncode)
                self.assertCountEqual(
                    report['stdout'].splitlines(),
                    [f'leader-{stream}', f'detached-{stream}'],
                )

    def test_interrupt_cleanup_is_bounded_with_detached_pipe(self):
        trial = self.detached_pipe_trial(interrupt=True)
        self.assertTrue(trial['returned'], trial)
        self.assertLess(trial['elapsed'], 2.5)
        self.assertEqual(json.loads(trial['output']), {'interrupted': True})

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
            (root/'crate').mkdir()
            (root/'crate/Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\n')
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
