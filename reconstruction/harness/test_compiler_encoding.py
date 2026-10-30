"""Exercise real compiler-wrapper children under an uncoerced legacy locale."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


class CompilerEncodingTests(unittest.TestCase):
    def run_wrapper(self, payload, status, encoding=None):
        child = f'import os,sys; os.write(1, {payload!r}); sys.exit({status})'
        options = {} if encoding is None else {'encoding':encoding}
        wrapper = ('import json,sys; from build_process import run_compiler; '
                   f'result,expired=run_compiler([sys.executable,"-c",{child!r}], **{options!r}); '
                   'print(json.dumps({"code":result.returncode,"text":result.stdout,"expired":expired}))')
        env = dict(os.environ, LC_ALL='C', PYTHONCOERCECLOCALE='0', PYTHONUTF8='0',
                   PYTHONPATH=str(Path(__file__).resolve().parent))
        result = subprocess.run([sys.executable, '-X', 'utf8=0', '-c', wrapper], env=env, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
        return json.loads(result.stdout)

    def test_valid_utf8_diagnostics_survive_legacy_locale(self):
        text = 'warning: caf\u00e9 \u20ac\n'
        for status in (0, 7):
            with self.subTest(status=status):
                result = self.run_wrapper(text.encode('utf-8'), status)
                self.assertEqual(result, {'code':status,'text':text,'expired':False})

    def test_explicit_encoding_override_is_preserved(self):
        self.assertEqual(self.run_wrapper(b'caf\xe9\n', 0, 'latin-1')['text'], 'caf\u00e9\n')


if __name__ == '__main__': unittest.main()
