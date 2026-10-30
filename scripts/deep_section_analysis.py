#!/usr/bin/env python3
"""Deep section-level analysis of Solana BPF programs — 5 analysis layers.

Layer 1: Data Layout — .rodata and .data.rel.ro structure, constant pools,
         vtable-like pointer tables, padding analysis
Layer 2: Relocation Map — full relocation table decode with symbol resolution,
         relocation type classification, pointer chain tracing
Layer 3: Cross-Section Correlation — which .text windows reference which data
         regions, data dependency graph, shared constant identification
Layer 4: Anchor IDL Recovery — instruction discriminator extraction, account
         struct size inference, argument type recovery from bytecode patterns
Layer 5: Bonding Curve Math — constant product arithmetic extraction, fee
         calculation patterns, overflow protection analysis, fixed-point math

Usage:
    python3 scripts/deep_section_analysis.py --program pump \
        --output research/pump-section-analysis-20261028
"""
import argparse
import collections
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from window_elf_reader import Elf

SYSCALL_NAMES = {
    0xb6fc1a11: "sol_log_", 0x207559bd: "sol_log_64_",
    0xa22b9c85: "sol_memcpy_", 0x5fdcde31: "sol_memmove_",
    0x73e3b3f5: "sol_memcmp_", 0x3b97b73c: "sol_memset_",
    0xd56b5fe9: "sol_invoke_signed_c", 0xe4042040: "sol_invoke_signed_rust",
    0x83f00e8f: "sol_alloc_free_", 0x5be92f43: "sol_set_return_data",
    0xe2e10497: "sol_log_data", 0xfee07a55: "sol_get_clock_sysvar",
    0xe7ce47dc: "sol_get_rent_sysvar", 0xcccd2005: "sol_remaining_compute_units",
    0x52ba5096: "sol_create_program_address",
    0x48f18ece: "sol_try_find_program_address",
    0x717cc4a3: "sol_sha256", 0x3770fb22: "sol_keccak256",
    0x33ef6958: "sol_get_return_data",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


# ──────────────────────────────────────────────────────────────
# Layer 1: Data Layout Analysis
# ──────────────────────────────────────────────────────────────

def analyze_data_layout(elf):
    """Analyze .rodata and .data.rel.ro sections in detail."""
    results = {}
    # SBPF V0-V2 use the lenient loader's legacy data relocations. V3+
    # uses a strict loader without relocation; unknown flags stay untouched.
    legacy_relocations = (len(elf.b) >= 52
                          and struct.unpack_from("<I", elf.b, 48)[0] in (0, 1, 2))

    for section_name in [".rodata", ".data.rel.ro"]:
        if section_name not in elf.secs:
            continue
        sec = elf.secs[section_name]
        start = sec[4]
        address_start = sec[3]
        size = sec[5]
        data = elf.b[start:start + size]

        # String extraction
        strings = []
        current = []
        current_start = None
        for i, byte in enumerate(data):
            if 32 <= byte < 127:
                if current_start is None:
                    current_start = i
                current.append(chr(byte))
            else:
                if len(current) >= 4:
                    strings.append({
                        "offset": current_start,
                        "address": hex(address_start + current_start),
                        "length": len(current),
                        "value": "".join(current)[:200],
                    })
                current = []
                current_start = None

        if len(current) >= 4:
            strings.append({
                "offset": current_start,
                "address": hex(start + current_start),
                "length": len(current),
                "value": "".join(current)[:200],
            })

        # Zero padding analysis
        zero_runs = []
        in_zero = False
        zero_start = 0
        for i, byte in enumerate(data):
            if byte == 0:
                if not in_zero:
                    in_zero = True
                    zero_start = i
            else:
                if in_zero and i - zero_start >= 8:
                    zero_runs.append({
                        "offset": zero_start,
                        "length": i - zero_start,
                    })
                in_zero = False
        if in_zero and len(data) - zero_start >= 8:
            zero_runs.append({"offset": zero_start, "length": len(data) - zero_start})

        # Pointer-like value scan (8-byte aligned values in program space)
        pointers = []
        for i in range(0, len(data) - 7, 8):
            val = struct.unpack_from("<Q", data, i)[0]
            provenance = {}
            if (legacy_relocations
                    and getattr(elf, "relocations", {}).get(start + i, {}).get("type") == 8
                    and not elf.lo <= start + i < elf.hi):
                # Legacy R_BPF_64_RELATIVE data slots encode the image-relative
                # target at r_offset+4. Keep the raw slot; do not rebase or write
                # captured bytes. This is pointer attribution, not execution.
                provenance = {"raw_value": hex(val), "relocation_type": 8}
                val >>= 32
            if elf.lo <= val < elf.hi and val % 8 == 0:
                pointers.append({
                    "offset": i,
                    "address": hex(address_start + i),
                    "points_to": hex(val),
                    "in_text": True,
                    **provenance,
                })
            elif address_start <= val < address_start + size:
                pointers.append({
                    "offset": i,
                    "address": hex(address_start + i),
                    "points_to": hex(val),
                    "in_text": False,
                    "self_reference": True,
                    **provenance,
                })

        # Constant value analysis (common numeric constants)
        constants_u64 = collections.Counter()
        constants_u32 = collections.Counter()
        for i in range(0, len(data) - 7, 8):
            val = struct.unpack_from("<Q", data, i)[0]
            if val != 0 and val < 0xFFFFFFFFFFFF:
                constants_u64[val] += 1
        for i in range(0, len(data) - 3, 4):
            val = struct.unpack_from("<I", data, i)[0]
            if val != 0 and val < 0xFFFFFFFF:
                constants_u32[val] += 1

        # Entropy analysis (16-byte blocks)
        block_entropies = []
        for i in range(0, len(data) - 15, 16):
            block = data[i:i+16]
            byte_counts = collections.Counter(block)
            import math
            entropy = -sum(c/16 * math.log2(c/16) for c in byte_counts.values() if c > 0)
            block_entropies.append(round(entropy, 3))

        results[section_name] = {
            "start": hex(start),
            "size": size,
            "sha256": sha256_bytes(data),
            "strings": strings,
            "string_count": len(strings),
            "zero_padding_runs": zero_runs,
            "total_zero_padding": sum(r["length"] for r in zero_runs),
            "pointer_like_values": pointers[:200],
            "pointer_count": len(pointers),
            "top_constants_u64": [
                {"value": hex(v), "decimal": v, "count": c}
                for v, c in constants_u64.most_common(50)
            ],
            "top_constants_u32": [
                {"value": hex(v), "decimal": v, "count": c}
                for v, c in constants_u32.most_common(50)
            ],
            "avg_entropy": round(sum(block_entropies) / max(len(block_entropies), 1), 3),
            "high_entropy_blocks": sum(1 for e in block_entropies if e > 3.5),
            "low_entropy_blocks": sum(1 for e in block_entropies if e < 1.0),
        }

    return results


# ──────────────────────────────────────────────────────────────
# Layer 2: Relocation Map
# ──────────────────────────────────────────────────────────────

def analyze_relocations(elf):
    """Full relocation table analysis with type classification."""
    # Solana's SBPF loader uses 8 for relative addresses and 10 for calls;
    # these are not the generic BPF absolute-data relocation names.
    # https://github.com/anza-xyz/sbpf/blob/f754c707f99779a756978f87c9afd25eeeb3d92e/src/elf.rs#L175-L207
    reloc_types = {
        0: "R_BPF_NONE", 1: "R_BPF_64_64",
        8: "R_BPF_64_RELATIVE", 10: "R_BPF_64_32",
    }

    rel_sec = elf.secs.get(".rel.dyn")
    if not rel_sec:
        return {"count": 0, "entries": [], "type_distribution": {}}

    entries = []
    type_counts = collections.Counter()
    symbol_refs = collections.Counter()

    for i in range(rel_sec[4], rel_sec[4] + rel_sec[5], 16):
        at, info = struct.unpack_from("<QQ", elf.b, i)
        typ = info & 0xFFFFFFFF
        sym_idx = info >> 32
        symbol = elf.symbols.get(sym_idx, "")
        type_name = reloc_types.get(typ, f"UNKNOWN_{typ}")

        type_counts[type_name] += 1
        if symbol:
            symbol_refs[symbol] += 1

        # Determine target
        target_section = "unknown"
        if elf.lo <= at < elf.hi:
            target_section = ".text"
        for sec_name, sec in elf.secs.items():
            if sec[3] <= at < sec[3] + sec[5] and sec_name != ".text":
                target_section = sec_name
                break

        entry = {
            "address": hex(at),
            "type": type_name,
            "type_id": typ,
            "symbol_index": sym_idx,
            "symbol": symbol,
            "target_section": target_section,
        }

        # For lddw relocations in .text, resolve the pointer value
        if target_section == ".text" and typ == 8 and elf.b[at] == 0x18:
            imm_lo = struct.unpack_from("<I", elf.b, at + 4)[0]
            imm_hi = struct.unpack_from("<I", elf.b, at + 12)[0]
            resolved = imm_lo | (imm_hi << 32)
            entry["resolved_value"] = hex(resolved)

        entries.append(entry)

    return {
        "count": len(entries),
        "type_distribution": dict(type_counts.most_common()),
        "symbol_references": dict(symbol_refs.most_common()),
        "entries": entries,
        "entries_in_text": sum(1 for e in entries if e["target_section"] == ".text"),
        "entries_in_rodata": sum(1 for e in entries if e["target_section"] == ".rodata"),
        "entries_in_data_rel_ro": sum(1 for e in entries if e["target_section"] == ".data.rel.ro"),
    }


# ──────────────────────────────────────────────────────────────
# Layer 3: Cross-Section Correlation
# ──────────────────────────────────────────────────────────────

def analyze_cross_section(elf):
    """Map which .text windows reference which data regions."""
    entries = elf.entries
    boundaries = entries + [elf.hi]

    # Build window index
    window_names = {}
    for f in elf.funcs:
        window_names[f["start"]] = f["name"]

    # For each window, find all data references via lddw instructions
    window_data_refs = []
    all_rodata_refs = collections.Counter()
    all_data_refs = collections.Counter()

    # lddw immediates are virtual addresses, so data-section extents must be
    # compared against the section address (sec[3]), not its file offset
    # (sec[4]). The two coincidentally agree only for identity-mapped ELFs.
    rodata = elf.secs.get(".rodata")
    data_rel_ro = elf.secs.get(".data.rel.ro")
    rodata_range = ((rodata[3], rodata[3] + rodata[5]) if rodata else None)
    data_rel_ro_range = (
        (data_rel_ro[3], data_rel_ro[3] + data_rel_ro[5]) if data_rel_ro else None)

    for idx, start in enumerate(entries):
        end = boundaries[idx + 1]
        name = window_names.get(start)

        refs = {"rodata": [], "data_rel_ro": [], "text": [], "other": []}

        for at in range(start, end, 8):
            if elf.b[at] == 0x18 and at + 16 <= end:
                imm_lo = struct.unpack_from("<I", elf.b, at + 4)[0]
                imm_hi = struct.unpack_from("<I", elf.b, at + 12)[0]
                val = imm_lo | (imm_hi << 32)

                if rodata_range and rodata_range[0] <= val < rodata_range[1]:
                    refs["rodata"].append(hex(val))
                elif data_rel_ro_range and data_rel_ro_range[0] <= val < data_rel_ro_range[1]:
                    refs["data_rel_ro"].append(hex(val))
                elif elf.lo <= val < elf.hi:
                    refs["text"].append(hex(val))
                elif val > 0:
                    refs["other"].append(hex(val))

        # Count the complete reference stream; the per-window lists below are
        # bounded presentation samples, not inputs to the frequency census.
        all_rodata_refs.update(refs["rodata"])
        all_data_refs.update(refs["data_rel_ro"])
        window_data_refs.append({
            "window_index": idx,
            "address": hex(start),
            "name": name,
            "size": end - start,
            "rodata_refs": len(refs["rodata"]),
            "data_rel_ro_refs": len(refs["data_rel_ro"]),
            "text_refs": len(refs["text"]),
            "other_refs": len(refs["other"]),
            "rodata_addresses": refs["rodata"][:20],
            "data_rel_ro_addresses": refs["data_rel_ro"][:20],
        })

    # Identify heavily-referenced data regions
    # Data dependency clusters
    clusters = collections.defaultdict(list)
    for w in window_data_refs:
        shared_refs = frozenset(w["rodata_addresses"][:5] + w["data_rel_ro_addresses"][:5])
        if shared_refs:
            clusters[shared_refs].append(w["address"])

    return {
        "window_data_refs": window_data_refs,
        "hot_rodata_addresses": [
            {"address": a, "ref_count": c}
            for a, c in all_rodata_refs.most_common(50)
        ],
        "hot_data_rel_ro_addresses": [
            {"address": a, "ref_count": c}
            for a, c in all_data_refs.most_common(50)
        ],
        "windows_with_rodata_refs": sum(
            1 for w in window_data_refs if w["rodata_refs"] > 0),
        "windows_with_data_refs": sum(
            1 for w in window_data_refs if w["data_rel_ro_refs"] > 0),
        "total_rodata_refs": sum(w["rodata_refs"] for w in window_data_refs),
        "total_data_refs": sum(w["data_rel_ro_refs"] for w in window_data_refs),
    }


# ──────────────────────────────────────────────────────────────
# Layer 4: Anchor IDL Recovery
# ──────────────────────────────────────────────────────────────

def recover_anchor_idl(elf):
    """Recover Anchor IDL elements from bytecode analysis."""
    b = elf.b
    entry = struct.unpack_from("<Q", b, 24)[0]

    # 1. Extract instruction discriminators (sighash values)
    # Anchor uses sha256("global:<name>")[..8] as 8-byte selectors
    discriminators = []
    if elf.lo <= entry < elf.hi:
        scan_end = min(entry + 8000, elf.hi)
        offset = entry
        while offset < scan_end:
            if b[offset] == 0x18:  # lddw
                imm_lo = struct.unpack_from("<I", b, offset + 4)[0]
                imm_hi = struct.unpack_from("<I", b, offset + 12)[0]
                val = imm_lo | (imm_hi << 32)
                if val != 0 and val < 0xFFFFFFFFFFFFFFFF:
                    # Look ahead for comparison or call
                    next_off = offset + 16
                    if next_off < scan_end:
                        if b[next_off] in (0x1d, 0x5d, 0x15, 0x55):
                            discriminators.append({
                                "value": hex(val),
                                "bytes": val.to_bytes(8, "little").hex(),
                                "found_at": hex(offset),
                            })
                offset += 16
            else:
                offset += 8

    # 2. Account struct size inference from allocation patterns
    # Look for alloc_free calls preceded by size loading
    account_sizes = []
    for at in range(elf.lo, elf.hi, 8):
        if b[at] == 0x85 and b[at + 1] == 0x00:
            uimm = struct.unpack_from("<I", b, at + 4)[0]
            if uimm == 0x83f00e8f:  # sol_alloc_free_
                # Check preceding instructions for size
                for back in range(1, 6):
                    prev = at - back * 8
                    if prev >= elf.lo:
                        if b[prev] in (0xb7, 0xb4) and b[prev + 1] & 0xF == 1:  # mov imm into size argument r1
                            size_val = struct.unpack_from("<i", b, prev + 4)[0]
                            if 8 < size_val < 100000:
                                account_sizes.append({
                                    "alloc_at": hex(at),
                                    "size": size_val,
                                    "size_loaded_at": hex(prev),
                                })
                            break

    # 3. Argument type recovery from deserialization patterns
    # Look for borsh-style sequential reads of specific sizes
    deser_patterns = []
    entries = elf.entries
    boundaries = entries + [elf.hi]
    for idx, start in enumerate(entries):
        end = boundaries[idx + 1]
        # Look for sequences of loads from incrementing offsets
        loads = []
        for at in range(start, end, 8):
            if b[at] in (0x61, 0x69, 0x71, 0x79):  # ldx variants
                off = struct.unpack_from("<h", b, at + 2)[0]
                src = (b[at + 1] >> 4) & 0xF
                size_map = {0x61: 4, 0x69: 2, 0x71: 1, 0x79: 8}
                loads.append({
                    "offset": at - start,
                    "src_reg": src,
                    "mem_offset": off,
                    "load_size": size_map.get(b[at], 0),
                })

        # Find sequential load patterns from same base register
        if len(loads) >= 3:
            by_reg = collections.defaultdict(list)
            for ld in loads:
                by_reg[ld["src_reg"]].append(ld)

            for reg, reg_loads in by_reg.items():
                if len(reg_loads) >= 3:
                    offsets = sorted(set(ld["mem_offset"] for ld in reg_loads))
                    if len(offsets) >= 3:
                        # Check for sequential pattern
                        diffs = [offsets[i+1] - offsets[i] for i in range(len(offsets)-1)]
                        if all(1 <= d <= 32 for d in diffs[:5]):
                            name = None
                            for f in elf.funcs:
                                if f["start"] == start:
                                    name = f["name"]
                                    break
                            deser_patterns.append({
                                "window": hex(start),
                                "name": name,
                                "base_reg": reg,
                                "field_offsets": offsets[:20],
                                "field_sizes": [
                                    next((ld["load_size"] for ld in reg_loads
                                          if ld["mem_offset"] == o), 0)
                                    for o in offsets[:20]
                                ],
                                "likely_struct_size": max(offsets[:20]) + 8 if offsets else 0,
                            })

    # Deduplicate account sizes
    unique_sizes = sorted(set(a["size"] for a in account_sizes))

    return {
        "discriminators": discriminators,
        "discriminator_count": len(discriminators),
        "allocation_sizes": account_sizes[:100],
        "unique_allocation_sizes": unique_sizes,
        "deserialization_patterns": deser_patterns[:100],
        "inferred_struct_sizes": sorted(set(
            d["likely_struct_size"] for d in deser_patterns
            if d["likely_struct_size"] > 0
        )),
    }


# ──────────────────────────────────────────────────────────────
# Layer 5: Bonding Curve Math Analysis
# ──────────────────────────────────────────────────────────────

def analyze_math_patterns(elf):
    """Extract mathematical computation patterns from bytecode.

    Looks for:
    - Multiplication/division sequences (constant product)
    - Overflow-checked arithmetic (saturating/wrapping)
    - Fixed-point multiplication patterns
    - Fee calculation (multiply then divide by basis points)
    - Square root approximation (for liquidity math)
    """
    b = elf.b
    entries = elf.entries
    boundaries = entries + [elf.hi]

    math_windows = []

    for idx, start in enumerate(entries):
        end = boundaries[idx + 1]
        name = None
        for f in elf.funcs:
            if f["start"] == start:
                name = f["name"]
                break

        # Count arithmetic operations
        mul_count = 0
        div_count = 0
        add_count = 0
        sub_count = 0
        shift_count = 0
        overflow_checks = 0
        u128_ops = 0

        # Track specific patterns
        mul_then_div = 0
        fee_patterns = 0
        basis_point_divs = 0

        prev_op = None
        for at in range(start, end, 8):
            opcode = b[at]
            imm = struct.unpack_from("<i", b, at + 4)[0]

            if opcode in (0x27, 0x2f):  # mul64
                mul_count += 1
                if prev_op == "mul":
                    u128_ops += 1  # double-width multiply
                prev_op = "mul"
            elif opcode in (0x37, 0x3f):  # div64
                div_count += 1
                if prev_op == "mul":
                    mul_then_div += 1
                # Check for basis point division (10000)
                if opcode == 0x37 and imm == 10000:
                    basis_point_divs += 1
                    fee_patterns += 1
                prev_op = "div"
            elif opcode in (0x07, 0x0f):  # add64
                add_count += 1
                prev_op = "add"
            elif opcode in (0x17, 0x1f):  # sub64
                sub_count += 1
                prev_op = "sub"
            elif opcode in (0x67, 0x6f, 0x77, 0x7f):  # shifts
                shift_count += 1
                prev_op = "shift"
            else:
                # Check for overflow detection pattern:
                # comparison after arithmetic followed by error branch
                if opcode in (0x25, 0x35, 0xa5, 0xb5) and prev_op in ("add", "sub", "mul"):
                    overflow_checks += 1
                prev_op = None

            # Detect 128-bit arithmetic patterns
            if b[at] == 0x18:  # lddw - skip the double-wide
                if at + 16 <= end:
                    imm_lo = struct.unpack_from("<I", b, at + 4)[0]
                    imm_hi = struct.unpack_from("<I", b, at + 12)[0]
                    val = imm_lo | (imm_hi << 32)
                    # Common math constants
                    if val in (10000, 1000000, 1000000000, 10**18):
                        fee_patterns += 1

        total_arith = mul_count + div_count + add_count + sub_count
        if total_arith >= 5:
            math_windows.append({
                "address": hex(start),
                "name": name,
                "size": end - start,
                "multiplications": mul_count,
                "divisions": div_count,
                "additions": add_count,
                "subtractions": sub_count,
                "shifts": shift_count,
                "overflow_checks": overflow_checks,
                "mul_then_div_patterns": mul_then_div,
                "fee_patterns": fee_patterns,
                "basis_point_divisions": basis_point_divs,
                "u128_likely": u128_ops > 0,
                "arithmetic_density": round(total_arith / max((end - start) // 8, 1), 4),
                "likely_function": (
                    "constant_product" if mul_then_div >= 2 else
                    "fee_calculation" if fee_patterns >= 1 else
                    "arithmetic_helper" if total_arith >= 10 else
                    "mixed_logic"
                ),
            })

    # Sort by arithmetic density
    math_windows.sort(key=lambda w: -(w["multiplications"] + w["divisions"]))

    return {
        "math_intensive_windows": math_windows,
        "total_math_windows": len(math_windows),
        "constant_product_candidates": sum(
            1 for w in math_windows if w["likely_function"] == "constant_product"),
        "fee_calculation_candidates": sum(
            1 for w in math_windows if w["likely_function"] == "fee_calculation"),
        "windows_with_overflow_checks": sum(
            1 for w in math_windows if w["overflow_checks"] > 0),
        "windows_with_u128": sum(
            1 for w in math_windows if w["u128_likely"]),
    }


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

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

    print(f"[deep] Reading {deployed_path}")
    elf = Elf(deployed_path)

    # Layer 1
    print(f"[deep] Layer 1: Data Layout Analysis...")
    data_layout = analyze_data_layout(elf)

    # Layer 2
    print(f"[deep] Layer 2: Relocation Map...")
    reloc_map = analyze_relocations(elf)

    # Layer 3
    print(f"[deep] Layer 3: Cross-Section Correlation...")
    cross_section = analyze_cross_section(elf)

    # Layer 4
    print(f"[deep] Layer 4: Anchor IDL Recovery...")
    idl_recovery = recover_anchor_idl(elf)

    # Layer 5
    print(f"[deep] Layer 5: Bonding Curve Math...")
    math_analysis = analyze_math_patterns(elf)

    # --- Write outputs ---

    (output_dir / "layer1-data-layout.json").write_text(
        json.dumps(data_layout, indent=2) + "\n")
    (output_dir / "layer2-relocation-map.json").write_text(
        json.dumps(reloc_map, indent=2) + "\n")
    (output_dir / "layer3-cross-section.json").write_text(
        json.dumps(cross_section, indent=2) + "\n")
    (output_dir / "layer4-anchor-idl.json").write_text(
        json.dumps(idl_recovery, indent=2) + "\n")
    (output_dir / "layer5-math-analysis.json").write_text(
        json.dumps(math_analysis, indent=2) + "\n")

    # Summary
    text_bytes = elf.hi - elf.lo
    summary = {
        "program": args.program,
        "deployed_sha256": sha256_file(str(deployed_path)),
        "text_bytes": text_bytes,
        "layer1_data_layout": {
            "sections_analyzed": len(data_layout),
            "total_strings": sum(d["string_count"] for d in data_layout.values()),
            "total_pointers": sum(d["pointer_count"] for d in data_layout.values()),
        },
        "layer2_relocations": {
            "total": reloc_map["count"],
            "in_text": reloc_map.get("entries_in_text", 0),
            "in_rodata": reloc_map.get("entries_in_rodata", 0),
            "unique_symbols": len(reloc_map.get("symbol_references", {})),
        },
        "layer3_cross_section": {
            "windows_with_rodata_refs": cross_section["windows_with_rodata_refs"],
            "windows_with_data_refs": cross_section["windows_with_data_refs"],
            "total_rodata_refs": cross_section["total_rodata_refs"],
        },
        "layer4_anchor_idl": {
            "discriminators": idl_recovery["discriminator_count"],
            "unique_alloc_sizes": len(idl_recovery["unique_allocation_sizes"]),
            "deser_patterns": len(idl_recovery["deserialization_patterns"]),
        },
        "layer5_math": {
            "math_windows": math_analysis["total_math_windows"],
            "constant_product": math_analysis["constant_product_candidates"],
            "fee_calculation": math_analysis["fee_calculation_candidates"],
            "overflow_protected": math_analysis["windows_with_overflow_checks"],
        },
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    # README
    l1 = summary["layer1_data_layout"]
    l2 = summary["layer2_relocations"]
    l3 = summary["layer3_cross_section"]
    l4 = summary["layer4_anchor_idl"]
    l5 = summary["layer5_math"]
    readme = f"""# {args.program} — 5-Layer Deep Section Analysis

## Scope
Comprehensive cross-section analysis of the deployed {args.program} binary,
covering data layout, relocations, data dependencies, Anchor IDL recovery,
and mathematical pattern extraction.

## Binary
- SHA-256: `{summary["deployed_sha256"]}`
- .text: {text_bytes:,} bytes

## Layer Results

### Layer 1: Data Layout
- Sections analyzed: {l1["sections_analyzed"]}
- Strings extracted: {l1["total_strings"]}
- Pointer-like values: {l1["total_pointers"]}

### Layer 2: Relocation Map
- Total relocations: {l2["total"]}
- In .text: {l2["in_text"]}
- In .rodata: {l2["in_rodata"]}
- Unique symbols: {l2["unique_symbols"]}

### Layer 3: Cross-Section Correlation
- Windows referencing .rodata: {l3["windows_with_rodata_refs"]}
- Windows referencing .data.rel.ro: {l3["windows_with_data_refs"]}
- Total data references: {l3["total_rodata_refs"]}

### Layer 4: Anchor IDL Recovery
- Instruction discriminators: {l4["discriminators"]}
- Unique allocation sizes: {l4["unique_alloc_sizes"]}
- Deserialization patterns: {l4["deser_patterns"]}

### Layer 5: Bonding Curve Math
- Math-intensive windows: {l5["math_windows"]}
- Constant product candidates: {l5["constant_product"]}
- Fee calculation candidates: {l5["fee_calculation"]}
- Overflow-protected windows: {l5["overflow_protected"]}

## Files
| File | Description |
|------|-------------|
| layer1-data-layout.json | .rodata/.data.rel.ro structure, strings, constants |
| layer2-relocation-map.json | Full relocation table with symbol resolution |
| layer3-cross-section.json | .text → data reference mapping per window |
| layer4-anchor-idl.json | Recovered discriminators, struct sizes, deser patterns |
| layer5-math-analysis.json | Arithmetic patterns, bonding curve, fee math |
| summary.json | Per-layer aggregate statistics |

## Verification
```bash
python3 verify.py
```
"""
    (output_dir / "README.md").write_text(readme)

    verify_py = '''#!/usr/bin/env python3
import hashlib, json, os, sys
PACKET = os.path.dirname(os.path.abspath(__file__))
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""): h.update(c)
    return h.hexdigest()
def main():
    m = json.load(open(os.path.join(PACKET, "manifest.json")))
    e = 0
    for n, x in m.items():
        p = os.path.join(PACKET, n)
        if not os.path.exists(p): print(f"FAIL: {n} missing"); e += 1; continue
        if sha256_file(p) != x: print(f"FAIL: {n} hash mismatch"); e += 1
        else: print(f"  OK: {n}")
    for layer in range(1, 6):
        f = f"layer{layer}-{'data-layout' if layer==1 else 'relocation-map' if layer==2 else 'cross-section' if layer==3 else 'anchor-idl' if layer==4 else 'math-analysis'}.json"
        if not os.path.exists(os.path.join(PACKET, f)):
            print(f"FAIL: {f} missing"); e += 1
        else: print(f"  OK: layer {layer} present")
    if e: print(f"\\n{e} error(s)"); return 1
    print("\\nAll checks passed."); return 0
if __name__ == "__main__": sys.exit(main())
'''
    (output_dir / "verify.py").write_text(verify_py)

    manifest = {}
    for name in sorted(os.listdir(output_dir)):
        if name == "manifest.json":
            continue
        path = output_dir / name
        if path.is_file():
            manifest[name] = sha256_file(str(path))
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    total_lines = sum(
        sum(1 for _ in open(output_dir / name))
        for name in os.listdir(output_dir) if (output_dir / name).is_file()
    )
    print(f"[deep] wrote {len(manifest)+1} files, ~{total_lines:,} lines to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
