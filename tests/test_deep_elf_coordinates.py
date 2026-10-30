"""Deep diagnostics use file offsets after reading ELF virtual coordinates."""
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import deep_disassembly as deep
from window_elf_reader import Elf

SELECTOR = 0x1122334455667788


def image(address):
    """One selector, one internal call and one relocated syscall in an ET_DYN."""
    insn = lambda op, regs=0, imm=0: struct.pack('<BBhi', op, regs, 0, imm)
    text = (insn(0x18, 1, SELECTOR & 0xffffffff)
            + insn(0, 0, SELECTOR >> 32)
            + insn(0x85, 0x10, 2) + insn(0x85, 0x10, -1)
            + insn(0x95) + insn(0x95))
    names = b'\0.text\0.shstrtab\0.dynstr\0.dynsym\0.rel.dyn\0'
    labels = b'\0entry\0handler\0sol_log_\0'
    symbols = (bytes(24)
               + struct.pack('<IBBHQQ', 1, 0x12, 0, 1, address, 40)
               + struct.pack('<IBBHQQ', 7, 0x12, 0, 1, address + 40, 8)
               + struct.pack('<IBBHQQ', 15, 0x10, 0, 0, 0, 0))
    data = bytearray(0x100) + text
    headers = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
               (names.index(b'.text'), 1, 6, address, 0x100, len(text), 0, 0, 8, 0)]
    for name, payload, kind, link, info, stride in (
        ('.shstrtab', names, 3, 0, 0, 0),
        ('.dynstr', labels, 3, 0, 0, 0),
        ('.dynsym', symbols, 11, 3, 1, 24),
        ('.rel.dyn', struct.pack('<QQ', address + 24, (3 << 32) | 10), 9, 4, 1, 16),
    ):
        data.extend(bytes(-len(data) % 8))
        headers.append((names.index(name.encode()), kind, 0, 0, len(data),
                        len(payload), link, info, 8, stride))
        data.extend(payload)
    data.extend(bytes(-len(data) % 8))
    table = len(data)
    data.extend(b''.join(struct.pack('<IIQQQQIIQQ', *row) for row in headers))
    data[:64] = struct.pack('<16sHHIQQQIHHHHHH', b'\x7fELF\x02\x01\x01' + bytes(9),
                           3, 247, 1, address, 0, table, 0, 64, 0, 0, 64, len(headers), 2)
    return bytes(data)


class DeepElfCoordinatesTests(unittest.TestCase):
    def read(self, address):
        temporary = self.enterContext(tempfile.TemporaryDirectory())
        path = Path(temporary) / 'fixture.so'
        path.write_bytes(image(address))
        return Elf(path)

    def test_relocated_syscall_keys_match_reader_file_offsets(self):
        for address in (0x100, 0x1000):
            with self.subTest(address=address):
                elf = self.read(address)
                self.assertEqual(elf.relocations[0x118]['symbol'], 'sol_log_')
                self.assertEqual(deep.relocated_syscalls(elf), {0x118: 'sol_log_'})
                self.assertEqual(deep.fingerprint_window(elf, elf.lo, elf.hi)['syscall_sequence'],
                                 ['sol_log_'])

    def test_fallback_entrypoint_maps_to_file_offset(self):
        for address in (0x100, 0x1000):
            with self.subTest(address=address):
                dispatch = deep.recover_anchor_dispatch(self.read(address))
                self.assertEqual(dispatch, {hex(SELECTOR): {
                    'selector': hex(SELECTOR), 'target_address': '0x128', 'target_name': 'handler'}})

    def test_outside_text_entry_still_has_no_fallback_dispatch(self):
        elf = self.read(0x1000)
        raw = bytearray(elf.b)
        struct.pack_into('<Q', raw, 24, 0x2000)
        elf.b = bytes(raw)
        self.assertEqual(deep.recover_anchor_dispatch(elf), {})

    def test_actual_cli_reports_same_calls_and_dispatch_for_both_layouts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'scripts').mkdir()
            for name in ('deep_disassembly.py', 'window_elf_reader.py'):
                shutil.copyfile(ROOT / 'scripts' / name, root / 'scripts' / name)
            source = root / 'evidence/original/fixture/deployed.so'
            source.parent.mkdir(parents=True)
            for address in (0x100, 0x1000):
                with self.subTest(address=address):
                    data = image(address)
                    source.write_bytes(data)
                    output = root / f'packet-{address}'
                    result = subprocess.run(
                        [sys.executable, '-B', str(root / 'scripts/deep_disassembly.py'),
                         '--program', 'fixture', '--output', str(output)],
                        capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    summary = json.loads((output / 'summary.json').read_text())
                    self.assertEqual((summary['total_syscalls'], summary['dispatch_selectors']), (1, 1))
                    self.assertEqual(json.loads((output / 'syscall-usage.json').read_text()), {'sol_log_': 1})
                    fingerprints = json.loads((output / 'fingerprints.json').read_text())
                    self.assertEqual(fingerprints[0]['syscall_sequence'], ['sol_log_'])
                    dispatch = json.loads((output / 'dispatch-table.json').read_text())
                    self.assertEqual(dispatch[hex(SELECTOR)]['target_address'], '0x128')
                    self.assertEqual(source.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
