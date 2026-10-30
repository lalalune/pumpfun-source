"""A round-trip run that raises must not leave a partial output directory."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sbpf_disassembly_roundtrip as tool


class RoundtripPublicationTests(unittest.TestCase):
    def run_main(self, worker):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        executable = root / 'tool/target/release/sbpf'
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'not executed by this test')
        inventory = root / 'inventory'
        inventory.mkdir()
        manifest = {'tool_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
                    'tool_revision': 'fixture', 'programs': [{'name': 'one'}, {'name': 'two'}]}
        (inventory / 'manifest.json').write_text(json.dumps(manifest))
        output = root / 'output'
        argv = ['roundtrip', '--tool-source', str(root / 'tool'),
                '--inventory', str(inventory), '--output', str(output)]
        with patch.object(sys, 'argv', argv), patch.object(tool, 'roundtrip', worker), \
                contextlib.redirect_stdout(io.StringIO()):
            try:
                status = tool.main()
            except ValueError:
                status = None
        return status, output

    def test_failed_program_leaves_no_output_directory(self):
        def worker(_tool, _inventory, entry, output):
            (output / entry['name']).mkdir()
            if entry['name'] == 'two':
                raise ValueError('inventory hash mismatch')
            return {'name': entry['name'], 'full_text_equality': True}

        status, output = self.run_main(worker)
        self.assertIsNone(status)
        self.assertFalse(output.exists(), 'failed run left a partial round-trip directory that blocks a rerun')

    def test_completed_run_publishes_report_and_program_folders(self):
        def worker(_tool, _inventory, entry, output):
            (output / entry['name']).mkdir()
            return {'name': entry['name'], 'full_text_equality': True}

        status, output = self.run_main(worker)
        self.assertEqual(status, 0)
        self.assertEqual(sorted(p.name for p in output.iterdir()), ['one', 'report.json', 'two'])


if __name__ == '__main__':
    unittest.main()
