import hashlib, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
import audit
ROOT = Path(__file__).resolve().parents[3]


def seal(packet):
    manifest = {
        name: hashlib.sha256((packet / name).read_bytes()).hexdigest()
        for name in sorted(path.name for path in packet.iterdir() if path.is_file())
    }
    (packet / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


class PacketIdentityStabilityTests(unittest.TestCase):
    def exercise(self, mutation):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "scripts").mkdir()
            shutil.copyfile(ROOT / audit.FROZEN_SOURCE, root / audit.FROZEN_SOURCE)
            first = root / "research/a-packet"
            first.mkdir(parents=True)
            (first / "artifact.txt").write_bytes(b"original")
            (first / "verify.py").write_bytes(b"print('a stable')\n")
            seal(first)
            last = root / "research/z-packet"
            last.mkdir(parents=True)
            if mutation == "swap":
                script = (
                    b"from pathlib import Path\n"
                    b"Path('../a-packet/artifact.txt').write_bytes(b'tampered')\n"
                )
            else:
                script = b"print('z stable')\n"
            (last / "verify.py").write_bytes(script)
            seal(last)
            output = root / "audit"
            result = subprocess.run(
                [sys.executable, "-B", str(Path(audit.__file__)),
                 "--repo", str(root), "--output", str(output)],
                capture_output=True, timeout=30)
            if mutation == "swap":
                self.assertEqual((first / "artifact.txt").read_bytes(), b"tampered")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(b"identity changed", result.stderr)
                self.assertFalse(output.exists())
            else:
                self.assertEqual(result.returncode, 0, result.stderr)
                census = json.loads(
                    (output / "provenance.json").read_text()
                )["packet_census"]
                self.assertEqual(census, ["a-packet", "z-packet"])

    def test_packet_swapped_after_its_audit_cannot_publish(self):
        self.exercise("swap")

    def test_stable_identities_still_publish(self):
        self.exercise("stable")


if __name__ == "__main__":
    unittest.main()
