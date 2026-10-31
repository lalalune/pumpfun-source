"""Exercise native-host receipt binding through all four real validator CLIs."""
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


@unittest.skipUnless(shutil.which('rustc') and os.name != 'nt', 'requires rustc and executable scripts')
class NativeHostReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='native-host-receipt-')
        cls.addClassCleanup(temporary.cleanup)
        cls.work = Path(temporary.name)
        cls.hosts = []
        for script, source in (
            ('pump_validate_constant_product.py', 'pump/recovered/constant_product_host.rs'),
            ('pump_validate_sell_accounting.py', 'pump/recovered/sell_accounting_host.rs'),
            ('validate_fee_selection.py', 'pump-fees/recovered/fee_selection_host.rs'),
        ):
            host = cls.work / Path(source).stem
            subprocess.run(['rustc', '--edition=2021', '-O', str(ROOT / 'programs' / source),
                            '-o', str(host)], check=True, capture_output=True)
            cls.hosts.append((script, host))
        quote = cls.work / 'quote'
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_quote_host.py'),
                        '--output', str(quote)], check=True, capture_output=True)
        cls.hosts.append(('validate_quote_fees.py', quote / 'quote-fees-host'))
        cls.curve_report = cls.work / 'curve.json'
        subprocess.run([sys.executable, str(ROOT / 'scripts/pump_validate_constant_product.py'),
                        '--host', str(cls.hosts[0][1]), '--output', str(cls.curve_report)],
                       check=True, capture_output=True, timeout=60)

    def validate(self, script, host, output):
        arguments = [sys.executable, '-B', str(ROOT / 'scripts' / script),
                     '--host', str(host), '--output', str(output)]
        if script == 'pump_validate_sell_accounting.py':
            arguments += ['--curve-report', str(self.curve_report)]
        return subprocess.run(arguments, capture_output=True, text=True, timeout=60)

    def test_unchanged_hosts_record_the_executed_digest(self):
        for script, host in self.hosts:
            with self.subTest(script=script):
                output = self.work / (script + '.json')
                result = self.validate(script, host, output)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(output.read_bytes())['host_sha256'],
                                 hashlib.sha256(host.read_bytes()).hexdigest())

    def test_replaced_host_cannot_publish_a_receipt_for_unexecuted_bytes(self):
        for script, host in self.hosts:
            with self.subTest(script=script):
                wrapper = self.work / (script + '-wrapper')
                # Forward every input to the genuinely compiled host. Replace
                # only this disposable wrapper, after the real computation.
                wrapper.write_text(f'#!{sys.executable}\n'
                    'import pathlib, subprocess, sys\n'
                    f'run = subprocess.run([{str(host)!r}], input=sys.stdin.read(), '
                    'text=True, capture_output=True, check=True)\n'
                    'pathlib.Path(__file__).write_text("replacement never executed\\n")\n'
                    'sys.stdout.write(run.stdout)\n', encoding='utf-8')
                wrapper.chmod(0o755)
                output = self.work / (script + '-previous.json')
                prior = b'previous retained report\n'
                output.write_bytes(prior)
                result = self.validate(script, wrapper, output)
                self.assertNotEqual(result.returncode, 0, script + ' published a receipt for replacement bytes')
                self.assertIn('native host changed during execution', result.stderr)
                self.assertEqual(output.read_bytes(), prior)


if __name__ == '__main__':
    unittest.main()
