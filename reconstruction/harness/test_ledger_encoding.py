import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from attempt_applicability import FIELDS


class LedgerEncodingTests(unittest.TestCase):
    def test_utf8_saved_ledger_and_context_under_legacy_locale(self):
        script = Path(__file__).resolve().with_name('attempt_applicability.py')
        for non_ascii in ('ledger', 'context', 'neither'):
            with self.subTest(non_ascii=non_ascii), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root/'evidence.json').write_bytes(b'{}')
                context = {key:'a'*64 for key in FIELDS}
                if non_ascii == 'context': context['note'] = '\u0394 \uacbd\uace0'
                row = {'target':16,'approach':'shape-A','hypothesis':'\u0394 \uacbd\uace0' if non_ascii == 'ledger' else 'plain',
                       'data':{'context':context, 'evidence':[{'path':'evidence.json','sha256':hashlib.sha256(b'{}').hexdigest()}]}}
                ledger, current = root/'ledger.jsonl', root/'context.json'
                ledger.write_text(json.dumps(row, ensure_ascii=False)+'\n',encoding='utf-8')
                current.write_text(json.dumps(context, ensure_ascii=False),encoding='utf-8')
                before = {path:path.read_bytes() for path in (ledger,current)}
                env = dict(os.environ,LC_ALL='C',PYTHONCOERCECLOCALE='0',PYTHONUTF8='0')
                result = subprocess.run([sys.executable,'-X','utf8=0',str(script),'--ledger',str(ledger),'--context',str(current),'--evidence-root',str(root),'--target','16','--approach','shape-A'],env=env,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                report = json.loads(result.stdout)
                self.assertEqual(report['counts'],{'compatible':1})
                self.assertEqual(report['rows'][0]['hypothesis'],row['hypothesis'])
                self.assertEqual({path:path.read_bytes() for path in before},before)


if __name__ == '__main__': unittest.main()
