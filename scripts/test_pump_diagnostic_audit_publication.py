#!/usr/bin/env python3
"""Do not publish a diagnostic audit after its source report changes."""
import contextlib
import io
import hashlib
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_diagnostic_audit as gate  # noqa: E402


class DiagnosticAuditPublicationTests(unittest.TestCase):
    def fixture(self, root):
        report, output = root / 'report.json', root / 'audit.json'
        raw = json.dumps({'suites': {'case': [{
            'original': {'logs': ['before']},
            'candidate': {'logs': ['before']},
        }]}}).encode()
        report.write_bytes(raw)
        return report, output, raw

    def invoke_windows_branch(self, report, output, rename):
        # Exercise branch selection without changing the host's pathlib/os
        # platform. The injected operation models Windows no-replace rename;
        # native Windows filesystem atomicity is outside this POSIX test.
        windows = types.SimpleNamespace(name='nt', fsync=os.fsync, rename=rename,
                                        link=mock.Mock(side_effect=AssertionError('hard link used')))
        with mock.patch.object(gate, 'os', windows), \
                mock.patch.object(sys, 'argv', ['audit', '--report', str(report), '--output', str(output)]), \
                contextlib.redirect_stdout(io.StringIO()):
            result = gate.main()
        windows.link.assert_not_called()
        return result

    def test_windows_branch_publishes_without_hardlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, output, raw = self.fixture(Path(temporary))
            renamed = []
            def rename(source, destination):
                renamed.append((source, destination))
                os.rename(source, destination)
            self.assertFalse(self.invoke_windows_branch(report, output, rename))
            self.assertEqual(len(renamed), 1)
            self.assertEqual(json.loads(output.read_bytes())['log_bearing_cases'], 1)
            self.assertEqual(report.read_bytes(), raw)
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_windows_branch_preserves_late_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, output, raw = self.fixture(Path(temporary))
            def rename(source, destination):
                output.write_bytes(b'late complete receipt')
                raise FileExistsError(destination)
            with self.assertRaises(FileExistsError):
                self.invoke_windows_branch(report, output, rename)
            self.assertEqual(output.read_bytes(), b'late complete receipt')
            self.assertEqual(report.read_bytes(), raw)
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_windows_rename_failure_removes_only_own_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, output, raw = self.fixture(Path(temporary))
            with self.assertRaisesRegex(OSError, 'rename failed'):
                self.invoke_windows_branch(report, output,
                                           mock.Mock(side_effect=OSError('rename failed')))
            self.assertFalse(output.exists())
            self.assertEqual(report.read_bytes(), raw)
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_windows_success_does_not_delete_recreated_staging_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, output, raw = self.fixture(Path(temporary))
            recreated = []
            def rename(source, destination):
                os.rename(source, destination)
                source.write_bytes(b'late writer staging')
                recreated.append(source)
            self.assertFalse(self.invoke_windows_branch(report, output, rename))
            self.assertEqual(recreated[0].read_bytes(), b'late writer staging')
            self.assertEqual(report.read_bytes(), raw)

    def test_postpublication_source_change_does_not_delete_later_writer(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, output, _ = self.fixture(Path(temporary))
            def rename(source, destination):
                os.rename(source, destination)
                output.write_bytes(b'later writer receipt')
                report.write_bytes(b'changed after publication')
            with self.assertRaisesRegex(ValueError, 'source report changed during audit') as caught:
                self.invoke_windows_branch(report, output, rename)
            self.assertEqual(output.read_bytes(), b'later writer receipt')
            self.assertTrue(any('already published' in note for note in caught.exception.__notes__))

    def test_postpublication_source_change_retains_admitted_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, output, raw = self.fixture(Path(temporary))
            def rename(source, destination):
                os.rename(source, destination)
                report.write_bytes(b'changed after publication')
            with self.assertRaisesRegex(ValueError, 'source report changed during audit') as caught:
                self.invoke_windows_branch(report, output, rename)
            receipt = json.loads(output.read_bytes())
            self.assertEqual(receipt['source_report_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(receipt['log_bearing_cases'], 1)
            self.assertEqual(receipt['mismatches'], [])
            self.assertTrue(any('already published' in note for note in caught.exception.__notes__))
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    @unittest.skipIf(os.name == 'nt', 'POSIX hard-link publication path')
    def test_posix_postpublication_failure_preserves_concurrent_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, output, _ = self.fixture(Path(temporary))
            link = os.link
            def publish_then_replace(source, destination):
                link(source, destination)
                output.unlink()
                output.write_bytes(b'complete receipt from another writer')
                report.write_bytes(b'changed after publication')
            with mock.patch.object(gate.os, 'link', publish_then_replace), \
                    mock.patch.object(sys, 'argv', ['audit', '--report', str(report), '--output', str(output)]):
                with self.assertRaisesRegex(ValueError, 'source report changed during audit'):
                    gate.main()
            self.assertEqual(output.read_bytes(), b'complete receipt from another writer')
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_failed_staging_leaves_no_report_or_temporary_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "report.json"
            output = root / "audit.json"
            report.write_text(json.dumps({"suites": {"case": [{
                "original": {"logs": ["before"]},
                "candidate": {"logs": ["before"]},
            }]}}), encoding="utf-8")
            with mock.patch.object(gate.os, "fsync", side_effect=OSError("staging failed")), \
                    mock.patch.object(sys, "argv", ["pump_diagnostic_audit.py",
                        "--report", str(report), "--output", str(output)]):
                with self.assertRaisesRegex(OSError, "staging failed"):
                    gate.main()
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".audit.json.*")), [])

    def test_input_change_during_audit_leaves_no_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report_path = root / "report.json"
            output = root / "audit.json"

            def document(message):
                return {"suites": {"case": [{
                    "original": {"logs": [message]},
                    "candidate": {"logs": [message]},
                }]}}

            report_path.write_text(json.dumps(document("before")), encoding="utf-8")
            original_audit = gate.audit

            def mutate_during_audit(*args, **kwargs):
                result = original_audit(*args, **kwargs)
                report_path.write_text(
                    json.dumps(document("changed during audit")), encoding="utf-8")
                return result

            with mock.patch.object(gate, "audit", mutate_during_audit), \
                    mock.patch.object(sys, "argv", [
                        "pump_diagnostic_audit.py",
                        "--report", str(report_path),
                        "--output", str(output),
                    ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "source report changed during audit"):
                    gate.main()

            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".audit.json.*")), [])

    def test_bound_input_keys_are_posix_on_every_host(self):
        # The bound_* receipt keys used by the differentials and the parallel
        # driver used str(Path), which spells separators per host; identical
        # inputs then hashed to different key sets on Windows than on the
        # Linux CI.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nested = root / "evidence" / "original" / "pump" / "deployed.so"
            nested.parent.mkdir(parents=True)
            nested.write_bytes(b"elf")
            external = root / "external-candidate.so"
            external.write_bytes(b"cand")
            self.assertEqual(
                gate.bound_input_key(nested, root),
                "evidence/original/pump/deployed.so")
            self.assertEqual(
                gate.bound_input_key(external, Path(temporary) / "elsewhere"),
                external.resolve().as_posix())


if __name__ == "__main__":
    unittest.main()
