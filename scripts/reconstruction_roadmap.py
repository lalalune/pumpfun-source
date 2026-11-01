#!/usr/bin/env python3
"""Generate a reconstruction roadmap by analyzing unmatched windows.

Cross-references function call chains, identifies instruction patterns,
and maps unnamed windows to likely handler functions based on call graph
analysis and size characteristics.

Usage:
    python3 scripts/reconstruction_roadmap.py --output research/reconstruction-roadmap-20261028
"""
import argparse
import bisect
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

PROGRAMS = {
    "pump": {
        "deployed": "evidence/original/pump/deployed.so",
        "frontier_normalized": 823,
        "frontier_raw": 203,
    },
    "pump_amm": {
        "deployed": "evidence/original/pump_amm/deployed.so",
        "frontier_normalized": 660,
        "frontier_raw": 159,
    },
    "mayhem": {
        "deployed": "evidence/original/mayhem/deployed.so",
        "frontier_normalized": 438,
        "frontier_raw": 141,
    },
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_instruction(b, offset, elf):
    """Classify a single BPF instruction at the given offset."""
    if offset + 8 > len(b):
        return "truncated"
    opcode = b[offset]
    src = (b[offset + 1] >> 4) & 0xF
    dst = b[offset + 1] & 0xF
    off = struct.unpack_from("<h", b, offset + 2)[0]
    imm = struct.unpack_from("<i", b, offset + 4)[0]

    # src is the high nibble (0..15). Comparing it with the raw register
    # byte 0x10 never matches, so every Pump call was labeled call_other.
    if opcode == 0x8d:  # sBPF callx: register number is the immediate
        return "callx"
    if opcode == 0x85:  # call
        if src == 1 and imm != -1:
            reloc = getattr(elf, "relocations", None)
            if isinstance(reloc, dict) and reloc.get(offset, {}).get("type") == 10:
                return "call_relocated"
            return "call_internal"
        if src == 1 and imm == -1:
            return "call_relocated"
        if src == 0:
            return f"syscall_{imm}"
        return "call_other"
    elif opcode == 0x18:  # lddw
        return "load_64bit"
    elif opcode == 0x95:  # exit
        return "exit"
    elif opcode in (0x05, 0x15, 0x1d, 0x25, 0x2d, 0x35, 0x3d, 0x45, 0x4d,
                    0x55, 0x5d, 0x65, 0x6d, 0x75, 0x7d, 0xa5, 0xad, 0xb5,
                    0xbd, 0xc5, 0xcd, 0xd5, 0xdd):
        return "branch"
    elif opcode & 0x07 == 0x01 or opcode & 0x07 == 0x02 or opcode & 0x07 == 0x03:
        return "memory"
    elif opcode & 0x07 == 0x04 or opcode & 0x07 == 0x07:
        return "alu"
    return f"other_{opcode:#04x}"


def analyze_window_patterns(elf, start, end):
    """Analyze instruction patterns within a window."""
    b = elf.b
    patterns = collections.Counter()
    syscalls = collections.Counter()
    call_count = 0
    branch_count = 0
    exit_count = 0
    memory_ops = 0
    alu_ops = 0

    offset = start
    while offset < end:
        cls = classify_instruction(b, offset, elf)
        patterns[cls] += 1
        if cls.startswith("call"):
            call_count += 1
        if cls.startswith("syscall"):
            syscalls[cls] += 1
        if cls == "branch":
            branch_count += 1
        if cls == "exit":
            exit_count += 1
        if cls == "memory":
            memory_ops += 1
        if cls == "alu":
            alu_ops += 1
        # lddw is 16 bytes
        if b[offset] == 0x18:
            offset += 16
        else:
            offset += 8

    instruction_count = sum(patterns.values())
    return {
        "instructions": instruction_count,
        "calls": call_count,
        "branches": branch_count,
        "exits": exit_count,
        "memory_ops": memory_ops,
        "alu_ops": alu_ops,
        "syscalls": dict(syscalls.most_common()),
        "branch_density": round(branch_count / max(instruction_count, 1), 4),
        "call_density": round(call_count / max(instruction_count, 1), 4),
        "complexity_score": branch_count + call_count * 2,
    }


def build_call_tree(elf, entries, windows_by_addr):
    """Build forward and reverse call trees."""
    forward = collections.defaultdict(set)  # caller -> set of callees
    reverse = collections.defaultdict(set)  # callee -> set of callers

    for at, target in elf.calls.items():
        # Find which window the call is in
        caller_addr = None
        for i, start in enumerate(entries):
            end = entries[i + 1] if i + 1 < len(entries) else elf.hi
            if start <= at < end:
                caller_addr = start
                break
        if caller_addr is not None and target in windows_by_addr:
            forward[caller_addr].add(target)
            reverse[target].add(caller_addr)

    return forward, reverse


def trace_handler_attribution(elf, entries, forward, reverse):
    """Trace named functions to find which unnamed windows they reach."""
    # Get named windows
    named = {}
    for f in elf.funcs:
        if f["name"]:
            named[f["start"]] = f["name"]

    # BFS from each named function
    attributions = {}
    for start in entries:
        if start in named:
            continue
        # Find all named ancestors (callers)
        ancestors = set()
        visited = set()
        queue = [start]
        depth = 0
        while queue and depth < 10:
            next_queue = []
            for addr in queue:
                if addr in visited:
                    continue
                visited.add(addr)
                for caller in reverse.get(addr, set()):
                    if caller in named:
                        ancestors.add((named[caller], depth + 1))
                    else:
                        next_queue.append(caller)
            queue = next_queue
            depth += 1

        # Find all named descendants (callees)
        descendants = set()
        visited = set()
        queue = [start]
        depth = 0
        while queue and depth < 10:
            next_queue = []
            for addr in queue:
                if addr in visited:
                    continue
                visited.add(addr)
                for callee in forward.get(addr, set()):
                    if callee in named:
                        descendants.add((named[callee], depth + 1))
                    else:
                        next_queue.append(callee)
            queue = next_queue
            depth += 1

        if ancestors or descendants:
            attributions[start] = {
                # Depth ties must break on the name: sets of (name, depth)
                # iterate in hash order, so a depth-only key made the
                # published attribution order depend on PYTHONHASHSEED.
                "likely_callers": sorted(ancestors, key=lambda x: (x[1], x[0])),
                "likely_callees": sorted(descendants, key=lambda x: (x[1], x[0])),
            }

    return attributions


def analyze_cross_references(elf, entries):
    """Analyze data references and string patterns in windows."""
    # Find .rodata section for string references
    rodata = elf.secs.get(".rodata")
    rodata_strings = {}
    if rodata:
        ro_addr, ro_off, ro_size = rodata[3], rodata[4], rodata[5]
        ro_bytes = elf.b[ro_off:ro_off + ro_size]
        # Keys are virtual addresses. lddw pointers are virtual, and a captured
        # section can have sh_addr != sh_offset.
        current = []
        current_start = None

        def commit():
            if current_start is not None and len(current) >= 4:
                rodata_strings[ro_addr + current_start] = "".join(current)

        for i, byte in enumerate(ro_bytes):
            if 32 <= byte < 127:
                if current_start is None:
                    current_start = i
                current.append(chr(byte))
            else:
                commit()
                current = []
                current_start = None
        commit()

    return rodata_strings


def rodata_string_preview(strings, starts, address):
    """Preview up to 80 bytes inside a printable run, not a Rust string length."""
    index = bisect.bisect_right(starts, address) - 1
    if index < 0:
        return None
    start = starts[index]
    text = strings[start]
    offset = address - start
    if offset >= len(text):
        return None
    return text[offset:offset + 80]


def planning_windows(data):
    return [{'address': w['address'], 'size': w['size'], 'complexity': w['complexity_score'],
             'callers': [c[0] for c in w['likely_callers'][:5]],
             'callees': [c[0] for c in w['likely_callees'][:5]],
             'strings': w['string_references'][:3]}
            for w in sorted(data['window_details'], key=lambda w: -w['size']) if not w['name']]


def cluster_windows(unnamed_windows):
    clusters = []
    for w in unnamed_windows:
        names = {c[0] for c in w['likely_callers']}
        if not names:
            continue
        joined = [c for c in clusters if c['callers'] & names]
        clusters = [c for c in clusters if not c['callers'] & names]
        clusters.append({'callers': names.union(*(c['callers'] for c in joined)),
                         'windows': [a for c in joined for a in c['windows']] + [w['address']],
                         'total_bytes': sum(c['total_bytes'] for c in joined) + w['size']})
    return clusters


def prepare_output_directory(output_dir):
    """Keep a new roadmap packet from adopting entries left by another run."""
    if output_dir.is_symlink():
        raise FileExistsError(f"output directory is a symlink: {output_dir}")
    if output_dir.exists():
        if not output_dir.is_dir() or any(output_dir.iterdir()):
            raise FileExistsError(f"output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def generate_roadmap(output_dir):
    output_dir = Path(output_dir)
    prepare_output_directory(output_dir)

    all_program_data = {}

    for prog_name, prog_info in PROGRAMS.items():
        deployed_path = REPO / prog_info["deployed"]
        if not deployed_path.exists():
            print(f"[roadmap] SKIP {prog_name}: {deployed_path} not found")
            continue

        print(f"[roadmap] Analyzing {prog_name}...")
        elf = Elf(deployed_path)
        entries = elf.entries
        boundaries = entries + [elf.hi]

        # Build window index
        windows_by_addr = {}
        for i, start in enumerate(entries):
            end = boundaries[i + 1]
            name = None
            for f in elf.funcs:
                if f["start"] == start:
                    name = f["name"]
                    break
            windows_by_addr[start] = {
                "index": i,
                "address": hex(start),
                "size": end - start,
                "name": name,
            }

        # Build call trees
        forward, reverse = build_call_tree(elf, entries, windows_by_addr)

        # Trace handler attributions
        attributions = trace_handler_attribution(elf, entries, forward, reverse)

        # Cross-reference analysis
        rodata_strings = analyze_cross_references(elf, entries)
        rodata_starts = sorted(rodata_strings)

        # Analyze each window's instruction patterns
        window_details = []
        for i, start in enumerate(entries):
            end = boundaries[i + 1]
            size = end - start
            name = windows_by_addr[start]["name"]

            patterns = analyze_window_patterns(elf, start, end)
            attr = attributions.get(start, {})

            # Check for string references in relocations
            string_refs = []
            for at, info in elf.relocations.items():
                if start <= at < end and info["type"] == 8:
                    # lddw relocation — might point to rodata
                    if elf.b[at] == 0x18:
                        ptr_lo = struct.unpack_from("<I", elf.b, at + 4)[0]
                        ptr_hi = struct.unpack_from("<I", elf.b, at + 12)[0]
                        ptr = ptr_lo | (ptr_hi << 32)
                        preview = rodata_string_preview(rodata_strings, rodata_starts, ptr)
                        if preview is not None:
                            string_refs.append(preview)

            window_details.append({
                "address": hex(start),
                "address_decimal": start,
                "size": size,
                "name": name,
                "instructions": patterns["instructions"],
                "complexity_score": patterns["complexity_score"],
                "branch_density": patterns["branch_density"],
                "call_density": patterns["call_density"],
                "calls": patterns["calls"],
                "branches": patterns["branches"],
                "exits": patterns["exits"],
                "syscalls": patterns["syscalls"],
                "likely_callers": attr.get("likely_callers", []),
                "likely_callees": attr.get("likely_callees", []),
                "string_references": string_refs[:10],
                "forward_call_targets": len(forward.get(start, set())),
                "reverse_callers": len(reverse.get(start, set())),
            })

        # Priority ranking for reconstruction
        unnamed_windows = [w for w in window_details if not w["name"]]
        unnamed_windows.sort(key=lambda w: -w["size"])

        # Identify clusters of related unnamed windows
        clusters = cluster_windows(unnamed_windows)

        # Sort clusters by total bytes
        clusters.sort(key=lambda c: -c["total_bytes"])
        serializable_clusters = [
            {
                "callers": sorted(c["callers"]),
                "windows": c["windows"],
                "total_bytes": c["total_bytes"],
                "window_count": len(c["windows"]),
            }
            for c in clusters[:50]
        ]

        unmatched_estimate = len(entries) - prog_info["frontier_normalized"]
        prog_data = {
            "program": prog_name,
            "deployed_sha256": sha256_file(str(deployed_path)),
            "total_windows": len(entries),
            "frontier_normalized": prog_info["frontier_normalized"],
            "unmatched_estimate": unmatched_estimate,
            # Preserve the historical largest-N estimate, but calculate it
            # before the display cap. Unnamed does not imply byte-unmatched.
            "unmatched_bytes_estimate": sum(w["size"] for w in unnamed_windows[:unmatched_estimate]),
            "unnamed_windows_total": len(unnamed_windows),
            "unnamed_bytes_total": sum(w["size"] for w in unnamed_windows),
            "window_details": window_details,
            "unnamed_windows_by_size": [
                {"address": w["address"], "size": w["size"],
                 "complexity": w["complexity_score"],
                 "callers": [c[0] for c in w["likely_callers"][:5]],
                 "callees": [c[0] for c in w["likely_callees"][:5]],
                 "strings": w["string_references"][:3]}
                for w in unnamed_windows[:100]
            ],
            "reconstruction_clusters": serializable_clusters,
            "reconstruction_clusters_total": len(clusters),
            "rodata_strings_count": len(rodata_strings),
        }
        all_program_data[prog_name] = prog_data

    # --- Write outputs ---

    # 1. Per-program detailed analysis
    for prog_name, data in all_program_data.items():
        prog_path = output_dir / f"{prog_name}-details.json"
        prog_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"[roadmap] {prog_name}: {data['total_windows']} windows, "
              f"{data['unmatched_estimate']} estimated unmatched")

    # 2. Cross-program summary
    summary = {
        "programs": {},
        "total_unmatched_estimate": 0,
        "total_unmatched_bytes_estimate": 0,
        "total_unnamed_windows": 0,
        "total_unnamed_bytes": 0,
        "estimate_basis": "Largest unnamed windows up to the historical unmatched count; not a candidate byte comparison.",
        "priority_order": [],
    }
    for prog_name, data in all_program_data.items():
        unmatched = data["unmatched_estimate"]
        unmatched_bytes = data["unmatched_bytes_estimate"]
        summary["programs"][prog_name] = {
            "total_windows": data["total_windows"],
            "frontier_normalized": data["frontier_normalized"],
            "unmatched_estimate": unmatched,
            "unmatched_bytes_estimate": unmatched_bytes,
            "unnamed_windows_total": data["unnamed_windows_total"],
            "unnamed_bytes_total": data["unnamed_bytes_total"],
            "largest_unnamed": data["unnamed_windows_by_size"][:5],
            "reconstruction_clusters": data["reconstruction_clusters_total"],
            "displayed_reconstruction_clusters": len(data["reconstruction_clusters"]),
        }
        summary["total_unmatched_estimate"] += unmatched
        summary["total_unmatched_bytes_estimate"] += unmatched_bytes
        summary["total_unnamed_windows"] += data["unnamed_windows_total"]
        summary["total_unnamed_bytes"] += data["unnamed_bytes_total"]

    # Priority: most unmatched first, then by bytes
    summary["priority_order"] = sorted(
        summary["programs"].keys(),
        key=lambda p: -summary["programs"][p]["unmatched_estimate"]
    )

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 3. Reconstruction plan
    plan = {
        "phases": [],
        "historical_unmatched_estimate": summary["total_unmatched_estimate"],
        "candidate_basis": "Unnamed captured windows selected by size and call context; not unmatched membership.",
    }

    # Phase 1: Low-hanging fruit (small unnamed windows with known callers)
    phase1_windows = []
    for prog_name, data in all_program_data.items():
        for w in planning_windows(data):
            if w["size"] <= 512 and w["callers"]:
                phase1_windows.append({
                    "program": prog_name,
                    "address": w["address"],
                    "size": w["size"],
                    "likely_callers": w["callers"],
                })
    plan["phases"].append({
        "name": "Phase 1: Small windows with known callers",
        "description": "Windows <= 512 bytes that are called by named functions. "
                       "These are likely utility functions, validators, or simple handlers "
                       "whose behavior can be inferred from calling context.",
        "window_count": len(phase1_windows),
        "total_bytes": sum(w["size"] for w in phase1_windows),
        "display_limit": 50,
        "displayed_window_count": min(50, len(phase1_windows)),
        "windows": phase1_windows[:50],
    })

    # Phase 2: Medium windows with call context
    phase2_windows = []
    for prog_name, data in all_program_data.items():
        for w in planning_windows(data):
            if 512 < w["size"] <= 4096 and (w["callers"] or w["callees"]):
                phase2_windows.append({
                    "program": prog_name,
                    "address": w["address"],
                    "size": w["size"],
                    "likely_callers": w["callers"],
                    "likely_callees": w["callees"],
                    "strings": w["strings"],
                })
    plan["phases"].append({
        "name": "Phase 2: Medium handler bodies",
        "description": "Windows 512-4096 bytes with call graph context. "
                       "These likely correspond to individual instruction handlers "
                       "or major helper functions.",
        "window_count": len(phase2_windows),
        "total_bytes": sum(w["size"] for w in phase2_windows),
        "display_limit": 50,
        "displayed_window_count": min(50, len(phase2_windows)),
        "windows": phase2_windows[:50],
    })

    # Phase 3: Large handler bodies
    phase3_windows = []
    for prog_name, data in all_program_data.items():
        for w in planning_windows(data):
            if w["size"] > 4096:
                phase3_windows.append({
                    "program": prog_name,
                    "address": w["address"],
                    "size": w["size"],
                    "instructions": next(
                        (wd["instructions"] for wd in data["window_details"]
                         if wd["address"] == w["address"]), None),
                    "complexity": w["complexity"],
                    "likely_callers": w["callers"],
                    "strings": w["strings"],
                })
    plan["phases"].append({
        "name": "Phase 3: Large handler bodies (hardest)",
        "description": "Windows > 4096 bytes. These are the complex trade handlers, "
                       "multi-hop routing, and state management functions. "
                       "They require deep understanding of the protocol and "
                       "careful IR-level matching.",
        "window_count": len(phase3_windows),
        "total_bytes": sum(w["size"] for w in phase3_windows),
        "display_limit": 30,
        "displayed_window_count": min(30, len(phase3_windows)),
        "windows": phase3_windows[:30],
    })

    plan["total_planning_candidates"] = sum(p["window_count"] for p in plan["phases"])
    plan["total_planning_bytes"] = sum(p["total_bytes"] for p in plan["phases"])

    plan_path = output_dir / "reconstruction-plan.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 4. README
    total_files = 0
    total_lines = 0
    readme_parts = [f"""# Reconstruction Roadmap — {', '.join(PROGRAMS.keys())}

## Overview

Cross-program analysis of all three incomplete program binaries, cataloguing
unnamed code windows, call graph relationships, instruction patterns, and
a phased reconstruction plan.

## Historical reference frontier

The fixed frontier counts below are historical references, not the official
current completion score. Byte estimates take the largest unnamed windows up
to each reference's unmatched count. An unnamed window may already byte-match;
only the official candidate scorer establishes matching membership.

| Program | Windows | Matched | Unmatched (est.) | Match % |
|---------|---------|---------|------------------|---------|"""]

    for prog_name in summary["priority_order"]:
        p = summary["programs"][prog_name]
        pct = round(100 * p["frontier_normalized"] / p["total_windows"], 1)
        readme_parts.append(
            f"| {prog_name} | {p['total_windows']} | {p['frontier_normalized']} "
            f"| {p['unmatched_estimate']} | {pct}% |")

    readme_parts.append(f"""
**Total estimated unmatched:** {summary["total_unmatched_estimate"]} windows, """
        f"""{summary["total_unmatched_bytes_estimate"]:,} bytes

**Full unnamed inventory:** {summary["total_unnamed_windows"]} windows,
{summary["total_unnamed_bytes"]:,} bytes. This is a separate naming diagnostic,
not a completion deficit. Phase totals below use every eligible unnamed window,
including windows that may already match. The JSON phase lists display at most
50, 50 and 30 entries respectively; those displayed lists are not exhaustive.

## Reconstruction Phases

| Phase | Description | Windows | Bytes |
|-------|-------------|---------|-------|""")

    for phase in plan["phases"]:
        readme_parts.append(
            f"| {phase['name'].split(':')[0]} | {phase['name'].split(': ')[1]} "
            f"| {phase['window_count']} | {phase['total_bytes']:,} |")

    readme_parts.append("""
## Files

| File | Description |
|------|-------------|
| summary.json | Cross-program frontier summary |
| reconstruction-plan.json | Phased reconstruction plan with priority windows |
| pump-details.json | Per-window instruction patterns and call context for Pump |
| pump_amm-details.json | Per-window analysis for PumpSwap AMM |
| mayhem-details.json | Per-window analysis for Mayhem |

## Verification

```bash
python3 verify.py
```
""")

    readme_text = "\n".join(readme_parts)
    (output_dir / "README.md").write_text(readme_text, encoding="utf-8", newline="\n")

    # 5. Verify script
    verify_py = '''#!/usr/bin/env python3
"""Verify integrity of this roadmap packet."""
import hashlib, json, os, sys

PACKET = os.path.dirname(os.path.abspath(__file__))
REQUIRED_FILES = frozenset(__REQUIRED_PACKET_FILES__)

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
    try:
        with open(os.path.join(PACKET, "manifest.json"), encoding="utf-8") as stream:
            manifest = json.load(stream, object_pairs_hook=manifest_members)
    except ValueError as error:
        print(f"FAIL: invalid manifest: {error}"); return 1
    if not isinstance(manifest, dict) or not REQUIRED_FILES.issubset(manifest):
        print("FAIL: manifest omits required roadmap artifacts"); return 1
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
    # Cross-check summary
    summary = json.load(open(os.path.join(PACKET, "summary.json")))
    for prog in summary.get("programs", {}):
        detail_file = os.path.join(PACKET, f"{prog}-details.json")
        if os.path.exists(detail_file):
            detail = json.load(open(detail_file))
            if detail["total_windows"] != summary["programs"][prog]["total_windows"]:
                print(f"FAIL: {prog} window count mismatch"); errors += 1
            else:
                print(f"  OK: {prog} window count consistent")
    if errors:
        print(f"\\n{errors} error(s)"); return 1
    print("\\nAll checks passed."); return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    verify_py = verify_py.replace('__REQUIRED_PACKET_FILES__', repr([
        'README.md', 'summary.json', 'reconstruction-plan.json', 'verify.py',
        *[f'{program}-details.json' for program in all_program_data],
    ]))
    (output_dir / "verify.py").write_text(verify_py, encoding="utf-8", newline="\n")

    # 6. Manifest
    manifest = {}
    for name in sorted(os.listdir(output_dir)):
        if name == "manifest.json":
            continue
        path = output_dir / name
        if path.is_file():
            manifest[name] = sha256_file(str(path))
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    total_lines = sum(
        sum(1 for _ in open(output_dir / name,encoding='utf-8'))
        for name in os.listdir(output_dir)
        if (output_dir / name).is_file()
    )
    print(f"[roadmap] wrote {len(manifest) + 1} files, ~{total_lines:,} lines to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    generate_roadmap(args.output)
