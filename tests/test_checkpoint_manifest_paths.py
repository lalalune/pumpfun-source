"""Path-boundary regressions for sealed checkpoint manifests."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_current_checkpoint as checkpoint


def write_manifest(package, manifest):
    raw = (json.dumps(manifest, indent=2) + '\n').encode()
    (package / 'manifest.json').write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class CheckpointManifestPathTests(unittest.TestCase):
    def test_ordinary_manifest_and_dict_entries_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / 'package'
            nested = package / 'nested'
            nested.mkdir(parents=True)
            payload = b'sealed-bytes\n'
            (nested / 'file.txt').write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            flat = write_manifest(package, {'nested/file.txt': digest})
            self.assertEqual(checkpoint.verify_manifest(package, flat)['nested/file.txt'], digest)
            recorded = write_manifest(package, {'files': {'nested/file.txt': {'sha256': digest}}})
            files = checkpoint.verify_manifest(package, recorded)
            self.assertEqual(files['nested/file.txt']['sha256'], digest)

    def test_symlinked_ancestor_is_rejected_when_the_hash_matches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / 'package'
            outside = root / 'outside'
            outside.mkdir()
            payload = b'sealed-bytes\n'
            (outside / 'file.txt').write_bytes(payload)
            package.mkdir()
            os.symlink(outside, package / 'nested', target_is_directory=True)
            digest = hashlib.sha256(payload).hexdigest()
            expected = write_manifest(package, {'nested/file.txt': digest})
            with self.assertRaisesRegex(AssertionError, 'Symlink ancestry'):
                checkpoint.verify_manifest(package, expected)

    def test_symlinked_parent_above_the_package_is_rejected_for_the_repo_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / 'repo'
            outside = root / 'outside' / 'pkg'
            nested = outside / 'nested'
            nested.mkdir(parents=True)
            payload = b'sealed-bytes\n'
            (nested / 'file.txt').write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            expected = write_manifest(outside, {'nested/file.txt': digest})
            repo.mkdir()
            os.symlink(root / 'outside', repo / 'repro', target_is_directory=True)
            package = repo / 'repro' / 'pkg'
            self.assertEqual(checkpoint.verify_manifest(package, expected)['nested/file.txt'], digest)
            with self.assertRaisesRegex(AssertionError, 'Symlink ancestry'):
                checkpoint.verify_manifest(package, expected, repo)

    def test_manifest_names_cannot_escape_and_changed_bytes_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / 'package'
            package.mkdir()
            payload = b'sealed-bytes\n'
            (package / 'file.txt').write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            outside = root / 'outside.txt'
            outside.write_bytes(payload)
            escaped = write_manifest(package, {'../outside.txt': digest})
            with self.assertRaisesRegex(AssertionError, 'Manifest path'):
                checkpoint.verify_manifest(package, escaped)
            changed = write_manifest(package, {'file.txt': hashlib.sha256(b'other\n').hexdigest()})
            with self.assertRaisesRegex(AssertionError, 'Manifest mismatch'):
                checkpoint.verify_manifest(package, changed)

    def test_optimized_interpreter_keeps_the_boundary_and_the_hash(self):
        script = r'''
import hashlib, json, os, tempfile
from pathlib import Path
import verify_current_checkpoint as checkpoint

def write(package, manifest):
    raw = (json.dumps(manifest, indent=2) + "\n").encode()
    (package / "manifest.json").write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    package = root / "package"
    nested = package / "nested"
    nested.mkdir(parents=True)
    payload = b"sealed-bytes\n"
    (nested / "file.txt").write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    expected = write(package, {"nested/file.txt": digest})
    if checkpoint.verify_manifest(package, expected)["nested/file.txt"] != digest:
        raise SystemExit("ordinary manifest was rejected")
    outside = root / "outside"
    outside.mkdir()
    (outside / "file.txt").write_bytes(payload)
    os.symlink(outside, package / "alias", target_is_directory=True)
    linked = write(package, {"alias/file.txt": digest})
    try:
        checkpoint.verify_manifest(package, linked)
    except AssertionError as error:
        if "Symlink ancestry" not in str(error):
            raise
    else:
        raise SystemExit("symlinked ancestor was accepted")
    mismatched = write(package, {"nested/file.txt": hashlib.sha256(b"other\n").hexdigest()})
    try:
        checkpoint.verify_manifest(package, mismatched)
    except AssertionError as error:
        if "Manifest mismatch" not in str(error):
            raise
    else:
        raise SystemExit("changed bytes were accepted")
'''
        env = os.environ.copy()
        env['PYTHONPATH'] = str(ROOT / 'scripts')
        result = subprocess.run(
            [sys.executable, '-O', '-c', script],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
