import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_elf_symbols import fixture
from test_control_flow import ControlFlowTests
from test_batch_target_metric import BatchMetricTests


class DiagnosticOutputTests(unittest.TestCase):
    def test_cli_preserves_candidate_and_prior_receipt(self):
        source = Path(__file__).resolve().parent
        for script in ('control_flow.py', 'target_metric.py'):
            for existing in ('candidate.so', 'receipt.json'):
                with self.subTest(script=script, existing=existing), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    harness, base = root/'harness', root/'base'
                    harness.mkdir(); base.mkdir()
                    for name in ('control_flow.py', 'target_metric.py', 'win.py', 'score.py', 'score_admission.py', 'elf_symbols.py', 'instruction_stream.py', 'llvm_tools.py'):
                        shutil.copyfile(source/name, harness/name)
                    image = bytes(fixture())
                    (base/'original.so').write_bytes(image)
                    (base/'functions.tsv').write_text('program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n', encoding='utf-8')
                    candidate = root/'candidate.so'; candidate.write_bytes(image)
                    receipt = root/'receipt.json'; receipt.write_bytes(b'prior receipt\n')
                    arguments = [str(candidate), '--start', '0x1000', '--size', '8'] if script == 'control_flow.py' else [str(candidate), '0x1000']
                    before = {candidate:candidate.read_bytes(), receipt:receipt.read_bytes()}
                    result = subprocess.run([sys.executable, str(harness/script), *arguments, '--json', str(root/existing)], capture_output=True)
                    self.assertEqual(result.returncode, 2, result.stderr.decode('utf-8'))
                    self.assertEqual({path:path.read_bytes() for path in before}, before)
                    output = root/'new'/'diagnostic.json'
                    result = subprocess.run([sys.executable, str(harness/script), *arguments, '--json', str(output)], capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
                    document = json.loads(output.read_text(encoding='utf-8'))
                    self.assertTrue(document)


if __name__ == '__main__': unittest.main()
