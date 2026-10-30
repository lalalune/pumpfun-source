"""Actual call/data audits must read Git's materialized original link as ELF."""
import gzip
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
LANE = Path('reconstruction/pump-main/lanes/callgraph-census')
ARCHIVE = Path('research/pump-multihop-sell-fees-20261029/build/candidate/symbols.so.gz')


class CensusOriginalInputTests(unittest.TestCase):
    def test_actual_callid_and_dataref_match_real_capture_control(self):
        with tempfile.TemporaryDirectory(prefix='pump-census-original-') as temporary:
            root = Path(temporary)
            candidate = root / 'symbols.so'
            candidate.write_bytes(gzip.decompress((REPO / ARCHIVE).read_bytes()))
            outputs = {}
            for mode in ('capture-bytes', 'materialized-link'):
                layout = root / mode
                files = [Path('reconstruction/harness') / name for name in (
                    'score.py', 'score_admission.py', 'llvm_tools.py', 'original_input.py',
                    'elf_symbols.py', 'instruction_stream.py', 'win.py', 'coords.py')]
                files += [LANE / name for name in ('census.py', 'callid_audit.py', 'dataref_audit.py')]
                files += [Path('reconstruction/base/functions.tsv'), Path('evidence/original/pump/deployed.so')]
                for relative in files:
                    target = layout / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(REPO / relative, target)
                original = layout / 'reconstruction/base/original.so'
                original.write_bytes(b'../../evidence/original/pump/deployed.so' if mode == 'materialized-link'
                                     else (layout / 'evidence/original/pump/deployed.so').read_bytes())
                for name in ('callid_audit.py', 'dataref_audit.py'):
                    with self.subTest(mode=mode, tool=name):
                        output = layout / (name + '.json')
                        result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8',
                            str(layout / LANE / name), '--cand', str(candidate), '--json', str(output)],
                            cwd=root, capture_output=True, encoding='utf-8')
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        outputs[mode, name] = output.read_bytes()
            for name in ('callid_audit.py', 'dataref_audit.py'):
                if ('capture-bytes', name) in outputs and ('materialized-link', name) in outputs:
                    self.assertEqual(outputs['capture-bytes', name], outputs['materialized-link', name])


if __name__ == '__main__':
    unittest.main()
