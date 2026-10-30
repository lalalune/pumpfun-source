"""A failed reassembly must carry the build log that its discarded folder held."""
import contextlib
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sbpf_disassembly_roundtrip as tool

DIAGNOSTIC = b'error: unknown mnemonic on line 3'
CAPTURE = 'evidence/original/mayhem/deployed.so'


class RoundtripBuildLogTests(unittest.TestCase):
    def test_failed_build_reports_its_log(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        executable = root / 'tool/target/release/sbpf'
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'not executed by this test')
        inventory = root / 'inventory'
        inventory.mkdir()
        record = {'input': CAPTURE, 'instructions': [],
                  'input_sha256': hashlib.sha256((tool.ROOT / CAPTURE).read_bytes()).hexdigest()}
        compressed = gzip.compress(json.dumps(record).encode(), mtime=0)
        (inventory / 'mayhem.json.gz').write_bytes(compressed)
        manifest = {'tool_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
                    'tool_revision': 'fixture',
                    'programs': [{'name': 'mayhem',
                                  'inventory_sha256': hashlib.sha256(compressed).hexdigest()}]}
        (inventory / 'manifest.json').write_text(json.dumps(manifest))
        output = root / 'output'
        failed = subprocess.CompletedProcess([], 1, stdout=b'', stderr=DIAGNOSTIC)
        argv = ['roundtrip', '--tool-source', str(root / 'tool'),
                '--inventory', str(inventory), '--output', str(output)]
        with patch.object(sys, 'argv', argv), \
                patch.object(tool.subprocess, 'run', lambda *args, **kwargs: failed), \
                contextlib.redirect_stdout(io.StringIO()), \
                self.assertRaises(Exception) as caught:
            tool.main()
        self.assertFalse(output.exists())
        self.assertIn(DIAGNOSTIC.decode(), str(caught.exception))


if __name__ == '__main__':
    unittest.main()
