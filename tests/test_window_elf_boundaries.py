"""Logical SBF instructions, ELF addresses and full function extents are distinct."""
from pathlib import Path
import struct
import gzip
import hashlib
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from window_elf_reader import Elf


def image(text, *, address=0x100, function_size=None, relocations=()):
    names = b'\0.text\0.shstrtab\0.strtab\0.symtab\0.rel.dyn\0'
    labels = {name: names.index(name.encode()) for name in ['.text', '.shstrtab', '.strtab', '.symtab', '.rel.dyn']}
    data = bytearray(0x100)
    data.extend(text)
    rows = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (labels['.text'], 1, 6, address, 0x100, len(text), 0, 0, 8, 0)]
    for name, payload, kind, link, entry_size in [
        ('.shstrtab', names, 3, 0, 0),
        ('.strtab', b'\0entry\0', 3, 0, 0),
        ('.symtab', bytes(24) + struct.pack('<IBBHQQ', 1, 0x12, 0, 1, address,
                                          len(text) if function_size is None else function_size), 2, 3, 24),
        ('.rel.dyn', b''.join(struct.pack('<QQ', address + offset, typ) for offset, typ in relocations), 9, 0, 16)]:
        rows.append((labels[name], kind, 0, 0, len(data), len(payload), link, 0, 8, entry_size))
        data.extend(payload)
    table = len(data)
    data.extend(b''.join(struct.pack('<IIQQQQIIQQ', *row) for row in rows))
    data[:64] = struct.pack('<16sHHIQQQIHHHHHH', b'\x7fELF\x02\x01\x01' + bytes(9),
                            3, 247, 1, address, 0, table, 0, 64, 0, 0, 64, len(rows), 2)
    return data


EXIT = struct.pack('<BBhi', 0x95, 0, 0, 0)


class WindowElfBoundaries(unittest.TestCase):
    def read(self, data):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        path = Path(directory) / 'fixture.so'
        path.write_bytes(data)
        return Elf(path)

    def test_lddw_continuation_is_neither_a_call_nor_an_entry(self):
        text = struct.pack('<BBhi', 0x18, 0, 0, 123) + struct.pack('<BBhi', 0x85, 0x10, 0, 1) + EXIT * 2
        elf = self.read(image(text))
        self.assertEqual(elf.calls, {})
        self.assertEqual(elf.entries, [elf.lo])
        self.assertEqual(elf.normalized[elf.lo:elf.hi], text)

    def test_truncated_lddw_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'truncated.*instruction'):
            self.read(image(struct.pack('<BBhi', 0x18, 0, 0, 123)))

    def test_symbol_and_relocation_addresses_map_to_file_offsets(self):
        signatures = []
        for address in [0x100, 0x1000]:
            text = (struct.pack('<BBhi', 0x18, 0, 0, address + 24) + bytes(8)
                    + struct.pack('<BBhi', 0x85, 0x10, 0, -1) + EXIT)
            elf = self.read(image(text, address=address, relocations=[(0, 8), (16, 10)]))
            self.assertEqual(elf.funcs, [{'name': 'entry', 'start': elf.lo, 'size': 32}])
            self.assertEqual(elf.entries, [elf.lo, elf.lo + 24])
            self.assertEqual(elf.calls, {})
            signatures.append((elf.normalized[elf.lo:elf.hi], elf.pattern(elf.lo, 32)))
        self.assertEqual(signatures[0], signatures[1])

    def test_function_must_fit_entirely_in_text(self):
        with self.assertRaisesRegex(ValueError, 'function.*extent'):
            self.read(image(EXIT, function_size=16))

    def test_text_extent_cannot_exceed_file_bytes(self):
        data = image(EXIT)
        table = struct.unpack_from('<Q', data, 40)[0]
        struct.pack_into('<Q', data, table + 64 + 32, len(data) + 8)
        with self.assertRaisesRegex(ValueError, 'section.*file|text.*extent'):
            self.read(data)


    def test_relocation_must_fit_its_file_backed_section(self):
        with self.assertRaisesRegex(ValueError, 'relocation.*section'):
            self.read(image(EXIT*2, relocations=[(12, 8)]))

    def test_text_relocation_must_target_a_logical_instruction(self):
        text = struct.pack('<BBhi', 0x18, 0, 0, 0) + bytes(8) + EXIT
        for offset, kind in ((4, 8), (8, 8), (4, 10)):
            with self.subTest(offset=offset, kind=kind), self.assertRaisesRegex(ValueError, 'relocation.*instruction'):
                self.read(image(text, relocations=[(offset, kind)]))

    def test_retained_reference_and_candidate_results_are_unchanged(self):
        root = Path(__file__).resolve().parents[1]
        expected = EXPECTED_READER_RESULTS
        for name, digest in expected.items():
            with self.subTest(name=name):
                if name == 'canonical-candidate':
                    image_path = root / 'reconstruction/pump-main/lanes/v3-sell-payment-layout/candidate.so.gz'
                    elf = self.read(gzip.decompress(image_path.read_bytes()))
                else:
                    elf = Elf(root / name)
                row = {'funcs': elf.funcs, 'entries': elf.entries, 'calls': elf.calls,
                       'relocations': elf.relocations,
                       'normalized_sha256': hashlib.sha256(elf.normalized).hexdigest()}
                # JSON keys for offset maps are strings in retained snapshots.
                row = json.loads(json.dumps(row))
                actual = hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',', ':')).encode()).hexdigest()
                self.assertEqual(actual, digest)


EXPECTED_READER_RESULTS = {'canonical-candidate': 'a170f43093b10b21ad6056ba72301af9f3324c5edbf5395aa6eb50be378de581', 'evidence/dependencies/associated_token/deployed.so': '0ace4ff2fde5e63b94cb40df0ce2dbb3045fa2d3f3418120e858a231a6a949cc', 'evidence/dependencies/donation_relay/deployed.so': 'd9b5c37c5b07670fd2ecf0bd56739952f8d1a33417cda6cb3644b68fe987c111', 'evidence/dependencies/spl_token/deployed.so': '528fc6fcf12a3ae29649a959b24595c87c0dc1dd9d3413ac80f89db0eac6e04d', 'evidence/dependencies/spl_token_2022/deployed.so': 'db2959a0a13d958e2ffc8c0f29adf06cf50569e682c1fb3040858b630a19793f', 'evidence/dependencies/token_metadata/deployed.so': 'f9a9538789b689f9f2c5b24d0c25f25179710a477bb0a9a46d128e5a411ec66a', 'evidence/original/mayhem/deployed.so': 'ebd71af1a7d3a7b3d6bf256ac58e3622c30cb2428e65d8ba24994e42b107cb56', 'evidence/original/pump/deployed.so': '6454230cae38921499987d920bd856316d5200d32b5a3548ceb5c1370c2e21b1', 'evidence/original/pump_amm/deployed.so': '1f659a8e98c70e73b01829eea538908f0b97ec01f18fda712dde5ffe1090671a', 'evidence/original/pump_fees/deployed.so': '6884c7649cbfd640e6d5c1852f97a6cef23c4a5da640228093ed4194a5b6f7fd'}

if __name__ == '__main__':
    unittest.main()
