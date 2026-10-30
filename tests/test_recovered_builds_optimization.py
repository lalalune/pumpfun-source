#!/usr/bin/env python3
"""verify_recovered_builds must fail closed when Python strips asserts.

Every acceptance check in scripts/verify_recovered_builds.py is a bare
assert, so under ``python -O``/``-OO`` a tampered provenance record is
still reported as consistent: the source-hash, comparison, build-log and
receipt checks all vanish. The fix refuses optimized interpreters up
front, like scripts/pump_validate_all.py already does.

The test materializes an isolated tree (the real repo root has no
repro/ or evidence/ in a sparse checkout) with a generic-path pump
entry, then runs the script three ways: normal Python accepts the valid
fixture and rejects the tampered one, and optimized Python must refuse
to run at all (the guard fires before any check). On the unfixed script
the two optimized runs exit 0 and print the "consistent" line for the
tampered fixture, which is the defect.
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
SCRIPT = "verify_recovered_builds.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build_tree(root, tampered):
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    for name in (SCRIPT, "compare.py", "analyze.py"):
        shutil.copy(REPO / "scripts" / name, scripts / name)
    generic = root / "repro" / "pump" / "generic"
    generic.mkdir(parents=True)
    original = b"ORIGINAL-BYTES"
    candidate = b"CANDIDATE-BYTES"
    (root / "evidence" / "original" / "pump").mkdir(parents=True)
    (root / "evidence" / "original" / "pump" / "deployed.so").write_bytes(original)
    (generic / "candidate.so").write_bytes(candidate)
    (generic / "source.txt").write_bytes(b"a source input")
    log = b"build log bytes\n"
    (generic / "build.log").write_bytes(log)
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        from compare import compare
    finally:
        sys.path.remove(str(REPO / "scripts"))
    report = {
        "source_sha256": {
            "repro/pump/generic/source.txt": (
                "0" * 64 if tampered else sha(b"a source input")
            ),
        },
        "comparison": compare(original, candidate),
        "build_log_sha256": sha(log),
    }
    (generic / "report.json").write_text(json.dumps(report))
    receipt = {
        "candidate_sha256": sha(candidate),
        "original_sha256": sha(original),
        "mismatches": [],
        "case_count": 1,
    }
    (generic / "receipt.json").write_text(json.dumps(receipt))
    status = {
        "pump": {
            "candidate_artifact": "repro/pump/generic/candidate.so",
            "comparison_report": "repro/pump/generic/report.json",
            "build_log": "repro/pump/generic/build.log",
            "validated_cases": 1,
            "validation_reports": ["repro/pump/generic/receipt.json"],
        },
    }
    (root / "repro" / "status.json").write_text(json.dumps(status))
    return scripts / SCRIPT


def run(script, flags):
    return subprocess.run(
        [sys.executable, *flags, "-B", str(script), "--program", "pump"],
        capture_output=True,
        text=True,
        timeout=60,
    )


class RecoveredBuildsOptimizationTests(unittest.TestCase):
    def test_valid_fixture_passes_and_tampered_fails_in_all_modes(self):
        for tampered in (False, True):
            with tempfile.TemporaryDirectory() as tmp:
                script = build_tree(Path(tmp), tampered)
                for flags in ([], ["-O"], ["-OO"]):
                    with self.subTest(tampered=tampered, flags=flags):
                        result = run(script, flags)
                        if flags:
                            # The guard refuses optimized runs outright,
                            # valid fixture or not, and never reports
                            # provenance as consistent.
                            self.assertNotEqual(
                                result.returncode,
                                0,
                                "optimized run accepted under %s:\n%s"
                                % (flags, result.stdout),
                            )
                            self.assertNotIn(
                                "provenance consistent", result.stdout
                            )
                        elif tampered:
                            self.assertNotEqual(
                                result.returncode,
                                0,
                                "tampered provenance accepted:\n%s" % result.stdout,
                            )
                            self.assertNotIn(
                                "provenance consistent", result.stdout
                            )
                        else:
                            self.assertEqual(
                                result.returncode,
                                0,
                                "valid fixture rejected:\n%s%s"
                                % (result.stdout, result.stderr),
                            )


if __name__ == "__main__":
    unittest.main()
