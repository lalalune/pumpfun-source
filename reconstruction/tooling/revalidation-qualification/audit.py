#!/usr/bin/env python3
"""Source-bound, mutation-aware research packet revalidation.

This is a narrow successor to the frozen scripts/revalidate_all.py.  It reuses
that reviewed source's manifest parsers and packet invocation registry while
adding pre/post input identities, bounded verifier supervision, and staged
output publication.
"""

from __future__ import annotations

import argparse
import codecs
import datetime
import errno
import hashlib
import json
import math
import os
import platform
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VERSION = "pump-revalidation-qualification-v1"
FROZEN_SOURCE = "scripts/revalidate_all.py"
FROZEN_SHA256 = '2d037c093e69a94c8a9f9c78a01a671506dd2c9f4fb50f603e752caf249c622a'
REPORT_MEMBERS = (
    "README.md",
    "failed.json",
    "inputs.json",
    "passed.json",
    "provenance.json",
    "results.json",
    "skipped.json",
    "summary.json",
    "verify.py",
)
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def auxiliary_stem(output):
    """Leave suffix room without sharing a lock for distinct long basenames."""
    prefix = ""
    for character in output.name:
        if len(os.fsencode(prefix + character)) > 64:
            break
        prefix += character
    if prefix != output.name:
        prefix += "-" + sha256_bytes(os.fsencode(output.name))
    return prefix


def is_reparse_point(info):
    return bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load_frozen(repo):
    source = repo / FROZEN_SOURCE
    raw = source.read_bytes()
    actual = sha256_bytes(raw)
    if actual != FROZEN_SHA256:
        raise ValueError(
            "reviewed revalidator source changed: " + actual + " != " + FROZEN_SHA256
        )
    module = types.ModuleType("reviewed_revalidate_all")
    module.__file__ = str(source)
    exec(compile(raw, str(source), "exec"), module.__dict__)
    module.REPO = repo
    return module


def entry_record(packet, path):
    relative = path.relative_to(packet).as_posix()
    info = path.lstat()
    if stat.S_ISREG(info.st_mode):
        return {
            "path": relative,
            "kind": "file",
            "mode": stat.S_IMODE(info.st_mode),
            "bytes": info.st_size,
            "sha256": sha256_file(path),
        }
    if stat.S_ISLNK(info.st_mode):
        return {"path": relative, "kind": "symlink", "target": os.readlink(path)}
    if is_reparse_point(info):
        try:
            target = os.readlink(path)
        except OSError:
            target = None
        return {"path": relative, "kind": "reparse-point", "target": target}
    if stat.S_ISDIR(info.st_mode):
        return {
            "path": relative,
            "kind": "directory",
            "mode": stat.S_IMODE(info.st_mode),
        }
    if stat.S_ISFIFO(info.st_mode):
        kind = "fifo"
    elif stat.S_ISSOCK(info.st_mode):
        kind = "socket"
    elif stat.S_ISCHR(info.st_mode):
        kind = "character-device"
    elif stat.S_ISBLK(info.st_mode):
        kind = "block-device"
    else:
        kind = "unsupported"
    return {"path": relative, "kind": kind, "mode": stat.S_IMODE(info.st_mode)}


def packet_snapshot(packet):
    """Inventory packet entries without following linked directories or files."""
    root_info = packet.lstat()
    if not stat.S_ISDIR(root_info.st_mode) or is_reparse_point(root_info):
        raise ValueError("packet root must be a real directory, not a link")
    entries = []
    stack = [packet]
    while stack:
        directory = stack.pop()
        for path in sorted(directory.iterdir(), key=lambda item: item.name, reverse=True):
            info = path.lstat()
            if stat.S_ISDIR(info.st_mode) and not is_reparse_point(info):
                entries.append(entry_record(packet, path))
                stack.append(path)
            else:
                entries.append(entry_record(packet, path))
    entries.sort(key=lambda row: row["path"])
    files = [row for row in entries if row["kind"] == "file"]
    by_name = {row["path"]: row for row in entries}
    return {
        "identity_sha256": sha256_bytes(canonical_bytes(entries)),
        "entry_count": len(entries),
        "regular_file_count": len(files),
        "regular_file_bytes": sum(row["bytes"] for row in files),
        "manifest_files": [
            by_name[name] for name in ("MANIFEST.json", "manifest.json") if name in by_name
        ],
        "verifier": by_name.get("verify.py"),
        "entries": entries,
    }


def snapshot_summary(snapshot):
    return {key: snapshot[key] for key in (
        "identity_sha256",
        "entry_count",
        "regular_file_count",
        "regular_file_bytes",
        "manifest_files",
        "verifier",
    )}


def changed_paths(before, after):
    left = {row["path"]: row for row in before["entries"]}
    right = {row["path"]: row for row in after["entries"]}
    return sorted(name for name in left.keys() | right.keys() if left.get(name) != right.get(name))


def process_group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def cleanup_process(proc, grace_seconds):
    """Bound cleanup of the verifier leader and its original process group."""
    if os.name == "posix":
        if process_group_exists(proc.pid):
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            deadline = time.monotonic() + grace_seconds
            while time.monotonic() < deadline and process_group_exists(proc.pid):
                time.sleep(0.01)
            if process_group_exists(proc.pid):
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
    elif proc.poll() is None:
        proc.kill()
    try:
        proc.wait(timeout=max(grace_seconds, 0.05))
    except subprocess.TimeoutExpired:
        if proc.poll() is None:
            proc.kill()
        try:
            proc.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            pass


def read_capture(handle):
    handle.flush()
    size = os.fstat(handle.fileno()).st_size
    handle.seek(0)
    digest = hashlib.sha256()
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    byte_count = character_count = 0
    tail = ""
    # Read only the size observed above: an escaped descendant can still
    # append, and receipt collection must not follow it indefinitely.
    while byte_count < size:
        raw = handle.read(min(65536, size - byte_count))
        if not raw:
            break
        digest.update(raw)
        byte_count += len(raw)
        text = decoder.decode(raw)
        character_count += len(text)
        tail = (tail + text)[-2000:]
    text = decoder.decode(b"", final=True)
    character_count += len(text)
    tail = (tail + text)[-2000:]
    return {
        "output": tail.strip(),
        "output_bytes": byte_count,
        "output_sha256": digest.hexdigest(),
        "output_truncated": character_count > 2000,
    }


def verifier_command(frozen, repo, packet):
    command = [sys.executable, "-B", str(packet / "verify.py")]
    try:
        relative = packet.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        relative = None
    if relative in frozen.REPOSITORY_ARGUMENT_PACKETS:
        command.extend(["--repo", str(repo.resolve())])
    return command


def validate_deadlines(timeout_seconds, cleanup_seconds):
    for value in (timeout_seconds, cleanup_seconds):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("process deadlines must be positive finite numbers")


def run_verifier(frozen, repo, packet, timeout_seconds=60.0, cleanup_seconds=1.0):
    validate_deadlines(timeout_seconds, cleanup_seconds)
    verify_path = packet / "verify.py"
    if not verify_path.exists():
        return {"status": "no_verify_script", "output": ""}
    try:
        info = verify_path.lstat()
    except OSError as error:
        return {"status": "error", "output": str(error)}
    if not stat.S_ISREG(info.st_mode):
        return {"status": "error", "output": "verify.py is not a regular file"}

    command = verifier_command(frozen, repo, packet)
    started = time.monotonic()
    with tempfile.TemporaryFile(prefix="pump-revalidation-output-") as capture:
        proc = None
        status = "error"
        returncode = None
        interrupted = False
        try:
            # An inherited PYTHONOPTIMIZE would strip verifier assertions.
            kwargs = {"env": {name: value for name, value in os.environ.items()
                              if name != "PYTHONOPTIMIZE"}}
            if os.name == "posix":
                kwargs["start_new_session"] = True
            elif os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(
                command,
                cwd=str(packet),
                stdout=capture,
                stderr=subprocess.STDOUT,
                **kwargs,
            )
            try:
                returncode = proc.wait(timeout=timeout_seconds)
                status = "pass" if returncode == 0 else "fail"
                # A successful leader may still leave same-group descendants.
                cleanup_process(proc, cleanup_seconds)
            except subprocess.TimeoutExpired:
                status = "timeout"
                cleanup_process(proc, cleanup_seconds)
                returncode = proc.returncode
        except KeyboardInterrupt:
            interrupted = True
            if proc is not None:
                cleanup_process(proc, cleanup_seconds)
            raise
        except BaseException as error:
            if proc is not None:
                cleanup_process(proc, cleanup_seconds)
            captured = read_capture(capture)
            captured.update({
                "status": "error",
                "returncode": proc.returncode if proc is not None else None,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "command": command,
                "error": f"{type(error).__name__}: {error}",
            })
            return captured
        finally:
            if interrupted and proc is not None and proc.poll() is None:
                cleanup_process(proc, cleanup_seconds)
        captured = read_capture(capture)
    captured.update({
        "status": status,
        "returncode": returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "timeout_seconds": timeout_seconds,
        "cleanup_seconds": cleanup_seconds,
        "command": command,
    })
    if status == "timeout":
        captured["error"] = f"verify.py exceeded {timeout_seconds:g}s"
    return captured


def classify(has_manifest, has_verify, manifest_before, verify, manifest_after, mutation):
    if mutation["status"] in {"fail", "error", "packet_mutated"}:
        return "fail"
    if not has_manifest and not has_verify:
        return "no_verification"
    checks = []
    if has_manifest:
        checks.extend([manifest_before, manifest_after])
    if has_verify:
        checks.append(verify)
    checks.append(mutation)
    if all(result["status"] == "pass" for result in checks):
        return "pass"
    if any(result["status"] in {
        "fail", "manifest_parse_error", "timeout", "error", "packet_mutated"
    } for result in checks):
        return "fail"
    return "inconclusive"


def unique_manifest_fields(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate manifest JSON field: ' + name)
        result[name] = value
    return result


def safe_manifest_check(frozen, packet):
    try:
        # The frozen parser keeps only the last occurrence of a JSON key.
        # Reject ambiguous declarations before delegating its format/hash checks.
        for path in frozen.manifest_paths(packet):
            if frozen.linked(path) or not stat.S_ISREG(path.lstat().st_mode):
                return {"status": "fail", "errors": ["manifest is not a regular file: " + path.name]}
            json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_manifest_fields)
        result = frozen.check_manifest(packet)
        if result.get("status") == "pass" and not result.get("files_expected"):
            # A manifest that declares no files verifies nothing.
            result = {**result, "status": "fail",
                      "errors": [*result.get("errors", []), "manifest declares no files"]}
        return result
    except Exception as error:
        return {
            "status": "error",
            "errors": [f"{type(error).__name__}: {error}"],
        }


def audit_packet(frozen, repo, packet, timeout_seconds, cleanup_seconds):
    before = packet_snapshot(packet)
    has_verify = bool(before["verifier"])
    has_manifest = bool(before["manifest_files"])
    non_file_manifests = [row["path"] for row in before["manifest_files"]
                          if row["kind"] != "file"]
    manifest_blocked = (
        {"status": "fail", "errors": [
            "manifest is not a regular file: " + name
            for name in non_file_manifests]}
        if non_file_manifests else None
    )
    non_file_members = [row["path"] for row in before["entries"]
                        if row["kind"] not in {"file", "directory"}]
    members_blocked = (
        {"status": "fail", "errors": [
            "packet member is not a regular file: " + name
            for name in non_file_members]}
        if non_file_members else None
    )
    manifest_before = manifest_blocked or members_blocked or (
        safe_manifest_check(frozen, packet) if has_manifest else {"status": "skipped"}
    )
    verify = (
        {"status": "skipped", "reason": "packet contains nonregular input members"}
        if members_blocked else run_verifier(frozen, repo, packet, timeout_seconds, cleanup_seconds)
        if has_verify else {"status": "skipped"}
    )
    try:
        after = packet_snapshot(packet)
        changes = changed_paths(before, after)
        mutation = {
            "status": "pass" if not changes else "packet_mutated",
            "changed_paths": changes,
            "before_sha256": before["identity_sha256"],
            "after_sha256": after["identity_sha256"],
        }
    except Exception as error:
        after = {"entries": [], "identity_sha256": None, "snapshot_error": str(error)}
        changes = ["<snapshot-error>"]
        mutation = {
            "status": "error",
            "changed_paths": changes,
            "before_sha256": before["identity_sha256"],
            "after_sha256": None,
            "error": f"{type(error).__name__}: {error}",
        }
    after_non_file_members = [row["path"] for row in after["entries"]
                             if row["kind"] not in {"file", "directory"}]
    non_file_members = sorted(set(non_file_members + after_non_file_members))
    if non_file_members:
        mutation = {
            **mutation,
            "status": "fail" if mutation["status"] == "pass" else mutation["status"],
            "errors": [
                "packet member is not a regular file: " + name
                for name in non_file_members
            ],
        }
    members_blocked_after = (
        {"status": "fail", "errors": mutation["errors"]}
        if non_file_members else None
    )
    manifest_after = manifest_blocked or members_blocked_after or (
        safe_manifest_check(frozen, packet) if has_manifest else {"status": "skipped"}
    )
    overall = classify(
        has_manifest, has_verify, manifest_before, verify, manifest_after, mutation
    )
    row = {
        "packet": packet.name,
        "has_verify": has_verify,
        "has_manifest": has_manifest,
        "input_before": snapshot_summary(before),
        "input_after": snapshot_summary(after) if "entry_count" in after else after,
        "input_check": mutation,
        "manifest_check": manifest_before,
        "verify_check": verify,
        "manifest_check_after": manifest_after,
        "overall": overall,
    }
    return row, {"before": before, "after": after, "changed_paths": changes}


def reject_linked_ancestors(path):
    absolute = path.absolute()
    current = Path(absolute.anchor)
    parts = absolute.parts[1:] if absolute.anchor else absolute.parts
    for part in parts:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or is_reparse_point(info):
            raise ValueError("linked output path component: " + str(current))


def output_preflight(output):
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("output already exists; preserve prior audit: " + str(output))
    reject_linked_ancestors(output.parent)
    return output


def generated_verifier():
    return '''#!/usr/bin/env python3
"""Verify the immutable members and internal counts of this audit."""
import hashlib,json,stat,sys
from pathlib import Path
PACKET=Path(__file__).resolve().parent
REQUIRED_MEMBERS=__REQUIRED_MEMBERS__
def manifest_members(pairs):
 result={}
 for name,value in pairs:
  if name in result:raise ValueError("duplicate manifest key: "+name)
  result[name]=value
 return result
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as source:
  for chunk in iter(lambda:source.read(65536),b""):h.update(chunk)
 return h.hexdigest()
def main():
 manifest_path=PACKET/"manifest.json";errors=[]
 if not stat.S_ISREG(manifest_path.lstat().st_mode):errors.append("manifest type")
 try:manifest=json.loads(manifest_path.read_text(encoding="utf-8"),object_pairs_hook=manifest_members)
 except ValueError as error:
  print(json.dumps({"verified":False,"errors":[str(error)]},indent=2));return 1
 if sorted(manifest)!=list(REQUIRED_MEMBERS):errors.append("required member inventory")
 entries={path.name:path for path in PACKET.iterdir() if path.name!="manifest.json"}
 actual=sorted(entries)
 if actual!=sorted(manifest):errors.append("member inventory")
 for name,expected in manifest.items():
  path=PACKET/name
  try:regular=stat.S_ISREG(path.lstat().st_mode)
  except OSError:regular=False
  if not regular or sha(path)!=expected:errors.append(name)
 try:
  results=json.loads((PACKET/"results.json").read_text(encoding="utf-8"))
  summary=json.loads((PACKET/"summary.json").read_text(encoding="utf-8"))
  if summary["total_packets"]!=len(results):errors.append("result count")
  provenance=json.loads((PACKET/"provenance.json").read_text(encoding="utf-8"))
  if provenance["schema"]!="pump-revalidation-audit-v1":errors.append("provenance schema")
 except Exception as error:errors.append("metadata: "+type(error).__name__+": "+str(error))
 print(json.dumps({"verified":not errors,"errors":errors},indent=2));return bool(errors)
if __name__=="__main__":sys.exit(main())
'''.replace("__REQUIRED_MEMBERS__", repr(REPORT_MEMBERS))


def report_readme(summary):
    failed = summary["failed_packets"]
    failed_text = "_None — all verified packets pass._" if not failed else "\n".join(
        f"- `{row['packet']}`: {row['reason']}" for row in failed[:30]
    )
    return f"""# Research Packet Revalidation Audit

## Scope

Mutation-aware revalidation of every research packet. Manifest checks are run
before and after each verifier, and the complete packet inventory must remain
unchanged for a passing result.

## Results

| Metric | Count |
|---|---:|
| Total packets | {summary['total_packets']} |
| With verify.py | {summary['packets_with_verify']} |
| With a manifest | {summary['packets_with_manifest']} |
| Pass | {summary['pass']} |
| Fail | {summary['fail']} |
| Skip/inconclusive | {summary['skip_or_inconclusive']} |

## Failed packets

{failed_text}

`inputs.json` binds complete pre/post packet inventories. `provenance.json`
binds the reviewed audit source, this adapter, interpreter, arguments and
packet census. A passing audit proves only execution and byte consistency under
these checks; it does not establish packet authorship or program equivalence.
"""


def summarize(results, elapsed):
    counts = {name: sum(row["overall"] == name for row in results)
              for name in ("pass", "fail")}
    skipped = len(results) - counts["pass"] - counts["fail"]
    failures = []
    for row in results:
        if row["overall"] != "fail":
            continue
        reason = "fail"
        for check in (
            row["input_check"], row["manifest_check"],
            row["verify_check"], row["manifest_check_after"],
        ):
            candidate = check.get("status", "")
            if candidate not in ("pass", "skipped"):
                reason = candidate
                break
        failures.append({"packet": row["packet"], "reason": reason})
    return {
        "total_packets": len(results),
        "packets_with_verify": sum(row["has_verify"] for row in results),
        "packets_with_manifest": sum(row["has_manifest"] for row in results),
        "pass": counts["pass"],
        "fail": counts["fail"],
        "skip_or_inconclusive": skipped,
        "elapsed_seconds": round(elapsed, 3),
        "failed_packets": failures,
    }


def write_member(path, raw):
    path.write_bytes(raw)


def write_outputs(stage, results, inputs, summary, provenance):
    payloads = {
        "README.md": report_readme(summary).encode(),
        "failed.json": canonical_bytes([row["packet"] for row in results if row["overall"] == "fail"]),
        "inputs.json": canonical_bytes(inputs),
        "passed.json": canonical_bytes([row["packet"] for row in results if row["overall"] == "pass"]),
        "provenance.json": canonical_bytes(provenance),
        "results.json": canonical_bytes(results),
        "skipped.json": canonical_bytes([
            row["packet"] for row in results if row["overall"] not in ("pass", "fail")
        ]),
        "summary.json": canonical_bytes(summary),
        "verify.py": generated_verifier().encode(),
    }
    if tuple(sorted(payloads)) != REPORT_MEMBERS:
        raise ValueError("internal report member inventory")
    for name in REPORT_MEMBERS:
        write_member(stage / name, payloads[name])
    manifest = {name: sha256_file(stage / name) for name in REPORT_MEMBERS}
    write_member(stage / "manifest.json", canonical_bytes(manifest))


def verify_stage(stage):
    manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
    if sorted(manifest) != list(REPORT_MEMBERS):
        raise ValueError("staged manifest inventory")
    entries = {path.name: path for path in stage.iterdir()}
    if sorted(entries) != sorted((*REPORT_MEMBERS, "manifest.json")):
        raise ValueError("staged member inventory")
    if any(not stat.S_ISREG(path.lstat().st_mode) for path in entries.values()):
        raise ValueError("staged member type")
    for name, expected in manifest.items():
        if sha256_file(stage / name) != expected:
            raise ValueError("staged member hash: " + name)
    results = json.loads((stage / "results.json").read_text(encoding="utf-8"))
    summary = json.loads((stage / "summary.json").read_text(encoding="utf-8"))
    if summary["total_packets"] != len(results):
        raise ValueError("staged result count")


def audit(repo, output, timeout_seconds=60.0, cleanup_seconds=1.0):
    validate_deadlines(timeout_seconds, cleanup_seconds)
    repo = repo.resolve()
    frozen = load_frozen(repo)
    adapter_path = Path(__file__).resolve()
    control_inputs = {
        "adapter_sha256": sha256_file(adapter_path),
        "reviewed_source_sha256": FROZEN_SHA256,
    }
    output = output_preflight(output)
    research = repo / "research"
    packets = sorted(
        (path for path in research.iterdir()
         if path.is_dir() and not path.name.startswith(".")),
        key=lambda path: path.name,
    )
    resolved_output = output.resolve()
    for packet in packets:
        packet_root = packet.resolve()
        if resolved_output == packet_root or packet_root in resolved_output.parents:
            raise ValueError("audit output must not be inside an input packet")
    packet_names = [packet.name for packet in packets]
    output.parent.mkdir(parents=True, exist_ok=True)
    reject_linked_ancestors(output.parent)
    if not output.parent.is_dir():
        raise NotADirectoryError(str(output.parent))
    stem = auxiliary_stem(output)
    lock = output.parent / ("." + stem + ".revalidation.lock")
    lock.mkdir()
    stage = None
    started = time.monotonic()
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        stage = Path(tempfile.mkdtemp(
            prefix="." + stem + ".staging-", dir=output.parent
        ))
        results = []
        inputs = {}
        for packet in packets:
            row, snapshots = audit_packet(
                frozen, repo, packet, timeout_seconds, cleanup_seconds
            )
            results.append(row)
            inputs[packet.name] = snapshots
        final_packet_names = sorted(path.name for path in research.iterdir()
                                    if path.is_dir() and not path.name.startswith("."))
        if final_packet_names != packet_names:
            raise ValueError("research packet census changed during verification")
        # A census of names alone does not bind content: a later packet's
        # verifier could replace an already-audited packet's files, and the
        # published inputs would still describe the pre-swap inventory.
        # Re-snapshot every packet and refuse to publish if any audited
        # identity moved after its own audit. Packets whose post-audit
        # snapshot already failed keep their published fail row.
        for packet in packets:
            audited_after = inputs[packet.name]["after"].get("identity_sha256")
            if audited_after is not None:
                fresh = packet_snapshot(packet)
                if fresh["identity_sha256"] != audited_after:
                    raise ValueError(
                        "packet identity changed during verification: " + packet.name
                    )
        elapsed = time.monotonic() - started
        summary = summarize(results, elapsed)
        control_inputs_after = {
            "adapter_sha256": sha256_file(adapter_path),
            "reviewed_source_sha256": sha256_file(repo / FROZEN_SOURCE),
        }
        if control_inputs_after != control_inputs:
            raise ValueError("audit implementation changed during verification")
        try:
            adapter_name = str(adapter_path.relative_to(repo))
        except ValueError:
            adapter_name = str(adapter_path)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo,
            capture_output=True, text=True
        )
        provenance = {
            "schema": "pump-revalidation-audit-v1",
            "tool_version": VERSION,
            "adapter": {
                "path": adapter_name,
                "sha256": control_inputs["adapter_sha256"],
            },
            "reviewed_source": {"path": FROZEN_SOURCE, "sha256": FROZEN_SHA256},
            "repo": str(repo),
            "repository_head": head.stdout.strip() if head.returncode == 0 else None,
            "interpreter": {
                "executable": sys.executable,
                "version": sys.version,
                "implementation": platform.python_implementation(),
                "platform": platform.platform(),
            },
            "arguments": {
                "timeout_seconds": timeout_seconds,
                "cleanup_seconds": cleanup_seconds,
            },
            "started_utc": started_utc,
            "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "packet_census": packet_names,
            "packet_census_sha256": sha256_bytes(canonical_bytes(packet_names)),
            "control_inputs_before": control_inputs,
            "control_inputs_after": control_inputs_after,
        }
        write_outputs(stage, results, inputs, summary, provenance)
        verify_stage(stage)
        if output.exists() or output.is_symlink():
            raise FileExistsError("output appeared during audit; preserve it: " + str(output))
        frozen.standalone_rename_directory(stage, output)
        stage = None
        return summary
    finally:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
        try:
            lock.rmdir()
        except FileNotFoundError:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-timeout", type=float, default=60.0)
    parser.add_argument("--cleanup-timeout", type=float, default=1.0)
    args = parser.parse_args()
    try:
        summary = audit(
            args.repo,
            args.output,
            args.verify_timeout,
            args.cleanup_timeout,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
