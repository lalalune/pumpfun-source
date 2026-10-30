#!/usr/bin/env python3
"""Regression tests: the qualification audit must reject packet members
that are not regular files.

packet_snapshot() records every member's kind, but audit_packet() only
acted on the manifest entries (#2978) and the verifier (run_verifier's own
admission). A data member could be a symlink to content outside the packet
and the audit still passed: the member's identity record holds only the
link target's path, so the bytes the verifier actually read were not bound
by identity_sha256 — mutating the external file left the packet's identity
unchanged. Non-regular, non-directory members now fail the input check
before manifest hashing or verifier execution.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("qualification_audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build_packet(packet, external, linked):
    packet.mkdir(parents=True)
    (packet / "README.md").write_text("packet\n")
    manifest = {"README.md": sha(b"packet\n")}
    (packet / "verify.py").write_text(
        "from pathlib import Path\n"
        "assert Path(__file__).with_name('evidence.txt').read_text() == 'GOOD-EVIDENCE'\n"
        "print('packet verifier ok')\n"
    )
    if linked:
        (packet / "evidence.txt").symlink_to(external)
    else:
        (packet / "evidence.txt").write_text("GOOD-EVIDENCE")
        manifest["evidence.txt"] = sha(b"GOOD-EVIDENCE")
    (packet / "manifest.json").write_text(json.dumps(manifest) + "\n")


class NonFileMemberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = audit.load_frozen(ROOT)

    def audit_packet(self, packet):
        row, _ = audit.audit_packet(self.frozen, ROOT, packet, 10.0, 1.0)
        return row

    def test_symlinked_data_member_fails_the_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            external = root / "external-evidence.txt"
            external.write_text("GOOD-EVIDENCE")
            packet = root / "packet"
            build_packet(packet, external, linked=True)
            row = self.audit_packet(packet)
            self.assertEqual(row["overall"], "fail")
            self.assertEqual(row["input_check"]["status"], "fail")
            self.assertTrue(any("evidence.txt" in error
                                for error in row["input_check"]["errors"]))
            self.assertEqual(row["verify_check"]["status"], "skipped")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFOs")
    def test_fifo_member_fails_the_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            external = root / "external-evidence.txt"
            external.write_text("GOOD-EVIDENCE")
            packet = root / "packet"
            build_packet(packet, external, linked=False)
            os.mkfifo(packet / "blob.fifo")
            row = self.audit_packet(packet)
            self.assertEqual(row["overall"], "fail")
            self.assertEqual(row["input_check"]["status"], "fail")

    def run_cli(self, root, packet):
        (root / "scripts").mkdir(exist_ok=True)
        shutil.copyfile(ROOT / audit.FROZEN_SOURCE, root / audit.FROZEN_SOURCE)
        output = root / "audit-output"
        result = subprocess.run([sys.executable, "-B", str(HERE / "audit.py"),
            "--repo", str(root), "--output", str(output)],
            text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((output / "results.json").read_bytes())
        self.assertEqual(len(rows), 1)
        return rows[0]

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFOs")
    def test_declared_fifo_is_rejected_before_manifest_read_or_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            packet = root / "research/packet"
            build_packet(packet, root / "unused", linked=False)
            marker = root / "verifier-ran"
            (packet / "verify.py").write_text(
                "from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('ran')\n")
            evidence = packet / "evidence.txt"
            evidence.unlink()
            os.mkfifo(evidence)
            row = self.run_cli(root, packet)
            self.assertEqual(row["overall"], "fail")
            self.assertEqual(row["verify_check"]["status"], "skipped")
            self.assertIn("evidence.txt", str(row["input_check"]["errors"]))
            self.assertFalse(marker.exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFOs")
    def test_fifo_created_by_verifier_cannot_block_post_manifest_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            packet = root / "research/packet"
            build_packet(packet, root / "unused", linked=False)
            (packet / "verify.py").write_text(
                "import os\nfrom pathlib import Path\n"
                "p=Path(__file__).with_name('evidence.txt')\np.unlink()\nos.mkfifo(p)\n")
            row = self.run_cli(root, packet)
            self.assertEqual(row["overall"], "fail")
            self.assertEqual(row["verify_check"]["status"], "pass")
            self.assertEqual(row["input_check"]["status"], "packet_mutated")
            self.assertEqual(row["input_check"]["changed_paths"], ["evidence.txt"])
            self.assertIn("evidence.txt", str(row["manifest_check_after"]["errors"]))

    def test_invalid_unverified_packet_is_still_an_input_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            packet = root / "research/packet"
            packet.mkdir(parents=True)
            (packet / "linked").symlink_to(root / "missing")
            row = self.run_cli(root, packet)
            self.assertEqual(row["overall"], "fail")
            self.assertEqual(row["input_check"]["status"], "fail")

    def test_regular_cli_control_preserves_receipt_semantics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            packet = root / "research/packet"
            build_packet(packet, root / "unused", linked=False)
            row = self.run_cli(root, packet)
            self.assertEqual(row["overall"], "pass")
            self.assertEqual(row["verify_check"]["status"], "pass")
            self.assertEqual(row["manifest_check"]["status"], "pass")
            self.assertEqual(row["input_check"]["status"], "pass")

    def test_dangling_verifier_is_an_input_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            packet = root / "research/packet"
            packet.mkdir(parents=True)
            (packet / "verify.py").symlink_to(root / "missing.py")
            row = self.run_cli(root, packet)
            self.assertEqual(row["overall"], "fail")
            self.assertEqual(row["input_check"]["status"], "fail")
            self.assertEqual(row["verify_check"]["status"], "skipped")

    def test_regular_packet_still_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            external = root / "external-evidence.txt"
            external.write_text("GOOD-EVIDENCE")
            packet = root / "packet"
            build_packet(packet, external, linked=False)
            row = self.audit_packet(packet)
            self.assertEqual(row["overall"], "pass")


if __name__ == "__main__":
    unittest.main()
