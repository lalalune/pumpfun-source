import struct
import unittest
from control_flow import analyze


def insn(op, regs=0, offset=0, immediate=0):
    return struct.pack('<BBhi',op,regs,offset,immediate)


class ControlFlowTests(unittest.TestCase):
    def test_straight_line_exit(self):
        result=analyze(insn(0xb7)+insn(0x95))
        self.assertEqual(result['instruction_count'],2)
        self.assertEqual(len(result['blocks']),1)
        self.assertEqual(result['blocks'][0]['successors'],[])

    def test_conditional_diamond(self):
        result=analyze(insn(0x15,offset=2)+insn(0xb7)+insn(0x05,offset=1)+insn(0xb7)+insn(0x95))
        self.assertEqual([b['offset'] for b in result['blocks']],[0,8,24,32])
        self.assertEqual([e['target'] for e in result['blocks'][0]['successors']],[24,8])
        self.assertTrue(all(b['reachable'] for b in result['blocks']))

    def test_backward_loop_and_unreachable_tail(self):
        result=analyze(insn(0x05,offset=-1)+insn(0x95))
        self.assertEqual(result['blocks'][0]['successors'][0]['target'],0)
        self.assertFalse(result['blocks'][1]['reachable'])

    def test_lddw_continuation_is_not_a_call_or_instruction(self):
        result=analyze(insn(0x18)+insn(0x85,regs=0x10,immediate=4)+insn(0x95))
        self.assertEqual(result['instruction_count'],2);self.assertEqual(result['calls'],[])
        result=analyze(insn(0x05,offset=1)+insn(0x18)+bytes(8)+insn(0x95))
        self.assertIn('continuation',result['diagnostics'][0]['error'])

    def test_call_classes_and_external_branch(self):
        result=analyze(insn(0x85,regs=0x10,immediate=4)+insn(0x85,regs=0x10,immediate=-1)+insn(0x8d,immediate=3)+insn(0x05,offset=10),start=0x1000)
        self.assertEqual([c['kind'] for c in result['calls']],['direct','syscall_or_relocated','indirect'])
        self.assertEqual(result['calls'][0]['target'],0x1028)
        self.assertFalse(result['blocks'][0]['successors'][0]['internal'])

    def test_bad_ranges_and_truncated_lddw(self):
        for raw,start in [(b'',0),(bytes(7),0),(insn(0x18),0),(insn(0x95),1)]:
            with self.assertRaises(ValueError):analyze(raw,start)


if __name__=='__main__':unittest.main()
