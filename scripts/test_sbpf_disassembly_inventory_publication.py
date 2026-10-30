"""A failed disassembly inventory must not leave a partial output directory."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sbpf_disassembly_inventory as tool


def fake_check_output(command, **kwargs):
    if command[-1] == 'HEAD':
        return 'fixture-revision\n'
    if command[-1] == '--version':
        return 'sbpf fixture\n'
    return b''  # clean `git status --porcelain`


class InventoryPublicationTests(unittest.TestCase):
    def run_main(self, inventory):
        directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        source = directory / 'tool'
        executable = source / 'target/release/sbpf'
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'not executed by this test')
        (source / 'Cargo.lock').write_text('')
        output = directory / 'inventory'
        argv = ['inventory', '--tool-source', str(source), '--output', str(output)]
        inputs = [('one', Path('one.so')), ('two', Path('two.so'))]
        with patch.object(sys, 'argv', argv), \
                patch.object(tool.subprocess, 'check_output', fake_check_output), \
                patch.object(tool, 'program_inputs', lambda root: inputs), \
                patch.object(tool, 'inventory', inventory), \
                patch.object(tool.Path, 'glob', lambda self, pattern: iter(())), \
                contextlib.redirect_stdout(io.StringIO()):
            try:
                tool.main()
            except ValueError:
                pass
        return output

    def test_failed_program_leaves_no_output_directory(self):
        def inventory(_tool, name, _path, output):
            (output / (name + '.json.gz')).write_bytes(b'partial')
            if name == 'two':
                raise ValueError('two: disassembler emitted diagnostics')
            return {'name': name}

        output = self.run_main(inventory)
        self.assertFalse(output.exists(), 'failed run left a partial inventory that blocks a rerun')

    def test_successful_run_publishes_manifest_and_programs(self):
        def inventory(_tool, name, _path, output):
            (output / (name + '.json.gz')).write_bytes(b'complete')
            return {'name': name}

        output = self.run_main(inventory)
        self.assertEqual(sorted(p.name for p in output.iterdir()),
                         ['manifest.json', 'one.json.gz', 'two.json.gz'])


if __name__ == '__main__':
    unittest.main()
