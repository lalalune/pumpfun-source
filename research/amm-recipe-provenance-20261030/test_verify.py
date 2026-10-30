#!/usr/bin/env python3
"""Synthetic controls for loading the pinned recipe source."""

import importlib.util
import copy
import json
import os
from pathlib import Path
import py_compile
import tempfile
import unittest
from unittest.mock import patch
import verify as verifier

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


class HistoricalRecipeTests(unittest.TestCase):
    def run_record(self, record):
        manifest = verifier.PACKET / 'recipe.json'
        original = Path.read_text
        def read(path, *args, **kwargs):
            return json.dumps(record) if path == manifest else original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            return verifier.verify()

    def record(self):
        return json.loads((verifier.PACKET / 'recipe.json').read_text())

    def test_exact_history_is_staged_without_current_recipe_or_sources(self):
        original = Path.read_bytes
        def read(path):
            if path.resolve().is_relative_to(verifier.ROOT):
                raise AssertionError('live source was read')
            return original(path)
        with patch.object(Path, 'read_bytes', read):
            result = self.run_record(self.record())
        self.assertEqual((result['source_inputs'], result['staged_workspace_inputs']), (68, 69))
        self.assertFalse(result['bytecode_identity_verified'])

    def test_corrupt_recipe_input_and_workspace_hashes_are_rejected(self):
        record = self.record()
        for kind in ('recipe', 'input', 'workspace'):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(record)
                if kind == 'recipe': changed['recipe_sha256'] = '0' * 64
                elif kind == 'input': changed['source_inputs'][next(iter(changed['source_inputs']))]['sha256'] = '0' * 64
                else: changed['staged_workspace_sha256'][next(iter(changed['staged_workspace_sha256']))] = '0' * 64
                with self.assertRaises(ValueError): self.run_record(changed)

    def test_revision_must_be_an_exact_commit_not_its_tree(self):
        record = self.record()
        tree = verifier.git('rev-parse', record['source_commit'] + '^{tree}').decode().strip()
        for revision in ('HEAD', record['source_commit'][:12], tree):
            with self.subTest(revision=revision):
                changed = copy.deepcopy(record); changed['source_commit'] = revision
                with self.assertRaises(ValueError): self.run_record(changed)


class AuditIntegrationTests(unittest.TestCase):
    def test_recipe_record_is_not_a_manifest_but_verifier_still_runs(self):
        spec = importlib.util.spec_from_file_location('recipe_revalidator', verifier.ROOT/'scripts/revalidate_all.py')
        revalidator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(revalidator)
        self.assertEqual(revalidator.check_manifest(verifier.PACKET), {'status': 'no_manifest', 'errors': []})
        result = revalidator.run_verify(verifier.PACKET)
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['returncode'], 0)
        self.assertIn('"bytecode_identity_verified": false', result['output'])
        self.assertIn('"source_inputs": 68', result['output'])


if __name__ == '__main__':
    unittest.main()
