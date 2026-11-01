#!/usr/bin/env python3
"""Regression witness: a saved baseline cannot prove current-main preservation."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


SUBJECT = Path(__file__).with_name("integrate.py")


def crate(root: Path, value: int) -> Path:
    (root / "src").mkdir(parents=True)
    (root / "Cargo.toml").write_text(
        '[package]\nname="synthetic"\nversion="0.0.0"\n\n[profile.release]\nopt-level=3\n\n[workspace]\n',
        encoding="utf-8",
    )
    (root / "Cargo.lock").write_text("version = 3\n", encoding="utf-8")
    (root / "src/lib.rs").write_text(f"pub fn value() -> u64 {{ {value} }}\n", encoding="utf-8")
    return root


class HistoricalBaselineGapTests(unittest.TestCase):
    def load_subject(self):
        spec = importlib.util.spec_from_file_location("fresh_regression_integrate", SUBJECT)
        module = importlib.util.module_from_spec(spec)
        original_path = sys.path[:]
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path[:] = original_path
        return module

    def test_historical_mode_cannot_see_a_match_added_on_current_base(self):
        module = self.load_subject()
        with tempfile.TemporaryDirectory(prefix="fresh-integration-regression-") as temporary:
            root = Path(temporary)
            base = crate(root / "base", 2)
            derived = crate(root / "derived", 1)
            part = crate(root / "part", 3)
            module.SC = root / "reconstruction"
            module.H = module.SC / "harness"
            baseline = module.SC / "pump-main/baseline/score.json"
            baseline.parent.mkdir(parents=True)
            # The historical baseline predates a current-main match at 0x100.
            baseline.write_text(
                json.dumps({"windows": {"256": {"bytes": 8, "normalized": False, "raw": False}}}),
                encoding="utf-8",
            )
            (module.H / "score.py").parent.mkdir(parents=True, exist_ok=True)
            (module.H / "score.py").write_text("# synthetic scorer\n", encoding="utf-8")

            builds = []

            def build(source, work, output, **kwargs):
                builds.append(Path(source))
                output.mkdir(parents=True, exist_ok=True)
                artifact = output / "unstripped.so"
                artifact.write_bytes(b"candidate loses current-main window 0x100")
                return {
                    "ok": True,
                    "runtime_valid": True,
                    "stack_warnings": [],
                    "unstripped_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                }

            historical_summary = {
                "candidate_sha256": hashlib.sha256(b"candidate loses current-main window 0x100").hexdigest(),
                "normalized": 0,
                "raw": 0,
                "total": 1,
                "matched_text_bytes": 0,
                "gains": [],
                "losses": [],
                "raw_gains": [],
                "raw_losses": [],
            }

            def scorer(argv, **kwargs):
                return types.SimpleNamespace(returncode=0, stdout=json.dumps(historical_summary), stderr="")

            argv = [
                "integrate.py",
                "--name",
                "historical-gap",
                "--base-src",
                str(base),
                "--part",
                "stale=" + str(part),
                "--base-of",
                "stale=" + str(derived),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module, "build_source", Mock(side_effect=build)),
                patch.object(module, "scoring_subprocess", side_effect=scorer),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                code = module.main()

            report = json.loads((module.SC / "integ/historical-gap/report.json").read_text())
            self.assertEqual(code, 0)
            self.assertEqual(len(builds), 1, "historical mode never builds its supplied base source")
            self.assertEqual(report["score"]["losses"], [])
            self.assertEqual(report["score"]["raw_losses"], [])
            self.assertNotIn("fresh_control", report)
            # Ground truth represented by the fixture: current base matched the
            # window, while the composed candidate did not. Historical mode has
            # no observation capable of reporting this loss.
            current_observation = {
                "base": {"0x100": {"normalized": True, "raw": True}},
                "candidate": {"0x100": {"normalized": False, "raw": False}},
            }
            self.assertTrue(current_observation["base"]["0x100"]["normalized"])
            self.assertFalse(current_observation["candidate"]["0x100"]["normalized"])


if __name__ == "__main__":
    unittest.main()
