#!/usr/bin/env python3
"""Real-process and filesystem regressions for the qualified audit adapter."""

import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().with_name("audit.py")
SPEC = importlib.util.spec_from_file_location("revalidation_qualification_audit", MODULE_PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


SOURCE_REPO = Path(__file__).resolve().parents[3]


def pid_exists(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def wait_pid_gone(pid, seconds=2.0):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not pid_exists(pid):
            return True
        time.sleep(0.02)
    return not pid_exists(pid)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="window-p-audit-")
        self.addCleanup(self.temporary.cleanup)
        # macOS exposes /var as a system symlink; use its canonical temporary
        # root so output-link tests exercise task-owned components only.
        self.root = Path(self.temporary.name).resolve()
        (self.root / "scripts").mkdir()
        (self.root / "research").mkdir()
        (self.root / "scripts/revalidate_all.py").write_bytes(
            (SOURCE_REPO / audit.FROZEN_SOURCE).read_bytes()
        )

    def packet(self, name="packet", verifier=None):
        packet = self.root / "research" / name
        packet.mkdir()
        artifact = packet / "artifact.txt"
        artifact.write_bytes("ordinary CRLF\r\n雪\r\n".encode())
        if verifier is not None:
            (packet / "verify.py").write_text(verifier, encoding="utf-8")
        return packet

    def seal(self, packet, names=None):
        names = names or [path.name for path in packet.iterdir() if path.is_file()]
        manifest = {
            name: hashlib.sha256((packet / name).read_bytes()).hexdigest()
            for name in names
        }
        (packet / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return manifest

    def run_adapter(self, output, *extra, optimized=False, timeout=10):
        command = [sys.executable]
        if optimized:
            command.append("-O")
        command += ["-B", str(Path(audit.__file__)), "--repo", str(self.root),
                    "--output", str(output), *map(str, extra)]
        return subprocess.run(command, cwd=self.root, capture_output=True,
                              text=True, timeout=timeout)

    def run_frozen(self, output, timeout=10):
        return subprocess.run(
            [sys.executable, "-B", str(self.root / audit.FROZEN_SOURCE),
             "--output", str(output)],
            cwd=self.root, capture_output=True, text=True, timeout=timeout,
        )

    def test_frozen_baseline_passes_after_bound_input_mutation(self):
        packet = self.packet(verifier=(
            "from pathlib import Path\n"
            "Path('artifact.txt').write_bytes(b'mutated\\n')\n"
        ))
        manifest = self.seal(packet)
        output = self.root / "old-audit"
        result = self.run_frozen(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        row = json.loads((output / "results.json").read_text())[0]
        self.assertEqual((row["manifest_check"]["status"],
                          row["verify_check"]["status"], row["overall"]),
                         ("pass", "pass", "pass"))
        self.assertNotEqual(hashlib.sha256((packet / "artifact.txt").read_bytes()).hexdigest(),
                            manifest["artifact.txt"])

    def test_adapter_fails_mutating_verifier_and_binds_pre_post_inputs(self):
        packet = self.packet(verifier=(
            "from pathlib import Path\n"
            "Path('artifact.txt').write_bytes(b'mutated\\n')\n"
        ))
        self.seal(packet)
        output = self.root / "new-audit"
        result = self.run_adapter(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        row = json.loads((output / "results.json").read_text())[0]
        self.assertEqual(row["verify_check"]["status"], "pass")
        self.assertEqual(row["manifest_check"]["status"], "pass")
        self.assertEqual(row["manifest_check_after"]["status"], "fail")
        self.assertEqual(row["input_check"]["status"], "packet_mutated")
        self.assertEqual(row["input_check"]["changed_paths"], ["artifact.txt"])
        self.assertEqual(row["overall"], "fail")
        inputs = json.loads((output / "inputs.json").read_text())["packet"]
        self.assertNotEqual(inputs["before"]["identity_sha256"],
                            inputs["after"]["identity_sha256"])

    def test_empty_directory_mutation_is_part_of_packet_identity(self):
        packet = self.packet(verifier=(
            "from pathlib import Path\n"
            "Path('created-empty-directory').mkdir()\n"
        ))
        self.seal(packet)
        output = self.root / "new-audit"
        result = self.run_adapter(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        row = json.loads((output / "results.json").read_text())[0]
        self.assertEqual(row["input_check"]["status"], "packet_mutated")
        self.assertEqual(row["input_check"]["changed_paths"],
                         ["created-empty-directory"])
        self.assertEqual(row["overall"], "fail")

    def test_verifier_cannot_modify_bound_audit_source_and_publish(self):
        source = self.root / audit.FROZEN_SOURCE
        packet = self.packet(verifier=(
            "from pathlib import Path\n"
            f"Path({str(source)!r}).write_text('changed during audit\\n')\n"
        ))
        self.seal(packet)
        output = self.root / "new-audit"
        result = self.run_adapter(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("audit implementation changed during verification", result.stderr)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".new-audit.staging-*")), [])
        self.assertFalse((self.root / ".new-audit.revalidation.lock").exists())

    def test_valid_publication_is_complete_self_verifying_and_optimized_safe(self):
        packet = self.packet(verifier="print('verified ordinary bytes')\n")
        original = {path.name: path.read_bytes() for path in packet.iterdir()}
        self.seal(packet)
        original["manifest.json"] = (packet / "manifest.json").read_bytes()
        output = self.root / "missing" / "parents" / "audit"
        result = self.run_adapter(output, optimized=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            sorted(path.name for path in output.iterdir()),
            sorted((*audit.REPORT_MEMBERS, "manifest.json")),
        )
        verify = subprocess.run([sys.executable, "-B", str(output / "verify.py")],
                                capture_output=True, text=True)
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
        self.assertEqual({path.name: path.read_bytes() for path in packet.iterdir()}, original)
        provenance = json.loads((output / "provenance.json").read_text())
        self.assertEqual(provenance["reviewed_source"]["sha256"], audit.FROZEN_SHA256)
        self.assertEqual(provenance["tool_version"], audit.VERSION)
        self.assertEqual(provenance["packet_census"], ["packet"])
        self.assertEqual(provenance["control_inputs_before"],
                         provenance["control_inputs_after"])
        row = json.loads((output / "results.json").read_text())[0]
        self.assertEqual(row["overall"], "pass")
        self.assertEqual(row["input_before"], row["input_after"])

    def test_manifest_declaring_no_files_is_not_a_pass(self):
        for name, declaration in (("flat", {}), ("records", {"files": []})):
            packet = self.packet(name)
            (packet / "manifest.json").write_text(json.dumps(declaration), encoding="utf-8")
        output = self.root / "empty-manifest-audit"
        result = self.run_adapter(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for row in json.loads((output / "results.json").read_text()):
            self.assertEqual(row["manifest_check"]["files_checked"], 0)
            self.assertEqual(row["manifest_check"]["status"], "fail", row["packet"])
            self.assertEqual(row["overall"], "fail", row["packet"])

    def test_existing_destination_is_byte_preserved_before_verifier(self):
        marker = self.root / "verifier-ran"
        self.packet(verifier=f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n")
        output = self.root / "existing"
        output.mkdir()
        prior = {"results.json": b"sealed prior results\n", "README.md": b"prior\n"}
        for name, raw in prior.items():
            (output / name).write_bytes(raw)
        result = self.run_adapter(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())
        self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, prior)

    def test_output_under_research_is_not_an_input(self):
        self.packet(verifier="print('ok')\n")
        output = self.root / "research" / "new-audit"
        result = self.run_adapter(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((output / "results.json").read_text())
        self.assertEqual([row["packet"] for row in rows], ["packet"])

    def test_source_pin_rejects_changed_frozen_script_before_verifier(self):
        marker = self.root / "verifier-ran"
        self.packet(verifier=f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n")
        with (self.root / audit.FROZEN_SOURCE).open("ab") as source:
            source.write(b"\n")
        result = self.run_adapter(self.root / "audit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reviewed revalidator source changed", result.stderr)
        self.assertFalse(marker.exists())
        self.assertFalse((self.root / "audit").exists())

    def test_failed_staged_write_leaves_no_destination_or_stage(self):
        self.packet(verifier="print('ok')\n")
        output = self.root / "audit"
        real = audit.write_member
        calls = []

        def fail_third(path, raw):
            calls.append(path.name)
            if len(calls) == 3:
                raise OSError("synthetic write failure")
            real(path, raw)

        with mock.patch.object(audit, "write_member", side_effect=fail_third):
            with self.assertRaisesRegex(OSError, "synthetic write failure"):
                audit.audit(self.root, output, 2, 0.1)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".audit.staging-*")), [])
        self.assertFalse((self.root / ".audit.revalidation.lock").exists())

    def test_generated_verifier_detects_report_mutation(self):
        self.packet(verifier="print('ok')\n")
        output = self.root / "audit"
        result = self.run_adapter(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        (output / "summary.json").write_text("{}\n", encoding="utf-8")
        verify = subprocess.run([sys.executable, "-B", str(output / "verify.py")],
                                capture_output=True, text=True)
        self.assertNotEqual(verify.returncode, 0)
        self.assertIn("summary.json", verify.stdout)

    def test_generated_verifier_rejects_linked_report_member(self):
        self.packet(verifier="print('ok')\n")
        output = self.root / "audit"
        result = self.run_adapter(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = output / "summary.json"
        saved = output / "saved-summary.json"
        summary.rename(saved)
        summary.symlink_to(saved.name)
        verify = subprocess.run([sys.executable, "-B", str(output / "verify.py")],
                                capture_output=True, text=True)
        self.assertNotEqual(verify.returncode, 0)
        self.assertIn("summary.json", verify.stdout)

    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics")
    def test_linked_output_parent_is_rejected_before_verifier(self):
        marker = self.root / "verifier-ran"
        self.packet(verifier=f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n")
        real = self.root / "real-output-parent"
        real.mkdir()
        link = self.root / "linked-output-parent"
        link.symlink_to(real, target_is_directory=True)
        result = self.run_adapter(link / "audit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("linked output path component", result.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(list(real.iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics")
    def test_unwritable_output_parent_fails_before_verifier(self):
        marker = self.root / "verifier-ran"
        self.packet(verifier=f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n")
        parent = self.root / "unwritable"
        parent.mkdir()
        parent.chmod(0o500)
        try:
            if os.access(parent, os.W_OK):
                self.skipTest("host privileges bypass directory write mode")
            result = self.run_adapter(parent / "audit")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(marker.exists())
            self.assertFalse((parent / "audit").exists())
        finally:
            parent.chmod(0o700)

    def test_nondirectory_output_parent_is_rejected_without_partial_output(self):
        marker = self.root / "verifier-ran"
        self.packet(verifier=f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n")
        parent = self.root / "not-a-directory"
        parent.write_bytes(b"preserve me\n")
        result = self.run_adapter(parent / "audit")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())
        self.assertEqual(parent.read_bytes(), b"preserve me\n")

    @unittest.skipUnless(os.name == "posix", "POSIX signals and process groups")
    def test_timeout_kills_same_group_descendants_and_keeps_diagnostics(self):
        child_pid = self.root / "child.pid"
        child = (
            "import os,time;"
            f"open({str(child_pid)!r},'w').write(str(os.getpid()));"
            "print('child diagnostic',flush=True);time.sleep(30)"
        )
        verifier = (
            "import subprocess,sys,time\n"
            f"subprocess.Popen([sys.executable,'-c',{child!r}])\n"
            "print('leader diagnostic',flush=True)\n"
            "time.sleep(30)\n"
        )
        self.packet(verifier=verifier)
        output = self.root / "audit"
        started = time.monotonic()
        result = self.run_adapter(
            output, "--verify-timeout", "0.2", "--cleanup-timeout", "0.2"
        )
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertLess(elapsed, 2.0)
        row = json.loads((output / "results.json").read_text())[0]
        self.assertEqual((row["verify_check"]["status"], row["overall"]),
                         ("timeout", "fail"))
        self.assertIn("leader diagnostic", row["verify_check"]["output"])
        self.assertIn("child diagnostic", row["verify_check"]["output"])
        pid = int(child_pid.read_text())
        self.assertTrue(wait_pid_gone(pid), f"same-group child {pid} survived")

    @unittest.skipUnless(os.name == "posix", "POSIX sessions and signals")
    def test_exited_leader_with_detached_output_inheritor_does_not_block(self):
        escaped_pid = self.root / "escaped.pid"
        child = (
            "import os,time;os.setsid();"
            f"open({str(escaped_pid)!r},'w').write(str(os.getpid()));"
            "print('escaped diagnostic',flush=True);time.sleep(30)"
        )
        verifier = (
            "import subprocess,sys\n"
            f"subprocess.Popen([sys.executable,'-c',{child!r}])\n"
            "print('leader diagnostic',flush=True)\n"
        )
        self.packet(verifier=verifier)
        output = self.root / "audit"
        started = time.monotonic()
        result = self.run_adapter(output, "--verify-timeout", "2")
        elapsed = time.monotonic() - started
        try:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertLess(elapsed, 1.5)
            row = json.loads((output / "results.json").read_text())[0]
            self.assertEqual(row["verify_check"]["status"], "pass")
            self.assertIn("leader diagnostic", row["verify_check"]["output"])
        finally:
            if escaped_pid.exists():
                pid = int(escaped_pid.read_text())
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.assertTrue(wait_pid_gone(pid), f"escaped fixture {pid} survived cleanup")

    @unittest.skipUnless(os.name == "posix", "POSIX sessions and signals")
    def test_interrupted_cli_removes_stage_and_kills_verifier_group(self):
        verifier_pid = self.root / "verifier.pid"
        verifier = (
            "import os,time\n"
            f"open({str(verifier_pid)!r},'w').write(str(os.getpid()))\n"
            "print('partial before interrupt',flush=True)\n"
            "time.sleep(30)\n"
        )
        self.packet(verifier=verifier)
        output = self.root / "audit"
        command = [sys.executable, "-B", str(Path(audit.__file__)),
                   "--repo", str(self.root), "--output", str(output)]
        proc = subprocess.Popen(command, cwd=self.root, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, start_new_session=True)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not verifier_pid.exists():
            time.sleep(0.02)
        self.assertTrue(verifier_pid.exists(), "verifier did not start")
        pid = int(verifier_pid.read_text())
        os.kill(proc.pid, signal.SIGINT)
        proc.communicate(timeout=3)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".audit.staging-*")), [])
        self.assertFalse((self.root / ".audit.revalidation.lock").exists())
        self.assertTrue(wait_pid_gone(pid), f"interrupted verifier {pid} survived")

    @unittest.skipUnless(os.name == "posix", "POSIX sessions and inherited pipes")
    def test_frozen_baseline_hangs_on_detached_pipe_inheritor(self):
        escaped_pid = self.root / "escaped.pid"
        packet = self.root / "packet-outside-research"
        packet.mkdir()
        child = (
            "import os,time;os.setsid();"
            f"open({str(escaped_pid)!r},'w').write(str(os.getpid()));"
            "print('escaped diagnostic',flush=True);time.sleep(30)"
        )
        (packet / "verify.py").write_text(
            "import subprocess,sys\n"
            f"subprocess.Popen([sys.executable,'-c',{child!r}])\n"
            "print('leader diagnostic',flush=True)\n",
            encoding="utf-8",
        )
        caller = self.root / "call-frozen.py"
        caller.write_text(
            "import importlib.util\nfrom pathlib import Path\n"
            f"spec=importlib.util.spec_from_file_location('frozen',{str(self.root / audit.FROZEN_SOURCE)!r})\n"
            "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)\n"
            f"print(module.run_verify(Path({str(packet)!r})),flush=True)\n",
            encoding="utf-8",
        )
        proc = subprocess.Popen([sys.executable, "-B", str(caller)], cwd=self.root,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, start_new_session=True)
        timed_out = False
        try:
            proc.communicate(timeout=1.2)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        finally:
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline and not escaped_pid.exists():
                time.sleep(0.01)
            if escaped_pid.exists():
                pid = int(escaped_pid.read_text())
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.assertTrue(wait_pid_gone(pid), f"baseline fixture {pid} survived cleanup")
            proc.communicate(timeout=1)
        self.assertTrue(timed_out, "frozen run_verify unexpectedly returned")

    def test_frozen_failed_publication_leaves_partial_destination(self):
        output = self.root / "old-audit"
        self.packet(verifier=(
            "from pathlib import Path\n"
            f"Path({str(output / 'results.json')!r}).mkdir()\n"
        ))
        result = self.run_frozen(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(output.is_dir())
        self.assertTrue((output / "results.json").is_dir())


if __name__ == "__main__":
    unittest.main()
