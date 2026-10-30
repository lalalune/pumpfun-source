import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_elf_symbols import fixture
from test_window_cache import WindowCacheTests


class InventoryColumnTests(unittest.TestCase):
    def test_duplicate_required_columns_do_not_silently_replace_selection_or_bounds(self):
        values = {'program':'pump','variant':'selected','original_start':'4096','original_end':'4112'}
        replaced = {'program':'other','variant':'other','original_start':'4104','original_end':'4104'}
        for duplicate in values:
            with self.subTest(duplicate=duplicate), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                harness, base = root/'harness',root/'base'
                harness.mkdir();base.mkdir()
                for name in ('score.py','score_admission.py','llvm_tools.py','elf_symbols.py','original_input.py'):
                    shutil.copyfile(Path(__file__).with_name(name),harness/name)
                candidate = root/'candidate.so';candidate.write_bytes(fixture())
                (base/'original.so').write_bytes(fixture())
                names = list(values)+[duplicate]
                row = [replaced[name] if name == duplicate else values[name] for name in values]+[values[duplicate]]
                inventory = base/'functions.tsv'
                inventory.write_text('\t'.join(names)+'\n'+'\t'.join(row)+'\n',encoding='utf-8')
                before = candidate.read_bytes(),inventory.read_bytes()
                output = root/'score.json'
                result = subprocess.run([sys.executable,str(harness/'score.py'),str(candidate),'--no-baseline','--json',str(output)],capture_output=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn(b'duplicate required columns',result.stderr)
                self.assertFalse(output.exists())
                self.assertEqual((candidate.read_bytes(),inventory.read_bytes()),before)
                # The same selected interval still scores normally when the
                # inventory has one unambiguous column for each required field.
                inventory.write_text('\t'.join(values)+'\n'+'\t'.join(values.values())+'\n',encoding='utf-8')
                result = subprocess.run([sys.executable,str(harness/'score.py'),str(candidate),'--no-baseline','--json',str(output)],capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['windows']['4096']['bytes'],16)


if __name__ == '__main__': unittest.main()
