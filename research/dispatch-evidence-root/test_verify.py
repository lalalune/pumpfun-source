"""Validate the landed transition against real history and corrupt receipts."""
import contextlib
import copy
import io
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'transition.json'
RECORD = json.loads(MANIFEST.read_text())


class LandedTransitionTests(unittest.TestCase):
    def run_record(self, record):
        original = Path.read_text
        def read(path, *args, **kwargs):
            if path.resolve() == MANIFEST:
                return json.dumps(record)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read), contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(HERE / 'verify.py'), run_name='__main__')

    def test_landed_history_does_not_read_current_source_bytes(self):
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('working source read')):
            self.run_record(RECORD)

    def test_corrupt_receipt_fields_are_rejected(self):
        cases = [('before hash', lambda r: r['asset'].update(beforeSha256='0' * 64)),
                 ('after hash', lambda r: r['asset'].update(afterSha256='0' * 64)),
                 ('script count', lambda r: r['directPythonScriptSet'].update(count=0)),
                 ('script digest', lambda r: r['directPythonScriptSet'].update(sha256='0' * 64)),
                 ('capture', lambda r: r['unchangedCaptures'].update({next(iter(r['unchangedCaptures'])): '0' * 64})),
                 ('wrong landed commit', lambda r: r.update(landedRevision=r['baseRevision']))]
        for name, change in cases:
            with self.subTest(name=name):
                record = copy.deepcopy(RECORD); change(record)
                with self.assertRaises(SystemExit): self.run_record(record)

    def test_symbolic_or_abbreviated_revisions_are_rejected(self):
        for field in ('baseRevision', 'landedRevision'):
            for value in ('HEAD', RECORD[field][:12]):
                with self.subTest(field=field, value=value):
                    record = copy.deepcopy(RECORD); record[field] = value
                    with self.assertRaises(SystemExit): self.run_record(record)


if __name__ == '__main__':
    unittest.main()
