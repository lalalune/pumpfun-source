#!/usr/bin/env python3
"""Cross-program bytecode signature analysis.

Builds a signature database from all three programs, identifying:
- Common bytecode patterns shared across programs
- Syscall calling conventions and sequences
- Error handling patterns (check + branch + error emission)
- Account validation sequences
- CPI (Cross-Program Invocation) patterns
- Token-program constant loads (not transfer or CPI evidence)
- Anchor serialization/deserialization patterns

Read-only helper imports require only window_elf_reader.py. Packet generation also
requires deep_disassembly.py for its shared publication implementation.

Publication uses shared atomic no-replace/exchange operations. Replacements
retain the prior packet in a printed .previous-* sibling; unsupported hosts
fail closed.

Usage:
    python3 scripts/bytecode_signatures.py --output research/bytecode-signatures-20261028
"""
import argparse
import collections
import hashlib
import json
import os
import shutil
import stat
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from window_elf_reader import Elf

PROGRAMS = ["pump", "pump_amm", "mayhem"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


SYSCALL_NAMES = {
    # SBPF hash_symbol_name: seed-zero MurmurHash3 x86_32 of symbol bytes.
    0x207559bd: "sol_log_",
    0x5c2a3178: "sol_log_64_",
    0x52ba5096: "sol_log_compute_units_",
    0x9377323c: "sol_create_program_address",
    0x48504a38: "sol_try_find_program_address",
    0x11f49d86: "sol_sha256",
    0xd7793abb: "sol_keccak256",
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
    0xd56b5fe9: "sol_get_clock_sysvar",
    0xbf7188f6: "sol_get_rent_sysvar",
    0xedef5aee: "sol_remaining_compute_units",
}

INVOKE_SYSCALLS = ("sol_invoke_signed_c", "sol_invoke_signed_rust")
TOKEN_PROGRAMS = {
    "Tokenkeg": bytes.fromhex(
        "06ddf6e1d765a193d9cbe146ceeb79ac1cb485ed5f5b37913a8cf5857eff00a9"),
    "Tokenz": bytes.fromhex(
        "06ddf6e1ee758fde18425dbce46ccddab61afc4d83b90d27febdf928d8a18bfc"),
}


def call_symbol(elf, offset):
    """Name a syscall call at offset, or return None.

    Captured programs relocate syscalls: opcode 0x85, src=1, imm=-1, and a
    type-10 relocation whose symbol is the syscall. The hash-immediate form
    (src=0, imm=the syscall hash) is still recognized.
    """
    blob = elf.b
    if offset < 0 or offset + 8 > len(blob) or blob[offset] != 0x85:
        return None
    regs = blob[offset + 1]
    if regs == 0x00:
        return SYSCALL_NAMES.get(struct.unpack_from("<I", blob, offset + 4)[0])
    if regs >> 4 == 1 and struct.unpack_from("<i", blob, offset + 4)[0] == -1:
        relocation = (getattr(elf, "relocations", None) or {}).get(offset) or {}
        if relocation.get("type") == 10 and relocation.get("symbol"):
            return relocation["symbol"]
    return None


def instruction_offsets(elf, start, end):
    """Return logical SBF instruction offsets fully contained in [start, end)."""
    b = elf.b
    limit = min(end, len(b))
    offsets = []
    offset = max(start, 0)
    while offset + 8 <= limit:
        width = 16 if b[offset] == 0x18 else 8
        if offset + width > limit:
            break
        offsets.append(offset)
        offset += width
    return offsets


def extract_opcode_ngrams(elf, start, end, n=3):
    """Extract instruction opcode n-grams from a window."""
    opcodes = [elf.b[offset] for offset in instruction_offsets(elf, start, end)]

    ngrams = collections.Counter()
    for i in range(len(opcodes) - n + 1):
        gram = tuple(opcodes[i:i + n])
        ngrams[gram] += 1
    return ngrams, opcodes


def detect_error_patterns(elf, start, end):
    """Detect Anchor error emission patterns.

    Typical pattern:
    1. Conditional branch (checking some condition)
    2. Load error code into register
    3. Call to error emission function
    """
    b = elf.b
    offsets = instruction_offsets(elf, start, end)
    valid_targets = set(offsets)
    patterns = []
    for offset in offsets:
        opcode = b[offset]
        # Look for: conditional branch + mov immediate + call/exit.
        # Every SBPF JMP64 conditional jump, including jset, jslt and jsle:
        # https://github.com/anza-xyz/sbpf/blob/f754c707f99779a756978f87c9afd25eeeb3d92e/src/ebpf.rs#L478-L521
        if opcode in (0x15, 0x1d, 0x25, 0x2d, 0x35, 0x3d, 0x45, 0x4d,
                      0x55, 0x5d, 0x65, 0x6d, 0x75, 0x7d,
                      0xa5, 0xad, 0xb5, 0xbd, 0xc5, 0xcd, 0xd5, 0xdd):
            branch_off = struct.unpack_from("<h", b, offset + 2)[0]
            branch_target = offset + 8 + branch_off * 8
            # Check if branch leads to a mov + error pattern
            if branch_target in valid_targets:
                next_at = branch_target
                if b[next_at] in (0xb7, 0xb4):  # mov imm
                    err_code = struct.unpack_from("<i", b, next_at + 4)[0]
                    patterns.append({
                        "offset": offset - start,
                        "branch_target_offset": branch_target - start,
                        "error_code": err_code,
                        "type": "conditional_error",
                    })
    return patterns


CALL_RELOCATION_TYPE = 10
CPI_SYSCALLS = ("sol_invoke_signed_rust", "sol_invoke_signed_c")


def call_symbols(elf):
    """Map call-site offset -> relocated symbol name.

    Call instructions in these artifacts always carry the 0xffffffff
    placeholder immediate; the callee lives in .rel.dyn, so the literal
    syscall hash never appears in the instruction stream.
    """
    relocations = getattr(elf, "relocations", None) or {}
    return {
        offset: entry["symbol"]
        for offset, entry in relocations.items()
        if entry.get("type") == CALL_RELOCATION_TYPE and entry.get("symbol")
    }


def detect_cpi_patterns(elf, start, end):
    """Detect Cross-Program Invocation patterns.

    CPI involves:
    1. Setting up AccountInfo array
    2. Setting up instruction data
    3. Calling sol_invoke_signed_rust or sol_invoke_signed_c
    """
    b = elf.b
    offsets = instruction_offsets(elf, start, end)
    patterns = []
    for idx, offset in enumerate(offsets):
        name = call_symbol(elf, offset)
        if name in INVOKE_SYSCALLS:
            # Look backwards for setup pattern
            setup_instrs = 0
            for scan in reversed(offsets[:idx]):
                if offset - scan >= 200:
                    break
                if b[scan] in (0x63, 0x6b, 0x73, 0x7b):  # stx variants
                    setup_instrs += 1
            patterns.append({
                "offset": offset - start,
                "syscall": name,
                "setup_stores": setup_instrs,
            })
    return patterns


def detect_token_transfer_patterns(elf, start, end):
    """Detect exact token-program constants; retain the historical callable name.

    Four consecutive LDDW immediates form a 32-byte Tokenkeg/Token-2022 address.
    Other instructions may separate these loads. This static constant sequence
    does not establish a transfer, CPI or runtime reachability. Based on the
    accepted research detector in PR #1159; use current logical boundaries.
    """
    b = elf.b
    relocations = getattr(elf, "relocations", None) or {}
    chunks = [(offset, b[offset + 4:offset + 8] + b[offset + 12:offset + 16])
              for offset in instruction_offsets(elf, start, end) if b[offset] == 0x18]
    patterns = []
    for index in range(len(chunks) - 3):
        group = chunks[index:index + 4]
        # Keep relocated loads in the sequence so skipping one cannot splice
        # unrelated literal chunks into an apparent four-load constant.
        if any(offset in relocations for offset, _ in group):
            continue
        value = b"".join(chunk for _, chunk in group)
        for name, program_id in TOKEN_PROGRAMS.items():
            if value == program_id:
                patterns.append({
                    "offset": group[0][0] - start,
                    "type": "token_program_constant",
                    "token_program": name,
                    "program_id_hex": program_id.hex(),
                    "lddw_slots": 4,
                })
    return patterns


def detect_serialization_patterns(elf, start, end):
    """Detect Anchor/Borsh serialization patterns.

    Borsh serialization typically involves:
    - Sequential stx instructions writing to a buffer
    - memcpy calls for larger fields
    - Size calculation before allocation
    """
    b = elf.b
    offsets = instruction_offsets(elf, start, end)
    sequential_stores = 0
    max_sequential = 0
    current_run = 0
    memcpy_count = sum(
        1 for offset in offsets if call_symbol(elf, offset) == "sol_memcpy_"
    )

    for offset in offsets:
        if b[offset] in (0x63, 0x6b, 0x73, 0x7b):  # stx
            current_run += 1
            sequential_stores += 1
        else:
            max_sequential = max(max_sequential, current_run)
            current_run = 0

    max_sequential = max(max_sequential, current_run)
    return {
        "sequential_stores": sequential_stores,
        "max_store_run": max_sequential,
        "memcpy_calls": memcpy_count,
        "likely_serialization": max_sequential >= 4 or memcpy_count >= 2,
    }


def detect_account_validation(elf, start, end):
    """Detect account validation patterns.

    Account validation typically involves:
    - Loading account discriminator (first 8 bytes)
    - Comparing against expected value
    - Checking owner/signer/writable flags
    """
    b = elf.b
    offsets = instruction_offsets(elf, start, end)
    discriminator_checks = 0
    owner_checks = 0

    for idx, offset in enumerate(offsets):
        # Pattern: ldxdw r?, [r? + 0] followed by comparison
        if b[offset] == 0x79:  # ldxdw
            off = struct.unpack_from("<h", b, offset + 2)[0]
            if off == 0:  # loading from offset 0 (discriminator position)
                # Check if followed by comparison
                if idx + 1 < len(offsets) and b[offsets[idx + 1]] in (0x15, 0x1d, 0x55, 0x5d):
                    discriminator_checks += 1

        # Pattern: ldxdw followed by memcmp (owner check)
        if b[offset] == 0x79:
            off = struct.unpack_from("<h", b, offset + 2)[0]
            if off in (32, 40, 48):  # typical AccountInfo field offsets
                owner_checks += 1

    return {
        "discriminator_checks": discriminator_checks,
        "owner_field_accesses": owner_checks,
        "likely_account_validation": discriminator_checks >= 1,
    }


def _build_packet(output_dir, output_label=None):
    output_dir = Path(output_dir)

    all_signatures = {}
    all_patterns = {}
    cross_program_ngrams = collections.Counter()
    program_summaries = {}

    for prog_name in PROGRAMS:
        deployed_path = REPO / "evidence" / "original" / prog_name / "deployed.so"

        print(f"[sigs] Analyzing {prog_name}...")
        elf = Elf(deployed_path)
        entries = elf.entries
        boundaries = entries + [elf.hi]

        prog_signatures = []
        prog_patterns = []
        prog_ngrams = collections.Counter()

        for idx, start in enumerate(entries):
            end = boundaries[idx + 1]
            size = end - start
            name = None
            for f in elf.funcs:
                if f["start"] == start:
                    name = f["name"]
                    break

            # Extract n-grams
            ngrams, opcodes = extract_opcode_ngrams(elf, start, end, n=4)
            prog_ngrams += ngrams

            # Detect patterns
            errors = detect_error_patterns(elf, start, end)
            cpis = detect_cpi_patterns(elf, start, end)
            tokens = detect_token_transfer_patterns(elf, start, end)
            serialization = detect_serialization_patterns(elf, start, end)
            validation = detect_account_validation(elf, start, end)

            # Create signature
            opcode_hash = hashlib.sha256(bytes(opcodes)).hexdigest()[:16]
            sig = {
                "program": prog_name,
                "address": hex(start),
                "size": size,
                "name": name,
                "opcode_hash": opcode_hash,
                "instruction_count": len(opcodes),
                "error_patterns": len(errors),
                "cpi_patterns": len(cpis),
                "token_patterns": len(tokens),
                "serialization": serialization,
                "account_validation": validation,
            }
            prog_signatures.append(sig)

            pattern_record = {
                "program": prog_name,
                "address": hex(start),
                "name": name,
                "size": size,
                "errors": errors,
                "cpis": cpis,
                "tokens": tokens,
                "serialization": serialization,
                "validation": validation,
            }
            prog_patterns.append(pattern_record)

            if (idx + 1) % 200 == 0:
                print(f"[sigs]   {idx + 1}/{len(entries)} windows")

        all_signatures[prog_name] = prog_signatures
        all_patterns[prog_name] = prog_patterns
        cross_program_ngrams += prog_ngrams

        # Program-level summary
        program_summaries[prog_name] = {
            "total_windows": len(entries),
            "windows_with_errors": sum(
                1 for s in prog_signatures if s["error_patterns"] > 0),
            "windows_with_cpi": sum(
                1 for s in prog_signatures if s["cpi_patterns"] > 0),
            "windows_with_tokens": sum(
                1 for s in prog_signatures if s["token_patterns"] > 0),
            "windows_with_serialization": sum(
                1 for s in prog_signatures
                if s["serialization"]["likely_serialization"]),
            "windows_with_validation": sum(
                1 for s in prog_signatures
                if s["account_validation"]["likely_account_validation"]),
            "total_error_patterns": sum(
                s["error_patterns"] for s in prog_signatures),
            "total_cpi_patterns": sum(
                s["cpi_patterns"] for s in prog_signatures),
            "unique_opcode_hashes": len(set(
                s["opcode_hash"] for s in prog_signatures)),
        }

        print(f"[sigs] {prog_name}: {len(entries)} windows, "
              f"{program_summaries[prog_name]['total_error_patterns']} error patterns, "
              f"{program_summaries[prog_name]['total_cpi_patterns']} CPI patterns")

    # Find cross-program shared signatures (same opcode hash)
    hash_to_windows = collections.defaultdict(list)
    for prog_name, sigs in all_signatures.items():
        for sig in sigs:
            hash_to_windows[sig["opcode_hash"]].append({
                "program": prog_name,
                "address": sig["address"],
                "size": sig["size"],
                "name": sig["name"],
            })
    shared_signatures = {
        h: windows for h, windows in hash_to_windows.items()
        if len(set(w["program"] for w in windows)) > 1
    }

    # The manifest hashes every file here and verify.py requires exactly the
    # generated set, so reject leftovers from another run before writing.
    packet_files = expected_packet_files(program_summaries)
    unexpected = sorted(path.name for path in output_dir.iterdir() if path.name not in packet_files)
    if unexpected:
        raise ValueError("unexpected packet entry: " + ", ".join(unexpected))
    invalid = sorted(name for name in packet_files
                     if linked(output_dir / name)
                     or ((output_dir / name).exists() and not (output_dir / name).is_file()))
    if invalid:
        raise ValueError("packet entry is not a regular file: " + ", ".join(invalid))

    # --- Write outputs ---

    # 1. Per-program signatures
    for prog_name, sigs in all_signatures.items():
        path = output_dir / f"{prog_name}-signatures.json"
        path.write_text(json.dumps(sigs, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 2. Per-program patterns
    for prog_name, patterns in all_patterns.items():
        path = output_dir / f"{prog_name}-patterns.json"
        path.write_text(json.dumps(patterns, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 3. Cross-program shared signatures
    (output_dir / "shared-signatures.json").write_text(
        json.dumps(shared_signatures, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 4. Top n-grams
    top_ngrams = [
        {"ngram": [f"0x{o:02x}" for o in gram], "count": count}
        for gram, count in cross_program_ngrams.most_common(500)
    ]
    (output_dir / "top-ngrams.json").write_text(
        json.dumps(top_ngrams, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 5. Summary
    summary = {
        "programs": program_summaries,
        "cross_program": {
            "shared_opcode_hashes": len(shared_signatures),
            "total_windows_in_shared": sum(
                len(ws) for ws in shared_signatures.values()),
            "unique_ngram_4grams": len(cross_program_ngrams),
        },
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 6. README
    readme = f"""# Cross-Program Bytecode Signature Analysis

## Scope
Bytecode pattern detection across all three incomplete Solana programs,
identifying shared code patterns, error handling, CPI (Cross-Program
Invocation), token-program constants, serialization, and account validation patterns.
Token constants alone do not prove a transfer or CPI.

## Programs Analyzed
{chr(10).join(f'- **{p}**: {s["total_windows"]} windows' for p, s in program_summaries.items())}

## Pattern Detection Results

| Program | Error Patterns | CPI Patterns | Token Patterns | Serialization | Validation |
|---------|---------------|-------------|----------------|---------------|------------|
{chr(10).join(f'| {p} | {s["total_error_patterns"]} | {s["total_cpi_patterns"]} | {s["windows_with_tokens"]} | {s["windows_with_serialization"]} | {s["windows_with_validation"]} |' for p, s in program_summaries.items())}

## Cross-Program Sharing
- **{len(shared_signatures)}** unique bytecode signatures shared across programs
- **{summary["cross_program"]["total_windows_in_shared"]}** total windows with shared code

## Files
| File | Description |
|------|-------------|
| {{program}}-signatures.json | Per-window bytecode signatures |
| {{program}}-patterns.json | Detected patterns (errors, CPI, tokens, serialization) |
| shared-signatures.json | Windows with identical opcodes across programs |
| top-ngrams.json | Most common instruction 4-grams |
| summary.json | Aggregate statistics |

## Verification
```bash
python3 verify.py
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    # 7. Verify script
    verify_py = '''#!/usr/bin/env python3
"""Verify integrity of bytecode signature packet."""
import hashlib, json, os, sys

PACKET = os.path.dirname(os.path.abspath(__file__))
EXPECTED_FILES = frozenset(__EXPECTED_PACKET_FILES__)

def manifest_members(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate manifest key: " + name)
        result[name] = value
    return result

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if set(os.listdir(PACKET)) != EXPECTED_FILES | {"manifest.json"}:
        print("FAIL: packet directory entry set mismatch"); return 1
    try:
        with open(os.path.join(PACKET, "manifest.json"), encoding="utf-8") as stream:
            manifest = json.load(stream, object_pairs_hook=manifest_members)
    except ValueError as error:
        print(f"FAIL: invalid manifest: {error}"); return 1
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
    if errors:
        print(f"\\n{errors} error(s)"); return 1
    print("\\nAll checks passed."); return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    verify_py = verify_py.replace('__EXPECTED_PACKET_FILES__', repr([
        'README.md', 'shared-signatures.json', 'summary.json', 'top-ngrams.json', 'verify.py',
        *[f'{program}-{kind}.json' for program in program_summaries for kind in ('patterns', 'signatures')],
    ]))
    (output_dir / "verify.py").write_text(verify_py, encoding="utf-8", newline="\n")

    # 8. Manifest
    manifest = {}
    for name in sorted(os.listdir(output_dir)):
        if name == "manifest.json":
            continue
        path = output_dir / name
        if path.is_file():
            manifest[name] = sha256_file(str(path))
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    total_lines = 0
    for name in os.listdir(output_dir):
        if (output_dir / name).is_file():
            with (output_dir / name).open(encoding="utf-8") as stream:
                total_lines += sum(1 for _ in stream)
    print(f"[sigs] wrote {len(manifest) + 1} files, ~{total_lines:,} lines to {output_label or output_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    from deep_disassembly import publish_packet, temporary_sibling
    # verify.py only expects the programs analyzed here, so a skipped ELF
    # would publish a smaller packet that still verifies.
    missing = [f"evidence/original/{program}/deployed.so" for program in PROGRAMS
               if not (REPO / "evidence" / "original" / program / "deployed.so").is_file()]
    if missing:
        raise SystemExit("missing captured program ELF: " + ", ".join(missing))
    output_dir = Path(args.output)
    identity = prepare_destination(output_dir)
    staging = temporary_sibling(output_dir, "staging")
    try:
        _build_packet(staging, output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    publish_packet(staging, output_dir, identity)


def expected_packet_files(programs=None):
    programs = programs or [
        program for program in PROGRAMS
        if (REPO / 'evidence/original' / program / 'deployed.so').is_file()
    ]
    return {
        "README.md", "manifest.json", "shared-signatures.json", "summary.json",
        "top-ngrams.json", "verify.py",
        *[f"{program}-{kind}.json" for program in programs
          for kind in ("patterns", "signatures")],
    }


def linked(path):
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(metadata.st_mode)
            or bool(getattr(metadata, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
            or bool(getattr(metadata, "st_reparse_tag", 0)))


def prepare_destination(output_dir):
    from deep_disassembly import directory_identity
    output_dir = Path(output_dir)
    if linked(output_dir):
        raise ValueError("output directory is a link")
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("output path is not a directory")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    packet_files = expected_packet_files()
    existing = list(output_dir.iterdir()) if output_dir.exists() else []
    unexpected = sorted(path.name for path in existing if path.name not in packet_files)
    if unexpected:
        raise ValueError("unexpected packet entry: " + ", ".join(unexpected))
    invalid = sorted(name for name in packet_files
                     if linked(output_dir / name)
                     or ((output_dir / name).exists()
                         and not (output_dir / name).is_file()))
    if invalid:
        raise ValueError("packet entry is not a regular file: " + ", ".join(invalid))
    return directory_identity(output_dir)


if __name__ == "__main__":
    main()
