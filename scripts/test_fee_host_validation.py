"""Exercise the real fee-validator CLIs with compiled Rust hosts and captured SBF."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODES = (((), None), (('-O',), None), (('-OO',), None), ((), '1'), ((), '2'))


@unittest.skipUnless(shutil.which('rustc'), 'native fee validation requires rustc')
class FeeHostValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='fee-host-validation-')
        cls.addClassCleanup(temporary.cleanup)
        cls.work = Path(temporary.name)
        cls.reports = cls.work / 'reports'
        cls.reports.mkdir()
        suffix = '.exe' if os.name == 'nt' else ''
        selector = cls.work / ('fee-selector' + suffix)
        subprocess.run(['rustc', '--edition=2021', '-O',
                        str(ROOT / 'programs/pump-fees/recovered/fee_selection_host.rs'),
                        '-o', str(selector)], check=True, capture_output=True)
        quote_dir = cls.work / 'quote'
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_quote_host.py'),
                        '--output', str(quote_dir)], check=True, capture_output=True)
        quote = quote_dir / 'quote-fees-host'
        cls.validators = (('validate_fee_selection.py', selector),
                          ('validate_quote_fees.py', quote))
        source = cls.work / 'bad_host.rs'
        source.write_text('''
use std::io::{self, Read};
fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let executable = std::env::current_exe().unwrap();
    let mode = executable.file_stem().unwrap().to_str().unwrap();
    let count = input.lines().count();
    let count = match mode {
        "empty" => 0,
        "short" => count.saturating_sub(1),
        "extra" => count + 1,
        _ => count,
    };
    for _ in 0..count { println!("0,0,0"); }
}
''', encoding='utf-8')
        bad = cls.work / ('bad-host' + suffix)
        subprocess.run(['rustc', '--edition=2021', str(source), '-o', str(bad)],
                       check=True, capture_output=True)
        cls.bad_hosts = []
        for name in ('empty', 'short', 'extra', 'wrong'):
            path = cls.work / (name + suffix)
            shutil.copy2(bad, path)
            cls.bad_hosts.append(path)

    def validate(self, script, host, flags, optimize):
        environment = dict(os.environ)
        environment.pop('PYTHONOPTIMIZE', None)
        if optimize is not None:
            environment['PYTHONOPTIMIZE'] = optimize
        output = self.reports / f'{script}-{host.name}-{flags}-{optimize}.json'
        result = subprocess.run(
            [sys.executable, '-B', *flags, str(ROOT / 'scripts' / script),
             '--host', str(host), '--output', str(output)],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=60)
        return result, output

    def test_genuine_recovered_hosts_match_captured_program_in_every_mode(self):
        for script, host in self.validators:
            for flags, optimize in MODES:
                with self.subTest(script=script, flags=flags, optimize=optimize):
                    result, output = self.validate(script, host, flags, optimize)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = json.loads(output.read_bytes())
                    if script == 'validate_fee_selection.py':
                        self.assertTrue(report['all_matched'])
                        self.assertGreater(report['differential_cases'], 1000)
                    else:
                        self.assertEqual(report['mismatches'], [])
                        self.assertGreater(report['case_count'], 1000)

    def test_successful_hosts_with_missing_extra_or_wrong_results_are_rejected(self):
        for script, _ in self.validators:
            for host in self.bad_hosts:
                for flags, optimize in MODES:
                    with self.subTest(script=script, host=host.name, flags=flags, optimize=optimize):
                        result, _ = self.validate(script, host, flags, optimize)
                        self.assertNotEqual(result.returncode, 0, result.stdout[:500])


if __name__ == '__main__':
    unittest.main()
