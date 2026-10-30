#!/usr/bin/env python3
"""Deep disassembly analysis of deployed Solana BPF programs.

Produces per-window disassembly with:
- Full BPF instruction decode (opcode, operands, mnemonics)
- Syscall identification and frequency
- Error string extraction from rodata cross-references
- Anchor dispatch table recovery (instruction selectors)
- Control flow graph edges (branch targets)
- Stack frame analysis (frame pointer usage)
- Bytecode signature fingerprints for pattern matching

Usage:
    python3 scripts/deep_disassembly.py --program pump --output research/pump-deep-disasm-20261028
"""
import argparse
import bisect
import collections
import gzip
import hashlib
import io
import json
import os
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from window_elf_reader import Elf

# BPF opcode mnemonics
BPF_ALU64  = 0x07
BPF_ALU32  = 0x04
BPF_LD     = 0x00
BPF_LDX    = 0x01
BPF_ST     = 0x02
BPF_STX    = 0x03
BPF_JMP    = 0x05
BPF_JMP32  = 0x06

REGS = ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10"]

SYSCALL_NAMES = {
    # SBPF hash_symbol_name: seed-zero MurmurHash3 x86_32 of symbol bytes.
    0x207559bd: "sol_log_",
    0x5c2a3178: "sol_log_64_",
    0x52ba5096: "sol_log_compute_units_",
    0x9377323c: "sol_create_program_address",
    0x48504a38: "sol_try_find_program_address",
    0x11f49d86: "sol_sha256",
    0xd7793abb: "sol_keccak256",
    0x17e40350: "sol_secp256k1_recover",
    0x717cc4a3: "sol_memcpy_",
    0x434371f8: "sol_memmove_",
    0x5fdcde31: "sol_memcmp_",
    0x3770fb22: "sol_memset_",
    0xa22b9c85: "sol_invoke_signed_c",
    0xd7449092: "sol_invoke_signed_rust",
    0x83f00e8f: "sol_alloc_free_",
    0xa226d3eb: "sol_set_return_data",
    0x5d2245e4: "sol_get_return_data",
    0x7317b434: "sol_log_data",
    0xadb8efc8: "sol_get_processed_sibling_instruction",
    0x85532d94: "sol_get_stack_height",
    0xaa2607ca: "sol_curve_validate_point",
    0xdd1c41a6: "sol_curve_group_op",
    0x60a40880: "sol_curve_multiscalar_mul",
    0xae0c318b: "sol_alt_bn128_group_op",
    0x780e4c15: "sol_big_mod_exp",
    0xedef5aee: "sol_remaining_compute_units",
    0xc4947c21: "sol_poseidon",
    0x5be92f4a: "sol_get_epoch_stake",
    0xd56b5fe9: "sol_get_clock_sysvar",
    0xbf7188f6: "sol_get_rent_sysvar",
    0x188a0031: "sol_get_last_restart_slot",
}


def decode_instruction(b, offset, elf):
    """Decode a single BPF instruction into a structured record."""
    if offset + 8 > len(b):
        return None, 8
    opcode = b[offset]
    regs = b[offset + 1]
    dst_reg = regs & 0xF
    src_reg = (regs >> 4) & 0xF
    off = struct.unpack_from("<h", b, offset + 2)[0]
    imm = struct.unpack_from("<i", b, offset + 4)[0]

    size = 16 if opcode == 0x18 else 8
    result = {
        "offset": offset,
        "hex": b[offset:offset + size].hex(),
        "opcode": f"0x{opcode:02x}",
        "dst": dst_reg,
        "src": src_reg,
        "off": off,
        "imm": imm,
    }

    dst = REGS[dst_reg] if dst_reg < 11 else f"r{dst_reg}"
    src = REGS[src_reg] if src_reg < 11 else f"r{src_reg}"

    # Decode mnemonic
    if opcode == 0x95:
        result["mnemonic"] = "exit"
    elif opcode == 0x85:
        # src_reg is the decoded nibble, not the packed register byte.
        # Type-10 external calls also use src=1 with a placeholder immediate.
        if src_reg == 1 and elf.relocations.get(offset, {}).get("type") != 10:
            target = offset + 8 + imm * 8
            target_name = None
            for f in elf.funcs:
                if f["start"] == target:
                    target_name = f["name"]
                    break
            result["mnemonic"] = f"call {target_name or hex(target)}"
            result["call_target"] = target
            result["call_name"] = target_name
        elif src_reg == 0:
            uimm = imm & 0xFFFFFFFF
            name = SYSCALL_NAMES.get(uimm, f"syscall_{uimm:#010x}")
            result["mnemonic"] = f"syscall {name}"
            result["syscall"] = name
        else:
            # Relocated external call
            reloc = elf.relocations.get(offset, {})
            sym = reloc.get("symbol", "?")
            result["mnemonic"] = f"call_extern {sym}"
            result["extern_symbol"] = sym
    elif opcode == 0x8d:
        # CALL_REG's register field changes across SBPF versions. The target
        # address is runtime data, not a statically resolved direct call.
        image = getattr(elf, "b", b"")
        version = struct.unpack_from("<I", image, 48)[0] if len(image) >= 52 else None
        register = (imm if version in (0, 1) else src_reg if version == 2
                    else dst_reg if version in (3, 4) else None)
        if register is not None and 0 <= register <= 10:
            result["mnemonic"] = f"callx r{register}"
            result["indirect_call_register"] = register
        else:
            result["mnemonic"] = f"raw_{opcode:#04x} {dst},{src},{off},{imm}"
    elif opcode == 0x18:
        imm2 = struct.unpack_from("<i", b, offset + 12)[0]
        val64 = (imm & 0xFFFFFFFF) | (imm2 << 32)
        result["mnemonic"] = f"lddw {dst}, {val64:#018x}"
        result["imm64"] = val64
    elif opcode == 0x05:
        target = offset + 8 + off * 8
        result["mnemonic"] = f"ja {off:+d} ({hex(target)})"
        result["branch_target"] = target
    elif opcode & 0xF0 in (0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
                            0xa0, 0xb0, 0xc0, 0xd0) and opcode & 0x07 == 0x05:
        target = offset + 8 + off * 8
        cond_map = {
            0x15: "jeq", 0x1d: "jeq", 0x25: "jgt", 0x2d: "jgt",
            0x35: "jge", 0x3d: "jge", 0x45: "jset", 0x4d: "jset",
            0x55: "jne", 0x5d: "jne", 0x65: "jsgt", 0x6d: "jsgt",
            0x75: "jsge", 0x7d: "jsge", 0xa5: "jlt", 0xad: "jlt",
            0xb5: "jle", 0xbd: "jle", 0xc5: "jslt", 0xcd: "jslt",
            0xd5: "jsle", 0xdd: "jsle",
        }
        cond = cond_map.get(opcode, f"j?{opcode:#04x}")
        if opcode & 0x08:
            result["mnemonic"] = f"{cond} {dst}, {src}, {off:+d} ({hex(target)})"
        else:
            result["mnemonic"] = f"{cond} {dst}, {imm}, {off:+d} ({hex(target)})"
        result["branch_target"] = target
    elif opcode in (0xd4, 0xdc):
        # Endian conversion uses the immediate as a bit width; opcode bit 3
        # selects the direction, not a register operand.
        direction = "le" if opcode == 0xd4 else "be"
        result["mnemonic"] = f"{direction}{imm} {dst}"
    elif opcode & 0x07 == 0x04 or opcode & 0x07 == 0x07:
        alu_map = {
            0x04: "add32", 0x07: "add64", 0x0c: "add32", 0x0f: "add64",
            0x14: "sub32", 0x17: "sub64", 0x1c: "sub32", 0x1f: "sub64",
            0x24: "mul32", 0x27: "mul64", 0x2c: "mul32", 0x2f: "mul64",
            0x34: "div32", 0x37: "div64", 0x3c: "div32", 0x3f: "div64",
            0x44: "or32",  0x47: "or64",  0x4c: "or32",  0x4f: "or64",
            0x54: "and32", 0x57: "and64", 0x5c: "and32", 0x5f: "and64",
            0x64: "lsh32", 0x67: "lsh64", 0x6c: "lsh32", 0x6f: "lsh64",
            0x74: "rsh32", 0x77: "rsh64", 0x7c: "rsh32", 0x7f: "rsh64",
            0x84: "neg32", 0x87: "neg64",
            0x94: "mod32", 0x97: "mod64", 0x9c: "mod32", 0x9f: "mod64",
            0xa4: "xor32", 0xa7: "xor64", 0xac: "xor32", 0xaf: "xor64",
            0xb4: "mov32", 0xb7: "mov64", 0xbc: "mov32", 0xbf: "mov64",
            0xc4: "arsh32", 0xc7: "arsh64", 0xcc: "arsh32", 0xcf: "arsh64",
        }
        op = alu_map.get(opcode, f"alu_{opcode:#04x}")
        if opcode in (0x84, 0x87):
            result["mnemonic"] = f"{op} {dst}"
        elif opcode & 0x08:
            result["mnemonic"] = f"{op} {dst}, {src}"
        else:
            result["mnemonic"] = f"{op} {dst}, {imm}"
    elif opcode & 0x07 in (0x01, 0x02, 0x03):
        size_map = {0x00: "w", 0x08: "h", 0x10: "b", 0x18: "dw"}
        sz = size_map.get(opcode & 0x18, "?")
        cls = opcode & 0x07
        if cls == 0x01:  # LDX
            result["mnemonic"] = f"ldx{sz} {dst}, [{src}{off:+d}]"
        elif cls == 0x02:  # ST imm
            result["mnemonic"] = f"st{sz} [{dst}{off:+d}], {imm}"
        elif cls == 0x03:  # STX
            result["mnemonic"] = f"stx{sz} [{dst}{off:+d}], {src}"
        result["memory_access"] = True
    else:
        result["mnemonic"] = f"raw_{opcode:#04x} {dst},{src},{off},{imm}"

    return result, size


def extract_rodata_strings(elf):
    """Extract all printable strings from .rodata section."""
    rodata = elf.secs.get(".rodata")
    if not rodata:
        return {}
    ro_start = rodata[4]
    ro_address = rodata[3]
    ro_size = rodata[5]
    strings = {}
    current = []
    current_start = None
    for i in range(ro_size):
        byte = elf.b[ro_start + i]
        if 32 <= byte < 127:
            if current_start is None:
                current_start = ro_address + i
            current.append(chr(byte))
        else:
            if len(current) >= 4:
                strings[current_start] = "".join(current)
            current = []
            current_start = None
    if len(current) >= 4:
        strings[current_start] = "".join(current)
    return strings


def rodata_string_preview(strings, starts, address):
    """Preview a printable-run suffix, not an inferred Rust string length."""
    index = bisect.bisect_right(starts, address) - 1
    if index < 0:
        return None
    start = starts[index]
    text = strings[start]
    offset = address - start
    if offset >= len(text):
        return None
    return text[offset:offset + 120]


def load_idl_discriminators(elf):
    """Return {8-byte selector: instruction name} from the archived IDL, if any."""
    try:
        program = Path(elf.path).parent.name
    except (AttributeError, TypeError):
        return {}
    idl_path = REPO / "evidence" / "upstream" / f"{program}.json"
    if not idl_path.is_file():
        return {}
    try:
        payload = json.loads(idl_path.read_text())
    except (OSError, ValueError):
        return {}
    discriminators = {}
    for insn in payload.get("instructions", []):
        selector = insn.get("discriminator")
        if (not isinstance(selector, list) or len(selector) != 8
                or not all(isinstance(v, int) and 0 <= v < 256 for v in selector)):
            continue
        discriminators[bytes(selector)] = insn.get("name")
    return discriminators


def _recover_dispatch_target(elf, constant_offset):
    """Follow a selector constant to its comparison branch and first direct call."""
    regs = elf.b[constant_offset + 1]
    dst_reg = regs & 0xF

    # The comparison usually operates on a register derived from the constant.
    cmp_offset = constant_offset + 16
    while cmp_offset + 8 <= elf.hi and cmp_offset < constant_offset + 48:
        op = elf.b[cmp_offset]
        if op in (0xbf, 0x79) and (elf.b[cmp_offset + 1] & 0xF) != dst_reg:
            cmp_offset += 8
        else:
            break

    if cmp_offset + 8 > elf.hi:
        return {}
    jop, jregs, joff, _ = struct.unpack_from("<BBhi", elf.b, cmp_offset)
    if jop not in (0x1d, 0x5d):
        return {}
    if (jregs >> 4) != dst_reg and (jregs & 0xF) != dst_reg:
        return {}

    # jeq branches to the handler body; jne falls through to it.
    branch_target = cmp_offset + 8 + joff * 8 if jop == 0x1d else cmp_offset + 8
    cursor = branch_target
    while elf.lo <= cursor and cursor + 8 <= elf.hi and cursor < branch_target + 256:
        cop, cregs, _, cimm = struct.unpack_from("<BBhi", elf.b, cursor)
        if cop == 0x85 and (cregs >> 4) == 1:
            call_target = cursor + 8 + cimm * 8
            target_name = None
            for f in elf.funcs:
                if f["start"] == call_target:
                    target_name = f["name"]
                    break
            return {
                "target_address": hex(call_target),
                "target_name": target_name,
                "call_address": hex(cursor),
            }
        if cop in (0x05, 0x95):
            break
        cursor += 16 if cop == 0x18 else 8

    return {}


def recover_idl_dispatch(elf, discriminators):
    """Scan the whole .text for known IDL selectors and recover their handlers."""
    selectors = {}
    offset = elf.lo
    while offset + 16 <= elf.hi:
        if elf.b[offset] == 0x18:  # lddw
            selector_bytes = elf.b[offset + 4:offset + 8] + elf.b[offset + 12:offset + 16]
            instruction_name = discriminators.get(selector_bytes)
            if instruction_name is not None:
                selector = hex(int.from_bytes(selector_bytes, "little"))
                recovered = _recover_dispatch_target(elf, offset)
                recovered.setdefault("target_address", None)
                recovered.setdefault("target_name", None)
                selectors[selector] = {
                    "selector": selector,
                    "target_address": recovered.get("target_address"),
                    "target_name": recovered.get("target_name"),
                    "instruction_name": instruction_name,
                }
                if "call_address" in recovered:
                    selectors[selector]["call_address"] = recovered["call_address"]
            offset += 16
        else:
            offset += 8
    return selectors


def recover_anchor_dispatch(elf):
    """Recover Anchor instruction dispatch table from the entrypoint.

    When the program has an archived IDL, scan the whole .text for its known
    discriminators so selectors outside the entrypoint window are not missed.
    Programs without an IDL keep the bounded entry-window heuristic.
    """
    discriminators = load_idl_discriminators(elf)
    if discriminators:
        return recover_idl_dispatch(elf, discriminators)

    entry = struct.unpack_from("<Q", elf.b, 24)[0]
    if not (elf.lo <= entry < elf.hi):
        return {}

    # Anchor dispatch: entrypoint computes sighash = sha256("global:<name>")[..8]
    # then does a series of comparisons against 8-byte selectors
    selectors = {}
    # Scan first ~2000 bytes from entry for lddw + comparison patterns
    scan_end = min(entry + 4000, elf.hi)
    offset = entry
    prev_imm64 = None
    while offset < scan_end:
        opcode = elf.b[offset]
        if opcode == 0x18:  # lddw
            imm_lo = struct.unpack_from("<I", elf.b, offset + 4)[0]
            imm_hi = struct.unpack_from("<I", elf.b, offset + 12)[0]
            prev_imm64 = (imm_lo | (imm_hi << 32)) & 0xFFFFFFFFFFFFFFFF
            offset += 16
        elif opcode == 0x85 and elf.b[offset + 1] == 0x10:
            # Internal call — this might be a handler dispatch
            imm = struct.unpack_from("<i", elf.b, offset + 4)[0]
            target = offset + 8 + imm * 8
            if prev_imm64 is not None:
                selectors[hex(prev_imm64)] = {
                    "selector": hex(prev_imm64),
                    "target_address": hex(target),
                    "target_name": None,
                }
                for f in elf.funcs:
                    if f["start"] == target:
                        selectors[hex(prev_imm64)]["target_name"] = f["name"]
                        break
            prev_imm64 = None
            offset += 8
        else:
            if opcode not in (0x05, 0x15, 0x1d, 0x25, 0x55, 0x5d,
                              0xb7, 0xbf, 0x79, 0x61, 0x71):
                prev_imm64 = None
            offset += 8

    return selectors


def build_cfg_edges(instructions, window_start, window_end):
    """Build control flow graph edges from decoded instructions."""
    edges = []
    for insn in instructions:
        addr = insn["offset"]
        if "branch_target" in insn:
            target = insn["branch_target"]
            # Mnemonics include operands (e.g. "ja +8 (0x1c8)"). Use the
            # decoded opcode so unconditional jumps never gain fallthroughs.
            conditional = insn["opcode"] != "0x05"
            edges.append({
                "from": hex(addr),
                "to": hex(target),
                "type": "branch",
                "conditional": conditional,
            })
            # Fall-through edge for conditional branches
            if conditional:
                next_addr = addr + (16 if insn.get("imm64") is not None else 8)
                edges.append({
                    "from": hex(addr),
                    "to": hex(next_addr),
                    "type": "fallthrough",
                    "conditional": False,
                })
        elif insn["mnemonic"] == "exit":
            edges.append({
                "from": hex(addr),
                "to": "return",
                "type": "exit",
                "conditional": False,
            })
    return edges


def analyze_stack_frame(instructions):
    """Analyze stack frame usage (r10-relative accesses)."""
    stack_accesses = collections.Counter()
    max_depth = 0
    for insn in instructions:
        if not insn.get("memory_access"):
            continue
        # LDX addresses through src; ST/STX address through dst. The other
        # register can carry the frame pointer as data without addressing it.
        base = insn["src"] if int(insn["opcode"], 16) & 7 == BPF_LDX else insn["dst"]
        if base == 10:
            stack_accesses[insn["off"]] += 1
            if insn["off"] < 0:
                max_depth = max(max_depth, -insn["off"])
    return {
        "max_stack_depth": max_depth,
        "stack_slots": len(stack_accesses),
        "most_accessed_offsets": [
            {"offset": off, "count": cnt}
            for off, cnt in stack_accesses.most_common(20)
        ],
    }


def relocated_syscalls(elf):
    """Resolve call relocations without changing the captured ELF reader.

    The pinned SBPF loader treats a function symbol with a nonzero value as
    BPF-to-BPF; other call symbols are resolved through its syscall registry.
    None retains a defined-function relocation or an unresolved symbol.
    """
    calls = {at: None for at, relocation in getattr(elf, 'relocations', {}).items()
             if relocation.get('type') == 10}
    rel = elf.secs.get('.rel.dyn')
    sym = elf.secs.get('.dynsym')
    if rel is None or sym is None:
        return calls
    if rel[9] != 16 or sym[9] != 24:
        return calls
    b = elf.b
    if (rel[4] + rel[5] > len(b) or sym[4] + sym[5] > len(b)
            or rel[5] % 16 or sym[5] % 24):
        return calls
    for pos in range(rel[4], rel[4] + rel[5], 16):
        at, info = struct.unpack_from('<QQ', b, pos)
        if info & 0xffffffff != 10:
            continue
        calls[at] = None
        index = info >> 32
        if index >= sym[5] // 24:
            continue
        _, kind, _, _, value, _ = struct.unpack_from(
            '<IBBHQQ', b, sym[4] + index * 24)
        if kind & 15 == 2 and value != 0:
            continue
        calls[at] = elf.symbols.get(index) or None
    return calls


def fingerprint_window(elf, start, end, call_symbols=None):
    """Create a bytecode signature fingerprint for pattern matching."""
    b = elf.b
    # Opcode sequence (normalized — ignore operands)
    opcodes = []
    offset = start
    while offset < end:
        opcodes.append(b[offset])
        if b[offset] == 0x18:
            offset += 16
        else:
            offset += 8

    # Walk logical instructions: the second LDDW slot is operand data.
    if call_symbols is None:
        call_symbols = relocated_syscalls(elf)
    syscalls = []
    at = start
    while at + 8 <= end:
        if b[at] == 0x85:
            if at in call_symbols:
                if call_symbols[at] is not None:
                    syscalls.append(call_symbols[at])
            elif b[at + 1] == 0x00:
                uimm = struct.unpack_from("<I", b, at + 4)[0]
                syscalls.append(SYSCALL_NAMES.get(uimm, f"unknown_{uimm:#x}"))
        at += 16 if b[at] == 0x18 else 8

    # Structural fingerprint (opcode bigrams)
    bigrams = collections.Counter()
    for i in range(len(opcodes) - 1):
        bigrams[(opcodes[i], opcodes[i + 1])] += 1

    return {
        "opcode_count": len(opcodes),
        "unique_opcodes": len(set(opcodes)),
        "syscall_sequence": syscalls,
        "opcode_sha256": hashlib.sha256(bytes(opcodes)).hexdigest()[:16],
        "top_bigrams": [
            {"pair": [f"0x{a:02x}", f"0x{b:02x}"], "count": c}
            for (a, b), c in bigrams.most_common(10)
        ],
    }


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    deployed_path = REPO / "evidence" / "original" / args.program / "deployed.so"
    if not deployed_path.exists():
        print(f"ERROR: {deployed_path} not found")
        return 1

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[disasm] Reading {deployed_path}")
    elf = Elf(deployed_path)
    call_symbols = relocated_syscalls(elf)
    entries = elf.entries
    boundaries = entries + [elf.hi]

    rodata_strings = extract_rodata_strings(elf)
    rodata_starts = sorted(rodata_strings)
    print(f"[disasm] {len(rodata_strings)} rodata strings extracted")

    dispatch = recover_anchor_dispatch(elf)
    print(f"[disasm] {len(dispatch)} dispatch selectors recovered")

    # --- Per-window deep analysis ---
    all_windows = []
    all_disasm = []
    syscall_usage = collections.Counter()
    extern_usage = collections.Counter()
    fingerprints = []

    for idx, start in enumerate(entries):
        end = boundaries[idx + 1]
        size = end - start
        name = None
        for f in elf.funcs:
            if f["start"] == start:
                name = f["name"]
                break

        # Decode instructions
        instructions = []
        offset = start
        while offset < end:
            insn, step = decode_instruction(elf.b, offset, elf)
            if insn:
                instructions.append(insn)
                if insn.get("syscall"):
                    syscall_usage[insn["syscall"]] += 1
                if insn.get("extern_symbol"):
                    extern_usage[insn["extern_symbol"]] += 1
            offset += step

        # String references
        string_refs = []
        for insn in instructions:
            if insn.get("imm64") is not None:
                val = insn["imm64"] & 0xFFFFFFFFFFFFFFFF
                preview = rodata_string_preview(rodata_strings, rodata_starts, val)
                if preview is not None:
                    string_refs.append({
                        "offset": insn["offset"] - start,
                        "string": preview,
                    })

        # CFG edges
        cfg = build_cfg_edges(instructions, start, end)

        # Stack analysis
        stack = analyze_stack_frame(instructions)

        # Fingerprint
        fp = fingerprint_window(elf, start, end, call_symbols)
        fp["address"] = hex(start)
        fp["name"] = name
        fingerprints.append(fp)

        window_record = {
            "index": idx,
            "address": hex(start),
            "address_decimal": start,
            "size": size,
            "name": name,
            "instruction_count": len(instructions),
            "syscalls": sorted(set(
                insn["syscall"] for insn in instructions if insn.get("syscall")
            )),
            "extern_calls": sorted(set(
                insn["extern_symbol"] for insn in instructions if insn.get("extern_symbol")
            )),
            "internal_calls": sum(1 for insn in instructions if insn.get("call_target")),
            "branches": sum(1 for insn in instructions if "branch_target" in insn),
            "exits": sum(1 for insn in instructions if insn["mnemonic"] == "exit"),
            "string_references": string_refs,
            "stack_frame": stack,
            "cfg_edges": len(cfg),
            "fingerprint": fp["opcode_sha256"],
        }
        all_windows.append(window_record)

        # Full disassembly (for the detailed dump)
        disasm_record = {
            "address": hex(start),
            "name": name,
            "size": size,
            "instructions": [
                {
                    "addr": hex(insn["offset"]),
                    "hex": insn["hex"],
                    "mnemonic": insn["mnemonic"],
                }
                for insn in instructions
            ],
            "cfg_edges": cfg,
        }
        all_disasm.append(disasm_record)

        if (idx + 1) % 100 == 0:
            print(f"[disasm] {idx + 1}/{len(entries)} windows processed")

    print(f"[disasm] {len(entries)} windows fully decoded")

    # --- Write outputs ---

    # 1. Window summary with deep analysis
    (output_dir / "windows-deep.json").write_text(
        json.dumps(all_windows, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 2. Full disassembly (gzipped — can be large)
    disasm_path = output_dir / "disassembly.json.gz"
    # Keep packet identity independent of wall time, output path and locale.
    with disasm_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as f:
                json.dump(all_disasm, f, indent=2)

    # 3. Dispatch table
    (output_dir / "dispatch-table.json").write_text(
        json.dumps(dispatch, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 4. Syscall usage
    (output_dir / "syscall-usage.json").write_text(
        json.dumps(dict(syscall_usage.most_common()), indent=2) + "\n",
        encoding="utf-8", newline="\n")

    # 5. External symbol usage
    (output_dir / "extern-usage.json").write_text(
        json.dumps(dict(extern_usage.most_common()), indent=2) + "\n",
        encoding="utf-8", newline="\n")

    # 6. Rodata strings
    rodata_for_json = [
        {"address": hex(addr), "string": s}
        for addr, s in sorted(rodata_strings.items())
    ]
    (output_dir / "rodata-strings.json").write_text(
        json.dumps(rodata_for_json, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 7. Bytecode fingerprints
    (output_dir / "fingerprints.json").write_text(
        json.dumps(fingerprints, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 8. Error messages (strings containing common error patterns)
    error_strings = [
        s for s in rodata_for_json
        if any(kw in s["string"].lower() for kw in [
            "error", "invalid", "overflow", "underflow", "fail",
            "unauthorized", "insufficient", "exceed", "mismatch",
            "closed", "frozen", "paused", "expired", "not allowed",
            "constraint", "already", "missing", "empty", "zero",
        ])
    ]
    (output_dir / "error-strings.json").write_text(
        json.dumps(error_strings, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 9. Summary
    summary = {
        "program": args.program,
        "deployed_sha256": hashlib.sha256(elf.b).hexdigest(),
        "text_section_bytes": elf.hi - elf.lo,
        "total_windows": len(entries),
        "total_instructions": sum(w["instruction_count"] for w in all_windows),
        "total_syscalls": sum(syscall_usage.values()),
        "unique_syscalls": len(syscall_usage),
        "total_internal_calls": sum(w["internal_calls"] for w in all_windows),
        "total_extern_calls": sum(extern_usage.values()),
        "total_branches": sum(w["branches"] for w in all_windows),
        "rodata_strings": len(rodata_strings),
        "error_strings": len(error_strings),
        "dispatch_selectors": len(dispatch),
        "largest_stack_frame": max(
            (w["stack_frame"]["max_stack_depth"] for w in all_windows), default=0),
        "syscall_breakdown": dict(syscall_usage.most_common()),
        "extern_breakdown": dict(extern_usage.most_common()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 10. README
    readme = f"""# {args.program} — Deep Disassembly Analysis

## Scope
Full BPF instruction-level decode of the deployed {args.program} program binary,
including syscall identification, error string extraction, Anchor dispatch table
recovery, control flow graph construction, stack frame analysis, and bytecode
fingerprinting for cross-window pattern matching.

## Binary Identity
- SHA-256: `{summary["deployed_sha256"]}`
- .text section: {summary["text_section_bytes"]:,} bytes

## Statistics
| Metric | Value |
|--------|-------|
| Total windows | {summary["total_windows"]} |
| Total instructions | {summary["total_instructions"]:,} |
| Total syscalls | {summary["total_syscalls"]:,} |
| Unique syscalls | {summary["unique_syscalls"]} |
| Internal calls | {summary["total_internal_calls"]:,} |
| External calls | {summary["total_extern_calls"]:,} |
| Branches | {summary["total_branches"]:,} |
| Error strings | {summary["error_strings"]} |
| Dispatch selectors | {summary["dispatch_selectors"]} |
| Largest stack frame | {summary["largest_stack_frame"]} bytes |

## Syscall Usage
{chr(10).join(f'- `{name}`: {count}' for name, count in syscall_usage.most_common(15))}

## Files
String references preview up to 120 printable bytes from the referenced address
to the end of its extracted ASCII run. They do not establish a Rust string's
length, a semantic string boundary, or runtime use.

| File | Description |
|------|-------------|
| windows-deep.json | Per-window analysis (syscalls, strings, stack, fingerprint) |
| disassembly.json.gz | Full instruction-level disassembly (gzipped) |
| dispatch-table.json | Recovered Anchor instruction selector dispatch |
| syscall-usage.json | Syscall frequency across all windows |
| extern-usage.json | External symbol call frequency |
| rodata-strings.json | All extracted .rodata printable strings |
| error-strings.json | Strings matching error/validation patterns |
| fingerprints.json | Bytecode signature fingerprints per window |

## Verification
```bash
python3 verify.py
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    # 11. Verify script
    verify_py = '''#!/usr/bin/env python3
"""Verify integrity of this deep disassembly packet."""
import hashlib, json, os, sys

PACKET = os.path.dirname(os.path.abspath(__file__))
EXPECTED_FILES = frozenset(__EXPECTED_PACKET_FILES__)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    manifest = json.load(open(os.path.join(PACKET, "manifest.json")))
    if not isinstance(manifest, dict) or set(manifest) != EXPECTED_FILES:
        print("FAIL: manifest artifact set mismatch"); return 1
    errors = 0
    for name, expected in manifest.items():
        path = os.path.join(PACKET, name)
        if not os.path.exists(path):
            print(f"FAIL: {name} missing"); errors += 1; continue
        actual = sha256_file(path)
        if actual != expected:
            print(f"FAIL: {name} hash mismatch"); errors += 1
        else:
            print(f"  OK: {name}")
    s = json.load(open(os.path.join(PACKET, "summary.json")))
    w = json.load(open(os.path.join(PACKET, "windows-deep.json")))
    if s["total_windows"] != len(w):
        print(f"FAIL: window count mismatch"); errors += 1
    else:
        print(f"  OK: windows consistent ({len(w)})")
    if errors:
        print(f"\\n{errors} error(s)"); return 1
    print("\\nAll checks passed."); return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    verify_py = verify_py.replace('__EXPECTED_PACKET_FILES__', repr([
        'README.md', 'disassembly.json.gz', 'dispatch-table.json', 'error-strings.json',
        'extern-usage.json', 'fingerprints.json', 'rodata-strings.json', 'summary.json',
        'syscall-usage.json', 'verify.py', 'windows-deep.json',
    ]))
    (output_dir / "verify.py").write_text(verify_py)


    (output_dir / "verify.py").write_text(verify_py, encoding="utf-8", newline="\n")

    # 12. Manifest
    manifest = {}
    for name in sorted(os.listdir(output_dir)):
        if name == "manifest.json":
            continue
        path = output_dir / name
        if path.is_file():
            manifest[name] = sha256_file(str(path))
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    total_lines = sum(
        sum(1 for _ in open(output_dir / name, encoding="utf-8"))
        for name in os.listdir(output_dir)
        if (output_dir / name).is_file() and not name.endswith(".gz")
    )
    print(f"[disasm] wrote {len(manifest) + 1} files, ~{total_lines:,} lines to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
