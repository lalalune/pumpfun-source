"""Offline archive/metadata regression controls; no installer, network or compiler."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import sys
import unittest

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prepare = module('amm_vendor_preparer', HERE/'prepare.py')
sha = lambda data: hashlib.sha256(data).hexdigest()
ARCHIVES = None


class VendorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)/'vendor'
        self.directory = 'fixture-1.0.0'
        # Deliberately non-sorted archive order, like the actual failed aes crate.
        self.files = [('src/z.rs', b'pub fn z() {}\r\n'), ('src/a.rs', b'pub fn a() {}\n')]

    def fixture(self, files=None, kind=tarfile.REGTYPE):
        entries = self.files if files is None else files
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as archive:
            for name, data in entries:
                item = tarfile.TarInfo(self.directory+'/'+name)
                item.type = kind
                item.size = len(data)
                item.linkname = '../../outside' if kind == tarfile.SYMTYPE else ''
                archive.addfile(item, io.BytesIO(data))
        blob = stream.getvalue()
        # Explicit lexical insertion order here; the production input is unsorted.
        files = {name: sha(data) for name, data in sorted(entries)}
        metadata = (json.dumps({'files': files, 'package': sha(blob)})+'\n').encode()
        record = {'directory': self.directory, 'package_sha256': sha(blob),
                  'file_count': len(entries), 'checksum_file_sha256': sha(metadata)}
        return blob, record, metadata

    def reject(self, blob, record, message):
        with self.assertRaisesRegex(ValueError, message):
            prepare.vendor_package(blob, self.output, record)
        self.assertFalse(self.output.exists(), 'authentication must precede writes')

    def test_sorted_checksum_bytes_and_unmodified_sources(self):
        blob, record, metadata = self.fixture()
        prepare.vendor_package(blob, self.output, record)
        root = self.output/self.directory
        self.assertEqual((root/'.cargo-checksum.json').read_bytes(), metadata)
        self.assertEqual({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()},
                         {name for name, _ in self.files} | {'.cargo-checksum.json'})
        for name, data in self.files:
            self.assertEqual((root/name).read_bytes(), data)

    def test_frozen_helper_reproduces_order_failure(self):
        pins = prepare.read(HERE/'proposal-pins.json')['preparer_helper']
        path = HERE.parents[1]/pins['path']
        self.assertEqual(sha(path.read_bytes()), pins['sha256'])
        helper = module('frozen_mayhem_vendor_helper', path)
        blob, record, _ = self.fixture()
        with self.assertRaisesRegex(ValueError, 'cannot reconstruct pinned vendor checksum map'):
            helper.vendor_package(blob, self.output, record)
        self.assertFalse(self.output.exists())

    def test_changed_archive_rejected(self):
        blob, record, _ = self.fixture()
        self.reject(blob+b'changed', record, 'registry archive differs')

    def test_changed_metadata_pin_rejected(self):
        blob, record, _ = self.fixture()
        record['checksum_file_sha256'] = '0'*64
        self.reject(blob, record, 'pinned vendor checksum map differs')

    def test_missing_file_count_rejected(self):
        blob, record, _ = self.fixture()
        record['file_count'] += 1
        self.reject(blob, record, 'registry file count differs')

    def test_duplicate_member_rejected(self):
        blob, record, _ = self.fixture([self.files[0], self.files[0]])
        self.reject(blob, record, 'unsafe crate path')

    def test_unsafe_member_paths_rejected(self):
        for name in ('../escape.rs', '/absolute.rs', 'C:/absolute.rs', r'src\bad.rs',
                     './dot.rs', 'src//alias.rs', '.', '.cargo-checksum.json'):
            with self.subTest(name=name):
                blob, record, _ = self.fixture([(name, b'untrusted')])
                self.reject(blob, record, 'unsafe crate path')

    def test_unsafe_package_directories_rejected(self):
        for name in ('', '.', '..', 'nested/package', r'nested\package', 'C:package'):
            with self.subTest(name=name):
                blob, record, _ = self.fixture()
                record['directory'] = name
                self.reject(blob, record, 'unsafe registry directory')

    def test_archive_prefix_mismatch_rejected(self):
        blob, record, _ = self.fixture()
        record['directory'] = 'other-1.0.0'
        self.reject(blob, record, 'unsafe crate member')

    def test_symlink_rejected(self):
        blob, record, _ = self.fixture(kind=tarfile.SYMTYPE)
        self.reject(blob, record, 'unsafe crate member')

    def test_unpinned_metadata_format_rejected(self):
        blob, record, metadata = self.fixture()
        record['checksum_file_sha256'] = sha(metadata.rstrip(b'\n'))
        self.reject(blob, record, 'pinned vendor checksum map differs')

    def test_existing_output_is_not_overwritten(self):
        blob, record, _ = self.fixture()
        target = self.output/self.directory
        target.mkdir(parents=True)
        sentinel = target/'keep.txt'
        sentinel.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            prepare.vendor_package(blob, self.output, record)
        self.assertEqual(sentinel.read_bytes(), b'keep')
        self.assertEqual(list(target.iterdir()), [sentinel])


class PinnedArchiveTests(unittest.TestCase):
    def test_all_published_vendor_bytes(self):
        if ARCHIVES is None:
            self.skipTest('supply --archives for the offline 257-package replay')
        packages = prepare.read(HERE/'vendor-acquisition.json')
        expected = prepare.read(HERE/'vendor-files.json.gz')
        self.assertEqual(len(packages), 257)
        with tempfile.TemporaryDirectory(prefix='amm-vendor-replay-') as directory:
            output = Path(directory)/'vendor'
            for package in packages:
                name = package['name']
                blob = (ARCHIVES/(name+'.crate')).read_bytes()
                prepare.vendor_package(blob, output, {
                    'directory': name, 'package_sha256': package['sha256'],
                    'file_count': package['files'],
                    'checksum_file_sha256': expected[name+'/.cargo-checksum.json'],
                })
            actual = {p.relative_to(output).as_posix(): sha(p.read_bytes())
                      for p in output.rglob('*') if p.is_file()}
            self.assertEqual(actual, expected)
            self.assertEqual(len(actual), 8437)
            print(json.dumps({'registry_packages': 257, 'exact_vendor_files': len(actual),
                              'source_files': len(actual)-257, 'network_or_compiler_calls': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--archives', type=Path)
    args, remaining = parser.parse_known_args()
    ARCHIVES = args.archives
    unittest.main(argv=[sys.argv[0], *remaining])
