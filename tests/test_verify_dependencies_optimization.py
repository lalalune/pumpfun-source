#!/usr/bin/env python3
"""pump_verify_dependencies must fail closed when Python strips asserts.

Every acceptance check in scripts/pump_verify_dependencies.py is a bare
assert, so under ``python -O``/``-OO`` a tampered dependency registry is
still reported as verified: the on-chain/executable hash checks, the
fresh-build byte-equality checks and the image-digest checks all vanish,
and the script prints both "confirmed" lines and exits 0. The fix refuses
optimized interpreters up front, like scripts/pump_validate_all.py
already does.

The test materializes an isolated tree (the real repo root has no repro/
or evidence/ in a sparse checkout) with a valid registry plus both
fresh-build proofs, then runs the script three ways: normal Python
accepts the valid fixture and rejects the tampered one, and optimized
Python must refuse to run at all. On the unfixed script the optimized
runs exit 0 and print the confirmation lines for the tampered fixture,
which is the defect.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = "pump_verify_dependencies.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build_tree(root, tampered):
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(REPO / "scripts" / SCRIPT, scripts / SCRIPT)
    token = b"TOKEN-BYTES\x00\x00"
    token22_raw = b"TOKEN22-RAW"
    token22 = token22_raw + b"\x00" * 4
    for name, blob in (("spl_token", token), ("spl_token_2022", token22)):
        dep = root / "evidence" / "dependencies" / name
        dep.mkdir(parents=True)
        (dep / "deployed.so").write_bytes(blob)
    registry = {
        "results": {
            "spl_token": {
                "is_verified": True,
                "on_chain_hash": "0" * 64 if tampered else sha(token.rstrip(b"\0")),
                "executable_hash": sha(token.rstrip(b"\0")),
                "commit": "token-commit",
            },
            "spl_token_2022": {
                "is_verified": True,
                "on_chain_hash": sha(token22.rstrip(b"\0")),
                "executable_hash": sha(token22.rstrip(b"\0")),
                "commit": "token22-commit",
            },
        },
    }
    reg_dir = root / "repro" / "pump"
    reg_dir.mkdir(parents=True)
    (reg_dir / "dependency-verification-registry.json").write_text(
        json.dumps(registry)
    )
    spl = root / "repro" / "pump" / "verified-spl-token"
    spl.mkdir(parents=True)
    (spl / "pinocchio_token_program.so").write_bytes(token)
    (spl / "source-manifest.json").write_bytes(b"token manifest")
    (spl / "build.log").write_bytes(b"token build log")
    (spl / "comparison.json").write_text(
        json.dumps(
            {
                "candidate_sha256": sha(token),
                "original_sha256": sha(token),
                "full_byte_equality": True,
                "source_commit": "token-commit",
                "image": "token-image@sha256:abc",
                "source_manifest_sha256": sha(b"token manifest"),
                "build_log_sha256": sha(b"token build log"),
            }
        )
    )
    (spl / "image-inspect.json").write_text(
        json.dumps([{"RepoDigests": ["token-image@sha256:abc"]}])
    )
    t22 = root / "repro" / "pump" / "verified-token-2022"
    t22.mkdir(parents=True)
    (t22 / "spl_token_2022.so").write_bytes(token22_raw)
    (t22 / "rebuilt.deployed.so").write_bytes(token22)
    (t22 / "source-manifest.json").write_bytes(b"token22 manifest")
    (t22 / "build.log").write_bytes(b"token22 build log")
    (t22 / "comparison.json").write_text(
        json.dumps(
            {
                "candidate_input_sha256": sha(token22_raw),
                "candidate_sha256": sha(token22),
                "original_sha256": sha(token22),
                "full_byte_equality": True,
                "source_commit": "token22-commit",
                "image": "token22-image@sha256:def",
                "source_manifest_sha256": sha(b"token22 manifest"),
                "build_log_sha256": sha(b"token22 build log"),
                "zero_padding_bytes": 4,
            }
        )
    )
    (t22 / "image-inspect.json").write_text(
        json.dumps([{"RepoDigests": ["token22-image@sha256:def"]}])
    )
    return scripts / SCRIPT


def run(script, flags):
    return subprocess.run(
        [sys.executable, *flags, "-B", str(script)],
        capture_output=True,
        text=True,
        timeout=60,
    )


class VerifyDependenciesOptimizationTests(unittest.TestCase):
    def test_valid_fixture_passes_and_tampered_fails_in_all_modes(self):
        for tampered in (False, True):
            with tempfile.TemporaryDirectory() as tmp:
                script = build_tree(Path(tmp), tampered)
                for flags in ([], ["-O"], ["-OO"]):
                    with self.subTest(tampered=tampered, flags=flags):
                        result = run(script, flags)
                        if flags:
                            # The guard refuses optimized runs outright,
                            # valid fixture or not, and never prints a
                            # confirmation line.
                            self.assertNotEqual(
                                result.returncode,
                                0,
                                "optimized run accepted under %s:\n%s"
                                % (flags, result.stdout),
                            )
                            self.assertNotIn("confirmed", result.stdout)
                        elif tampered:
                            self.assertNotEqual(
                                result.returncode,
                                0,
                                "tampered registry accepted:\n%s" % result.stdout,
                            )
                            self.assertNotIn("confirmed", result.stdout)
                        else:
                            self.assertEqual(
                                result.returncode,
                                0,
                                "valid fixture rejected:\n%s%s"
                                % (result.stdout, result.stderr),
                            )


if __name__ == "__main__":
    unittest.main()
