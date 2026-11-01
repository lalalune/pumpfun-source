#!/usr/bin/env python3
import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus as C  # noqa: E402


class CorpusTests(unittest.TestCase):
    def test_snapshot_binds_bytes_and_detects_source_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "program.so"
            source.write_bytes(b"original")
            expected = C.file_sha(source)
            with C.InputSnapshot({"program": source}, {"program": expected}) as snapshot:
                source.write_bytes(b"changed")
                self.assertEqual(snapshot.paths["program"].read_bytes(), b"original")
                self.assertIn("program", snapshot.changed_sources())

    def test_tampered_executable_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "program.so"
            source.write_bytes(b"actual")
            with self.assertRaisesRegex(ValueError, "input hash mismatch"):
                with C.InputSnapshot({"program": source}, {"program": "0" * 64}):
                    pass

    def test_atomic_publication_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "campaign"
            with C.CampaignPublisher(output, {"seed": 1}) as publisher:
                publisher.write_json("summary.json", {"ok": True})
                publisher.commit({"case_count": 1})
            self.assertTrue((output / "complete.json").is_file())
            self.assertEqual(json.loads((output / "summary.json").read_text()), {"ok": True})
            with self.assertRaisesRegex(FileExistsError, "overwrite"):
                with C.CampaignPublisher(output, {"seed": 1}):
                    pass

    def test_concurrent_destination_locking(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "campaign"
            with C.CampaignPublisher(output, {"seed": 1}):
                with self.assertRaisesRegex(FileExistsError, "locked"):
                    with C.CampaignPublisher(output, {"seed": 2}):
                        pass

    def test_interrupted_attempt_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "campaign"
            with self.assertRaisesRegex(RuntimeError, "bounded failure"):
                with C.CampaignPublisher(output, {"seed": 1}) as publisher:
                    publisher.write_json("cases/0.json", {"partial": True})
                    raise RuntimeError("bounded failure")
            partials = C.find_partial_attempts(output)
            self.assertEqual(len(partials), 1)
            self.assertTrue((partials[0] / "attempt.json").is_file())
            self.assertTrue((partials[0] / "interrupted.json").is_file())
            self.assertTrue((partials[0] / "cases/0.json").is_file())

    def test_compressed_json_is_reproducible(self):
        value = {"z": 1, "a": [2, 3]}
        self.assertEqual(C.compressed_json(value), C.compressed_json(value))

    def test_private_source_loader_ignores_canonical_alias_and_rejects_symlink(self):
        import types
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            source = Path(temp) / "sample.py"
            source.write_text("VALUE = 'source'\n")
            poison = types.ModuleType("sample")
            poison.VALUE = "cached"
            previous = sys.modules.get("sample")
            sys.modules["sample"] = poison
            try:
                loaded = C.source_module("sample", source)
                self.assertEqual(loaded.VALUE, "source")
                self.assertIs(sys.modules["sample"], poison)
                self.assertNotIn(loaded.__name__, sys.modules)
                self.assertEqual(loaded.__source_sha256__, hashlib.sha256(source.read_bytes()).hexdigest())
                alias = Path(temp) / "alias.py"
                alias.symlink_to(source)
                with self.assertRaises(ValueError):
                    C.source_module("alias", alias)
            finally:
                if previous is None:
                    sys.modules.pop("sample", None)
                else:
                    sys.modules["sample"] = previous

    def _sealed_report(self, directory):
        output = Path(directory) / "report"
        with C.CampaignPublisher(output, {"seed": 1}) as publisher:
            publisher.write_json("cases.json", [{"id": "one"}])
            publisher.write_json("receipts/one.json", {"receipt": True})
            digest = publisher.write_manifest()
            publisher.write_json("summary.json", {"artifact_manifest_sha256": digest})
            publisher.commit({"artifact_manifest_sha256": digest})
        return output, digest

    def test_report_census_rejects_unlisted_members_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            output, digest = self._sealed_report(temp)
            self.assertIn("cases.json", C.verify_artifacts(output, digest)["files"])
            extra = output / "receipts/unlisted.txt"
            extra.write_text("unlisted")
            with self.assertRaises(ValueError):
                C.verify_artifacts(output, digest)
            extra.unlink()
            member = output / "receipts/one.json"
            outside = Path(temp) / "outside.json"
            outside.write_bytes(member.read_bytes())
            member.unlink()
            member.symlink_to(outside)
            with self.assertRaises(ValueError):
                C.verify_artifacts(output, digest)

    def test_resealed_duplicate_manifest_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output, _ = self._sealed_report(temp)
            path = output / "artifacts.json"
            raw = path.read_bytes().replace(b'{"files":', b'{"schema":"pump-admin-cto-fuzz-artifacts-v1","files":', 1)
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "duplicate JSON"):
                C.verify_artifacts(output, hashlib.sha256(raw).hexdigest())


    def test_json_rejects_nonfinite_constants_and_overflowed_numbers(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nonfinite.json"
            for literal in ("NaN", "Infinity", "-Infinity", "1e999"):
                path.write_text('{"value":' + literal + '}')
                with self.subTest(literal=literal), self.assertRaisesRegex(ValueError, "nonfinite JSON"):
                    C.read_json(path)


if __name__ == "__main__":
    unittest.main()
