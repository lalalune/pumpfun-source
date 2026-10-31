"""An output name at the filesystem's component limit must not fail on its staging name."""
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
import sbpf_disassembly_inventory as tool


class InventoryLongOutputTests(unittest.TestCase):
    def run_main(self, inventory, name):
        directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        source = directory / 'tool'
        executable = source / 'target/release/sbpf'
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'not executed by this test')
        (source / 'Cargo.lock').write_text('')
        output = directory / 'out' / name
        argv = ['inventory', '--tool-source', str(source), '--output', str(output)]
        inputs = [('one', Path('one.so'))]

        def fake_check_output(command, **kwargs):
            if command[-1] == 'HEAD':
                return 'fixture-revision\n'
            if command[-1] == '--version':
                return 'sbpf fixture\n'
            return b''

        with mock.patch.object(sys, 'argv', argv), \
                mock.patch.object(tool.subprocess, 'check_output', fake_check_output), \
                mock.patch.object(tool, 'program_inputs', lambda root: inputs), \
                mock.patch.object(tool, 'inventory', inventory), \
                mock.patch.object(tool.Path, 'glob', lambda self, pattern: iter(())), \
                contextlib.redirect_stdout(io.StringIO()):
            tool.main()
        return output

    def test_output_name_at_the_component_limit_is_published(self):
        def inventory(_tool, name, _path, output):
            (output / (name + '.json.gz')).write_bytes(b'complete')
            return {'name': name}

        output = self.run_main(inventory, 'i' * 250)
        self.assertEqual(sorted(p.name for p in output.iterdir()), ['manifest.json', 'one.json.gz'])
        self.assertEqual([path.name for path in output.parent.iterdir()], [output.name])

    def test_short_output_name_keeps_the_readable_staging_prefix(self):
        def inventory(_tool, name, _path, output):
            (output / (name + '.json.gz')).write_bytes(b'complete')
            return {'name': name}

        output = self.run_main(inventory, 'inventory')
        self.assertEqual(list(output.parent.glob('.inventory.*')), [])


if __name__ == '__main__':
    unittest.main()
