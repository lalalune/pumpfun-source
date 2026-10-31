"""Source and registry inventories must see every undeclared non-directory entry."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('donation_replay_inventory', HERE / 'replay.py')
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)

PACKAGE_NAME = 'example-1.0.0'
BODY = b'declared\n'
BODY_DIGEST = hashlib.sha256(BODY).hexdigest()


def extras(root):
    yield 'dangling link', lambda path: path.symlink_to(root / 'absent')
    yield 'directory link', lambda path: path.symlink_to(root, target_is_directory=True)
    if hasattr(os, 'mkfifo'):
        yield 'fifo', os.mkfifo


class SourceInventoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='relay-inventory-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'lib.rs').write_bytes(BODY)
        rows = {'files': [{'path': 'lib.rs', 'sha256': BODY_DIGEST}]}
        patcher = mock.patch.object(replay, 'load', return_value=rows)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_declared_tree_passes(self):
        replay.check_source(self.source, modes=False)

    def test_undeclared_entries_are_rejected(self):
        for label, create in extras(self.root):
            with self.subTest(label):
                path = self.source / 'extra'
                create(path)
                try:
                    with self.assertRaisesRegex(ValueError, 'inventory'):
                        replay.check_source(self.source, modes=False)
                finally:
                    path.unlink()


class RegistryInventoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='relay-registry-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.registry = self.root / 'registry'
        self.src = self.registry / 'src/ns' / PACKAGE_NAME
        self.src.mkdir(parents=True)
        (self.src / 'lib.rs').write_bytes(BODY)
        (self.src / 'lib.rs').chmod(0o644)
        for name in ('.cargo-checksum.json', '.cargo-ok'):
            (self.src / name).write_bytes(BODY)
        cache = self.registry / 'cache/ns'
        cache.mkdir(parents=True)
        (cache / (PACKAGE_NAME + '.crate')).write_bytes(BODY)
        (self.registry / 'index/ns').mkdir(parents=True)
        spec = {'indexDirectory': 'ns', 'publicSparseIndex': {'retainedFiles': []},
                'packages': [{'name': PACKAGE_NAME, 'checksum': BODY_DIGEST,
                              'generatedChecksumSHA256': BODY_DIGEST,
                              'generatedMarkerSHA256': BODY_DIGEST}]}
        rows = [{'package': PACKAGE_NAME, 'path': 'lib.rs', 'bytes': len(BODY),
                 'sha256': BODY_DIGEST, 'mode': '100644'}]
        vector = gzip.compress(json.dumps(rows * 7968).encode())
        real_read_bytes = Path.read_bytes

        def read_bytes(path):
            return vector if path.name == 'registry-source-vector.json.gz' else real_read_bytes(path)

        for patcher in (mock.patch.object(replay, 'load', return_value=spec),
                        mock.patch.object(Path, 'read_bytes', read_bytes)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_declared_package_passes(self):
        replay.check_registry(self.registry)

    def test_undeclared_entries_are_rejected(self):
        for label, create in extras(self.root):
            with self.subTest(label):
                path = self.src / 'extra'
                create(path)
                try:
                    with self.assertRaisesRegex(ValueError, 'inventory'):
                        replay.check_registry(self.registry)
                finally:
                    path.unlink()


if __name__ == '__main__':
    unittest.main()
