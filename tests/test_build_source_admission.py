"""Build comparison admission must cover compiler inputs and fail on traversal errors."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pump_validate_parallel as validator
import source_manifest_guard as guard
import test_pump_validate_parallel as fixtures
import verify_pump_main_checkpoint as checkpoint


class BuildSourceAdmission(fixtures.ParallelReportPublicationTests):
    def test_empty_or_incomplete_source_binding_is_rejected_before_publication(self):
        report = json.loads(self.build_comparison.read_text())
        sources = report['source_sha256']
        for omitted in [None, *sources]:
            with self.subTest(omitted=omitted):
                altered = {} if omitted is None else {k: v for k, v in sources.items() if k != omitted}
                self.build_comparison.write_text(json.dumps(report | {'source_sha256': altered}))
                output = self.root / 'rejected.json'
                with self.assertRaisesRegex(AssertionError, 'source'):
                    self.run_validator(output)
                self.assertFalse(output.exists())
                self.assertFalse(output.with_name(output.name + '.suites').exists())

    def test_workspace_inputs_follow_the_existing_manifest_contract(self):
        (self.source / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n')
        (self.root / 'Cargo.toml').write_text('[workspace]\nmembers=["source"]\n')
        (self.root / 'Cargo.lock').write_text('version = 3\n')
        report = json.loads(self.build_comparison.read_text())
        sources = guard.strict_manifest(self.source, self.root, self.root, cwd=self.root)
        self.build_comparison.write_text(json.dumps(report | {'source_sha256': sources}))
        self.assertFalse(self.run_validator(self.root / 'workspace-ok.json'))
        self.build_comparison.write_text(json.dumps(report | {'source_sha256': {
            k: v for k, v in sources.items() if k != 'Cargo.lock'}}))
        with self.assertRaisesRegex(AssertionError, 'source'):
            self.run_validator(self.root / 'workspace-missing-lock.json')

    def portable_report(self):
        crate = self.root / 'programs/pump'
        shutil.copytree(self.source, crate)
        self.source = crate
        sources = guard.strict_manifest(crate, crate, self.root, cwd=crate)
        package = self.root / 'repro/portable-fixture'
        package.mkdir(parents=True)
        original_sources = {'historic-source/lib.rs': 'historical-compiler-input'}
        original = {'returncode': 0, 'source_unchanged': True,
                    'source_sha256': original_sources,
                    'comparison': {'candidate_sha256': validator.sha(self.candidate)}}
        (package / 'canonical-build.json').write_text(json.dumps(original))
        (package / 'CHECKPOINT.json').write_text(json.dumps({
            'candidate_sha256': validator.sha(self.candidate),
            'primary_source_sha256': {k.removeprefix('programs/pump/'): v for k, v in sources.items()}}))
        manifest = {name: validator.sha(package / name) for name in ['canonical-build.json', 'CHECKPOINT.json']}
        (package / 'MANIFEST.json').write_text(json.dumps(manifest))
        report = original | {'source_sha256': sources, 'portable_source_binding': {
            'kind': 'verified-equal-canonical-primary-source',
            'origin_build_record': 'repro/portable-fixture/canonical-build.json',
            'origin_build_record_sha256': manifest['canonical-build.json'],
            'original_compiled_source_sha256': original_sources}}
        self.build_comparison.write_text(json.dumps(report))
        return report, package

    def test_supported_portable_binding_remains_valid_but_cannot_be_incomplete(self):
        report, package = self.portable_report()
        with patch.object(checkpoint, 'PACKAGE', 'repro/portable-fixture'), \
                patch.object(checkpoint, 'MANIFEST_SHA256', validator.sha(package / 'MANIFEST.json')):
            self.assertFalse(self.run_validator(self.root / 'portable-ok.json'))
            self.build_comparison.write_text(json.dumps(report | {'source_sha256': {}}))
            with self.assertRaisesRegex(AssertionError, 'source'):
                self.run_validator(self.root / 'portable-incomplete.json')

    def test_portable_binding_cannot_claim_an_unverified_origin(self):
        report, package = self.portable_report()
        report['portable_source_binding']['origin_build_record_sha256'] = '0' * 64
        self.build_comparison.write_text(json.dumps(report))
        with patch.object(checkpoint, 'PACKAGE', 'repro/portable-fixture'), \
                patch.object(checkpoint, 'MANIFEST_SHA256', validator.sha(package / 'MANIFEST.json')):
            with self.assertRaisesRegex(AssertionError, 'portable'):
                self.run_validator(self.root / 'portable-invalid.json')


class ManifestTraversal(unittest.TestCase):
    def test_unreadable_required_subtree_cannot_silently_disappear(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            crate = root / 'programs/pump'
            (crate / 'src/required').mkdir(parents=True)
            (crate / 'src/required/lib.rs').write_text('pub fn required() {}')
            scan = os.scandir
            def denied(path):
                if Path(path) == crate / 'src/required':
                    raise PermissionError(13, 'injected traversal denial', str(path))
                return scan(path)
            with patch.object(os, 'scandir', denied), self.assertRaisesRegex(ValueError, 'travers'):
                guard.strict_manifest(crate, root, root)
            self.assertIn('programs/pump/src/required/lib.rs', guard.strict_manifest(crate, root, root))


if __name__ == '__main__':
    unittest.main()
