"""Capture metadata lookup must not initialize an optional VM dependency."""
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MetadataImportTests(unittest.TestCase):
    def run_isolated(self, expression):
        code = 'import sys;sys.path.insert(0,' + repr(str(ROOT / 'scripts')) + ');' + expression
        return subprocess.run([sys.executable, '-I', '-S', '-c', code],
                              capture_output=True, text=True, encoding='utf-8')

    def test_retained_capture_addresses_without_site_packages(self):
        result = self.run_isolated('import json,local_validation;print(json.dumps(local_validation.program_addresses()))')
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(result.stdout)
        expected = {name: json.loads((ROOT / 'evidence/original' / name / 'capture.json').read_text(encoding='utf-8'))['program']
                    for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem')}
        self.assertEqual(actual, expected)

    def test_vm_entry_point_still_requires_real_dependency(self):
        result = self.run_isolated('import local_validation;local_validation.main()')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No module named 'solders'", result.stderr)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
