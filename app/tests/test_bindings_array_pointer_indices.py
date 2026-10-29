import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('subject', Path(__file__).resolve().parents[1] / 'scripts/verify-bindings.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

class PointerTests(unittest.TestCase):

    def test_array_indices_do_not_alias_noncanonical_spellings(self):
        for pointer in ['#/00', '#/01', '#/١']:
            with self.subTest(pointer=pointer), self.assertRaises(ValueError):
                subject.resolve_pointer(['first', 'second'], pointer)
        self.assertEqual(subject.resolve_pointer(['first', 'second'], '#/1'), 'second')
        self.assertEqual(subject.resolve_pointer({'00': 'key'}, '#/00'), 'key')
