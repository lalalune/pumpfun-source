"""Mutation controls for the mint-authority seed string and descriptor."""
from pathlib import Path
import copy
import gzip
import json
import os
import shutil
import struct
import tempfile
import unittest
import proof

P = Path(__file__).resolve().parent
R = proof.REPO


class MintAuthoritySeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = proof.Elf(R / proof.ORIGINAL)
        cls.candidate = proof.elf_from_gzip(R / proof.CANDIDATE)
        cls.report = proof.verify_images(cls.original, cls.candidate)

    def image(self, image, blob):
        changed = copy.copy(image)
        changed.b = bytes(blob)
        return changed

    def offset(self, image, address, name):
        section = image.secs[name]
        assert section[3] <= address < section[3] + section[5]
        return section[4] + address - section[3]

    def relocation_offset(self, image, address):
        section = image.secs['.rel.dyn']
        for position in range(section[4], section[4] + section[5], 16):
            if struct.unpack_from('<Q', image.b, position)[0] == address:
                return position
        raise AssertionError(address)

    def mutated(self, image, address, name, format_string, value, delta=0):
        blob = bytearray(image.b)
        struct.pack_into(format_string, blob, self.offset(image, address, name) + delta, value)
        return self.image(image, blob)

    def test_complete(self):
        summary = proof.check(P, R)
        self.assertEqual(
            (summary['string_bytes'], summary['descriptor_bytes'],
             summary['descriptor_raw_bytes'], summary['descriptor_mapped_bytes'],
             summary['new_payload_bytes']),
            (14, 16, 8, 8, 30),
        )

    def test_every_string_byte(self):
        for index in range(proof.STRING['length']):
            with self.subTest(byte=index):
                at = proof.STRING['candidate'] + index
                blob = bytearray(self.candidate.b)
                blob[self.offset(self.candidate, at, '.rodata')] ^= 1
                with self.assertRaises(AssertionError):
                    proof.verify_images(self.original, self.image(self.candidate, blob))

    def test_descriptor_low_word(self):
        for side, image in (('original', self.original), ('candidate', self.candidate)):
            with self.subTest(side=side):
                changed = self.mutated(
                    image, proof.DESCRIPTOR[side], '.data.rel.ro', '<I', 1
                )
                with self.assertRaises(AssertionError):
                    proof.verify_images(
                        changed if side == 'original' else self.original,
                        changed if side == 'candidate' else self.candidate,
                    )

    def test_descriptor_pointer(self):
        for side, image in (('original', self.original), ('candidate', self.candidate)):
            with self.subTest(side=side):
                changed = self.mutated(
                    image, proof.DESCRIPTOR[side], '.data.rel.ro', '<I', 0, 4
                )
                with self.assertRaises(AssertionError):
                    proof.verify_images(
                        changed if side == 'original' else self.original,
                        changed if side == 'candidate' else self.candidate,
                    )

    def test_descriptor_length(self):
        for side, image in (('original', self.original), ('candidate', self.candidate)):
            with self.subTest(side=side):
                changed = self.mutated(
                    image, proof.DESCRIPTOR[side], '.data.rel.ro', '<Q', 15, 8
                )
                with self.assertRaises(AssertionError):
                    proof.verify_images(
                        changed if side == 'original' else self.original,
                        changed if side == 'candidate' else self.candidate,
                    )

    def test_descriptor_relocation_type(self):
        for side, image in (('original', self.original), ('candidate', self.candidate)):
            with self.subTest(side=side):
                position = self.relocation_offset(image, proof.DESCRIPTOR[side])
                blob = bytearray(image.b)
                info = struct.unpack_from('<Q', blob, position + 8)[0]
                struct.pack_into('<Q', blob, position + 8, (info & ~0xffffffff) | 9)
                with self.assertRaises(AssertionError):
                    proof.verify_images(
                        self.image(image, blob) if side == 'original' else self.original,
                        self.image(image, blob) if side == 'candidate' else self.candidate,
                    )

    def test_descriptor_relocation_symbol(self):
        for side, image in (('original', self.original), ('candidate', self.candidate)):
            with self.subTest(side=side):
                position = self.relocation_offset(image, proof.DESCRIPTOR[side])
                blob = bytearray(image.b)
                info = struct.unpack_from('<Q', blob, position + 8)[0]
                struct.pack_into('<Q', blob, position + 8, (1 << 32) | (info & 0xffffffff))
                with self.assertRaises(AssertionError):
                    proof.verify_images(
                        self.image(image, blob) if side == 'original' else self.original,
                        self.image(image, blob) if side == 'candidate' else self.candidate,
                    )

    def test_following_byte_is_not_absorbed(self):
        at = proof.STRING['candidate'] + proof.STRING['length']
        blob = bytearray(self.candidate.b)
        blob[self.offset(self.candidate, at, '.rodata')] ^= 1
        self.assertEqual(
            proof.verify_images(self.original, self.image(self.candidate, blob)),
            self.report,
        )

    def test_candidate_pointer_mismatch(self):
        changed = self.mutated(
            self.candidate, proof.DESCRIPTOR['candidate'], '.data.rel.ro', '<I',
            proof.STRING['candidate'] + 8, 4,
        )
        with self.assertRaises(AssertionError):
            proof.verify_images(self.original, changed)

    def copied(self, change, reseal=False):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary) / 'packet'
            shutil.copytree(P, packet, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            change(packet)
            if reseal:
                inventory = {
                    str(path.relative_to(packet)): proof.sha(path.read_bytes())
                    for path in packet.rglob('*')
                    if path.is_file()
                    and path.name != 'manifest.json'
                    and '__pycache__' not in path.parts
                    and path.suffix != '.pyc'
                }
                (packet / 'manifest.json').write_text(json.dumps(inventory, indent=2) + '\n')
            with self.assertRaises((AssertionError, ValueError)):
                proof.check(packet, R)

    def test_unlisted_file(self):
        self.copied(lambda packet: (packet / 'extra').write_bytes(b'x'))

    def test_symlink(self):
        self.copied(lambda packet: (packet / 'alias').symlink_to('inputs.json'))

    def test_fifo(self):
        self.copied(lambda packet: os.mkfifo(packet / 'pipe'))

    def test_resealed_observations(self):
        def change(packet):
            report = json.loads(gzip.decompress((packet / 'observations.json.gz').read_bytes()))
            report['string']['candidate_ptr'] += 1
            (packet / 'observations.json.gz').write_bytes(
                gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0)
            )
        self.copied(change, True)

    def test_resealed_coverage(self):
        def change(packet):
            delta = json.loads((packet / 'coverage-delta.json').read_bytes())
            delta['new_payload_bytes'] += 1
            (packet / 'coverage-delta.json').write_text(json.dumps(delta))
        self.copied(change, True)

    def test_baseline_tamper(self):
        def change(packet):
            baseline = json.loads((packet / 'baseline/sources.json').read_bytes())
            path = next(iter(baseline['deltas']))
            baseline['deltas'][path] = '0' * 64
            (packet / 'baseline/sources.json').write_text(json.dumps(baseline))
        self.copied(change, True)

    def test_inputs_tamper(self):
        def change(packet):
            pins = json.loads((packet / 'inputs.json').read_bytes())
            path = next(iter(pins))
            pins[path] = '0' * 64
            (packet / 'inputs.json').write_text(json.dumps(pins))
        self.copied(change, True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
