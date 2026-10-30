import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

H = Path(__file__).resolve().parent
CLI = H.parents[1] / 'tests/dispatch_encoding_cli.py'
PATCH = b'''diff --git a/added.txt b/added.txt
new file mode 100644
--- /dev/null
+++ b/added.txt
@@ -0,0 +1 @@
+added
'''


class MinimizePatchListEncodingTests(unittest.TestCase):
    def test_patch_list_is_utf8_on_a_host_with_another_text_default(self):
        # Sibling of minimize_experiment.load_oracle (merged #2618): the patch
        # list holds file paths, so a non-ASCII directory must survive a host
        # whose default text encoding is not UTF-8.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / 'source'
            source.mkdir()
            (source / 'lib.rs').write_text('fixture\n', encoding='utf-8')
            unit = root / 'SOL → tokens.patch'
            unit.write_bytes(PATCH)
            patches = root / 'patches.json'
            patches.write_text(json.dumps([str(unit)], ensure_ascii=False), encoding='utf-8')
            oracle = root / 'oracle.json'
            oracle.write_text(json.dumps({'command': [sys.executable, '-c', 'pass'], 'timeout': 30}), encoding='utf-8')
            result = subprocess.run(
                [sys.executable, '-B', str(CLI), str(H / 'minimize_experiment.py'),
                 '--source', str(source), '--patches', str(patches), '--oracle', str(oracle),
                 '--out', str(root / 'out')],
                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr[-600:])
            self.assertEqual(json.loads(result.stdout)['selected'], [])


if __name__ == '__main__':
    unittest.main()
