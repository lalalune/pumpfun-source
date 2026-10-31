"""--only must name paired windows; a typo must not publish an empty census."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('census_only', Path(__file__).with_name('census.py'))
census = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(census)


class FakeImage:
    def __init__(self, path, funcs):
        self.funcs, self.secs, self.blob = funcs, {}, b''

    def raw(self, start):
        return b''

    def calls(self, start):
        return []

    def external_counts(self, start):
        return {}

    def text(self, start):
        return {}


class CensusOnlyTests(unittest.TestCase):
    def run_census(self, only):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pairs = root / 'pairs.json'
            pairs.write_text(json.dumps({'0x10': 'paired$'}), encoding='utf-8')
            output = root / 'census.json'
            argv = ['census.py', '--cand', 'candidate.so', '--pairs', str(pairs),
                    '--only', only, '--json', str(output)]
            with patch.object(sys, 'argv', argv), \
                 patch.object(census, 'original_windows', return_value=[{'start': 0x10, 'bytes': 8}]), \
                 patch.object(census, 'candidate_functions', return_value=[(0x20, 8, 'paired')]), \
                 patch.object(census, 'Image', FakeImage), \
                 patch.object(census, 'normalize', return_value=b''), \
                 patch.object(census, 'ratio', return_value=1.0), \
                 patch.object(census, 'source_sites', return_value=[]), \
                 patch.object(census, 'demangle', side_effect=lambda name: name), \
                 contextlib.redirect_stderr(io.StringIO()) as errors:
                census.main()
            return json.loads(output.read_text(encoding='utf-8'))['targets'], errors

    def test_paired_window_is_reported(self):
        targets, _ = self.run_census('0x10')
        self.assertEqual([row['original'] for row in targets], ['0x10'])

    def test_unknown_or_malformed_windows_are_rejected(self):
        for only in ('0x11', '0x10,0x11', 'nonsense', '0x10,'):
            with self.subTest(only=only):
                with self.assertRaises(SystemExit) as caught:
                    self.run_census(only)
                self.assertEqual(caught.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
