"""A comparison's dst field is a read, not a pointer-register clobber."""
import struct
import unittest
from coords import sites


def instruction(op, regs=0, offset=0, immediate=0):
    return struct.pack('<BBhi', op, regs, offset, immediate)


class BranchPointerTests(unittest.TestCase):
    path = b'programs/pump/src/example.rs'
    sections = {'.rodata': {'addr': 0x2000, 'offset': 0, 'size': len(path)}}

    def descriptor(self, between):
        return (instruction(0x18, 1, immediate=0x2000) + bytes(8) + between +
                instruction(0x7b, 0x1a, -16) +
                instruction(0x7a, 10, -8, len(self.path)) +
                instruction(0x62, 10, 0, 42))

    def test_comparison_does_not_kill_pointer(self):
        # Zero displacement makes both comparison outcomes use the same store.
        for opcode in (0x15, 0x1d, 0x55, 0x5d, 0x16, 0x1e):
            with self.subTest(opcode=hex(opcode)):
                result = sites(self.path, self.sections, 0,
                               self.descriptor(instruction(opcode, 1)))
                self.assertEqual([(row['path'], row['line']) for row in result],
                                 [(self.path.decode(), 42)])

    def test_real_writes_and_calls_still_kill_pointer(self):
        for opcode in (0xb7, 0x07, 0xbf, 0x79, 0x85, 0x8d):
            with self.subTest(opcode=hex(opcode)):
                self.assertEqual(sites(self.path, self.sections, 0,
                                       self.descriptor(instruction(opcode, 1))), [])


if __name__ == '__main__': unittest.main()
