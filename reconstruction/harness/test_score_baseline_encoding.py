import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_elf_symbols import fixture


class BaselineEncodingTests(unittest.TestCase):
    def test_saved_utf8_baseline_scores_under_legacy_locale(self):
        for symbols in (['plain'], ['caf\u00e9 \u0394']):
            with self.subTest(symbols=symbols), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                harness, base = root/'harness',root/'base'
                harness.mkdir();base.mkdir()
                for name in ('score.py','score_admission.py','llvm_tools.py','elf_symbols.py','original_input.py'):
                    shutil.copyfile(Path(__file__).with_name(name),harness/name)
                image = bytes(fixture())
                candidate = root/'candidate.so';candidate.write_bytes(image)
                (base/'original.so').write_bytes(image)
                (base/'functions.tsv').write_text('program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n',encoding='utf-8')
                baseline, output = root/'baseline.json',root/'report.json'
                document = {'windows':{'4096':{'bytes':8,'normalized':True,'raw':True,'symbols':symbols}}}
                baseline.write_text(json.dumps(document,ensure_ascii=False),encoding='utf-8')
                original = baseline.read_bytes()
                env = dict(os.environ,LC_ALL='C',PYTHONCOERCECLOCALE='0',PYTHONUTF8='0')
                arguments = [sys.executable,'-X','utf8=0',str(harness/'score.py'),str(candidate),'--baseline',str(baseline),'--json',str(output)]
                result = subprocess.run(arguments,env=env,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                summary = json.loads(output.read_text(encoding='utf-8'))['summary']
                self.assertEqual(summary['normalized'],1)
                self.assertEqual(summary['losses'],[])
                self.assertEqual(summary['raw_losses'],[])
                self.assertEqual(baseline.read_bytes(),original)
                self.assertEqual(candidate.read_bytes(),image)

    def test_malformed_utf8_is_not_lossily_admitted(self):
        import score_admission
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'baseline.json'
            raw = b'{"windows":{},"note":"\x80"}'
            path.write_bytes(raw)
            with self.assertRaises(UnicodeError): score_admission.baseline(path)
            self.assertEqual(path.read_bytes(),raw)


if __name__ == '__main__': unittest.main()
