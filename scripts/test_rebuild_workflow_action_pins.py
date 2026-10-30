#!/usr/bin/env python3
"""The byte-exact rebuild workflows pin every action by commit SHA.

rebuild-canonical-mayhem*.yml pin checkout and upload-artifact by SHA because
a tag move would mutate what the byte-exact rebuild path executes; setup-python
was the one remaining mutable tag in those files.
"""
import re
import unittest
from pathlib import Path


WORKFLOWS = Path(__file__).resolve().parents[1] / '.github/workflows'
FAMILY = sorted(WORKFLOWS.glob('rebuild-canonical-mayhem*.yml'))
MUTABLE = re.compile(r'uses:\s*\S+@v\d+\s*$')


class RebuildWorkflowActionPins(unittest.TestCase):
    def test_family_is_present(self):
        self.assertGreaterEqual(len(FAMILY), 4)

    def test_every_action_reference_is_sha_pinned(self):
        for path in FAMILY:
            with self.subTest(workflow=path.name):
                for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                    if line.lstrip().startswith('- uses:') or line.lstrip().startswith('uses:'):
                        self.assertIsNone(
                            MUTABLE.match(line),
                            f'{path.name}:{number}: mutable action tag: {line.strip()}')
                        self.assertRegex(line.strip(), r'@([0-9a-f]{40}|[0-9a-f]{32})($| #)',
                                         f'{path.name}:{number}: not SHA-pinned: {line.strip()}')


if __name__ == '__main__':
    unittest.main()
