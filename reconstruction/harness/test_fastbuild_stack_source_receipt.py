"""Every compiled build result names its sources, including stack-rejected ones."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fastbuild  # noqa: E402

STACK = 'Error: Function example Stack offset of 4104 exceeded max offset of 4096 by 8 bytes.\n'


class StackRejectedSourceReceiptTests(unittest.TestCase):
    def build(self, log, returncode=0):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            src, work, out = (root / name for name in ('src', 'work', 'out'))
            src.mkdir()
            (src / 'lib.rs').write_text('// synthetic input\n')
            crate = work / 'ws/programs/pump'
            crate.mkdir(parents=True)
            (crate / 'Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\n')
            recipe = {'triple': 'sbpf-solana-solana', 'rustc': root / 'rustc',
                      'template': root / 'absent-template'}

            def compiler(command, **_):
                return subprocess.CompletedProcess(command, returncode, stdout=log), False

            with patch.object(fastbuild, 'RECIPES', {'identity': recipe}), \
                 patch.object(fastbuild, 'stage', return_value=crate), \
                 patch.object(fastbuild, 'acquire_slot', side_effect=lambda: io.StringIO()), \
                 patch.object(fastbuild, 'run_compiler', side_effect=compiler):
                result = fastbuild.build(src, work, out, quiet=True, recipe='identity')
            return result, json.loads((out / 'source-inputs.json').read_text(encoding='utf-8'))

    def test_stack_rejected_result_names_the_rejected_sources(self):
        result, receipt = self.build(STACK)
        self.assertFalse(result['ok'])
        self.assertEqual(result['stack_warnings'], [STACK.strip()])
        self.assertEqual(result.get('source_sha256'), receipt['sha256'])

    def test_compiler_failure_result_keeps_its_source_identity(self):
        result, receipt = self.build('compiler failed\n', returncode=1)
        self.assertFalse(result['ok'])
        self.assertEqual(result.get('source_sha256'), receipt['sha256'])


if __name__ == '__main__':
    unittest.main()
