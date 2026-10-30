#!/usr/bin/env python3
"""Comprehensive ELF analysis of a deployed Solana program.

Produces a detailed window inventory, call graph, function size distribution,
and cross-referencing data for reconstruction work.

Usage:
    python3 scripts/analyze_program.py --program pump --output research/pump-window-analysis-20261028
    python3 scripts/analyze_program.py --program pump_amm --output research/amm-window-analysis-20261028
"""
import argparse
import collections
import hashlib
import json
import stat
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from window_elf_reader import Elf

PACKET_FILES = frozenset({
    "README.md",
    "call-graph.json",
    "function-index.json",
    "manifest.json",
    "section-layout.json",
    "summary.json",
    "verify.py",
    "window-inventory.json",
})


def linked(path):
    """Recognize symlinks and Windows reparse-point aliases without following them."""
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return (stat.S_ISLNK(metadata.st_mode) or
            bool(getattr(metadata, "st_file_attributes", 0) &
                 getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)) or
            bool(getattr(metadata, "st_reparse_tag", 0)))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def prepare_output_directory(output_dir):
    """Reject stale packet entries before any analysis output is replaced."""
    if linked(output_dir):
        raise ValueError("output directory is a link")
    output_dir.mkdir(parents=True, exist_ok=True)
    if linked(output_dir):
        raise ValueError("output directory is a link")
    unexpected = sorted(path.name for path in output_dir.iterdir()
                        if path.name not in PACKET_FILES)
    if unexpected:
        raise ValueError("unexpected packet entry: " + ", ".join(unexpected))
    invalid = sorted(name for name in PACKET_FILES
                     if linked(output_dir / name)
                     or ((output_dir / name).exists()
                         and not (output_dir / name).is_file()))
    if invalid:
        raise ValueError("packet entry is not a regular file: " + ", ".join(invalid))


def analyze_program(program_name, output_dir):
    deployed_path = REPO / "evidence" / "original" / program_name / "deployed.so"
    if not deployed_path.exists():
        print(f"ERROR: {deployed_path} not found")
        return 1

    print(f"[analyze] Reading {deployed_path} ({deployed_path.stat().st_size:,} bytes)")
    elf = Elf(deployed_path)

    output_dir = Path(output_dir)
    prepare_output_directory(output_dir)

    # --- Window inventory ---
    windows = []
    entries = elf.entries
    boundaries = entries + [elf.hi]

    for i, start in enumerate(entries):
        end = boundaries[i + 1]
        size = end - start
        # Find function name if any
        name = None
        for f in elf.funcs:
            if f["start"] == start:
                name = f["name"]
                break

        # Analyze calls from this window
        calls_out = []
        for at, target in elf.calls.items():
            if start <= at < end:
                target_name = None
                for f in elf.funcs:
                    if f["start"] == target:
                        target_name = f["name"]
                        break
                calls_out.append({
                    "offset": at - start,
                    "target_address": hex(target),
                    "target_name": target_name,
                })

        # Analyze calls into this window
        calls_in = []
        for at, target in elf.calls.items():
            if target == start:
                caller_name = None
                for f in elf.funcs:
                    if f["start"] <= at < f["start"] + f["size"]:
                        caller_name = f["name"]
                        break
                calls_in.append({
                    "caller_address": hex(at),
                    "caller_name": caller_name,
                })

        # Relocation analysis
        relocs = elf.pattern(start, size)

        # Compute normalized hash for this window
        norm_bytes = elf.normalized[start:end]
        raw_bytes = elf.b[start:end]
        norm_hash = hashlib.sha256(norm_bytes).hexdigest()
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()

        windows.append({
            "index": i,
            "address": hex(start),
            "address_decimal": start,
            "size": size,
            "name": name,
            "normalized_sha256": norm_hash,
            "raw_sha256": raw_hash,
            "calls_out": len(calls_out),
            "calls_in": len(calls_in),
            "relocations": len(relocs),
            "call_targets": calls_out,
            "callers": calls_in,
            "relocation_details": relocs,
        })

    # --- Summary statistics ---
    total_text = elf.hi - elf.lo
    sizes = [w["size"] for w in windows]
    named_count = sum(1 for w in windows if w["name"])
    unnamed_count = sum(1 for w in windows if not w["name"])

    # Size distribution buckets
    buckets = collections.OrderedDict([
        ("0-64", 0), ("65-256", 0), ("257-1024", 0),
        ("1025-4096", 0), ("4097-16384", 0), ("16385+", 0),
    ])
    for s in sizes:
        if s <= 64:
            buckets["0-64"] += 1
        elif s <= 256:
            buckets["65-256"] += 1
        elif s <= 1024:
            buckets["257-1024"] += 1
        elif s <= 4096:
            buckets["1025-4096"] += 1
        elif s <= 16384:
            buckets["4097-16384"] += 1
        else:
            buckets["16385+"] += 1

    # Call graph density
    total_calls = sum(w["calls_out"] for w in windows)
    call_graph_edges = []
    for w in windows:
        for c in w["call_targets"]:
            call_graph_edges.append({
                "from": w["address"],
                "from_name": w["name"],
                "to": c["target_address"],
                "to_name": c["target_name"],
            })

    # Identify large unmatched windows (potential handler bodies)
    large_windows = sorted(
        [w for w in windows if w["size"] >= 1024],
        key=lambda w: -w["size"]
    )

    summary = {
        "program": program_name,
        "deployed_path": str(deployed_path.relative_to(REPO)),
        "deployed_sha256": hashlib.sha256(elf.b).hexdigest(),
        "file_size": len(elf.b),
        "text_section": {
            "start": hex(elf.lo),
            "end": hex(elf.hi),
            "size": total_text,
        },
        "total_windows": len(windows),
        "named_functions": named_count,
        "unnamed_windows": unnamed_count,
        "total_call_edges": total_calls,
        "size_distribution": buckets,
        "largest_windows": [
            {"address": w["address"], "size": w["size"], "name": w["name"]}
            for w in large_windows[:30]
        ],
        "total_relocations": sum(w["relocations"] for w in windows),
    }

    # --- Write outputs ---
    # 1. Summary
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[analyze] summary: {len(windows)} windows, {total_text:,} text bytes")

    # 2. Full window inventory
    inventory_path = output_dir / "window-inventory.json"
    inventory_path.write_text(json.dumps(windows, indent=2) + "\n", encoding="utf-8")

    # 3. Call graph
    callgraph_path = output_dir / "call-graph.json"
    callgraph_path.write_text(json.dumps(call_graph_edges, indent=2) + "\n", encoding="utf-8")

    # 4. Function index (name -> address mapping)
    func_index = {f["name"]: hex(f["start"]) for f in elf.funcs if f["name"]}
    func_index_path = output_dir / "function-index.json"
    func_index_path.write_text(json.dumps(func_index, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # 5. Section layout
    section_layout = {}
    for name, s in elf.secs.items():
        section_layout[name] = {
            "type": s[1],
            "flags": s[2],
            "address": hex(s[3]),
            "offset": hex(s[4]),
            "size": s[5],
            "sha256": hashlib.sha256(elf.b[s[4]:s[4] + s[5]]).hexdigest() if s[1] != 8 else None,
        }
    layout_path = output_dir / "section-layout.json"
    layout_path.write_text(json.dumps(section_layout, indent=2) + "\n", encoding="utf-8")

    # 6. README
    readme = f"""# {program_name} — Deployed Binary Analysis

## Source
- Binary: `{deployed_path.relative_to(REPO)}`
- SHA-256: `{summary["deployed_sha256"]}`
- File size: {summary["file_size"]:,} bytes

## .text Section
- Start: `{hex(elf.lo)}`
- End: `{hex(elf.hi)}`
- Size: {total_text:,} bytes ({total_text // 8:,} BPF instructions)

## Window Summary
| Metric | Value |
|--------|-------|
| Total windows | {len(windows)} |
| Named functions | {named_count} |
| Unnamed windows | {unnamed_count} |
| Total call edges | {total_calls} |
| Total relocations | {sum(w["relocations"] for w in windows)} |

## Size Distribution
| Range (bytes) | Count |
|---------------|-------|
{chr(10).join(f'| {k} | {v} |' for k, v in buckets.items())}

## Largest Windows (potential handler bodies)
| Address | Size (bytes) | BPF Instructions | Name |
|---------|-------------|-----------------|------|
{chr(10).join(f'| {w["address"]} | {w["size"]:,} | {w["size"]//8:,} | {w["name"] or "(unnamed)"} |' for w in large_windows[:20])}

## Files
| File | Description |
|------|-------------|
| summary.json | Program-level statistics |
| window-inventory.json | Per-window detail (address, size, calls, relocations, hashes) |
| call-graph.json | All inter-window call edges |
| function-index.json | Symbol name → address mapping |
| section-layout.json | ELF section sizes and hashes |

## Verification
```bash
python3 verify.py
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    # 7. Verify script
    verify_py = '''#!/usr/bin/env python3
"""Verify integrity of this analysis packet."""
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
    manifest = json.load(open(os.path.join(PACKET, "manifest.json"), encoding="utf-8"))
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
    summary = json.load(open(os.path.join(PACKET, "summary.json"), encoding="utf-8"))
    inventory = json.load(open(os.path.join(PACKET, "window-inventory.json"), encoding="utf-8"))
    if summary["total_windows"] != len(inventory):
        print(f"FAIL: summary says {summary['total_windows']} windows but inventory has {len(inventory)}")
        errors += 1
    else:
        print(f"  OK: window count consistent ({len(inventory)})")
    if errors:
        print(f"\\n{errors} error(s)"); return 1
    print("\\nAll checks passed."); return 0

if __name__ == "__main__":
    sys.exit(main())
'''
    verify_py = verify_py.replace('__EXPECTED_PACKET_FILES__', repr([
        'README.md', 'call-graph.json', 'function-index.json', 'section-layout.json',
        'summary.json', 'verify.py', 'window-inventory.json',
    ]))
    (output_dir / "verify.py").write_text(verify_py, encoding="utf-8")

    # 8. Manifest
    manifest = {
        name: sha256_file(str(output_dir / name))
        for name in sorted(PACKET_FILES - {"manifest.json"})
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    total_lines = sum(
        len((output_dir / name).read_text(encoding="utf-8").splitlines()) for name in manifest
    )
    print(f"[analyze] wrote {len(manifest) + 1} files, ~{total_lines:,} lines to {output_dir}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", required=True, help="Program name: pump, pump_amm, mayhem")
    parser.add_argument("--output", required=True, help="Output directory for evidence packet")
    args = parser.parse_args()
    sys.exit(analyze_program(args.program, args.output))
