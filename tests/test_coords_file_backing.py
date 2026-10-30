"""Source-coordinate paths must come from file-backed ELF section bytes."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'reconstruction/harness'
sys.path.insert(0, str(HARNESS))
from coords import read_cstr_at, sites
from score import normalize, sections


PATH = b'programs/pump/src/example.rs'


def candidate(section_type, section_name='.bss'):
    """An unstripped SBPF ELF whose descriptor points at section virtual memory.

    For SHT_NOBITS the path bytes are only inactive file padding at sh_offset;
    for SHT_PROGBITS the identical bytes actually belong to the section.
    """
    def instruction(op, regs=0, offset=0, immediate=0):
        return struct.pack('<BBhi', op, regs, offset, immediate)

    raw = (instruction(0x18, 1, immediate=0x2000) + bytes(8)
           + instruction(0x7b, 0x1a, -16)
           + instruction(0x7a, 10, -8, len(PATH))
           + instruction(0x62, 10, 0, 42) + instruction(0x95))
    blob = bytearray(768)
    blob[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHI', blob, 16, 3, 247, 1)
    struct.pack_into('<Q', blob, 40, 64)
    struct.pack_into('<H', blob, 52, 64)
    struct.pack_into('<HHH', blob, 58, 64, 6, 1)
    names = b'\0.shstrtab\0.text\0.strtab\0.symtab\0' + section_name.encode() + b'\0'
    blob[448:448 + len(names)] = names
    blob[512:512 + len(raw)] = raw
    blob[600:600 + len(PATH)] = PATH
    blob[640:648] = b'\0source\0'
    headers = [
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 3, 0, 0, 448, len(names), 0, 0, 1, 0),
        (11, 1, 6, 0x1000, 512, len(raw), 0, 0, 8, 0),
        (17, 3, 0, 0, 640, 8, 0, 0, 1, 0),
        (25, 2, 0, 0, 680, 48, 3, 1, 8, 24),
        (33, section_type, 3, 0x2000, 600, len(PATH), 0, 0, 8, 0),
    ]
    for index, header in enumerate(headers):
        struct.pack_into('<IIQQQQIIQQ', blob, 64 + 64 * index, *header)
    struct.pack_into('<IBBHQQ', blob, 704, 1, 18, 0, 2, 0x1000, len(raw))
    return bytes(blob), raw


class CoordinateFileBackingTests(unittest.TestCase):
    def test_nobits_is_not_a_source_string_even_when_offset_points_to_one(self):
        for name in ('.bss', '.rodata'):
            with self.subTest(name=name):
                blob, raw = candidate(8, name)
                parsed = sections(blob)
                self.assertIsNone(read_cstr_at(blob, parsed, 0x2000, len(PATH)))
                self.assertEqual(sites(blob, parsed, 0x1000, raw), [])

    def test_progbits_coordinates_are_preserved_independent_of_section_name(self):
        for name in ('.bss', '.rodata'):
            with self.subTest(name=name):
                blob, raw = candidate(1, name)
                parsed = sections(blob)
                self.assertEqual(read_cstr_at(blob, parsed, 0x2000, len(PATH)), PATH)
                self.assertEqual(sites(blob, parsed, 0x1000, raw)[0]['path'], PATH.decode())

    def test_cli_omits_nobits_coordinate_but_recovers_file_backed_control(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'candidate.so'
            for section_type in (8, 1):
                with self.subTest(section_type=section_type):
                    path.write_bytes(candidate(section_type)[0])
                    result = subprocess.run(
                        [sys.executable, '-B', str(HARNESS / 'coords.py'),
                         'fn', '0x1000', '--cand', str(path)],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    rows = json.loads(result.stdout)
                    self.assertEqual([row['path'] for row in rows],
                                     [] if section_type == 8 else [PATH.decode()])

    def test_nobits_virtual_range_still_participates_in_normalization(self):
        nobits, raw = candidate(8)
        progbits, _ = candidate(1)
        self.assertEqual(normalize(raw, 0x1000, sections(nobits)),
                         normalize(raw, 0x1000, sections(progbits)))
        self.assertEqual(normalize(raw, 0x1000, sections(nobits))[4:8], bytes(4))


if __name__ == '__main__':
    unittest.main()
