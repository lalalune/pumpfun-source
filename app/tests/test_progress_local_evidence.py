import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('subject', Path(__file__).resolve().parents[1] / 'scripts/progress.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
import tempfile

class EvidenceTests(unittest.TestCase):

    def test_external_files_cannot_support_local_milestone_credit(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / 'app'
            root.mkdir()
            (base / 'outside.txt').write_text('fixture')
            (root / 'inside.txt').write_text('fixture')
            with patch.object(subject, 'ROOT', root):
                for evidence in ['../outside.txt', str(base / 'outside.txt')]:
                    with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                        subject.score({'gate': {'status': 'accepted', 'evidence': [evidence]}})
                self.assertEqual(subject.score({'gate': {'status': 'accepted', 'evidence': ['inside.txt#section']}}), '1/1 (100%)')
