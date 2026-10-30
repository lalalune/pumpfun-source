"""Actual verifier CLIs prepare nested paths and preserve their public inputs."""
import copy
import gzip
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
sys.path.insert(0, str(ROOT / 'scripts'))
import test_mayhem_receipt_admission as mayhem_receipts

PUMP = ROOT / 'evidence/original/pump/deployed.so'
MAYHEM = ROOT / 'evidence/original/mayhem/deployed.so'
PUMP_SCRIPTS = ('pump_set_mayhem_virtual_params_differential.py',
                'pump_validate_authority.py', 'pump_validate_config_admin.py', 'pump_validate_volume.py')
VERIFIERS = (('verify_mayhem_buy.py', 'buy'), ('verify_mayhem_buy_v2.py', 'buy_v2'),
             ('verify_mayhem_sell.py', 'sell'), ('verify_mayhem_sell_v2.py', 'sell_v2'),
             ('verify_mayhem_pump_swap.py', 'buy_pump_swap'))


def run(script, arguments, driver=None):
    command = [sys.executable, '-B']
    if driver:
        command += ['-c', driver, str(ROOT / 'scripts' / script)]
    else:
        command += [str(ROOT / 'scripts' / script)]
    return subprocess.run(command + list(map(str, arguments)), cwd=ROOT,
                          capture_output=True, text=True, timeout=120)


def read_report(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)


@unittest.skipUnless(shutil.which('rustc'), 'actual recovered-host controls require rustc')
class RemainingOutputParentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='remaining-output-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.hosts = {}
        for script, source in (
                ('validate_fee_selection.py', 'programs/pump-fees/recovered/fee_selection_host.rs'),
                ('pump_validate_sell_accounting.py', 'programs/pump/recovered/sell_accounting_host.rs'),
                ('constant', 'programs/pump/recovered/constant_product_host.rs')):
            host = cls.work / (script + ('.exe' if os.name == 'nt' else '.host'))
            subprocess.run(['rustc', '--edition=2021', '-O', str(ROOT/source), '-o', str(host)],
                           check=True, capture_output=True, text=True)
            cls.hosts[script] = host
        quote_dir = cls.work / 'quote-host'
        result = run('build_quote_host.py', ['--output', quote_dir])
        if result.returncode:
            raise RuntimeError(result.stderr)
        cls.hosts['validate_quote_fees.py'] = quote_dir / 'quote-fees-host'
        cls.curve = cls.work / 'curve.json'
        result = run('pump_validate_constant_product.py', ['--host', cls.hosts['constant'], '--output', cls.curve])
        if result.returncode:
            raise RuntimeError(result.stderr)
        cls.documents = {}
        for _, name in VERIFIERS:
            original = mayhem_receipts.execute_rejection(name)
            candidate = mayhem_receipts.execute_rejection(name)
            if original['transaction_base64'] != candidate['transaction_base64']:
                raise RuntimeError('independent original and candidate transactions differ')
            cls.documents[name] = {
                'original_sha256': hashlib.sha256(MAYHEM.read_bytes()).hexdigest(),
                'candidate_sha256': hashlib.sha256(MAYHEM.read_bytes()).hexdigest(),
                'harness_sha256': {'scripts/test_mayhem_receipt_admission.py':
                                  hashlib.sha256((ROOT/'scripts/test_mayhem_receipt_admission.py').read_bytes()).hexdigest()},
                'case_count': 1, 'mismatches': [], 'cases': [{'case': {'instruction': name},
                    'original': original, 'candidate': candidate, 'different_fields': []}]}

    def directory(self):
        temporary = tempfile.TemporaryDirectory(dir=self.work)
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def arguments(self, script, directory):
        if script in PUMP_SCRIPTS:
            candidate = directory / 'pump.so'
            shutil.copyfile(PUMP, candidate)
            return ['--candidate', candidate], candidate
        if script in self.hosts:
            host = directory / 'host'
            shutil.copy2(self.hosts[script], host)
            args = ['--host', host]
            if script == 'pump_validate_sell_accounting.py':
                args += ['--curve-report', self.curve]
            return args, host
        name = dict(VERIFIERS)[script]
        candidate = directory / 'mayhem.so'
        receipt = directory / 'receipt.json'
        shutil.copyfile(MAYHEM, candidate)
        receipt.write_text(json.dumps(self.documents[name]), encoding='utf-8')
        return ['--candidate', candidate, '--receipts', receipt], candidate

    def test_all_twelve_clis_reject_candidate_or_host_alias(self):
        scripts = (*PUMP_SCRIPTS, *[s for s, _ in VERIFIERS],
                   'validate_fee_selection.py', 'validate_quote_fees.py', 'pump_validate_sell_accounting.py')
        for script in scripts:
            with self.subTest(script=script):
                directory = self.directory()
                args, protected = self.arguments(script, directory)
                before = protected.read_bytes()
                result = run(script, args + ['--output', protected])
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('report output aliases an input', result.stderr)
                self.assertEqual(protected.read_bytes(), before)

    def test_receipts_and_curve_report_are_protected(self):
        for script, _ in VERIFIERS:
            with self.subTest(script=script):
                directory = self.directory()
                args, _ = self.arguments(script, directory)
                receipt = directory / 'receipt.json'
                before = receipt.read_bytes()
                result = run(script, args + ['--output', receipt])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('report output aliases an input', result.stderr)
                self.assertEqual(receipt.read_bytes(), before)
        directory = self.directory()
        args, _ = self.arguments('pump_validate_sell_accounting.py', directory)
        before = self.curve.read_bytes()
        result = run('pump_validate_sell_accounting.py', args + ['--output', self.curve])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('report output aliases an input', result.stderr)
        self.assertEqual(self.curve.read_bytes(), before)

    def test_real_execution_and_receipts_publish_to_nested_parents(self):
        scripts = (*PUMP_SCRIPTS, *[s for s, _ in VERIFIERS],
                   'validate_fee_selection.py', 'validate_quote_fees.py', 'pump_validate_sell_accounting.py')
        for script in scripts:
            with self.subTest(script=script):
                directory = self.directory()
                args, _ = self.arguments(script, directory)
                output = directory / 'new' / 'nested' / 'report.json'
                result = run(script, args + ['--output', output])
                self.assertEqual(result.returncode, 0, result.stderr)
                report = read_report(output)
                self.assertTrue(report)
                self.assertEqual(report.get('mismatches', []), [])
                self.assertEqual(list(output.parent.glob('.report.json.*')), [])

    def test_optional_output_still_allows_original_only_execution(self):
        result = run('pump_set_mayhem_virtual_params_differential.py', [])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('0 mismatches', result.stdout)

    def test_receipt_digest_binds_the_bytes_actually_verified(self):
        driver = r'''
import sys, runpy
from pathlib import Path
script, receipt = sys.argv[1:3]
sys.path.insert(0, str(Path(script).parent))
original = Path.read_bytes
changed = False
def read(path):
    global changed
    data = original(path)
    if path == Path(receipt) and not changed:
        changed = True
        path.write_bytes(b'replaced after admission')
    return data
Path.read_bytes = read
sys.argv = [script, *sys.argv[3:]]
runpy.run_path(script, run_name='__main__')
if not changed:
    raise RuntimeError('receipt mutation did not execute')
'''
        for script, _ in VERIFIERS:
            with self.subTest(script=script):
                directory = self.directory()
                args, _ = self.arguments(script, directory)
                receipt, output = directory / 'receipt.json', directory / 'verified.json'
                digest = hashlib.sha256(receipt.read_bytes()).hexdigest()
                result = subprocess.run([sys.executable, '-B', '-c', driver,
                                         str(ROOT / 'scripts' / script), str(receipt),
                                         *map(str, args), '--output', str(output)],
                                        cwd=ROOT, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(receipt.read_bytes(), b'replaced after admission')
                self.assertEqual(read_report(output)['receipt_sha256'], digest)

    def test_failed_validation_and_failed_staging_preserve_prior_report(self):
        directory = self.directory()
        args, _ = self.arguments('verify_mayhem_buy.py', directory)
        output = directory / 'verified.json'
        output.write_bytes(b'previous complete report')
        receipt = directory / 'receipt.json'
        document = copy.deepcopy(self.documents['buy'])
        document['candidate_sha256'] = 'wrong hash'
        receipt.write_text(json.dumps(document), encoding='utf-8')
        result = run('verify_mayhem_buy.py', args + ['--output', output])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), b'previous complete report')
        receipt.write_text(json.dumps(self.documents['buy']), encoding='utf-8')
        driver = r'''
import sys, runpy
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
import pump_differential_output
def fail(*args): raise OSError('staging failed')
pump_differential_output.os.fsync = fail
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
'''
        result = run('verify_mayhem_buy.py', args + ['--output', output], driver)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('staging failed', result.stderr)
        self.assertEqual(output.read_bytes(), b'previous complete report')
        self.assertEqual(list(directory.glob('.verified.json.*')), [])


if __name__ == '__main__':
    unittest.main()
