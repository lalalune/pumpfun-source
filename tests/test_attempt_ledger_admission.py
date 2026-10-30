"""Reject invalid requests before they can mutate or split the live ledger lock."""
import contextlib
import fcntl
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reconstruction/pump-main"))
import log_attempt as ledger
from test_ledger_publication import FIRST


class LedgerAdmission(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.live = self.root / 'live/ATTEMPTS.jsonl'
        self.lock = self.live.with_name('.attempts.lock')
        self.tracked = self.root / 'tracked.jsonl'
        self.tracked.write_text(json.dumps(FIRST) + '\n')
        globals = patch.multiple(ledger, LEDGER=self.live, LOCK=self.lock, TRACKED=self.tracked)
        globals.start()
        self.addCleanup(globals.stop)

    def invoke(self, arguments):
        with patch.object(sys, 'argv', ['ledger', *arguments]), contextlib.redirect_stdout(io.StringIO()):
            return ledger.main()

    def record(self, *extra):
        return self.invoke(['record', '--lane', 'test', '--approach', 'test', '--target', 'all',
                            '--dedupe-key', 'new', '--hypothesis', 'test', '--status', 'analyzed', *extra])

    def test_duplicate_metadata_is_rejected_before_initialization(self):
        for data in ['{"metric":1,"metric":2}', '{"nested":{"metric":1,"metric":2}}']:
            with self.subTest(data=data), self.assertRaisesRegex(SystemExit, 'duplicate JSON property'):
                self.record('--data', data)
            self.assertFalse(self.live.parent.exists())

    def test_invalid_fields_do_not_seed_or_lock_live_ledger(self):
        for extra in [('--lane', ' '), ('--data', '{"metric":NaN}'), ('--data', '[]')]:
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                self.record(*extra)
            self.assertFalse(self.live.parent.exists())
            self.assertEqual(self.tracked.read_text(), json.dumps(FIRST) + '\n')

    def test_lock_destinations_are_rejected_without_replacing_locked_inode(self):
        ledger.locked(lambda rows: None)
        alias = self.root / 'alias'
        alias.symlink_to(self.live.parent, target_is_directory=True)
        direct_alias = self.root / 'lock-link'
        direct_alias.symlink_to(self.lock)
        hardlink = self.root / 'lock-hardlink'
        os.link(self.lock, hardlink)
        before = self.lock.stat().st_ino
        for destination in [self.lock, alias / self.lock.name, direct_alias, hardlink]:
            with self.subTest(destination=destination), self.assertRaisesRegex(SystemExit, 'lock'):
                self.invoke(['sync', '--to', str(destination)])
            self.assertEqual(self.lock.stat().st_ino, before)
            self.assertEqual(self.lock.read_bytes(), b'')
        # A second process opening the canonical pathname must still contend
        # with an existing writer's descriptor, rather than a replacement inode.
        with self.lock.open('r+') as writer:
            fcntl.flock(writer, fcntl.LOCK_EX)
            probe = subprocess.run([sys.executable, '-c',
                'import fcntl,sys; f=open(sys.argv[1],"r+"); '
                'fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)', str(self.lock)], capture_output=True)
        self.assertNotEqual(probe.returncode, 0)
        self.assertIn(b'BlockingIOError', probe.stderr)

    def copied_cli(self):
        tool = self.root/'tool';tool.mkdir(exist_ok=True)
        for name in ('log_attempt.py','ledger_schema.py'):
            shutil.copy2(Path(ledger.__file__).parent/name,tool/name)
        (tool/'ATTEMPTS.jsonl').write_text(json.dumps(FIRST)+'\n')
        return tool/'log_attempt.py'

    def test_actual_cli_rejects_duplicate_data_without_initializing(self):
        script=self.copied_cli()
        environment=dict(os.environ,PUMP_SWARM_LEDGER=str(self.live))
        arguments=['record','--lane','test','--approach','test','--target','all',
                   '--dedupe-key','new','--hypothesis','test','--status','analyzed']
        invalid=subprocess.run([sys.executable,str(script),*arguments,'--data','{"x":1,"x":2}'],
                               env=environment,capture_output=True,text=True,timeout=15)
        self.assertNotEqual(invalid.returncode,0)
        self.assertIn('duplicate JSON property',invalid.stderr)
        self.assertFalse(self.live.parent.exists())
        valid=subprocess.run([sys.executable,str(script),*arguments,'--data','{"nested":{"x":2}}'],
                             env=environment,capture_output=True,text=True,timeout=15)
        self.assertEqual(valid.returncode,0,valid.stderr)
        self.assertEqual(json.loads(self.live.read_text().splitlines()[-1])['data'],{'nested':{'x':2}})

    def test_parent_alias_retarget_during_real_lock_wait_cannot_replace_lock(self):
        script=self.copied_cli()
        ledger.locked(lambda rows:None)
        elsewhere=self.root/'elsewhere';elsewhere.mkdir()
        alias=self.root/'destination';alias.symlink_to(elsewhere,target_is_directory=True)
        marker=self.root/'waiting'
        code=r'''
import fcntl,sys
from pathlib import Path
script,marker,destination=sys.argv[1:]
sys.path.insert(0,str(Path(script).parent))
import log_attempt
original=fcntl.flock
def wait(fd,operation):
    Path(marker).touch()
    return original(fd,operation)
fcntl.flock=wait
sys.argv=[script,'sync','--to',destination]
log_attempt.main()
'''
        before=self.lock.stat().st_ino
        with self.lock.open('r+') as writer:
            fcntl.flock(writer,fcntl.LOCK_EX)
            process=subprocess.Popen([sys.executable,'-c',code,str(script),str(marker),str(alias/self.lock.name)],
                env=dict(os.environ,PUMP_SWARM_LEDGER=str(self.live)),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                deadline=time.monotonic()+5
                while not marker.exists() and time.monotonic()<deadline:
                    time.sleep(0.01)
                self.assertTrue(marker.exists(),'child did not reach lock wait')
                alias.unlink();alias.symlink_to(self.live.parent,target_is_directory=True)
            finally:
                fcntl.flock(writer,fcntl.LOCK_UN)
            output,error=process.communicate(timeout=15)
        self.assertNotEqual(process.returncode,0,output)
        self.assertIn('destination changed',error)
        self.assertEqual(self.lock.stat().st_ino,before)
        self.assertEqual(self.lock.read_bytes(),b'')
        self.assertFalse((elsewhere/self.lock.name).exists())

    def test_successful_copy_does_not_delete_recreated_staging_name(self):
        destination=self.root/'snapshot.jsonl'
        replace=os.replace;recreated=[]
        def replace_and_recreate(source,target):
            replace(source,target)
            Path(source).write_bytes(b'new owner')
            recreated.append(Path(source))
        with patch.object(ledger.os,'replace',replace_and_recreate):
            ledger.atomic_copy(self.tracked,destination)
        self.assertEqual(destination.read_bytes(),self.tracked.read_bytes())
        self.assertEqual(recreated[0].read_bytes(),b'new owner')

    def test_valid_nested_metadata_and_duplicate_attempt_admission(self):
        self.record('--data', '{"nested":{"metric":2}}')
        rows = ledger.read_rows()
        self.assertEqual(rows[-1]['data'], {'nested': {'metric': 2}})
        before = self.live.read_bytes()
        with self.assertRaisesRegex(SystemExit, 'duplicate dedupe key'):
            self.record()
        self.assertEqual(self.live.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
