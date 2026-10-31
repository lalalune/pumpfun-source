#!/usr/bin/env python3
"""A data-order certificate is published complete and never replaces an output.

The CLI refuses an existing output, so a partial write left by a failed run
blocked every retry with that path, and an output created during derivation
was silently overwritten.
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import pump_data_order  # noqa: E402


def arguments(root, output):
    return [str(Path(pump_data_order.__file__)),
            "--baseline-build", str(root / "build"),
            "--text-section-order", str(root / "order.ld"),
            "--output", str(output)]


class DataOrderPublicationTests(unittest.TestCase):
    def test_complete_certificate_is_published_without_staging_residue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "certificate.json"
            payload = {"roles": ["role"]}
            with mock.patch.object(sys, "argv", arguments(root, output)), \
                    mock.patch.object(pump_data_order, "derive_payload", return_value=payload), \
                    contextlib.redirect_stdout(io.StringIO()):
                pump_data_order.main()
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                             {"schema": 1, "payload": payload})
            self.assertEqual([path.name for path in root.iterdir()], [output.name])

    def test_output_created_during_derivation_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "certificate.json"
            prior = b"prior evidence\n"

            def derive(*_):
                output.write_bytes(prior)
                return {"roles": []}

            with mock.patch.object(sys, "argv", arguments(root, output)), \
                    mock.patch.object(pump_data_order, "derive_payload", derive):
                with self.assertRaises(FileExistsError):
                    pump_data_order.main()
            self.assertEqual(output.read_bytes(), prior)
            self.assertEqual([path.name for path in root.iterdir()], [output.name])

    def test_module_runs_its_cli_when_invoked_as_a_script(self):
        # Every other test calls main() directly, so none exercise the real
        # `python scripts/pump_data_order.py ...` entrypoint. Without the
        # `if __name__ == "__main__"` guard the script is a silent no-op:
        # argparse never runs, a missing required --output goes unreported, and
        # no certificate is ever published. Invoking it with no arguments must
        # reach argparse and fail with its usage error (exit 2).
        completed = subprocess.run(
            [sys.executable, "-B", str(Path(pump_data_order.__file__))],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertIn("usage", completed.stderr.lower())
        self.assertIn("--baseline-build", completed.stderr)

    @unittest.skipUnless(os.name == "posix", "RLIMIT_FSIZE requires POSIX")
    def test_failed_write_leaves_the_output_path_free_for_a_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "certificate.json"
            program = textwrap.dedent(f"""
                import resource
                import signal
                import sys
                from unittest import mock
                sys.path.insert(0, {str(SCRIPTS)!r})
                import pump_data_order
                payload = {{"roles": [], "filler": "x" * 200000}}
                resource.setrlimit(resource.RLIMIT_FSIZE, (4096, 4096))
                signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
                sys.argv = {arguments(root, output)!r}
                with mock.patch.object(pump_data_order, "derive_payload", return_value=payload):
                    pump_data_order.main()
            """)

            completed = subprocess.run(
                [sys.executable, "-B", "-c", program],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("File too large", completed.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
