"""Extract guards without importing or executing research campaigns."""
import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.transaction import Transaction, VersionedTransaction
from solders.message import MessageV0
ROOT = Path(__file__).resolve().parents[1]
HARNESSES = (
    'research/pump-multi-hop-corpus/harness.py',
    'research/handler-closure-multihop-mayhem-20261029/suites/pump_create_v2_mayhem_mode_differential.py',
)
VERSIONED = 'research/runtime-versioned-reset-20261101/reproduce.py'


def extract(relative, name, optimize=0):
    path = ROOT / relative
    tree = ast.parse(path.read_bytes(), filename=str(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(nodes) != 1:
        raise AssertionError(f'{relative}: expected one {name}')
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec',
                 optimize=optimize), namespace)
    return namespace[name]


def vectors(versioned=False):
    payer = Keypair.from_seed(bytes([31]) * 32)
    other = Keypair.from_seed(bytes([32]) * 32)
    ix = Instruction(Pubkey.new_unique(), b'', [AccountMeta(other.pubkey(), True, False)])
    if versioned:
        msg = MessageV0.try_compile(payer.pubkey(), [ix], [], Hash.default())
        full = VersionedTransaction(msg, [payer, other])
        populate = VersionedTransaction.populate
    else:
        full = Transaction.new_signed_with_payer([ix], payer.pubkey(), [payer, other], Hash.default())
        populate = Transaction.populate
    return {
        'valid': full,
        'empty': populate(full.message, []),
        'partial': populate(full.message, full.signatures[:1]),
        'corrupt': populate(full.message, [Signature.default(), full.signatures[1]]),
        'extra': populate(full.message, [*full.signatures, full.signatures[0]]),
    }


class ResearchSignatureGuardTests(unittest.TestCase):
    def test_complete_header_required_in_normal_and_optimized_guards(self):
        for optimize in (0, 1, 2):
            for relative in HARNESSES:
                guard = extract(relative, 'require_signed', optimize)
                for label, tx in vectors().items():
                    with self.subTest(optimize=optimize, module=relative, vector=label):
                        if label == 'valid':
                            guard(tx)
                        else:
                            with self.assertRaises(AssertionError):
                                guard(tx)

    def test_partial_vector_really_verifies_only_its_present_signature(self):
        tx = vectors()['partial']
        self.assertEqual(tx.message.header.num_required_signatures, 2)
        self.assertEqual(list(tx.verify_with_results()), [True])

    def test_versioned_recorder_requires_all_header_signatures(self):
        for optimize in (0, 1, 2):
            guard = extract(VERSIONED, 'signatures_verified', optimize)
            for versioned in (False, True):
                for label, tx in vectors(versioned).items():
                    with self.subTest(optimize=optimize, versioned=versioned, vector=label):
                        self.assertIs(guard(tx), label == 'valid')

    def test_campaigns_refuse_optimized_python_before_imports(self):
        for relative in (*HARNESSES, VERSIONED):
            for flags, value in ((('-O',), None), (('-OO',), None), ((), '2')):
                environment = dict(os.environ)
                environment.pop('PYTHONOPTIMIZE', None)
                if value is not None:
                    environment['PYTHONOPTIMIZE'] = value
                run = subprocess.run([sys.executable, '-B', *flags, str(ROOT / relative), '--help'],
                                     env=environment, text=True, capture_output=True)
                with self.subTest(module=relative, flags=flags, environment=value):
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn('requires normal Python', run.stderr)
                    self.assertNotIn('Traceback', run.stderr)


if __name__ == '__main__':
    unittest.main()
