"""The first toggle must preserve unrelated config fields too."""
import collections
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = "research/amm-multi-hop-split-boost-tf-mode-toggle-five-hop-chains-20261029"
CONFIG = "ADyA8hdefvWN2dbGGWFotbzWxrAvLW83WG6QCVXvJKqw"


class ToggleRoundtripBaselineTests(unittest.TestCase):
    def test_unrelated_config_drift_is_rejected_at_every_boundary(self):
        # Rebind recorded snapshots and summaries together, so rejection must
        # come from the round-trip property rather than a digest mismatch.
        for start in (None, 0, 1, 2, 3, 4, 5):
            with self.subTest(first_changed_step=start), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                packet = root / PACKET
                shutil.copytree(ROOT / PACKET, packet)
                for relative in ("scripts", "evidence/upstream", "research/imported-lab/analysis/pump_fun"):
                    shutil.copytree(ROOT / relative, root / relative)
                for relative in ("evidence/original/pump_amm/deployed.so",
                                 "research/amm-multi-hop-images/control.so.gz",
                                 "research/amm-multi-hop-images/candidate.so.gz"):
                    target = root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / relative, target)
                if start is not None:
                    self.mutate(packet, start)
                result = subprocess.run([sys.executable, "-I", "-B", str(packet / "verify.py")],
                                        cwd=root, capture_output=True, text=True, timeout=120)
                output = result.stdout + result.stderr
                if start is None:
                    self.assertEqual(result.returncode, 0, output)
                    self.assertIn("PASS:", result.stdout)
                else:
                    self.assertNotEqual(result.returncode, 0, output)
                    self.assertIn("moves no other config field", output)
                    self.assertNotIn("PASS:", result.stdout)

    @staticmethod
    def mutate(packet, start):
        report_path = packet / "runtime/report.json.gz"
        report = json.loads(gzip.decompress(report_path.read_bytes()))
        sequence = collections.Counter()
        for part in report["parts"]:
            path = packet / part["file"]
            records = [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
            changed = False
            for record in records:
                if record["case"] != "T-all-roundtrip":
                    continue
                index = sequence[record["image"]]
                sequence[record["image"]] += 1
                for surface in ("before", "after"):
                    if index >= start + (surface == "before"):
                        raw = bytearray.fromhex(record[surface][CONFIG]["data_hex"])
                        raw[899:907] = (5001).to_bytes(8, "little")
                        record[surface][CONFIG]["data_hex"] = raw.hex()
                        changed = True
            if changed:
                data = gzip.compress(b"".join(json.dumps(record, separators=(",", ":")).encode() + b"\n"
                                              for record in records), mtime=0)
                path.write_bytes(data)
                part["sha256"], part["bytes"] = hashlib.sha256(data).hexdigest(), len(data)
        if sequence != {"original": 6, "control": 6, "candidate": 6}:
            raise AssertionError(f"unexpected round-trip receipt groups: {sequence}")
        case = next(case for case in report["cases"] if case["label"] == "T-all-roundtrip")
        for summaries in case["summaries"].values():
            for index in range(start, len(summaries)):
                summaries[index]["cfg"]["bps"] = 5001
        report_path.write_bytes(gzip.compress(json.dumps(report, separators=(",", ":")).encode(), mtime=0))
        manifest_path = packet / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text())
        for entry in manifest["files"]:
            data = (packet / entry["path"]).read_bytes()
            entry["sha256"], entry["bytes"] = hashlib.sha256(data).hexdigest(), len(data)
        manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")


if __name__ == "__main__":
    unittest.main()
