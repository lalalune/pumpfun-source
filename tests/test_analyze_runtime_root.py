"""Use the complete retained Mayhem ELF to qualify redirected analysis roots."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('runtime_root_analyze', REPO / 'scripts/analyze.py')
ANALYZE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZE)


class RuntimeRootTests(unittest.TestCase):
    def fixture(self, root):
        source = REPO / 'evidence/original/mayhem/deployed.so'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         'a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb')
        destination = root / 'evidence/original/mayhem/deployed.so'
        destination.parent.mkdir(parents=True)
        shutil.copyfile(source, destination)
        upstream = root / 'evidence/upstream'
        upstream.mkdir(parents=True)
        for path in (REPO / 'evidence/upstream').glob('pump*.json'):
            shutil.copyfile(path, upstream / path.name)

    def test_default_selector_and_complete_workflow_use_current_root(self):
        with tempfile.TemporaryDirectory(prefix='analysis-live-root-') as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(ANALYZE, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ANALYZE.program_names(), ['mayhem'])
                ANALYZE.analyze()
            result = json.loads((root / 'evidence/binary-analysis.json').read_text(encoding='utf-8'))
            self.assertEqual(set(result), {'mayhem'})
            self.assertEqual(result['mayhem']['allocation_bytes'], 777408)
            self.assertEqual(result['mayhem']['elf_extent'], 775416)
            self.assertTrue(result['mayhem']['trailing_all_zero'])
            self.assertIn('pump', json.loads((root / 'evidence/interface-inventory.json').read_text(encoding='utf-8')))

    def test_explicit_root_remains_independent_of_redirected_default(self):
        with tempfile.TemporaryDirectory(prefix='analysis-explicit-root-') as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(ANALYZE, 'ROOT', root / 'absent'):
                self.assertEqual(ANALYZE.program_names(root), ['mayhem'])

    def test_archived_selector_is_resolved_from_the_current_root(self):
        with tempfile.TemporaryDirectory(prefix='analysis-archive-root-') as directory:
            root = Path(directory)
            self.fixture(root)
            capture = json.loads((REPO / 'evidence/original/mayhem/capture.json').read_text(encoding='utf-8'))
            selected = {'mayhem': capture['program']}
            (root / 'repro').mkdir()
            (root / 'repro/programs.json').write_text(json.dumps(selected), encoding='utf-8')
            with patch.object(ANALYZE, 'ROOT', root):
                self.assertEqual(ANALYZE.program_names(), selected)


if __name__ == '__main__':
    unittest.main()
