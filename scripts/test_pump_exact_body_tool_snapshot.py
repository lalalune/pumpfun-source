#!/usr/bin/env python3
"""The inventory receipt identifies the admitted executable used for symbols."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_exact_body_inventory as inventory


class ExactBodyToolSnapshotTests(unittest.TestCase):
    def test_report_keeps_used_tool_identity_after_source_replacement_or_deletion(self):
        for action in ('replace', 'delete'):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                tool = root / 'objdump'
                shutil.copy2(sys.executable, tool)
                expected = inventory.sha(tool.read_bytes())
                output = root / 'report.json'
                seen = []

                def symbols(path, executable, pattern, *, image):
                    snapshot = Path(executable)
                    self.assertNotEqual(snapshot, tool)
                    self.assertEqual(inventory.sha(snapshot.read_bytes()), expected)
                    seen.append(snapshot)
                    if action == 'replace':
                        tool.write_bytes(b'unused replacement')
                    else:
                        tool.unlink()
                    return []

                argv = ['pump_exact_body_inventory.py', '--candidate', str(inventory.ORIGINAL),
                        '--objdump', str(tool), '--output', str(output)]
                with mock.patch.object(sys, 'argv', argv), \
                        mock.patch.object(inventory, 'candidate_functions', symbols), \
                        contextlib.redirect_stdout(io.StringIO()):
                    inventory.main()
                self.assertEqual(json.loads(output.read_text())['objdump_sha256'], expected)
                self.assertTrue(seen)
                self.assertFalse(seen[0].exists())

    def test_private_tool_mutation_refuses_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tool = root / 'objdump'
            shutil.copy2(sys.executable, tool)
            expected = tool.read_bytes()
            output = root / 'report.json'

            def symbols(path, executable, pattern, *, image):
                snapshot = Path(executable)
                snapshot.chmod(0o755)
                snapshot.write_bytes(b'changed private executable')
                return []

            argv = ['pump_exact_body_inventory.py', '--candidate', str(inventory.ORIGINAL),
                    '--objdump', str(tool), '--output', str(output)]
            with mock.patch.object(sys, 'argv', argv), \
                    mock.patch.object(inventory, 'candidate_functions', symbols), \
                    self.assertRaisesRegex(ValueError, 'objdump snapshot changed'):
                inventory.main()
            self.assertFalse(output.exists())
            self.assertEqual(tool.read_bytes(), expected)

    @unittest.skipIf(sys.platform == 'win32', 'native symlink privilege is not assumed')
    def test_snapshot_preserves_llvm_library_lookup_and_resolves_tool_alias(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'bin').mkdir()
            (root / 'lib').mkdir()
            tool = root / 'bin/llvm-objdump'
            shutil.copy2(sys.executable, tool)
            alias = root / 'selected-objdump'
            alias.symlink_to(tool)
            with inventory.objdump_snapshot(alias) as (executable, digest):
                snapshot = Path(executable)
                self.assertEqual(snapshot.name, tool.name)
                self.assertEqual((snapshot.parent.parent / 'lib').resolve(), (root / 'lib').resolve())
                self.assertEqual(digest, inventory.sha(tool.read_bytes()))
            self.assertFalse(snapshot.exists())


if __name__ == '__main__':
    unittest.main()
