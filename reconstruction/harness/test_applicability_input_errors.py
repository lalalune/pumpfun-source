import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from attempt_applicability import FIELDS


class ApplicabilityInputErrorTests(unittest.TestCase):
    def test_bad_saved_inputs_report_cli_errors_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger,current = root/'ledger.jsonl',root/'context.json'
            context = {field:'a'*64 for field in FIELDS}
            arguments = [sys.executable,str(Path(__file__).with_name('attempt_applicability.py')),'--ledger',str(ledger),'--context',str(current),'--evidence-root',str(root),'--target','16','--approach','shape-A']
            for invalid in ('missing-ledger','missing-context','broken-context','duplicate-context','wrong-context','invalid-target'):
                with self.subTest(invalid=invalid):
                    ledger.write_text('',encoding='utf-8')
                    current.write_text(json.dumps(context),encoding='utf-8')
                    command = arguments[:]
                    if invalid == 'missing-ledger': ledger.unlink()
                    elif invalid == 'missing-context': current.unlink()
                    elif invalid == 'broken-context': current.write_text('{',encoding='utf-8')
                    elif invalid == 'duplicate-context': current.write_text('{"x":1,"x":2}',encoding='utf-8')
                    elif invalid == 'wrong-context': current.write_text('[]',encoding='utf-8')
                    elif invalid == 'invalid-target': command[command.index('--target')+1] = '-1'
                    before = {path:path.read_bytes() for path in (ledger,current) if path.exists()}
                    result = subprocess.run(command,capture_output=True)
                    self.assertEqual(result.returncode,2,result.stderr.decode('utf-8',errors='replace'))
                    self.assertNotIn(b'Traceback',result.stderr)
                    self.assertIn(b'error:',result.stderr)
                    self.assertEqual({path:path.read_bytes() for path in before},before)
            ledger.write_text('',encoding='utf-8')
            current.write_text(json.dumps(context),encoding='utf-8')
            result = subprocess.run(arguments,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
            self.assertEqual(json.loads(result.stdout)['rows'],[])


if __name__ == '__main__': unittest.main()
