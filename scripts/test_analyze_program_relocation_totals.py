#!/usr/bin/env python3
"""Current CLI totals include data relocations, as originally corrected in #1091."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]


class ProgramRelocationTotalTests(unittest.TestCase):
    def test_actual_cli_counts_raw_relocation_rows_and_preserves_window_subtotal(self):
        for name in ('pump', 'pump_amm', 'pump_fees', 'mayhem'):
            with self.subTest(program=name), tempfile.TemporaryDirectory() as temporary:
                capture = ROOT / f'evidence/original/{name}/deployed.so'
                image = capture.read_bytes()
                elf = ELFFile(io.BytesIO(image))
                text = elf.get_section_by_name('.text')
                relocations = list(elf.get_section_by_name('.rel.dyn').iter_relocations())
                in_text = sum(text['sh_addr'] <= row['r_offset'] < text['sh_addr'] + text['sh_size']
                              for row in relocations)
                self.assertGreater(len(relocations), in_text)
                output = Path(temporary) / 'packet'
                run = subprocess.run([
                    sys.executable, '-B', str(ROOT / 'scripts/analyze_program.py'),
                    '--program', name, '--output', str(output),
                ], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                summary = json.loads((output / 'summary.json').read_text())
                windows = json.loads((output / 'window-inventory.json').read_text())
                readme = (output / 'README.md').read_text()
                self.assertEqual(summary['total_relocations'], len(relocations))
                self.assertEqual(summary['text_window_relocations'], in_text)
                self.assertEqual(sum(row['relocations'] for row in windows), in_text)
                self.assertEqual(summary['deployed_sha256'], hashlib.sha256(image).hexdigest())
                self.assertIn(f'| Total ELF relocations | {len(relocations)} |', readme)
                self.assertIn(f'| Text-window relocations | {in_text} |', readme)
                verify = subprocess.run([sys.executable, '-B', str(output / 'verify.py')],
                                        capture_output=True, text=True)
                self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
                self.assertEqual(capture.read_bytes(), image)


if __name__ == '__main__':
    unittest.main()
