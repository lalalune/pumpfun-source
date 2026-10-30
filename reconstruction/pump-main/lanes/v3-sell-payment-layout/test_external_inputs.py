"""Exercise historical input admission with real Git objects."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import verify


class HistoricalInputsTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((verify.HERE / 'manifest.json').read_text())
        self.git_dir = subprocess.check_output(
            ['git', '-C', str(verify.ROOT), 'rev-parse', '--absolute-git-dir'],
            text=True).strip()

    def test_real_blobs_need_no_working_tree_inputs(self):
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(verify, 'ROOT', Path(temporary)), \
                patch.dict(os.environ, {'GIT_DIR': self.git_dir}):
            blobs = verify.external_inputs(self.manifest)
        self.assertEqual(set(blobs), set(self.manifest['external']))
        for name, data in blobs.items():
            self.assertEqual(verify.digest(data), self.manifest['external'][name])

    def test_revision_must_be_a_full_commit_object(self):
        revision = self.manifest['externalRevision']
        tree = subprocess.check_output(
            ['git', '-C', str(verify.ROOT), 'rev-parse', revision + '^{tree}'],
            text=True).strip()
        for value in (revision[:12], tree, '0' * 40):
            with self.subTest(revision=value):
                changed = copy.deepcopy(self.manifest)
                changed['externalRevision'] = value
                with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                    verify.external_inputs(changed)

    def test_recorded_digest_is_still_required(self):
        changed = copy.deepcopy(self.manifest)
        name = 'reconstruction/base/functions.tsv'
        changed['external'][name] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'external hash:'):
            verify.external_inputs(changed)


if __name__ == '__main__':
    unittest.main()
