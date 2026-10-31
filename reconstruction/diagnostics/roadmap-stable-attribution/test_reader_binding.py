import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import generate

ROOT = Path(__file__).resolve().parents[3]
READER = 'scripts/window_elf_reader.py'


class AttributionReaderBindingTests(unittest.TestCase):
    def prepare(self, root, captures=False):
        for name in (generate.SOURCE, READER):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        if captures:
            for program in ('pump', 'pump_amm', 'mayhem'):
                relative = f'evidence/original/{program}/deployed.so'
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)

    def test_unreviewed_reader_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.prepare(root)
            marker = root / 'executed'
            reader = root / READER
            reader.write_bytes(reader.read_bytes() +
                               f'\nPath({str(marker)!r}).write_text("executed")\n'.encode())
            with patch.dict(sys.modules):
                sys.modules.pop('window_elf_reader', None)
                with self.assertRaisesRegex(ValueError, 'unreviewed roadmap ELF reader'):
                    generate.generate(root, root / 'output')
            self.assertFalse(marker.exists())
            self.assertFalse((root / 'output').exists())

    def test_cached_reader_cannot_supply_different_analysis_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.prepare(root, captures=True)
            cached = types.ModuleType('window_elf_reader')
            def forbidden(*args, **kwargs):
                raise RuntimeError('unbound cached reader executed')
            cached.Elf = forbidden
            with patch.dict(sys.modules, {'window_elf_reader': cached}):
                generate.generate(root, root / 'output')
                self.assertIs(sys.modules['window_elf_reader'], cached)
            bindings = json.loads((root / 'output/attribution-inputs.json').read_text(encoding='utf-8'))
            self.assertEqual(bindings[READER], hashlib.sha256((root / READER).read_bytes()).hexdigest())
            manifest = json.loads((root / 'output/manifest.json').read_text(encoding='utf-8'))
            for name, digest in manifest.items():
                self.assertEqual(hashlib.sha256((root / 'output' / name).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
