"""Retained-input regression; no captured code executes."""
import unittest

class HarnessSymbolNameTests(unittest.TestCase):
    def test_retained_impl_symbols_drop_only_the_compiler_escape_prefix(self):
        import json
        from pathlib import Path
        import shutil
        import subprocess
        import sys
        import tempfile

        repo = Path(__file__).resolve().parents[2]
        baseline = json.loads((repo / 'reconstruction/pump-main/baseline/score.json').read_text(encoding='utf-8'))
        symbols = baseline['windows']['288']['symbols']
        self.assertEqual(len(symbols), 2)
        # Load the actual analyzer in an isolated layout. On Windows git may
        # materialize original.so as link text; copy its real capture target.
        with tempfile.TemporaryDirectory(prefix='pump-symbol-names-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-symbol-names-'))
            (root / 'harness').mkdir()
            (root / 'base').mkdir()
            for name in ['win.py', 'score.py', 'score_admission.py', 'llvm_tools.py', 'instruction_stream.py', 'elf_symbols.py', 'original_input.py']:
                shutil.copyfile(repo / 'reconstruction/harness' / name, root / 'harness' / name)
            shutil.copyfile(repo / 'evidence/original/pump/deployed.so', root / 'base/original.so')
            result = subprocess.run(
                [sys.executable, '-B', '-c',
                 'import json,sys;sys.path.insert(0,sys.argv[1]);import win;'
                 'print(json.dumps([win.demangle(s) for s in json.load(sys.stdin)]))',
                 str(root / 'harness')],
                input=json.dumps([*symbols, '_ZN15__STATIC_FMTSTRE', '_ZN4testE', 'ordinary_symbol']),
                capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            names = json.loads(result.stdout)
            self.assertEqual(names[0], '<anchor_lang::accounts::interface::Interface<T> as anchor_lang::Accounts<B>>::try_accounts')
            self.assertEqual(names[1], '<anchor_lang::accounts::signer::Signer as anchor_lang::Accounts<B>>::try_accounts')
            self.assertRegex(names[0], r'^<anchor_lang::accounts::interface::Interface<T> ')
            self.assertEqual(names[2:], ['__STATIC_FMTSTR', 'test', 'ordinary_symbol'])


if __name__ == '__main__': unittest.main()
