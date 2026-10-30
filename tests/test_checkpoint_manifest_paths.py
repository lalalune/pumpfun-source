"""Path-boundary regressions for sealed checkpoint manifests."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_current_checkpoint as checkpoint


def symlink_directories_available():
    """False when the process cannot create a directory symlink (WinError 1314)."""
    try:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            os.symlink(root, root / 'link', target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        return False
    return True


SYMLINK_DIRECTORIES = symlink_directories_available()


FIFO_PRELUDE = r'''
import hashlib, json, os, tempfile
from pathlib import Path
import verify_current_checkpoint as checkpoint

def write(package, manifest):
    raw = (json.dumps(manifest, indent=2) + "\n").encode()
    (package / "manifest.json").write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

def expect_nonregular(call):
    try:
        call()
    except AssertionError as error:
        if "Nonregular path" not in str(error):
            raise
    else:
        raise SystemExit("a nonregular path was accepted")
'''


def create_junction(link, target):
    """Create an NTFS junction at link pointing at an existing target directory.

    _winapi.CreateJunction(target, link) matches CPython's Windows tests.
    `cmd /c mklink /J link target` is the same operation with reversed arguments.
    """
    import _winapi
    _winapi.CreateJunction(os.fspath(target), os.fspath(link))


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

    @unittest.skipUnless(SYMLINK_DIRECTORIES, 'creating a directory symlink is not permitted')
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

    @unittest.skipUnless(SYMLINK_DIRECTORIES, 'creating a directory symlink is not permitted')
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

    @unittest.skipUnless(SYMLINK_DIRECTORIES, 'creating a directory symlink is not permitted')
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

    def run_bounded(self, script):
        """Run script in a child; a blocking open shows up as a timeout, not a hang."""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(ROOT / 'scripts')
        try:
            result = subprocess.run([sys.executable, '-c', FIFO_PRELUDE + script], cwd=ROOT, env=env,
                                    capture_output=True, text=True, check=False, timeout=20)
        except subprocess.TimeoutExpired:
            self.fail('read_regular blocked on a FIFO')
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFOs need POSIX')
    def test_fifo_entry_and_fifo_manifest_are_rejected_without_blocking(self):
        self.run_bounded(r'''
with tempfile.TemporaryDirectory() as temporary:
    package = Path(temporary) / "package"
    package.mkdir()
    os.mkfifo(package / "file.txt")
    expect_nonregular(lambda: checkpoint.verify_manifest(package, write(package, {"file.txt": "0" * 64})))
    (package / "manifest.json").unlink()
    os.mkfifo(package / "manifest.json")
    expect_nonregular(lambda: checkpoint.verify_manifest(package, "0" * 64))
''')

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFOs need POSIX')
    def test_file_swapped_for_a_fifo_after_lstat_does_not_block(self):
        # lstat reports the regular file that was there; the open then meets a
        # FIFO. Only the nonblocking open keeps this from waiting for a writer.
        self.run_bounded(r'''
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    regular = root / "regular.txt"
    regular.write_bytes(b"sealed-bytes\n")
    fifo = root / "file.txt"
    os.mkfifo(fifo)
    real_lstat = os.lstat
    os.lstat = lambda path, *a, **k: real_lstat(regular if os.fspath(path) == os.fspath(fifo) else path, *a, **k)
    expect_nonregular(lambda: checkpoint.read_regular(root, fifo))
''')

    def test_file_replaced_between_lstat_and_open_is_rejected(self):
        # lstat sees one regular file and the descriptor another: the read
        # must not return bytes from a file that was not the one checked.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'file.txt').write_bytes(b'sealed-bytes\n')
            (root / 'other.txt').write_bytes(b'other-bytes\n')
            real_lstat = os.lstat
            def swapped(path, *args, **kwargs):
                if os.fspath(path) == os.fspath(root / 'file.txt'):
                    path = root / 'other.txt'
                return real_lstat(path, *args, **kwargs)
            with mock.patch.object(checkpoint.os, 'lstat', swapped):
                with self.assertRaisesRegex(AssertionError, 'Path changed during read'):
                    checkpoint.read_regular(root, root / 'file.txt')

    @unittest.skipUnless(hasattr(socket, 'AF_UNIX'), 'Unix sockets need POSIX')
    def test_socket_entry_is_rejected_before_open(self):
        # open() of a socket fails with ENXIO; the type check must come first.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            listener = socket.socket(socket.AF_UNIX)
            try:
                listener.bind(os.fspath(root / 'file.txt'))
                with self.assertRaisesRegex(AssertionError, 'Nonregular path'):
                    checkpoint.read_regular(root, root / 'file.txt')
            finally:
                listener.close()

    @unittest.skipUnless(sys.platform == 'win32', 'NTFS junctions exist only on Windows')
    def test_junction_inside_the_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / 'package'
            outside = root / 'outside'
            outside.mkdir()
            payload = b'sealed-bytes\n'
            (outside / 'file.txt').write_bytes(payload)
            package.mkdir()
            create_junction(package / 'nested', outside)
            digest = hashlib.sha256(payload).hexdigest()
            expected = write_manifest(package, {'nested/file.txt': digest})
            with self.assertRaisesRegex(AssertionError, 'Symlink ancestry'):
                checkpoint.verify_manifest(package, expected)

    @unittest.skipUnless(sys.platform == 'win32', 'NTFS junctions exist only on Windows')
    def test_junction_parent_is_rejected_for_the_repo_bound(self):
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
            create_junction(repo / 'repro', root / 'outside')
            package = repo / 'repro' / 'pkg'
            self.assertEqual(checkpoint.verify_manifest(package, expected)['nested/file.txt'], digest)
            with self.assertRaisesRegex(AssertionError, 'Symlink ancestry'):
                checkpoint.verify_manifest(package, expected, repo)

    @unittest.skipUnless(sys.platform == 'win32', 'NTFS junctions exist only on Windows')
    def test_junction_used_as_the_bound_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / 'outside'
            nested = outside / 'nested'
            nested.mkdir(parents=True)
            payload = b'sealed-bytes\n'
            (nested / 'file.txt').write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            expected = write_manifest(outside, {'nested/file.txt': digest})
            repo = root / 'repo'
            repo.mkdir()
            package = repo / 'pkg'
            create_junction(package, outside)
            with self.assertRaisesRegex(AssertionError, 'Symlink ancestry'):
                checkpoint.verify_manifest(package, expected)
            with self.assertRaisesRegex(AssertionError, 'Symlink ancestry'):
                checkpoint.verify_manifest(package, expected, repo)


if __name__ == '__main__':
    unittest.main(verbosity=2)
