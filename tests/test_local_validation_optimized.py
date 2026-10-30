"""The malformed-input smoke test must fail on an accepted input under optimized Python too."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STUB = '''
ACCEPT_EMPTY = {accept_empty}
class FailedTransactionMetadata:
    def err(self): return 'InstructionError'
    def meta(self): return self
    def logs(self): return []
class Accepted:
    def logs(self): return ['accepted']
class LiteSVM:
    def with_transaction_history(self, _): return self
    def airdrop(self, *_): pass
    def add_program_from_file(self, *_): pass
    def latest_blockhash(self): return None
    def send_transaction(self, tx):
        return Accepted() if ACCEPT_EMPTY and tx.data == b'' else FailedTransactionMetadata()
class Keypair:
    @staticmethod
    def from_seed(_): return Keypair()
    def pubkey(self): return None
class Pubkey:
    @staticmethod
    def from_string(value): return value
class Instruction:
    def __init__(self, program, data, accounts): self.data = data
class Transaction:
    @staticmethod
    def new_signed_with_payer(instructions, *_): return instructions[0]
'''


class OptimizedSmokeTests(unittest.TestCase):
    def run_smoke(self, flags, accept_empty=True):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            stub = temporary / 'site' / 'solders'
            stub.mkdir(parents=True)
            (stub / '__init__.py').write_text('')
            # One shared module, so isinstance() sees the same failure class main() imports.
            (stub / '_stub.py').write_text(STUB.format(accept_empty=accept_empty))
            for module in ('litesvm', 'keypair', 'pubkey', 'instruction', 'transaction', 'transaction_metadata'):
                (stub / f'{module}.py').write_text('from solders._stub import *\n')
            # One captured program; the stubbed runtime rejects everything, or accepts only empty data.
            program = temporary / 'repo' / 'evidence/original/pump'
            program.mkdir(parents=True)
            (program / 'deployed.so').write_bytes(b'\x7fELF')
            (program / 'capture.json').write_text(json.dumps({'program': 'synthetic-program'}))
            code = ('import sys,pathlib;sys.path[:0]=[sys.argv[1],sys.argv[2]];import local_validation as v;'
                    'v.ROOT=pathlib.Path(sys.argv[3]);v.main()')
            result = subprocess.run(
                [sys.executable, *flags, '-B', '-I', '-S', '-c', code, str(temporary / 'site'),
                 str(ROOT / 'scripts'), str(temporary / 'repo')],
                capture_output=True, text=True, encoding='utf-8')
            report = json.loads((temporary / 'repo/audit/local-validation.json').read_text(encoding='utf-8'))
            return result, report

    def test_accepted_malformed_input_fails_in_normal_and_optimized_modes(self):
        for flags in ([], ['-O'], ['-OO']):
            with self.subTest(flags=flags):
                result, report = self.run_smoke(flags)
                self.assertFalse(report['programs']['pump']['all_rejected'])
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('malformed input accepted by: pump', result.stderr)
                rejected = report['programs']['pump']['cases']
                self.assertEqual([c['case'] for c in rejected if not c['rejected']], ['empty'])

    def test_all_rejected_passes_in_normal_and_optimized_modes(self):
        for flags in ([], ['-O'], ['-OO']):
            with self.subTest(flags=flags):
                result, report = self.run_smoke(flags, accept_empty=False)
                self.assertTrue(report['programs']['pump']['all_rejected'])
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
