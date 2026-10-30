#!/usr/bin/env python3
"""Revalidate every research packet in the repository.

Runs each packet's verify.py and/or checks manifest.json integrity,
producing a comprehensive audit report.

Usage:
    python3 scripts/revalidate_all.py --output research/revalidation-audit-20261028
"""
import argparse
import hashlib
import json
import os
from pathlib import PureWindowsPath
import subprocess
import stat
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# These archived verifiers document --repo and otherwise default it to cwd.
# Keep packet-relative cwd for legacy verifiers; supply only this known option.
REPOSITORY_ARGUMENT_PACKETS = frozenset({
    'research/tooling-legacy-capture-metadata-20261029',
    'research/tooling-roadmap-call-classification-20261029',
    'research/tooling-source-manifest-symlinks-20261029',
    'research/tooling-token-program-constant-detector-20261029',
})


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def linked(path):
    """Recognize symlinks and Windows reparse-point aliases without following them."""
    metadata = path.lstat()
    return (stat.S_ISLNK(metadata.st_mode) or
            bool(getattr(metadata, "st_file_attributes", 0) &
                 getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def manifest_file(packet_dir, name):
    """Resolve one manifest entry inside packet_dir without admitting aliases."""
    windows_path = PureWindowsPath(name)
    relative = Path(name)
    if (windows_path.anchor or windows_path.drive or "\\" in name or
            relative.anchor or not relative.parts or ".." in relative.parts):
        return None, "unsafe_path"

    full = packet_dir / relative
    try:
        for path in (full, *full.parents):
            if path == packet_dir:
                break
            if linked(path):
                return None, "linked_path"
        if not full.exists():
            return None, "missing"
        if not stat.S_ISREG(full.lstat().st_mode):
            return None, "not_a_file"
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError):
        return None, "unreadable"
    return full, None


def manifest_paths(packet_dir):
    """Recognize retained manifest filenames by exact directory-entry spelling."""
    return sorted(path for path in packet_dir.iterdir()
                  if path.name in ("manifest.json", "MANIFEST.json"))


def manifest_records(manifest):
    """Read retained flat hash maps or files records with optional byte counts."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if set(manifest) == {"files"} and isinstance(manifest["files"], list):
        records = manifest["files"]
    else:
        records = [{"path": name, "sha256": digest} for name, digest in manifest.items()]
    names = set()
    for row in records:
        if not isinstance(row, dict) or not {"path", "sha256"} <= row.keys():
            raise ValueError("manifest record requires path and sha256")
        if not row.keys() <= {"path", "sha256", "bytes"}:
            raise ValueError("unsupported manifest record fields")
        name, digest = row["path"], row["sha256"]
        if not isinstance(name, str) or not name:
            raise ValueError("manifest path must be a nonempty string")
        if name in names:
            raise ValueError("duplicate manifest path: " + name)
        names.add(name)
        if (not isinstance(digest, str) or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)):
            raise ValueError("invalid SHA-256 for: " + name)
        if "bytes" in row and (type(row["bytes"]) is not int or row["bytes"] < 0):
            raise ValueError("invalid byte count for: " + name)
    return records


def check_manifest(packet_dir):
    """Check either retained manifest format without running verify.py."""
    paths = manifest_paths(packet_dir)
    if not paths:
        return {"status": "no_manifest", "errors": []}
    if len(paths) != 1:
        return {"status": "fail", "errors": ["ambiguous manifest filenames"]}
    try:
        manifest = json.loads(paths[0].read_text(encoding="utf-8"))
        records = manifest_records(manifest)
    except Exception as e:
        return {"status": "manifest_parse_error", "errors": [str(e)]}

    errors = []
    checked = 0
    for row in records:
        name, expected = row["path"], row["sha256"]
        full, path_error = manifest_file(packet_dir, name)
        if path_error:
            errors.append(f"{path_error}: {name}")
            continue
        actual = sha256_file(str(full))
        if actual != expected:
            errors.append(f"hash_mismatch: {name}")
        if "bytes" in row and full.stat().st_size != row["bytes"]:
            errors.append(f"size_mismatch: {name}")
        checked += 1

    return {
        "status": "pass" if not errors else "fail",
        "files_checked": checked,
        "files_expected": len(records),
        "errors": errors,
    }


def run_verify(packet_dir):
    """Run the packet's verify.py script."""
    verify_path = packet_dir / "verify.py"
    if not verify_path.exists():
        return {"status": "no_verify_script", "output": ""}

    command = [sys.executable, "-B", str(verify_path)]
    try:
        relative = packet_dir.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        relative = None
    if relative in REPOSITORY_ARGUMENT_PACKETS:
        command.extend(["--repo", str(REPO.resolve())])

    try:
        result = subprocess.run(
            command,
            cwd=str(packet_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout + result.stderr).strip()
        passed = result.returncode == 0
        return {
            "status": "pass" if passed else "fail",
            "returncode": result.returncode,
            "output": output[-500:] if len(output) > 500 else output,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "output": "verify.py exceeded 60s"}
    except Exception as e:
        return {"status": "error", "output": str(e)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output)

    research_dir = REPO / "research"
    packets = sorted([
        d for d in research_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])

    # Snapshot inputs before creating an audit beneath research/, and preserve
    # prior reports by refusing an existing output before running any verifier.
    output_dir.mkdir(parents=True, exist_ok=False)

    print(f"[revalidate] Found {len(packets)} research packets")

    results = []
    pass_count = 0
    fail_count = 0
    skip_count = 0
    manifest_only = 0
    start_time = time.time()

    for i, packet in enumerate(packets):
        has_verify = (packet / "verify.py").exists()
        has_manifest = bool(manifest_paths(packet))

        if not has_verify and not has_manifest:
            results.append({
                "packet": packet.name,
                "has_verify": False,
                "has_manifest": False,
                "manifest_check": {"status": "skipped"},
                "verify_check": {"status": "skipped"},
                "overall": "no_verification",
            })
            skip_count += 1
            continue

        # Check manifest
        manifest_result = check_manifest(packet) if has_manifest else {"status": "skipped"}

        # Run verify.py
        verify_result = run_verify(packet) if has_verify else {"status": "skipped"}

        # Determine overall status
        checks = [result for enabled, result in (
            (has_manifest, manifest_result), (has_verify, verify_result)
        ) if enabled]
        if all(result["status"] == "pass" for result in checks):
            overall = "pass"
            pass_count += 1
        elif any(result["status"] in {
            "fail", "manifest_parse_error", "timeout", "error"
        } for result in checks):
            overall = "fail"
            fail_count += 1
        else:
            overall = "inconclusive"
            skip_count += 1

        results.append({
            "packet": packet.name,
            "has_verify": has_verify,
            "has_manifest": has_manifest,
            "manifest_check": manifest_result,
            "verify_check": verify_result,
            "overall": overall,
        })

        if (i + 1) % 50 == 0:
            elapsed = time.time() - start_time
            print(f"[revalidate] {i+1}/{len(packets)} "
                  f"({pass_count} pass, {fail_count} fail, {skip_count} skip) "
                  f"[{elapsed:.0f}s]")

    elapsed = time.time() - start_time
    print(f"[revalidate] Done: {len(packets)} packets in {elapsed:.0f}s")
    print(f"[revalidate] {pass_count} pass, {fail_count} fail, {skip_count} skip/inconclusive")

    # --- Write outputs ---

    # 1. Full results
    (output_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n")

    # 2. Summary
    summary = {
        "total_packets": len(packets),
        "packets_with_verify": sum(1 for r in results if r["has_verify"]),
        "packets_with_manifest": sum(1 for r in results if r["has_manifest"]),
        "pass": pass_count,
        "fail": fail_count,
        "skip_or_inconclusive": skip_count,
        "elapsed_seconds": round(elapsed, 1),
        "failed_packets": [
            {"packet": r["packet"],
             "manifest_errors": r["manifest_check"].get("errors", []),
             "verify_output": r["verify_check"].get("output", "")}
            for r in results if r["overall"] == "fail"
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    # 3. Pass/fail lists
    (output_dir / "passed.json").write_text(json.dumps(
        [r["packet"] for r in results if r["overall"] == "pass"],
        indent=2) + "\n")
    (output_dir / "failed.json").write_text(json.dumps(
        [r["packet"] for r in results if r["overall"] == "fail"],
        indent=2) + "\n")
    (output_dir / "skipped.json").write_text(json.dumps(
        [r["packet"] for r in results if r["overall"] not in ("pass", "fail")],
        indent=2) + "\n")

    # 4. README
    readme = f"""# Research Packet Revalidation Audit — {time.strftime('%Y-%m-%d')}

## Scope
Systematic revalidation of every research packet in the repository.
Each packet is checked via its manifest.json or MANIFEST.json (SHA-256 integrity) and
verify.py (standalone verification script).

## Results

| Metric | Count |
|--------|------:|
| Total packets | {len(packets)} |
| With verify.py | {sum(1 for r in results if r["has_verify"])} |
| With a manifest | {sum(1 for r in results if r["has_manifest"])} |
| **Pass** | **{pass_count}** |
| **Fail** | **{fail_count}** |
| Skip/inconclusive | {skip_count} |
| Elapsed | {elapsed:.0f}s |

## Failed Packets
{"_None — all verified packets pass._" if fail_count == 0 else chr(10).join(
    f"- `{f['packet']}`: {'; '.join(f['manifest_errors'][:3]) or f['verify_output'][:100]}"
    for f in summary["failed_packets"][:30]
)}

## Files
| File | Description |
|------|-------------|
| results.json | Per-packet detailed results |
| summary.json | Aggregate statistics and failure details |
| passed.json | List of passing packet names |
| failed.json | List of failing packet names |
| skipped.json | List of packets without verification |

## Verification
```bash
python3 verify.py
```
"""
    (output_dir / "README.md").write_text(readme)

    # 5. Verify script
    verify_py = '''#!/usr/bin/env python3
"""Verify integrity of this audit packet."""
import hashlib, json, os, sys
PACKET = os.path.dirname(os.path.abspath(__file__))
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()
def main():
    manifest = json.load(open(os.path.join(PACKET, "manifest.json")))
    errors = 0
    for name, expected in manifest.items():
        path = os.path.join(PACKET, name)
        if not os.path.exists(path):
            print(f"FAIL: {name} missing"); errors += 1; continue
        if sha256_file(path) != expected:
            print(f"FAIL: {name} hash mismatch"); errors += 1
        else:
            print(f"  OK: {name}")
    s = json.load(open(os.path.join(PACKET, "summary.json")))
    r = json.load(open(os.path.join(PACKET, "results.json")))
    if s["total_packets"] != len(r):
        print(f"FAIL: count mismatch"); errors += 1
    else:
        print(f"  OK: {len(r)} results consistent")
    if errors:
        print(f"\\n{errors} error(s)"); return 1
    print("\\nAll checks passed."); return 0
if __name__ == "__main__":
    sys.exit(main())
'''
    (output_dir / "verify.py").write_text(verify_py)

    # 6. Manifest
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
    print(f"[revalidate] wrote {len(manifest)+1} files, ~{total_lines:,} lines")


if __name__ == "__main__":
    main()
