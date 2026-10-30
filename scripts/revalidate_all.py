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
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(packet_dir):
    """Check manifest.json integrity without running verify.py."""
    manifest_path = packet_dir / "manifest.json"
    if not manifest_path.exists():
        return {"status": "no_manifest", "errors": []}

    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as e:
        return {"status": "manifest_parse_error", "errors": [str(e)]}

    errors = []
    checked = 0
    for name, expected in manifest.items():
        full = packet_dir / name
        if not full.exists():
            errors.append(f"missing: {name}")
            continue
        if full.is_dir():
            continue  # skip directory entries in manifest
        actual = sha256_file(str(full))
        if actual != expected:
            errors.append(f"hash_mismatch: {name}")
        checked += 1

    return {
        "status": "pass" if not errors else "fail",
        "files_checked": checked,
        "files_expected": len(manifest),
        "errors": errors,
    }


def run_verify(packet_dir):
    """Run the packet's verify.py script."""
    verify_path = packet_dir / "verify.py"
    if not verify_path.exists():
        return {"status": "no_verify_script", "output": ""}

    try:
        result = subprocess.run(
            [sys.executable, "-B", str(verify_path)],
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
        has_manifest = (packet / "manifest.json").exists()

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
Each packet is checked via its manifest.json (SHA-256 integrity) and
verify.py (standalone verification script).

## Results

| Metric | Count |
|--------|------:|
| Total packets | {len(packets)} |
| With verify.py | {sum(1 for r in results if r["has_verify"])} |
| With manifest.json | {sum(1 for r in results if r["has_manifest"])} |
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
