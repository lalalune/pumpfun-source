#!/usr/bin/env python3
"""A packet whose manifest is a symlink must not audit as a pass.

The adapter's packet snapshot already records the manifest entry's kind;
a linked manifest pointing outside the packet and declaring only a subset
of its files must fail the manifest checks instead of passing on the
strength of the external declaration.
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().with_name("audit.py")
SPEC = importlib.util.spec_from_file_location(
    "revalidation_qualification_audit", MODULE_PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)

SOURCE_REPO = Path(__file__).resolve().parents[3]


class AuditManifestLinkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / "scripts").mkdir()
        (self.root / "research").mkdir()
        (self.root / "scripts/revalidate_all.py").write_bytes(
            (SOURCE_REPO / audit.FROZEN_SOURCE).read_bytes()
        )
        self.packet = self.root / "research" / "packet"
        self.packet.mkdir()
        (self.packet / "artifact.txt").write_bytes(b"declared bytes\n")
        (self.packet / "undeclared.txt").write_bytes(b"never hashed\n")
        self.subset = json.dumps({
            "artifact.txt": hashlib.sha256(b"declared bytes\n").hexdigest()
        })

    def run_adapter(self):
        output = self.root / "audit-output"
        run = subprocess.run(
            [sys.executable, "-B", str(Path(audit.__file__)),
             "--repo", str(self.root), "--output", str(output)],
            cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = json.loads((output / "results.json").read_text())
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_regular_subset_manifest_passes(self):
        (self.packet / "manifest.json").write_text(self.subset)
        row = self.run_adapter()
        self.assertEqual(row["overall"], "pass", row)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO control')
    def test_verifier_replacing_manifest_with_fifo_cannot_block_postcheck(self):
        (self.packet / 'manifest.json').write_text(self.subset)
        (self.packet / 'verify.py').write_text('import os\nfrom pathlib import Path\np=Path(__file__).with_name("manifest.json")\np.unlink()\nos.mkfifo(p)\n')
        row = self.run_adapter()
        self.assertEqual(row['manifest_check']['status'], 'pass')
        self.assertEqual(row['manifest_check_after']['status'], 'fail')
        self.assertNotEqual(row['overall'], 'pass')

    def test_symlinked_manifest_fails_the_audit(self):
        external = self.root / "external-manifest.json"
        external.write_text(self.subset)
        (self.packet / "manifest.json").symlink_to(external)
        row = self.run_adapter()
        self.assertEqual(row["manifest_check"]["status"], "fail", row)
        self.assertEqual(row["overall"], "fail", row)


if __name__ == "__main__":
    unittest.main(verbosity=2)
