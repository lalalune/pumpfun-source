"""Packet verifiers must check the folder, not only the files their manifest names.

Every packet under `research/` pins its files in `MANIFEST.json` and its verifier
hashes the entries the manifest lists. A file the packet ships with no entry is
never named, so it is never hashed: the packet carries it, the record does not
mention it, and the verifier still reports success.
"""
import json
import importlib.util
import py_compile
import struct
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'research'
PACKET = RESEARCH / 'pump-trade-cu-scaling-20261030'
FEE_PACKET = RESEARCH / 'pump-fees-authority-transition-sequences-20261029'
MARKER = 'packet file set differs from MANIFEST.json'
MEMBER = 'packet member differs from MANIFEST.json'
WALKS = ('rglob(', 'iterdir(', 'os.walk(', 'os.scandir(')


def verifiers():
    for path in sorted(RESEARCH.glob('*/verify.py')):
        text = path.read_text(encoding='utf-8')
        if 'MANIFEST.json' in text:
            yield path, text


def manifests():
    """Packets that ship a MANIFEST.json, whatever their verifier does with it."""
    for path in sorted(RESEARCH.glob('*/verify.py')):
        if any(entry.name == 'MANIFEST.json' for entry in path.parent.iterdir()):
            yield path, path.read_text(encoding='utf-8')


def run(packet):
    return subprocess.run(
        [sys.executable, '-B', str(packet / 'verify.py'),
         '--images', json.dumps({'original': '/nonexistent/original.so',
                                 'candidate': '/nonexistent/candidate.so'})],
        cwd=packet, capture_output=True, text=True)


class PacketManifestCensus(unittest.TestCase):
    def test_every_manifest_verifier_walks_its_packet(self):
        """A verifier that trusts MANIFEST.json has to compare it with the folder."""
        missing = [str(path.relative_to(ROOT)) for path, text in verifiers()
                   if not any(walk in text for walk in WALKS)]
        self.assertEqual([], missing)

    def test_unlisted_file_is_refused_before_any_image_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / 'packet'
            shutil.copytree(PACKET, packet)
            (packet / 'runtime' / 'unlisted.bin').write_bytes(b'\x00')
            result = run(packet)
        self.assertEqual(1, result.returncode)
        self.assertIn(MARKER, result.stdout + result.stderr)
        self.assertIn('runtime/unlisted.bin', result.stdout + result.stderr)
        # Stopped at the packet, not at the missing images handed to it.
        self.assertNotIn('Nonexistent', result.stdout + result.stderr)
        self.assertNotIn('/nonexistent/', result.stdout + result.stderr)

    def test_pristine_packet_reaches_the_image_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / 'packet'
            shutil.copytree(PACKET, packet)
            result = run(packet)
        self.assertNotIn(MARKER, result.stdout + result.stderr)
        self.assertIn('/nonexistent/', result.stdout + result.stderr)

    def test_every_packet_that_ships_a_manifest_reads_it(self):
        """Publishing a file record and never consulting it records nothing."""
        unread = [str(path.relative_to(ROOT)) for path, text in manifests()
                  if 'MANIFEST.json' not in text]
        self.assertEqual([], unread)

    def test_altered_packet_member_is_refused_before_any_image_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / 'packet'
            shutil.copytree(FEE_PACKET, packet)
            (packet / 'README.md').write_bytes(b'altered packet member\n')
            result = run(packet)
        self.assertEqual(1, result.returncode)
        self.assertIn(f'{MEMBER}: README.md', result.stdout + result.stderr)
        self.assertNotIn('/nonexistent/', result.stdout + result.stderr)

    def test_added_packet_member_is_refused_before_any_image_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / 'packet'
            shutil.copytree(FEE_PACKET, packet)
            (packet / 'runtime' / 'unlisted.bin').write_bytes(b'\x00')
            result = run(packet)
        self.assertEqual(1, result.returncode)
        self.assertIn(MARKER, result.stdout + result.stderr)
        self.assertIn('runtime/unlisted.bin', result.stdout + result.stderr)
        self.assertNotIn('/nonexistent/', result.stdout + result.stderr)


    def test_all_three_fee_packet_admissions_preserve_pristine_and_reject_tampering(self):
        names = ('pump-fees-authority-transition-sequences-20261029',
                 'pump-fees-buyback-init-withdraw-sequences-20261030',
                 'pump-fees-social-claim-sequences-20261030')
        for name in names:
            for mode in ('pristine', 'changed', 'extra', 'nested', 'symlink', 'cache', 'duplicate'):
                with self.subTest(packet=name, mode=mode), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    packet = root / 'packet'
                    shutil.copytree(RESEARCH / name, packet)
                    if mode == 'changed': (packet / 'README.md').write_bytes(b'changed')
                    elif mode == 'extra': (packet / 'runtime/unlisted.bin').write_bytes(b'extra')
                    elif mode == 'nested': (packet / 'runtime/MANIFEST.json').write_bytes(b'{}')
                    elif mode == 'symlink':
                        source = packet / 'README.md'
                        source.replace(root / 'README.md')
                        source.symlink_to(root / 'README.md')
                    elif mode == 'cache':
                        folder = packet / '__pycache__'
                        folder.mkdir()
                        (folder / 'producer.pyc').write_bytes(b'unlisted bytecode')
                    elif mode == 'duplicate':
                        path = packet / 'MANIFEST.json'
                        manifest = json.loads(path.read_text())
                        manifest['files'].append(dict(manifest['files'][0]))
                        path.write_text(json.dumps(manifest))
                    result = run(packet)
                    text = result.stdout + result.stderr
                    if mode == 'pristine':
                        self.assertIn('/nonexistent/', text)
                        self.assertNotIn('packet file set differs', text)
                        self.assertNotIn('packet member differs', text)
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertNotIn('/nonexistent/', text)
                        self.assertTrue(any(mark in text for mark in
                            ('packet file set differs', 'packet member differs', 'symlink',
                             'cached Python bytecode', 'duplicate packet manifest path')), text)

    def test_nested_manifest_name_is_not_an_ignored_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary) / 'packet'
            shutil.copytree(PACKET, packet)
            (packet / 'runtime/MANIFEST.json').write_text('{}')
            result = run(packet)
            self.assertIn(MARKER, result.stdout + result.stderr)
            self.assertIn('runtime/MANIFEST.json', result.stdout + result.stderr)

    def test_valid_cached_producer_cannot_bypass_source_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = root / 'packet'
            shutil.copytree(PACKET, packet)
            producer = packet / 'producer.py'
            source = root / 'cached_source.py'
            marker = root / 'executed'
            source.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n')
            cached = Path(importlib.util.cache_from_source(str(producer)))
            cached.parent.mkdir(parents=True, exist_ok=True)
            py_compile.compile(str(source), cfile=str(cached), doraise=True)
            data = bytearray(cached.read_bytes())
            data[8:16] = struct.pack('<II', int(producer.stat().st_mtime), producer.stat().st_size)
            cached.write_bytes(data)
            result = run(packet)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('cached Python bytecode', result.stdout + result.stderr)
            self.assertFalse(marker.exists(), 'unlisted cached producer executed')

    def test_symlink_and_repeated_manifest_path_are_rejected(self):
        for mode in ('symlink', 'duplicate'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                packet = root / 'packet'
                shutil.copytree(PACKET, packet)
                if mode == 'symlink':
                    producer = packet / 'producer.py'
                    outside = root / 'producer.py'
                    producer.replace(outside)
                    producer.symlink_to(outside)
                else:
                    path = packet / 'MANIFEST.json'
                    data = json.loads(path.read_text())
                    data['files'].append(dict(data['files'][0]))
                    path.write_text(json.dumps(data))
                result = run(packet)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('symlink' if mode == 'symlink' else 'duplicate packet manifest path',
                              result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
