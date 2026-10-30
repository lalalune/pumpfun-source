"""The identity audit must reject bad bindings even under python -O/-OO."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('reconstruction_identity_audit.py')

def elf():
    names = b'\0.shstrtab\0'
    raw = bytearray(192 + len(names))
    raw[:6] = b'\x7fELF\x02\x01'
    struct.pack_into('<HHIQQQIHHHHHH', raw, 16, 3, 247, 1, 0, 0, 64, 0, 64, 56, 0, 64, 2, 1)
    struct.pack_into('<IIQQQQIIQQ', raw, 128, 1, 3, 0, 0, 192, len(names), 0, 0, 1, 0)
    raw[192:] = names
    return bytes(raw)

class AuditOptimizationTests(unittest.TestCase):
    def fixture(self, root, bad=None):
        (root/'repro').mkdir()
        (root/'repro/status.json').write_text('{}', encoding='utf-8')
        raw = elf()
        digest = hashlib.sha256(raw).hexdigest()
        (root/'original.so').write_bytes(raw)
        (root/'candidate.so').write_bytes(raw)
        row = dict(original_path='original.so',candidate_path='candidate.so',original_sha256=digest,candidate_sha256=digest)
        if bad: row[bad] = '0'*64
        (root/'index.json').write_text(json.dumps({'programs':{'synthetic':row}}),encoding='utf-8')

    def run_audit(self, root, optimization):
        return subprocess.run([sys.executable, *optimization, str(SCRIPT),'--repo',str(root),'--index','index.json','--output',str(root/'audit.json')], capture_output=True, text=True)

    def test_wrong_source_or_candidate_digest_cannot_be_optimized_away(self):
        for option in [[],['-O'],['-OO']]:
            for field in ['original_sha256','candidate_sha256']:
                with self.subTest(option=option,field=field), tempfile.TemporaryDirectory() as directory:
                    root=Path(directory);self.fixture(root,field)
                    result=self.run_audit(root,option)
                    self.assertNotEqual(result.returncode,0,result.stdout)
                    self.assertFalse((root/'audit.json').exists())

    def test_existing_receipt_is_preserved_in_every_mode(self):
        for option in [[],['-O'],['-OO']]:
            with self.subTest(option=option), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);self.fixture(root)
                receipt=root/'audit.json';receipt.write_bytes(b'prior synthetic receipt\n')
                result=self.run_audit(root,option)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(receipt.read_bytes(),b'prior synthetic receipt\n')

    def test_valid_synthetic_artifact_still_has_no_source_identity_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root)
            result=self.run_audit(root,[])
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads((root/'audit.json').read_text(encoding='utf-8'))
            self.assertTrue(report['snapshot_programs']['synthetic']['allocation_comparison']['full_byte_equality'])
            self.assertFalse(report['snapshot_programs']['synthetic']['source_completeness_inferred'])

if __name__=='__main__':unittest.main()
