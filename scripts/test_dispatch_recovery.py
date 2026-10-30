#!/usr/bin/env python3
"""Check Anchor dispatch recovery against the archived IDL and a no-IDL capture."""
import json
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from deep_disassembly import _recover_dispatch_target, recover_anchor_dispatch  # noqa: E402
from window_elf_reader import Elf  # noqa: E402


def lddw(dst, value):
    return (struct.pack("<BBHI", 0x18, dst, 0, value & 0xFFFFFFFF)
            + struct.pack("<BBHI", 0x00, 0x00, 0, (value >> 32) & 0xFFFFFFFF))


def call(imm):
    # src=1 pseudo call with byte one 0x10, as emitted for direct calls.
    return struct.pack("<BBhi", 0x85, 0x10, 0, imm)


def fake_elf(instructions, relocations=None, funcs=None, entry=0x40, size=0x120):
    blob = bytearray(size)
    struct.pack_into("<Q", blob, 24, entry)
    for offset, data in instructions.items():
        blob[offset:offset + len(data)] = data
    return SimpleNamespace(b=bytes(blob), lo=0x40, hi=size,
                           text_offset=lambda address: address if 0x40 <= address < size else None,
                           relocations=relocations or {}, funcs=funcs or [])


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

    def test_fallback_scan_does_not_bind_selectors_through_relocated_calls(self):
        # A type-10 relocation marks an extern call whose immediate (-1 here)
        # is a placeholder: the old scan bound the preceding selector literal
        # to the call site itself (0x50).
        elf = fake_elf({
            0x40: lddw(1, 0x1122334455667788),
            0x50: call(-1),                       # extern, relocated
            0x58: lddw(1, 0x99AABBCCDDEEFF00),
            0x68: call(4),                        # internal: 0x68 + 8 + 32 = 0x90
        }, relocations={0x50: {"type": 10}})
        dispatch = recover_anchor_dispatch(elf)
        self.assertEqual(set(dispatch), {"0x99aabbccddeeff00"})
        self.assertEqual(dispatch["0x99aabbccddeeff00"]["target_address"], hex(0x90))

    def test_handler_scan_skips_relocated_extern_calls(self):
        # The handler body starts with a relocated extern call; the recovery
        # must keep scanning to the first internal direct call.
        handler = 0x60
        internal = 0x70
        target = internal + 8 + 2 * 8            # 0x88
        elf = fake_elf({
            0x40: lddw(2, 0x0102030405060708),
            0x50: struct.pack("<BBhi", 0x1d, 0x20, 1, 0),   # jeq r2, +1 -> handler
            handler: call(-1),                    # extern, relocated
            internal: call(2),                    # internal handler call
        }, relocations={handler: {"type": 10}},
           funcs=[{"start": target, "name": "handler"}])
        recovered = _recover_dispatch_target(elf, 0x40)
        self.assertEqual(recovered.get("target_address"), hex(target))
        self.assertEqual(recovered.get("target_name"), "handler")


if __name__ == "__main__":
    unittest.main()
