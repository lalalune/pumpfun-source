#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import controls
import producer
import verify


class GenuineReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="relay-multidonor-tests-")
        cls.root = producer.ROOT
        cls.candidate = cls.root / "evidence/dependencies/donation_relay/deployed.so"
        cls.report_path = Path(cls.temporary.name) / "report.json"
        if not producer.execute(cls.root, cls.candidate, cls.report_path):
            raise AssertionError("original/original multi-donor control failed")
        cls.raw = cls.report_path.read_bytes()
        cls.report = json.loads(cls.raw)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_genuine_original_control_is_independently_accepted(self):
        self.assertEqual(verify.validate(self.report, self.root, self.candidate), [])
        self.assertEqual(self.raw, verify.canonical(self.report))

    def test_all_required_adversarial_mutations_are_detected(self):
        result = controls.run(self.report, self.root, self.candidate)
        self.assertTrue(result["all_detected"])
        self.assertEqual(result["control_count"], 14)
        self.assertEqual(result["detected_count"], 14)
        self.assertEqual(set(result["controls"]), set(controls.MUTATIONS))

    def test_duplicate_transaction_is_rejected(self):
        changed = copy.deepcopy(self.report)
        first = changed["cases"][0]["steps"][0]
        second = changed["cases"][0]["steps"][1]
        for field in ("transaction_base64", "transaction_sha256", "message_base64",
                      "message_sha256", "recent_blockhash", "signatures",
                      "signature_verification", "required_signer_pubkeys", "donor_signers"):
            second[field] = copy.deepcopy(first[field])
        problems = verify.validate(changed, self.root, self.candidate)
        self.assertTrue(problems)

    def test_tampered_executable_hash_is_rejected(self):
        changed = copy.deepcopy(self.report)
        changed["inputs"]["candidate"]["sha256"] = "0" * 64
        self.assertTrue(any("candidate identity" in p for p in verify.validate(changed, self.root, self.candidate)))

    def test_corrupt_source_provenance_is_rejected(self):
        changed = copy.deepcopy(self.report)
        changed["inputs"]["source_manifest_sha256"] = "f" * 64
        self.assertTrue(any("source/package context" in p for p in verify.validate(changed, self.root, self.candidate)))

    def authenticated_build_report(self):
        changed = copy.deepcopy(self.report)
        source_files, source_digest = producer.source_manifest(self.root)
        executable = Path(sys.executable).resolve()
        builder = self.root / "reconstruction/verification/donation-relay-multidonor/producer.py"
        build = {
            "schema": "donation-relay-candidate-build-v1",
            "builder": {"path": builder.relative_to(self.root).as_posix(),
                        "sha256": verify.file_sha(builder)},
            "command": [str(executable), "rustc", "--release", "--target",
                        "sbpf-solana-solana", "--locked", "--offline",
                        "--manifest-path", "fixture", "--lib", "--"],
            "offline": True,
            "locked": True,
            "source_files": source_files,
            "source_manifest_sha256": source_digest,
            "toolchain": {"rust/bin/cargo": {"path": str(executable),
                                                "sha256": verify.file_sha(executable)}},
            "tool_versions": {},
            "unstripped": {"sha256": "1" * 64, "bytes": 1},
            "candidate": {"sha256": verify.file_sha(self.candidate),
                          "bytes": self.candidate.stat().st_size},
        }
        changed["inputs"]["candidate_build"] = build
        changed["inputs"]["candidate_build_receipt_sha256"] = verify.sha(
            (json.dumps(build, indent=2, sort_keys=True) + "\n").encode())
        return changed

    def test_fabricated_build_receipt_is_explicitly_refused(self):
        problems = verify.validate(self.authenticated_build_report(), self.root, self.candidate)
        self.assertTrue(any("source-build claims are not admitted" in p for p in problems), problems)

    def test_corrupt_build_source_provenance_is_rejected(self):
        changed = self.authenticated_build_report()
        changed["inputs"]["candidate_build"]["source_manifest_sha256"] = "f" * 64
        changed["inputs"]["candidate_build_receipt_sha256"] = verify.sha(
            (json.dumps(changed["inputs"]["candidate_build"], indent=2,
                        sort_keys=True) + "\n").encode())
        self.assertTrue(verify.validate(changed, self.root, self.candidate))

    def test_missing_required_evidence_is_rejected(self):
        changed = copy.deepcopy(self.report)
        del changed["inputs"]["original"]
        self.assertTrue(verify.validate(changed, self.root, self.candidate))

    def test_replay_is_byte_deterministic(self):
        second = Path(self.temporary.name) / "second.json"
        self.assertTrue(producer.execute(self.root, self.candidate, second))
        self.assertEqual(self.raw, second.read_bytes())

    def test_executable_none_substitution_and_integer_runtime_flags_are_rejected(self):
        for kind in ("none", "flag", "rent"):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(self.report)
                if kind == "none":
                    for case in changed["cases"]:
                        for step in case["steps"]:
                            for side in ("original", "candidate"):
                                for stage in ("before", "after"):
                                    step[side][stage][str(verify.RELAY)] = None
                elif kind == "flag":
                    changed["runtime"]["signature_verification"] = 1
                else:
                    changed["cases"][0]["steps"][0]["original"]["after"][str(verify.RELAY)]["rent_epoch"] = False
                self.assertTrue(verify.validate(changed, self.root, self.candidate))

    def test_saved_receipt_mutation_is_rejected_by_real_cli(self):
        import subprocess
        changed = copy.deepcopy(self.report)
        controls.corrupt_canonical_budget_with_valid_signatures(changed)
        path = Path(self.temporary.name) / "forged-canonical-report.json"
        path.write_bytes(verify.canonical(changed))
        result = subprocess.run([sys.executable, "-B", str(producer.HERE / "verify.py"),
                                 "--root", str(self.root), "--candidate", str(self.candidate),
                                 "--report", str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(result.stdout)["accepted"])

    def test_optimized_python_is_refused_before_transactions(self):
        import subprocess
        result = subprocess.run([sys.executable, "-O", "-B", str(producer.HERE / "verify.py"), "--help"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Normal Python is required", result.stderr)

    def test_reader_and_producer_reject_midoperation_image_mutation(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "candidate.so"
            original_bytes = self.candidate.read_bytes()
            candidate.write_bytes(original_bytes)
            original_validate = verify._validate
            def changing(*args, **kwargs):
                result = original_validate(*args, **kwargs)
                candidate.write_bytes(original_bytes + b"mutated")
                return result
            with mock.patch.object(verify, "_validate", side_effect=changing):
                self.assertTrue(any("candidate changed" in p for p in verify.validate(self.report, self.root, candidate)))
            candidate.write_bytes(original_bytes)
            saved = {case["name"]: case for case in self.report["cases"]}
            def reuse_receipt(name, *args, **kwargs):
                candidate.write_bytes(original_bytes + b"mutated")
                return copy.deepcopy(saved[name])
            output = Path(temp) / "must-not-publish.json"
            with mock.patch.object(producer, "run_case", side_effect=reuse_receipt):
                with self.assertRaisesRegex(ValueError, "candidate changed"):
                    producer.execute(self.root, candidate, output)
            self.assertFalse(output.exists())

    def test_executable_timestamp_cache_and_canonical_alias_are_ignored(self):
        import importlib.util
        import os
        import py_compile
        import shutil
        import types
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            for source in [producer.HERE / name for name in ("admission.py", "fixture.py", "producer.py", "verify.py")]:
                target = root / source.relative_to(self.root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            helper = root / "scripts/pump_differential_output.py"
            helper.parent.mkdir(parents=True)
            shutil.copyfile(self.root / "scripts/pump_differential_output.py", helper)
            fixture_path = root / "reconstruction/verification/donation-relay-multidonor/fixture.py"
            clean = fixture_path.read_bytes()
            marker = Path(temp) / "cached-code-executed"
            malicious = ("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\n").encode()
            malicious += b"#" * (len(clean) - len(malicious))
            self.assertEqual(len(malicious), len(clean))
            fixture_path.write_bytes(malicious)
            os.utime(fixture_path, (1_700_000_000, 1_700_000_000))
            py_compile.compile(str(fixture_path), doraise=True)
            fixture_path.write_bytes(clean)
            os.utime(fixture_path, (1_700_000_000, 1_700_000_000))
            spec = importlib.util.spec_from_file_location("_relay_cached_negative_control", fixture_path)
            cached = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cached)
            self.assertTrue(marker.exists(), "prove cache executable before testing bypass")
            marker.unlink()
            admission_path = root / "reconstruction/verification/donation-relay-multidonor/admission.py"
            loader = types.ModuleType("_relay_private_loader")
            loader.__file__ = str(admission_path.resolve())
            exec(compile(admission_path.read_bytes(), str(admission_path), "exec"), loader.__dict__)
            fake = types.ModuleType("fixture")
            previous = sys.modules.get("fixture")
            sys.modules["fixture"] = fake
            try:
                loaded = loader.source_module("verify", (root / "reconstruction/verification/donation-relay-multidonor/verify.py").resolve(), bindings={"_ADMISSION": loader})
                self.assertFalse(marker.exists())
                self.assertIs(sys.modules["fixture"], fake)
                self.assertEqual(loaded.F.Fixture.create("same_epoch_a_then_b").fee.pubkey(),
                                 producer.fixture.Fixture.create("same_epoch_a_then_b").fee.pubkey())
            finally:
                if previous is None:
                    sys.modules.pop("fixture", None)
                else:
                    sys.modules["fixture"] = previous

    def test_real_source_drift_during_produce_is_refused_before_publication(self):
        import shutil
        import types
        from unittest import mock
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            for name in self.report["inputs"]["admitted_input_sha256"]:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.root / name, target)
            admission_path = root / "reconstruction/verification/donation-relay-multidonor/admission.py"
            loader = types.ModuleType("_relay_private_loader")
            loader.__file__ = str(admission_path.resolve())
            exec(compile(admission_path.read_bytes(), str(admission_path), "exec"), loader.__dict__)
            package = root / "reconstruction/verification/donation-relay-multidonor"
            loaded = loader.source_module("producer", (package / "producer.py").resolve(), bindings={"_ADMISSION": loader})
            saved = {case["name"]: case for case in self.report["cases"]}
            source = package / "fixture.py"
            clean = source.read_bytes()
            def controlled_receipt_reuse(name, *args, **kwargs):
                source.write_bytes(clean + b"\n# deliberately changed after admission\n")
                return copy.deepcopy(saved[name])
            output = Path(temp) / "must-not-publish.json"
            with mock.patch.object(loaded, "run_case", side_effect=controlled_receipt_reuse):
                with self.assertRaisesRegex(ValueError, "source differs|input inventory|executed source"):
                    loaded.execute(root.resolve(), root / "evidence/dependencies/donation_relay/deployed.so", output)
            self.assertFalse(output.exists())

    def test_receipt_changed_after_parse_is_refused(self):
        from unittest import mock
        path = Path(self.temporary.name) / "mid-read-change.json"
        path.write_bytes(self.raw)
        original_validate = verify.validate
        def changing(*args, **kwargs):
            result = original_validate(*args, **kwargs)
            path.write_bytes(path.read_bytes() + b" ")
            return result
        with mock.patch.object(verify, "validate", side_effect=changing):
            result = verify.verify_file(self.root, self.candidate, path)
        self.assertFalse(result["accepted"])
        self.assertIn("report changed during verification", result["problems"])

    def test_duplicate_or_nonfinite_saved_json_is_refused(self):
        for raw in (b'{"schema":1,"schema":2}', b'{"schema":NaN}'):
            with self.subTest(raw=raw):
                path = Path(self.temporary.name) / "malformed.json"
                path.write_bytes(raw)
                result = verify.verify_file(self.root, self.candidate, path)
                self.assertFalse(result["accepted"])

    def test_entrypoint_self_bytes_are_frozen_before_dependency_bootstrap(self):
        import hashlib
        import shutil
        import types
        for entry_name in ("producer.py", "verify.py", "controls.py"):
            with self.subTest(entry=entry_name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "repo"
                for name in ("admission.py", "fixture.py", "producer.py", "verify.py", "controls.py"):
                    source = producer.HERE / name
                    target = root / source.relative_to(self.root)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
                helper = root / "scripts/pump_differential_output.py"
                helper.parent.mkdir(parents=True)
                shutil.copyfile(self.root / "scripts/pump_differential_output.py", helper)
                package = root / "reconstruction/verification/donation-relay-multidonor"
                admission_path = (package / "admission.py").resolve()
                loader = types.ModuleType("_relay_proxy_loader")
                loader.__file__ = str(admission_path)
                exec(compile(admission_path.read_bytes(), str(admission_path), "exec"), loader.__dict__)
                entry = (package / entry_name).resolve()
                admitted = entry.read_bytes()
                real_load = loader.source_module
                changed = []
                def proxy(*args, **kwargs):
                    if not changed:
                        entry.write_bytes(admitted + b"\n# edited during dependency bootstrap\n")
                        changed.append(True)
                    return real_load(*args, **kwargs)
                loader.source_module = proxy
                direct = types.ModuleType("_relay_direct_entrypoint")
                direct.__file__ = str(entry)
                direct._ADMISSION = loader
                exec(compile(admitted, str(entry), "exec"), direct.__dict__)
                self.assertTrue(changed)
                self.assertEqual(loader.LOADED[str(entry)], hashlib.sha256(admitted).hexdigest())
                self.assertNotEqual(loader.LOADED[str(entry)], hashlib.sha256(entry.read_bytes()).hexdigest())
                with self.assertRaisesRegex(ValueError, "source changed"):
                    real_load("entrypoint", entry)

    def test_existing_output_is_never_replaced(self):
        occupied = Path(self.temporary.name) / "occupied.json"
        occupied.write_bytes(b"retained\n")
        with self.assertRaises(FileExistsError):
            producer.execute(self.root, self.candidate, occupied)
        self.assertEqual(occupied.read_bytes(), b"retained\n")


if __name__ == "__main__":
    unittest.main()
