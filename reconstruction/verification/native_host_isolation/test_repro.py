"""Normalized compiler diagnostics must name the path that actually appeared."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCES = ('programs/pump/recovered/global_admin_host.rs', 'programs/pump/recovered/global_admin.rs')
# Every compile fails, so the report keeps exactly what the compiler printed.
COMPILER = f"""#!{sys.executable}
import sys
if '--version' in sys.argv:
    print('rustc stub')
    raise SystemExit(0)
print(sys.argv[3], '->', sys.argv[5], file=sys.stderr)
raise SystemExit(1)
"""


class DiagnosticNormalizationTests(unittest.TestCase):
    def test_paths_sharing_a_prefix_keep_their_own_labels(self):
        with tempfile.TemporaryDirectory(prefix='pump-native-host-') as temporary:
            parent = Path(temporary).resolve()
            root_a, root_b = parent / 'checkout', parent / 'checkout-b'
            for root in (root_a, root_b):
                for name in SOURCES:
                    (root / name).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / name, root / name)
            compiler = parent / 'rustc-stub'
            compiler.write_text(COMPILER, encoding='utf-8')
            os.chmod(compiler, 0o755)
            output = root_a / 'results'
            result = subprocess.run(
                [sys.executable, '-B', str(HERE / 'repro.py'), str(root_a), str(root_b),
                 '--rustc', str(compiler), '--output-dir', str(output), '--trials', '1'],
                capture_output=True, text=True, encoding='utf-8', timeout=120)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            records = json.loads((output / 'results.json').read_text(encoding='utf-8'))['results']
        excerpts = [worker['normalized_diagnostic_excerpt'] for row in records for worker in row['workers']]
        self.assertEqual(len(excerpts), 4)
        for index, excerpt in enumerate(excerpts):
            label = ('<root-a>', '<root-b>')[index % 2]
            self.assertTrue(excerpt.startswith(f'{label}/{SOURCES[0]} -> <output>/build-'), excerpt)


if __name__ == '__main__':
    unittest.main()
