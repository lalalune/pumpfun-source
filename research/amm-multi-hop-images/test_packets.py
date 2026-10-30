"""Run every multi-hop packet verifier against the retained images, without a home workspace."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent


def packets():
    return sorted(path.parent for path in RESEARCH.glob("amm-multi-hop-*/verify.py")
                  if path.parent != HERE)


class MultiHopPacketTests(unittest.TestCase):
    def run_verifier(self, path, home):
        return subprocess.run(
            [sys.executable, "-B", str(path)],
            cwd=home,
            env=dict(os.environ, HOME=home),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_retained_images_match_their_provenance(self):
        with tempfile.TemporaryDirectory(prefix="multi-hop-home-") as home:
            completed = self.run_verifier(HERE / "verify.py", home)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(completed.stdout.startswith("PASS:"), completed.stdout)

    def test_packets_do_not_read_the_home_directory(self):
        for packet in packets():
            for name in ("verify.py", "producer.py"):
                path = packet / name
                if path.exists():
                    with self.subTest(path=f"{packet.name}/{name}"):
                        self.assertNotIn("Path.home()", path.read_text(encoding="utf-8"))

    def test_every_packet_verifies_from_the_repository(self):
        found = packets()
        self.assertGreaterEqual(len(found), 103)
        with tempfile.TemporaryDirectory(prefix="multi-hop-home-") as home:
            for packet in found:
                with self.subTest(packet=packet.name):
                    completed = self.run_verifier(packet / "verify.py", home)
                    self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                    self.assertTrue(completed.stdout.startswith("PASS:"), completed.stdout)


if __name__ == "__main__":
    unittest.main()
