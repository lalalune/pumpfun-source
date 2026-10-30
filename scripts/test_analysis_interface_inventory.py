"""Exercise interface inventory generation using retained Mayhem/IDL bytes."""
import contextlib
import io
import json
import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

import analyze

REPOSITORY = pathlib.Path(__file__).resolve().parents[1]


class InterfaceInventoryEncodingTests(unittest.TestCase):
    def test_retained_interfaces_are_independent_of_default_text_encoding(self):
        original_read = pathlib.Path.read_text
        outputs = []
        for default_encoding in ('cp936', 'utf-8'):
            with self.subTest(default_encoding=default_encoding):
                with tempfile.TemporaryDirectory(prefix='pump-interface-') as temporary:
                    root = pathlib.Path(temporary)
                    self.assertEqual(root.resolve().parent, pathlib.Path(tempfile.gettempdir()).resolve())
                    self.assertTrue(root.name.startswith('pump-interface-'))
                    program = root / 'evidence/original/mayhem'
                    program.mkdir(parents=True)
                    shutil.copyfile(REPOSITORY / 'evidence/original/mayhem/deployed.so', program / 'deployed.so')
                    upstream = root / 'evidence/upstream'
                    upstream.mkdir(parents=True)
                    for source in (REPOSITORY / 'evidence/upstream').glob('pump*.json'):
                        shutil.copyfile(source, upstream / source.name)

                    def locale_read(path, encoding=None, errors=None):
                        return original_read(path, encoding=encoding or default_encoding, errors=errors)

                    with mock.patch.object(analyze, 'ROOT', root), mock.patch.object(pathlib.Path, 'read_text', locale_read), contextlib.redirect_stdout(io.StringIO()):
                        analyze.analyze()
                    output = (root / 'evidence/interface-inventory.json').read_bytes()
                    inventory = json.loads(output)
                    captured = json.loads((upstream / 'pump.json').read_bytes())
                    self.assertEqual(inventory['pump']['address'], captured['address'])
                    self.assertEqual(inventory['pump']['instructions'], len(captured['instructions']))
                    self.assertEqual(set(json.loads((root / 'evidence/binary-analysis.json').read_bytes())), {'mayhem'})
                    outputs.append(output)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == '__main__':
    unittest.main()
