import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HARNESS = Path(__file__).resolve().parents[1] / 'reconstruction/harness'
sys.path.insert(0, str(HARNESS))

import build_score_pair as pair  # noqa: E402


def imported_harness_modules(name):
    """Every sibling module the named harness script loads, including itself."""
    seen, pending = set(), [name]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        for node in ast.walk(ast.parse((HARNESS / current).read_text(encoding='utf-8'))):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            pending.extend(module + '.py' for module in modules if (HARNESS / (module + '.py')).is_file())
    return seen


class ReceiptToolIdentityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.addCleanup(setattr, pair.score, 'BASE', pair.score.BASE)
        self.addCleanup(setattr, pair.fastbuild, 'SDK', pair.fastbuild.SDK)
        self.addCleanup(setattr, pair.fastbuild, 'LOCKDIR', pair.fastbuild.LOCKDIR)
        self.addCleanup(pair.fastbuild.RECIPES.__setitem__, 'identity', pair.fastbuild.RECIPES['identity'])

    def receipt_tools(self):
        sdk, hybrid = self.root / 'sdk', self.root / 'hybrid'
        for path in (sdk / 'llvm/bin/llvm-objdump', hybrid / 'rust/bin/rustc'):
            path.parent.mkdir(parents=True)
            path.write_bytes(b'tool fixture')

        def build(source, work, out, **kwargs):
            out.mkdir(parents=True)
            (out / 'unstripped.so').write_bytes(b'fixture, not a real ELF')
            return {'ok': True, 'runtime_valid': True, 'stack_warnings': []}

        windows = {0: {'bytes': 8, 'normalized': True, 'raw': True}}
        out = self.root / 'output'
        with patch.object(pair, 'source_receipt', return_value={'revision': 'fixture'}), \
             patch.object(pair.fastbuild, 'build', side_effect=build), \
             patch.object(pair.score, 'score', return_value=windows):
            self.assertEqual(pair.run_pair(self.root / 'base', self.root / 'candidate', out, sdk, hybrid), 0)
        return json.loads((out / 'receipt.json').read_text())['tools']

    def test_receipt_binds_every_harness_module_the_gate_executes(self):
        tools = self.receipt_tools()
        executed = imported_harness_modules('build_score_pair.py')
        for hook in ('pump_physical_source_wrapper.py', 'pump_link_rustc.py', 'pump_link_lld.py'):
            executed |= imported_harness_modules(hook)
        self.assertEqual(sorted(executed - tools.keys()), [])


if __name__ == '__main__':
    unittest.main()
