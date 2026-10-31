"""A round-trip output name at the filesystem's component limit must not fail on its staging name."""
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sbpf_disassembly_roundtrip as tool


class RoundtripLongOutputTests(unittest.TestCase):
    def run_main(self, worker, name):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        executable = root / 'tool/target/release/sbpf'
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'not executed by this test')
        inventory = root / 'inventory'
        inventory.mkdir()
        manifest = {'tool_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
                    'tool_revision': 'fixture', 'programs': [{'name': 'one'}, {'name': 'two'}]}
        (inventory / 'manifest.json').write_text(json.dumps(manifest))
        output = root / 'out' / name
        argv = ['roundtrip', '--tool-source', str(root / 'tool'),
                '--inventory', str(inventory), '--output', str(output)]
        with mock.patch.object(sys, 'argv', argv), mock.patch.object(tool, 'roundtrip', worker), \
                contextlib.redirect_stdout(io.StringIO()):
            status = tool.main()
        return status, output

    def worker(self):
        def roundtrip(_tool, _inventory, entry, output):
            (output / entry['name']).mkdir()
            return {'name': entry['name'], 'full_text_equality': True}
        return roundtrip

    def test_output_name_at_the_component_limit_is_published(self):
        status, output = self.run_main(self.worker(), 'r' * 250)
        self.assertEqual(status, 0)
        self.assertEqual(sorted(p.name for p in output.iterdir()), ['one', 'report.json', 'two'])
        self.assertEqual([path.name for path in output.parent.iterdir()], [output.name])

    def test_short_output_name_keeps_the_readable_staging_prefix(self):
        status, output = self.run_main(self.worker(), 'roundtrip')
        self.assertEqual(status, 0)
        self.assertEqual(list(output.parent.glob('.roundtrip.*')), [])


if __name__ == '__main__':
    unittest.main()
