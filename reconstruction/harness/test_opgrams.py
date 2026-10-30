# Regression cases retained from crypto-projects-x/pumpfun-source PR #1316
# (c845bc248e2a251768c38372c5dcfc65af36a59e); implementation lives in instruction_stream.py.
#!/usr/bin/env python3
"""Opcode n-grams follow the same instruction width as insns()."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('window_analysis', Path(__file__).with_name('win.py'))
win = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(win)


class OpgramTests(unittest.TestCase):
    def test_lddw_tail_is_not_an_opcode(self):
        raw = bytes([0x18, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0x85, 0x10, 0, 0, 0, 0, 0, 0])
        self.assertEqual(win.opgrams(raw, 1), {(0x18,): 1, (0x85,): 1})
        self.assertEqual(win.opgrams(raw, 2), {(0x18, 0x85): 1})
        self.assertEqual([insn[1][0] for insn in win.insns(raw, 0, {})], [0x18, 0x85])

    def test_captured_pump_text_counts_instructions_not_slots(self):
        section = win.ORIG_SECS['.text']
        raw = win.ORIG[section['offset']:section['offset'] + section['size']]
        instructions = lddw = i = 0
        while i < len(raw):
            lddw += raw[i] == 0x18
            i += 16 if raw[i] == 0x18 else 8
            instructions += 1
        self.assertGreater(lddw, 0)
        self.assertEqual(len(raw) // 8, instructions + lddw)
        self.assertEqual(sum(win.opgrams(raw, 1).values()), instructions)


if __name__ == '__main__':
    unittest.main()
