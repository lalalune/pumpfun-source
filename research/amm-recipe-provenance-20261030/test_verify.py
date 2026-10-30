#!/usr/bin/env python3
"""Synthetic controls for loading the pinned recipe source."""

import importlib.util
import os
from pathlib import Path
import py_compile
import tempfile
import unittest

from verify import load_recipe, sha


RELATIVE = 'scripts/amm_sell/workspace_recipe.py'


class RecipeLoadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='amm-recipe-load-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.recipe = self.root / RELATIVE
        self.recipe.parent.mkdir(parents=True)

    def test_hash_mismatch_rejects_before_side_effect(self):
        marker = self.root / 'sentinel.txt'
        self.recipe.write_text(f'from pathlib import Path\nPath({str(marker)!r}).write_text("executed")\n')
        with self.assertRaisesRegex(ValueError, 'pinned source'):
            load_recipe(self.root, RELATIVE, '0' * 64)
        self.assertFalse(marker.exists())

    def test_stale_bytecode_cannot_replace_verified_source(self):
        old = b"VALUE = 'old'\n"
        new = b"VALUE = 'new'\n"
        self.assertEqual(len(old), len(new))
        self.recipe.write_bytes(old)
        timestamp = self.recipe.stat()
        cache = Path(py_compile.compile(str(self.recipe), doraise=True))
        self.assertTrue(cache.is_file())
        self.recipe.write_bytes(new)
        os.utime(self.recipe, ns=(timestamp.st_atime_ns, timestamp.st_mtime_ns))

        # Confirm the synthetic cache would fool a timestamp-based import.
        spec = importlib.util.spec_from_file_location('synthetic_stale_recipe', self.recipe)
        cached = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cached)
        self.assertEqual(cached.VALUE, 'old')
        self.assertEqual(load_recipe(self.root, RELATIVE, sha(new)).VALUE, 'new')

    def test_symlinked_recipe_is_rejected(self):
        actual = self.root / 'ordinary.py'
        actual.write_bytes(b"VALUE = 'ordinary'\n")
        self.recipe.symlink_to(actual)
        with self.assertRaisesRegex(ValueError, 'Symlinked'):
            load_recipe(self.root, RELATIVE, sha(actual.read_bytes()))


if __name__ == '__main__':
    unittest.main()
