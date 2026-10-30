import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from attempt_applicability import FIELDS

SCHEMA_PATH = Path(__file__).resolve().parents[1]/'pump-main/ledger_schema.py'
SPEC = importlib.util.spec_from_file_location('boundary_ledger_schema', SCHEMA_PATH)
schema = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(schema)


class LedgerBoundaryTests(unittest.TestCase):
    def test_unicode_string_characters_do_not_create_jsonl_records(self):
        context = {key:'a'*64 for key in FIELDS}
        for separator in ('\u0085', '\u2028', '\u2029', 'ordinary space'):
            row = dict(schema='main-pump-attempt-v1',attempt_id='id',timestamp_utc='2026-10-29T00:00:00+00:00',lane='lane',approach='shape-A',target='16',dedupe_key='key',hypothesis='first'+separator+'second',status='analyzed',data={'context':context,'evidence':[{'path':'evidence.json','sha256':hashlib.sha256(b'{}').hexdigest()}]})
            text = json.dumps(row,ensure_ascii=False)+'\nnot json\n'
            with self.subTest(separator=separator):
                rows, errors = schema.inspect_ledger(text, ['analyzed'])
                self.assertEqual(rows,[row])
                self.assertEqual([error['line'] for error in errors],[2])
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    (root/'evidence.json').write_bytes(b'{}')
                    ledger, current = root/'ledger.jsonl', root/'context.json'
                    ledger.write_text(text,encoding='utf-8')
                    current.write_text(json.dumps(context),encoding='utf-8')
                    original = ledger.read_bytes()
                    result = subprocess.run([sys.executable,'-X','utf8=1',str(Path(__file__).with_name('attempt_applicability.py')),'--ledger',str(ledger),'--context',str(current),'--evidence-root',str(root),'--target','16','--approach','shape-A'],capture_output=True)
                    self.assertEqual(result.returncode,2,result.stderr.decode('utf-8',errors='replace'))
                    report = json.loads(result.stdout)
                    self.assertEqual(report['counts'],{'compatible':1})
                    self.assertEqual(report['rows'][0]['hypothesis'],row['hypothesis'])
                    self.assertEqual([error['line'] for error in report['parse_errors']],[2])
                    self.assertEqual(ledger.read_bytes(),original)

    def test_retained_pump_ledger_still_validates(self):
        text = SCHEMA_PATH.with_name('ATTEMPTS.jsonl').read_text(encoding='utf-8')
        statuses = ['analyzed','built','compile-failed','rejected','partial','normalized-match','raw-match']
        rows, errors = schema.inspect_ledger(text,statuses)
        self.assertEqual(errors,[])
        self.assertGreater(len(rows),1000)


if __name__ == '__main__': unittest.main()
