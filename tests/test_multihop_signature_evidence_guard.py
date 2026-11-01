"""Exercise actual recorder methods with a fake base and no campaign imports."""
import ast
import base64
import json
import types
import unittest
from test_research_signature_assert_guard import ROOT, vectors
RECORDERS = (
    'research/pump-multihop-sell-fees-20261029/runtime/inputs/focused.py',
    'research/pump-multihop-token-quote-20261029/runtime/inputs/focused.py',
)


def recorder(relative, optimize):
    path = ROOT / relative
    tree = ast.parse(path.read_bytes(), filename=str(path))
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'signatures_verified')
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ObservedVM')
    # Retain the actual send method and its super() closure; no LiteSVM exists.
    cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'send_transaction']

    class Base:
        def get_account(self, key):
            return None

        def send_transaction(self, tx):
            return types.SimpleNamespace(to_json=lambda: '{}')

    namespace = dict(Base=Base, base64=base64, json=json, SENDS=[],
                     f=types.SimpleNamespace(FailedTransactionMetadata=type('Failed', (), {})),
                     loader=types.SimpleNamespace(LOADS=[]))
    exec(compile(ast.Module(body=[helper, cls], type_ignores=[]), str(path), 'exec',
                 optimize=optimize), namespace)
    obj = namespace['ObservedVM']()
    obj.observed_loads = []
    return obj, namespace


class RecorderSignatureEvidenceTests(unittest.TestCase):
    def test_real_recorder_records_complete_valid_vectors_only(self):
        for relative in RECORDERS:
            for optimize in (0, 1, 2):
                obj, namespace = recorder(relative, optimize)
                for label, tx in vectors().items():
                    with self.subTest(module=relative, optimize=optimize, vector=label):
                        obj.send_transaction(tx)
                        row = namespace['SENDS'][-1]
                        self.assertIs(row['signatures_verified'], label == 'valid')
                        self.assertEqual(base64.b64decode(row['transaction_base64']), bytes(tx))

    def test_producers_keep_crlf(self):
        for relative in RECORDERS:
            raw = (ROOT / relative).read_bytes()
            self.assertEqual(raw.count(b'\r\n'), raw.count(b'\n'))


if __name__ == '__main__':
    unittest.main()
