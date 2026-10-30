"""Round-trip command status must agree with its saved comparison result."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import sbpf_disassembly_roundtrip as tool


class RoundtripStatusTests(unittest.TestCase):
    def run_main(self, equalities):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / 'tool/target/release/sbpf'
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b'not executed by this orchestration test')
            inventory = root / 'inventory'
            inventory.mkdir()
            manifest = {'tool_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
                        'tool_revision': 'fixture', 'programs': list(equalities)}
            (inventory / 'manifest.json').write_text(json.dumps(manifest))
            output = root / 'output'
            def worker(_tool, _inventory, entry, _output):
                return {'name': entry, 'full_text_equality': equalities[entry]}
            argv = ['roundtrip', '--tool-source', str(root / 'tool'),
                    '--inventory', str(inventory), '--output', str(output)]
            with patch.object(sys, 'argv', argv), patch.object(tool, 'roundtrip', worker), \
                    contextlib.redirect_stdout(io.StringIO()):
                status = tool.main() or 0  # sys.exit(None) is success in the old CLI.
            return status, json.loads((output / 'report.json').read_text())

    def test_all_exact_returns_success(self):
        status, report = self.run_main({'one': True})
        self.assertEqual(status, 0)
        self.assertTrue(report['all_text_roundtrips_exact'])

    def test_mismatch_returns_failure_and_keeps_report(self):
        status, report = self.run_main({'one': True, 'two': False})
        self.assertEqual(status, 1)
        self.assertFalse(report['all_text_roundtrips_exact'])
        self.assertEqual(len(report['programs']), 2)

    def test_empty_inventory_is_not_a_successful_validation(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            self.run_main({})
        self.assertEqual(error.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
