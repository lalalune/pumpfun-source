"""Legacy SBPFv0/v1 control-flow opcode admission regressions for reconstruction/harness/control_flow.py."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

HARNESS = Path(__file__).resolve().parents[1] / 'reconstruction/harness'
sys.path.insert(0, str(HARNESS))

from control_flow import analyze  # noqa: E402
from test_elf_symbols import fixture  # noqa: E402


def insn(op, regs=0, offset=0, immediate=0):
    return struct.pack('<BBhi', op, regs, offset, immediate)


class ControlFlowSBPFOpcodeTests(unittest.TestCase):
    def test_class6_opcodes_are_not_decoded_as_jumps_calls_or_exits(self):
        for op in (0x06, 0x0e, 0x16, 0x1e, 0x86, 0x8e, 0x96, 0x9e):
            with self.subTest(opcode=hex(op)):
                report = analyze(insn(op, offset=-1, immediate=2) + insn(0x95))
                self.assertEqual(report['calls'], [])
                self.assertEqual(report['cyclic_regions'], [])
                self.assertTrue(all(block['reachable'] for block in report['blocks']))
                self.assertEqual(
                    report['diagnostics'],
                    [{'offset': 0, 'opcode': op, 'error': 'unsupported control-flow opcode'}],
                )

    def test_cli_flags_class6_opcode_inside_legacy_elf_header(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = fixture()
            struct.pack_into('<I', image, 0x30, 0)
            image[424:440] = insn(0x86, immediate=2) + insn(0x95)
            candidate, output = root / 'candidate.so', root / 'cfg.json'
            candidate.write_bytes(image)
            result = subprocess.run(
                [
                    sys.executable, '-B', str(HARNESS / 'control_flow.py'),
                    str(candidate), '--start', '0x1000', '--size', '16', '--json', str(output),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            saved = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(saved['calls'], [])
            self.assertEqual(saved['diagnostics'][0]['error'], 'unsupported control-flow opcode')

    def test_unassigned_class5_opcodes_report_diagnostics_instead_of_edges_or_exits(self):
        for op in (0x0d, 0x9d, 0xe5, 0xed, 0xf5, 0xfd):
            with self.subTest(opcode=hex(op)):
                report = analyze(insn(op, offset=-1) + insn(0x95))
                self.assertEqual(report['calls'], [])
                self.assertEqual(report['cyclic_regions'], [])
                self.assertTrue(all(block['reachable'] for block in report['blocks']))
                self.assertEqual(
                    report['diagnostics'],
                    [{'offset': 0, 'opcode': op, 'error': 'unsupported control-flow opcode'}],
                )

    def test_callx_validates_legacy_register_number(self):
        for reg in range(11):
            with self.subTest(valid_register=reg):
                report = analyze(insn(0x8d, immediate=reg) + insn(0x95))
                self.assertEqual(report['diagnostics'], [])
                self.assertEqual(report['calls'], [{'offset': 0, 'kind': 'indirect', 'register': reg}])

        for bad_reg in (-1, 11, 258):
            with self.subTest(invalid_register=bad_reg):
                report = analyze(insn(0x8d, immediate=bad_reg) + insn(0x95))
                self.assertEqual(report['calls'], [])
                self.assertEqual(
                    report['diagnostics'],
                    [{'offset': 0, 'register': bad_reg, 'error': 'invalid indirect call register'}],
                )

    def test_all_valid_sbpf_v1_conditional_jumps_remain_supported(self):
        valid_cond = (
            0x15, 0x1d, 0x25, 0x2d, 0x35, 0x3d, 0x45, 0x4d,
            0x55, 0x5d, 0x65, 0x6d, 0x75, 0x7d,
            0xa5, 0xad, 0xb5, 0xbd, 0xc5, 0xcd, 0xd5, 0xdd,
        )
        for op in valid_cond:
            with self.subTest(opcode=hex(op)):
                report = analyze(insn(op, offset=1) + insn(0xb7) + insn(0x95))
                self.assertEqual(report['diagnostics'], [])
                self.assertEqual([e['kind'] for e in report['blocks'][0]['successors']], ['taken', 'fallthrough'])


if __name__ == '__main__':
    unittest.main()
