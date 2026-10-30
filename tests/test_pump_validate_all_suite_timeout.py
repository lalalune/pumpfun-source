"""The serial Pump aggregate must bound each suite with a killable process group."""
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/pump_validate_all.py'
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'


class PumpAggregateSuiteTimeoutTests(unittest.TestCase):
    def fixture(self, root):
        """Give the aggregate the candidate and producer receipts it binds."""
        candidate = root / 'candidate.so'
        shutil.copyfile(ORIGINAL, candidate)
        (root / 'build-comparison.json').write_text('{}')
        (root / 'build-attempt.json').write_text('{}')
        return candidate

    def invoke(self, candidate, output, timeout):
        return subprocess.run(
            [sys.executable, '-B', str(SCRIPT), '--candidate', str(candidate),
             '--output', str(output), '--suite-timeout', timeout],
            cwd=ROOT, capture_output=True, text=True, timeout=120)

    def test_expired_suite_is_killed_and_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = self.fixture(root)
            output = root / 'report.json.gz'
            result = self.invoke(candidate, output, '0.001')
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stderr.strip().splitlines()[-1], 'suite volume exceeded 0.001s')
            self.assertFalse(output.exists())

    def test_nonpositive_timeout_is_rejected(self):
        for timeout in ('0', '-1', 'nan', 'inf'):
            with self.subTest(timeout=timeout), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                candidate = self.fixture(root)
                output = root / 'report.json.gz'
                result = self.invoke(candidate, output, timeout)
                self.assertEqual(result.returncode, 1)
                self.assertIn('compiler timeout must be a positive finite number of seconds',
                              result.stderr)
                self.assertFalse(output.exists())


    def isolated_aggregate(self, root):
        scripts = root/'scripts';scripts.mkdir()
        for source in (ROOT/'scripts').glob('*.py'):
            shutil.copyfile(source, scripts/source.name)
        harness = root/'reconstruction/harness';harness.mkdir(parents=True)
        shutil.copyfile(ROOT/'reconstruction/harness/build_process.py', harness/'build_process.py')
        original = root/'evidence/original/pump/deployed.so';original.parent.mkdir(parents=True)
        shutil.copyfile(ORIGINAL, original)
        source = root/'programs/pump/lib.rs';source.parent.mkdir(parents=True)
        source.write_text('// test-only admitted source input')
        return self.fixture(root)

    @unittest.skipUnless(sys.platform != 'win32', 'POSIX process-group guarantee')
    def test_actual_aggregate_timeout_kills_descendant_and_cleans_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);candidate=self.isolated_aggregate(root);marker=root/'survivor'
            code=('import subprocess,sys,time;print("suite started",flush=True);'
                  'subprocess.Popen([sys.executable,"-c",'
                  f'"import time,pathlib;time.sleep(0.8);pathlib.Path({str(marker)!r}).write_text(\'survived\')"]);'
                  'time.sleep(30)')
            (root/'scripts/pump_validate_volume.py').write_text(code)
            output=root/'report.json.gz'
            result=subprocess.run([sys.executable,'-B',str(root/'scripts/pump_validate_all.py'),
                '--candidate',str(candidate),'--output',str(output),'--suite-timeout','0.3'],
                cwd=root,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertIn('suite volume exceeded 0.3s',result.stderr)
            self.assertIn('suite started',result.stdout)
            self.assertFalse(output.exists());self.assertFalse(output.with_name(output.name+'.suites').exists())
            self.assertFalse(list(root.glob('.*staging*')))
            time.sleep(1);self.assertFalse(marker.exists())

    def test_process_helper_output_alias_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);candidate=self.isolated_aggregate(root)
            output=root/'reconstruction/harness/build_process.py';before=output.read_bytes()
            result=subprocess.run([sys.executable,'-B',str(root/'scripts/pump_validate_all.py'),
                '--candidate',str(candidate),'--output',str(output)],cwd=root,capture_output=True,text=True,timeout=10)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('aliases',result.stderr)
            self.assertEqual(output.read_bytes(),before)


    def test_process_helper_mutation_is_detected_before_receipt_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);candidate=self.isolated_aggregate(root)
            changed=root/'reconstruction/harness/build_process.py'
            (root/'scripts/pump_validate_volume.py').write_text(
                'from pathlib import Path\nPath('+repr(str(changed))+').write_bytes(b"changed helper")\n')
            output=root/'report.json.gz'
            result=subprocess.run([sys.executable,'-B',str(root/'scripts/pump_validate_all.py'),
                '--candidate',str(candidate),'--output',str(output)],cwd=root,capture_output=True,text=True,timeout=10)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('suite process helper changed',result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
