#!/usr/bin/env python3
"""Revalidate every research packet in the repository.

Runs each packet's verify.py and/or checks manifest.json integrity,
producing a comprehensive audit report.

Usage:
    python3 scripts/revalidate_all.py --output research/revalidation-audit-20261028
"""
import argparse
import ctypes
import errno
import hashlib
import json
import os
import re
from pathlib import PureWindowsPath
import shutil
import subprocess
import stat
import sys
import time
import uuid
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
            if linked(path):
                return None, "linked_path"
            if path == packet_dir:
                break
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


def manifest_object(text):
    """Parse a manifest object, rejecting keys that repeat.

    json.loads() keeps the last of several entries for the same key, so a
    manifest that lists one path with conflicting digests silently verifies
    against whichever entry happened to be written last.
    """
    def reject_repeats(pairs):
        seen = set()
        for name, _ in pairs:
            if name in seen:
                raise ValueError("duplicate manifest key: " + name)
            seen.add(name)
        return dict(pairs)

    return json.loads(text, object_pairs_hook=reject_repeats)


def manifest_records(manifest):
    """Read retained flat hash maps, path-keyed records or files records.

    Records may carry optional byte counts.
    """
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if set(manifest) == {"files"} and isinstance(manifest["files"], list):
        records = manifest["files"]
    else:
        records = []
        for name, value in manifest.items():
            if isinstance(value, dict) and "path" in value:
                raise ValueError("path-keyed record repeats its path: " + name)
            fields = value if isinstance(value, dict) else {"sha256": value}
            records.append({"path": name, **fields})
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
    if linked(paths[0]):
        return {"status": "fail", "errors": [f"linked_path: {paths[0].name}"]}
    try:
        if not stat.S_ISREG(paths[0].lstat().st_mode):
            return {"status": "fail", "errors": [f"not_a_file: {paths[0].name}"]}
        manifest = manifest_object(paths[0].read_text(encoding="utf-8"))
        records = manifest_records(manifest)
    except Exception as e:
        return {"status": "manifest_parse_error", "errors": [str(e)]}

    if not records:
        # A manifest that declares no files verifies nothing.
        return {"status": "fail", "files_checked": 0,
                "files_expected": 0, "errors": ["manifest declares no files"]}

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


def required_arguments(stderr):
    """Recognize argparse's missing-argument diagnostic, not arbitrary output.

    This observes a usage failure; the process may already have performed setup
    or checks before calling parse_args. It is not proof of non-execution.
    """
    lines = stderr.splitlines()
    for line in lines:
        match = re.fullmatch(r"(.+): error: the following arguments are required: (.+)", line)
        if not match:
            continue
        program, listed = match.groups()
        if not any(value.startswith("usage: " + program + " ") or value == "usage: " + program
                   for value in lines):
            continue
        names = [part.strip() for part in listed.split(",")]
        if all(names):
            return names
    return []


def run_verify(packet_dir):
    """Run the packet's verify.py script."""
    try:
        root_is_link = linked(packet_dir)
    except FileNotFoundError:
        return {"status": "fail", "output": "packet root is not a real directory"}
    except OSError as error:
        return {"status": "fail", "output": "packet root is unreadable: " + str(error)}
    if root_is_link:
        return {"status": "fail", "output": "packet root is not a real directory"}
    verify_path = packet_dir / "verify.py"
    try:
        metadata = verify_path.lstat()
    except FileNotFoundError:
        return {"status": "no_verify_script", "output": ""}
    except OSError as error:
        return {"status": "fail", "output": "verify.py is unreadable: " + str(error)}
    if (stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode)
            or bool(getattr(metadata, "st_file_attributes", 0) &
                    getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))):
        return {"status": "fail", "output": "verify.py is not a regular file"}

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
        # Keep missing-argument failures distinct while retaining the process
        # output. A verifier may perform work before argument parsing.
        required = required_arguments(result.stderr) if result.returncode == 2 else []
        if required:
            return {
                "status": "invocation_error",
                "returncode": result.returncode,
                "required": required,
                "output": output[-500:] if len(output) > 500 else output,
            }
        return {
            "status": "pass" if passed else "fail",
            "returncode": result.returncode,
            "output": output[-500:] if len(output) > 500 else output,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "output": "verify.py exceeded 60s"}
    except Exception as e:
        return {"status": "error", "output": str(e)}


def write_reports(output_dir, packets, results, pass_count, fail_count,
                  skip_count, elapsed, invocation_error_count=0):
    """Write all audit artifacts into an unpublished directory."""
    # --- Write outputs ---

    # 1. Full results
    (output_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 2. Summary
    summary = {
        "total_packets": len(packets),
        "packets_with_verify": sum(1 for r in results if r["has_verify"]),
        "packets_with_manifest": sum(1 for r in results if r["has_manifest"]),
        "pass": pass_count,
        "fail": fail_count,
        "skip_or_inconclusive": skip_count,
        "invocation_error": invocation_error_count,
        "elapsed_seconds": round(elapsed, 1),
        "failed_packets": [
            {"packet": r["packet"],
             "manifest_errors": r["manifest_check"].get("errors", []),
             "verify_output": r["verify_check"].get("output", "")}
            for r in results if r["overall"] == "fail"
        ],
        "invocation_error_packets": [
            {"packet": r["packet"],
             "required": r["verify_check"].get("required", [])}
            for r in results if r["overall"] == "invocation_error"
        ],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 3. Pass/fail lists
    (output_dir / "passed.json").write_text(json.dumps(
        [r["packet"] for r in results if r["overall"] == "pass"],
        indent=2) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "failed.json").write_text(json.dumps(
        [r["packet"] for r in results if r["overall"] == "fail"],
        indent=2) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "invocation-errors.json").write_text(json.dumps(
        [r["packet"] for r in results if r["overall"] == "invocation_error"],
        indent=2) + "\n", encoding="utf-8", newline="\n")
    (output_dir / "skipped.json").write_text(json.dumps(
        [r["packet"] for r in results
         if r["overall"] not in ("pass", "fail", "invocation_error")],
        indent=2) + "\n", encoding="utf-8", newline="\n")

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
| Invocation error (missing required arguments) | {invocation_error_count} |
| Elapsed | {elapsed:.0f}s |

## Failed Packets
{"_None — all verified packets pass._" if fail_count == 0 else chr(10).join(
    f"- `{f['packet']}`: {'; '.join(f['manifest_errors'][:3]) or f['verify_output'][:100]}"
    for f in summary["failed_packets"][:30]
)}

## Invocation Errors
{"_None._" if invocation_error_count == 0 else chr(10).join(
    f"- `{f['packet']}`: requires {', '.join(f['required']) or 'an undeclared argument'}"
    for f in summary["invocation_error_packets"][:30]
)}

These processes reported an argparse-style missing-argument error and remain
unverified. Setup or checks may have run before parsing; this category does not
prove that the verifier was never invoked. Other nonzero exits remain failures,
and a failed manifest check takes precedence over an invocation error.

## Files
| File | Description |
|------|-------------|
| results.json | Per-packet detailed results |
| summary.json | Aggregate statistics and failure details |
| passed.json | List of passing packet names |
| failed.json | List of failing packet names |
| skipped.json | List of packets without verification |
| invocation-errors.json | List of missing-argument invocation errors |

## Verification
```bash
python3 verify.py
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    # 5. Verify script
    verify_py = '''#!/usr/bin/env python3
"""Verify integrity of this audit packet."""
import hashlib, json, os, sys
PACKET = os.path.dirname(os.path.abspath(__file__))
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
        len((output_dir / name).read_text(encoding="utf-8").splitlines())
        for name in os.listdir(output_dir) if (output_dir / name).is_file()
    )
    print(f"[revalidate] wrote {len(manifest)+1} files, ~{total_lines:,} lines")


def standalone_temporary_sibling(output_dir, label):
    # Match the shared publisher's bounded, whole-character name prefix.
    prefix = output_dir.name[:64]
    while len(os.fsencode(prefix)) > 64:
        prefix = prefix[:-1]
    while True:
        staging = output_dir.parent / (
            f".{prefix}.{label}-{os.getpid()}-{uuid.uuid4().hex}")
        try:
            staging.mkdir()
        except FileExistsError:
            continue
        return staging


def standalone_rename_directory(source, destination):
    """Publish a directory without replacing a late writer."""
    if os.name == "nt":
        source.rename(destination)
        return
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        rename = getattr(library, "renamex_np", None)
        args = (os.fsencode(source), os.fsencode(destination), 4)
        types = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    elif sys.platform.startswith("linux"):
        rename = getattr(library, "renameat2", None)
        args = (-100, os.fsencode(source), -100, os.fsencode(destination), 1)
        types = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                 ctypes.c_char_p, ctypes.c_uint]
    else:
        rename = None
    if rename is None:
        raise OSError(errno.ENOTSUP,
                      "atomic audit publication unavailable; use a supported host")
    rename.argtypes = types
    rename.restype = ctypes.c_int
    if rename(*args) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(destination))


def publication_operations():
    """Use the shared publisher when present and remain copyable otherwise."""
    try:
        from deep_disassembly import rename_directory, temporary_sibling
    except ModuleNotFoundError as error:
        if error.name != "deep_disassembly":
            raise
        return standalone_rename_directory, standalone_temporary_sibling
    return rename_directory, temporary_sibling


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
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists() or output_dir.is_symlink():
        raise FileExistsError(output_dir)

    print(f"[revalidate] Found {len(packets)} research packets")

    results = []
    pass_count = 0
    fail_count = 0
    skip_count = 0
    invocation_error_count = 0
    manifest_only = 0
    start_time = time.time()

    for i, packet in enumerate(packets):
        has_verify = os.path.lexists(packet / "verify.py")
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
        elif any(result["status"] == "invocation_error" for result in checks):
            overall = "invocation_error"
            invocation_error_count += 1
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
                  f"({pass_count} pass, {fail_count} fail, "
                  f"{invocation_error_count} invocation errors, {skip_count} skip) "
                  f"[{elapsed:.0f}s]")

    elapsed = time.time() - start_time
    print(f"[revalidate] Done: {len(packets)} packets in {elapsed:.0f}s")
    print(f"[revalidate] {pass_count} pass, {fail_count} fail, "
          f"{invocation_error_count} invocation errors, {skip_count} skip/inconclusive")

    rename_directory, temporary_sibling = publication_operations()
    staging = temporary_sibling(output_dir, "staging")
    published = False
    try:
        write_reports(
            staging, packets, results, pass_count, fail_count,
            skip_count, elapsed, invocation_error_count=invocation_error_count)
        rename_directory(staging, output_dir)
        published = True
    finally:
        if not published:
            shutil.rmtree(staging, ignore_errors=True)

if __name__ == "__main__":
    main()
