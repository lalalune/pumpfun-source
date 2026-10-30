#!/usr/bin/env python3
"""Check Anchor dispatch recovery against the archived IDL and a no-IDL capture."""
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from deep_disassembly import recover_anchor_dispatch  # noqa: E402
from window_elf_reader import Elf  # noqa: E402


def idl_selectors(program):
    payload = json.loads((REPO / "evidence" / "upstream" / f"{program}.json").read_text())
    return {
        hex(int.from_bytes(bytes(insn["discriminator"]), "little"))
        for insn in payload["instructions"]
    }


class AnchorDispatchRecoveryTests(unittest.TestCase):
    def test_pump_recovers_every_idl_selector(self):
        elf = Elf(REPO / "evidence" / "original" / "pump" / "deployed.so")
        dispatch = recover_anchor_dispatch(elf)
        expected = idl_selectors("pump")

        self.assertEqual(len(expected), 56)
        self.assertEqual(len(dispatch), 56)
        self.assertEqual(set(dispatch), expected)
        for selector, entry in dispatch.items():
            self.assertEqual(entry["selector"], selector)
            self.assertIsNotNone(entry["target_address"], selector)

    def test_programs_with_idl_recover_their_selector_counts(self):
        for program, count in (("pump_amm", 38), ("pump_fees", 31)):
            elf = Elf(REPO / "evidence" / "original" / program / "deployed.so")
            dispatch = recover_anchor_dispatch(elf)
            self.assertEqual(len(dispatch), count, program)
            self.assertTrue(set(dispatch) <= idl_selectors(program), program)

    def test_mayhem_without_idl_falls_back_without_crashing(self):
        elf = Elf(REPO / "evidence" / "original" / "mayhem" / "deployed.so")
        dispatch = recover_anchor_dispatch(elf)
        self.assertIsInstance(dispatch, dict)


if __name__ == "__main__":
    unittest.main()
