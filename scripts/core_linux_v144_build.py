#!/usr/bin/env python3
"""Fixed-source Fees v1.44 compile and recorded v1.52 strip pipeline.

No execution is authorized by this file. The frozen recorded SDK is copied, not
patched. Public Linux Criterion v2.3.3 follows its existing platform branch.
Captured program binaries are opened only after the single successful build.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import time
import tomllib
import traceback
import urllib.request

REVISION = "4ffe8bd88761059693e481ae972443c10204f7af"
PLATFORM_URL = "https://github.com/anza-xyz/platform-tools/releases/download/v1.44/platform-tools-linux-x86_64.tar.bz2"
PLATFORM_SHA = "6719b889d60677a8a2fcf4c82f68441a1afe0ab093edd2efe9f84a67a808b3e9"
PLATFORM_SIZE = 490710349
CLI_URL = "https://github.com/anza-xyz/agave/releases/download/v2.1.21/solana-release-x86_64-unknown-linux-gnu.tar.bz2"
CLI_SIZE = 298782636
CLI_SHA = "5da3359e296f1e6c13522b874317cb4cfe33e73301a9dc60b1e1435cc133b397"
CLI_ASSET_ID = 247593735
CLI_COMMIT = "8a085eebcb901b6846d1f82f4636667742146545"
RUSTUP_URL = "https://static.rust-lang.org/rustup/archive/1.29.0/x86_64-unknown-linux-gnu/rustup-init"
RUSTUP_SHA = "4acc9acc76d5079515b46346a485974457b5a79893cfb01112423c89aeb5aa10"
HOST_CHANNEL_URL = "https://static.rust-lang.org/dist/channel-rust-1.94.0.toml"
HOST_CHANNEL_SHA = "aaa177def36e01d539bee6bde95295230b9ce378f81057845db8d0ebe97898ee"
ORIGINAL_PATH = "evidence/original/pump_fees/deployed.so"
ORIGINAL_SHA = "4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e"
DARWIN_SHA = "a9c4ea9e47356a91bf9bd97318746a7c207b873e32485d7786853f048d7d4afa"
SYSTEM_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
REGISTRY_NAMESPACES = ("index.crates.io-1949cf8c6b5b557f", "index.crates.io-6f17d22bba15001f")
REGISTRY_PACKAGE_COUNT = 252
TRACE_FILTER = "trace=execve,execveat,fork,vfork,clone,clone3,chdir,fchdir,symlink,symlinkat,unlink,unlinkat,rename,renameat,renameat2"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def generated_keypair_path(relative_path):
    """Classify by path spelling only; never open/stat the excluded entry."""
    return any(part.endswith("-keypair.json") for part in Path(relative_path).parts)


def tree_hashes(root, *, exclude=None, excluded_paths=None):
    """Exclude before file inspection; prune excluded directories without opening.

    Nonexcluded directory links are not followed. Exclusions retain paths only,
    never sizes, hashes, link targets or file contents.
    """
    root = Path(root)
    rows = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        directory = Path(directory)
        for name in list(dirs):
            relative = (directory / name).relative_to(root)
            if exclude is not None and exclude(relative):
                dirs.remove(name)
                if excluded_paths is not None:
                    excluded_paths.append(str(relative))
        for name in sorted(dirs + files):
            path = directory / name
            relative = path.relative_to(root)
            rel = str(relative)
            if exclude is not None and exclude(relative):
                if excluded_paths is not None:
                    excluded_paths.append(rel)
                continue
            if path.is_symlink():
                rows[rel] = {"symlink": os.readlink(path)}
            elif path.is_file():
                rows[rel] = {"sha256": digest(path), "bytes": path.stat().st_size}
    return rows


def excluded_keypair_paths(root):
    """Inventory names only; this helper performs no file-content access."""
    root = Path(root)
    excluded = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs) + files:
            relative = (Path(directory) / name).relative_to(root)
            if generated_keypair_path(relative):
                excluded.append(str(relative))
                if name in dirs:
                    dirs.remove(name)
    return sorted(excluded)


def source_hashes(source, expected):
    # Check the complete path set before opening any file. In particular, an
    # unexpected build-generated keypair in the source tree is never hashed.
    paths = {str(p.relative_to(source)): p for p in source.rglob("*") if p.is_file() or p.is_symlink()}
    if set(paths) != set(expected) or any(p.is_symlink() for p in paths.values()):
        raise ValueError("Source file paths differ from the frozen 22-file input set")
    return {name: digest(path) for name, path in paths.items()}


def prepare_compile_inputs(source, expected, fetch_target, target, evidence, env):
    """Keep Cargo's fetch metadata separate from the fresh compiler target."""
    before = source_hashes(source, expected)
    write_json(evidence / "source-after-fetch.json", before)
    excluded = []
    write_json(evidence / "fetch-target-files.json", tree_hashes(
        fetch_target, exclude=generated_keypair_path, excluded_paths=excluded))
    write_json(evidence / "fetch-target-excluded-paths.json", excluded)
    if before != expected:
        raise ValueError("Frozen source changed during locked fetch")
    if any(target.iterdir()):
        raise ValueError("The separate compiler target is not empty before build")
    env["CARGO_TARGET_DIR"] = str(target)
    write_json(evidence / "compiler-environment.json", env)
    return before


def retain_generated_outputs(attempt):
    """Retain emitted stripped/symbol ELFs on success/failure, omitting keys."""
    if attempt.state["build_attempts"] == 0:
        return
    emitted = {
        "artifacts/pump_fees_candidate.so": "pump_fees_candidate.so",
        "target/sbf-solana-solana/release/pump_fees_candidate.so": "pump_fees_candidate-unstripped.so",
    }
    # os.walk follows a symlink supplied as its root even with followlinks=False.
    # Reject the complete emitted path chains before any inventory hashes files.
    for relative in emitted:
        chain = [attempt.output / Path(*Path(relative).parts[:i])
                 for i in range(1, len(Path(relative).parts) + 1)]
        if any(path.is_symlink() for path in chain):
            raise ValueError("Candidate must be a regular emitted file, not a symlink")
    excluded = set(attempt.state.get("excluded_generated_keypair_paths", []))
    for name, report in [("target", "target-files.json"), ("artifacts", "artifact-files.json")]:
        root = attempt.output / name
        if not root.exists():
            continue
        omitted = []
        rows = tree_hashes(root, exclude=generated_keypair_path, excluded_paths=omitted)
        write_json(attempt.evidence / report, rows)
        excluded.update(str(Path(name) / path) for path in omitted)
    attempt.state["excluded_generated_keypair_paths"] = sorted(excluded)
    attempt.save()
    for relative, retained in emitted.items():
        candidate = attempt.output / relative
        if candidate.is_file():
            shutil.copy2(candidate, attempt.evidence / retained)


def seal_evidence(attempt):
    excluded = set(attempt.state.get("excluded_generated_keypair_paths", []))
    excluded.update(str(Path("evidence") / path) for path in excluded_keypair_paths(attempt.evidence))
    attempt.state["excluded_generated_keypair_paths"] = sorted(excluded)
    attempt.save()
    # Never include this manifest in its own digest set when resealing a test.
    rows = tree_hashes(attempt.evidence, exclude=lambda path: generated_keypair_path(path) or str(path) == "artifact-hashes.json")
    write_json(attempt.evidence / "artifact-hashes.json", rows)


class Attempt:
    def __init__(self, output):
        self.output = output
        self.evidence = output / "evidence"
        self.evidence.mkdir(parents=True)
        self.state = {"schema": 1, "source_revision": REVISION,
                      "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                      "status": "preparing", "build_attempts": 0,
                      "commands": [], "downloads": [],
                      "scope": "One fixed Fees Linux build: v1.44 compilation, v1.52 post-processing, recorded SDK bytes; no runtime probes or variants."}
        self.save()

    def save(self):
        write_json(self.evidence / "attempt.json", self.state)

    def run(self, name, command, cwd, env, check=True):
        logfile = self.evidence / "logs" / (name + ".log")
        logfile.parent.mkdir(parents=True, exist_ok=True)
        row = {"name": name, "command": [str(x) for x in command],
               "cwd": str(cwd), "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "log": str(logfile.relative_to(self.evidence)), "returncode": None}
        self.state["commands"].append(row)
        self.save()
        start = time.monotonic()
        with logfile.open("wb") as log:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        row.update(returncode=result.returncode, seconds=time.monotonic() - start,
                   log_sha256=digest(logfile))
        self.save()
        if check and result.returncode:
            raise RuntimeError(f"{name} failed with {result.returncode}; retain {logfile}")
        return result.returncode

    def download(self, name, url, expected_sha=None, expected_size=None):
        destination = self.evidence / "downloads" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_name(destination.name + ".partial")
        row = {"url": url, "file": str(destination.relative_to(self.evidence)),
               "expected_sha256": expected_sha, "expected_bytes": expected_size,
               "status": "started"}
        self.state["downloads"].append(row)
        self.save()
        request = urllib.request.Request(url, headers={"User-Agent": "pumpfun-source-fixed-build-evidence"})
        with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as target:
            row["resolved_url"] = response.geturl().split("?")[0]
            shutil.copyfileobj(response, target, length=1024 * 1024)
        row.update(sha256=digest(partial), bytes=partial.stat().st_size)
        self.save()
        if expected_sha is not None and row["sha256"] != expected_sha:
            raise ValueError(f"Unexpected archive hash: {name}")
        if expected_size is not None and row["bytes"] != expected_size:
            raise ValueError(f"Unexpected archive size: {name}")
        partial.rename(destination)
        row["status"] = ("verified" if expected_sha else "official-url-size-checked-content-hash-recorded"
                         if expected_size is not None else "downloaded-content-hash-recorded")
        self.save()
        return destination


def git_blob(repository, name):
    return subprocess.check_output(["git", "-C", str(repository), "show", REVISION + ":" + name])


def unpack(archive, destination):
    destination.mkdir(parents=True)
    with tarfile.open(archive, "r:*") as tar:
        tar.extractall(destination, filter="data")


def unpack_criterion(archive, destination):
    # The unchanged installer uses tar --strip-components 1. Materialize the
    # authentic cache payload only; do not create installer completion markers.
    staging = destination.with_name(destination.name + "-unpack")
    unpack(archive, staging)
    entries = list(staging.iterdir())
    if len(entries) != 1 or entries[0].name != "criterion-v2.3.3" or not entries[0].is_dir():
        raise ValueError("Unexpected official Criterion archive root")
    entries[0].rename(destination)
    staging.rmdir()


def check_sdk_executable_modes(sdk, evidence, label):
    """Check shipped script modes; never chmod or rewrite the frozen SDK."""
    names = ["scripts/" + name + ".sh" for name in ["dump", "install", "objcopy", "package", "strip"]]
    rows, invalid = {}, []
    for name in names:
        path = sdk / name
        if path.is_symlink() or not path.is_file():
            rows[name] = {"regular_file": False, "symlink": path.is_symlink()}
            invalid.append(name)
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        rows[name] = {"mode": oct(mode), "sha256": digest(path), "executable": os.access(path, os.X_OK)}
        if mode != 0o755 or not rows[name]["executable"]:
            invalid.append(name)
    write_json(evidence / ("sdk-script-modes-" + label + ".json"), rows)
    if invalid:
        raise ValueError("Recorded SDK scripts must be regular files with authentic executable 0755 modes: " + ", ".join(invalid))
    return rows


def preflight_tracer(attempt, source, env):
    """Exercise the exact observer on /bin/true, before any compiler attempt."""
    tracer_name = shutil.which("strace", path=SYSTEM_PATH)
    if tracer_name is None:
        raise ValueError("Required external strace observer is absent; no tool-install fallback")
    tracer = Path(tracer_name).resolve()
    if not tracer.is_file() or not os.access(tracer, os.X_OK):
        raise ValueError("Native strace is not executable")
    write_json(attempt.evidence / "tracer-binary.json", {"path": str(tracer), "bytes": tracer.stat().st_size, "sha256": digest(tracer)})
    attempt.run("tracer-version", [str(tracer), "--version"], source, env)
    package_status = attempt.run("tracer-package", ["dpkg-query", "-W", "strace"], source, env, check=False)
    target = Path("/bin/true")
    prefix = attempt.evidence / "logs/tracer-preflight"
    command = [str(tracer), "-ff", "-ttt", "-s", "4096", "-y", "-o", str(prefix), "-e", TRACE_FILTER, "--", str(target)]
    code = attempt.run("tracer-preflight", command, source, env, check=False)
    files = sorted(p for p in prefix.parent.glob(prefix.name + ".*") if p.suffix[1:].isdigit())
    rows = [{"path": str(p.relative_to(attempt.evidence)), "sha256": digest(p), "bytes": p.stat().st_size} for p in files]
    successful_exec = any(re.search(r'execve\("/bin/true",.*\)\s+=\s+0(?:\s|$)', p.read_text()) for p in files)
    result = {"command": command, "returncode": code, "trace_files": rows, "successful_true_exec_recorded": successful_exec,
              "target_realpath": str(target.resolve()), "target_sha256": digest(target), "package_query_returncode": package_status,
              "build_attempts": attempt.state["build_attempts"], "compiler_executed": False,
              "scope": "Native observer readiness only; no installer/compiler/runtime program. No fallback observer or installation."}
    write_json(attempt.evidence / "tracer-preflight.json", result)
    if code or not files or not successful_exec:
        raise ValueError("Native strace cannot record the required child trace; compiler not attempted")
    return tracer


def capture_tool_phase(evidence, label, sdk, rustup_home, compiler, stripper, criterion, tracer):
    def link(path):
        if not os.path.lexists(path):
            return {"exists": False}
        return {"exists": True, "is_symlink": path.is_symlink(),
                "link": os.readlink(path) if path.is_symlink() else None,
                "resolved": str(path.resolve())}
    result = {"phase": label, "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "sdk_platform": link(sdk / "dependencies/platform-tools"),
              "sdk_criterion": link(sdk / "dependencies/criterion"),
              "solana_alias": link(rustup_home / "toolchains/solana"),
              "sdk_dependencies": tree_hashes(sdk / "dependencies"),
              "compiler_rustc": {"path": str(compiler / "rust/bin/rustc"), "sha256": digest(compiler / "rust/bin/rustc")},
              "stripper_objcopy": {"path": str(stripper / "llvm/bin/llvm-objcopy"), "sha256": digest(stripper / "llvm/bin/llvm-objcopy")},
              "tracer": {"path": str(tracer), "sha256": digest(tracer)},
              "criterion_payload": tree_hashes(criterion)}
    write_json(evidence / ("tool-phase-" + label + ".json"), result)
    return result


def compare_strip_sections(unstripped, stripped, evidence):
    def sections(path):
        data = path.read_bytes()
        if data[:6] != b"\x7fELF\x02\x01":
            raise ValueError("Expected little-endian ELF64 output")
        offset = struct.unpack_from("<Q", data, 40)[0]
        stride, count, names_index = struct.unpack_from("<HHH", data, 58)
        rows = [struct.unpack_from("<IIQQQQIIQQ", data, offset + i * stride) for i in range(count)]
        names = rows[names_index]
        strings = data[names[4]:names[4] + names[5]]
        result = {}
        for row in rows:
            name = strings[row[0]:].split(b"\0", 1)[0].decode()
            if name:
                body = data[row[4]:row[4] + row[5]] if row[1] != 8 else b""
                result[name] = {"type": row[1], "flags": row[2], "address": row[3],
                                "bytes": row[5], "sha256": hashlib.sha256(body).hexdigest()}
        return result
    before, after = sections(unstripped), sections(stripped)
    allocated_before = {n: r for n, r in before.items() if r["flags"] & 2}
    allocated_after = {n: r for n, r in after.items() if r["flags"] & 2}
    result = {"unstripped_sha256": digest(unstripped), "stripped_sha256": digest(stripped),
              "unstripped_sections": before, "stripped_sections": after,
              "text_identical": before[".text"] == after[".text"],
              "allocated_runtime_sections_identical": allocated_before == allocated_after,
              "shared_payload_differences": sorted(n for n in before.keys() & after.keys() if before[n]["sha256"] != after[n]["sha256"]),
              "tool_version_counterfactual": "No alternative strip version was executed or compared."}
    write_json(evidence / "strip-section-comparison.json", result)
    if not result["text_identical"] or not result["allocated_runtime_sections_identical"]:
        raise ValueError("Stripping changed .text or allocated runtime section bytes/layout")
    return result


def snapshot_source(source, expected, evidence):
    actual = source_hashes(source, expected)
    if actual != expected:
        raise ValueError("The source workspace does not contain exactly the frozen 22 inputs")
    write_json(evidence / "source-before.json", actual)
    with tarfile.open(evidence / "source-snapshot.tar.gz", "w:gz") as tar:
        for name in sorted(expected):
            tar.add(source / name, arcname=name, recursive=False)


def locked_registry_packages(source):
    lock = tomllib.loads((source / "Cargo.lock").read_text())
    locked = [p for p in lock["package"] if p.get("source")]
    if len(locked) != REGISTRY_PACKAGE_COUNT or any(p["source"] != "registry+https://github.com/rust-lang/crates.io-index" for p in locked):
        raise ValueError("Frozen dependency graph unexpectedly differs from 252 public registry packages")
    if len({(p["name"], p["version"]) for p in locked}) != len(locked):
        raise ValueError("Duplicate locked registry package")
    return locked


def registry_namespace_sets(cargo_home):
    result = {}
    registry = cargo_home / "registry"
    for kind in ["cache", "src", "index"]:
        root = registry / kind
        if any(path.is_symlink() or not path.is_dir() for path in [cargo_home, registry, root]):
            raise ValueError("Registry views must be real directories: " + kind)
        paths = list(root.iterdir()) if root.is_dir() else []
        if any(p.is_symlink() or not p.is_dir() for p in paths):
            raise ValueError("Registry views must be real directories: " + kind)
        result[kind] = {p.name for p in paths}
    if len({tuple(sorted(v)) for v in result.values()}) != 1:
        raise ValueError("Cache/source/index namespace sets disagree")
    names = result["cache"]
    if not names or not names.issubset(REGISTRY_NAMESPACES):
        raise ValueError("Unexpected registry namespace set: " + repr(sorted(names)))
    return names


def inventory_registry_view(cargo_home, locked, namespace):
    """Validate every selected archive and extracted byte in one real view."""
    cache = cargo_home / "registry/cache" / namespace
    src = cargo_home / "registry/src" / namespace
    stems = {p["name"] + "-" + p["version"] for p in locked}
    if {p.name for p in cache.iterdir()} != {s + ".crate" for s in stems}:
        raise ValueError("Archive path set differs from locked packages: " + namespace)
    if {p.name for p in src.iterdir()} != stems:
        raise ValueError("Source path set differs from locked packages: " + namespace)
    inventory, metadata = [], {}
    for package in locked:
        stem = package["name"] + "-" + package["version"]
        archive, directory = cache / (stem + ".crate"), src / stem
        if archive.is_symlink() or not archive.is_file() or directory.is_symlink() or not directory.is_dir():
            raise ValueError("Registry archive/source must not be symlink aliases: " + stem)
        observed = digest(archive)
        if observed != package["checksum"]:
            raise ValueError(f"Lock checksum mismatch: {stem}")
        files = tree_hashes(directory)
        if any("symlink" in row for row in files.values()):
            raise ValueError("Registry source contains symlink: " + stem)
        archive_files = {}
        with tarfile.open(archive, "r:gz") as crate:
            for member in crate:
                if member.isdir():
                    continue
                name = Path(member.name)
                if not member.isfile() or name.is_absolute() or ".." in name.parts or name.parts[0] != stem:
                    raise ValueError(f"Unexpected crate archive member: {stem}/{member.name}")
                rel = str(Path(*name.parts[1:]))
                if rel in archive_files:
                    raise ValueError(f"Duplicate crate archive member: {stem}/{rel}")
                archive_files[rel] = hashlib.sha256(crate.extractfile(member).read()).hexdigest()
                if digest(directory / rel) != archive_files[rel]:
                    raise ValueError(f"Unpacked source checksum mismatch: {stem}/{rel}")
        if set(files) - set(archive_files) - {".cargo-ok"}:
            raise ValueError(f"Unexpected files in fresh dependency tree: {stem}")
        if set(archive_files) - set(files):
            raise ValueError(f"Missing files in dependency tree: {stem}")
        metadata[stem] = {n: row for n, row in files.items() if n == ".cargo-ok"}
        inventory.append({"name": package["name"], "version": package["version"],
                          "source": package["source"], "lock_checksum": package["checksum"],
                          "registry_namespace": namespace,
                          "archive": str(archive.relative_to(cargo_home)),
                          "archive_sha256": observed, "archive_bytes": archive.stat().st_size,
                          "unpacked_source": str(directory.relative_to(cargo_home)),
                          "archive_file_sha256": archive_files,
                          "files": {n: files[n] for n in archive_files}})
    return inventory, metadata


def prepare_registry_views(cargo_home, source, evidence):
    """Copy authenticated fetched bytes into both observed Cargo-family views.

    No index entries, archives, source files, symlinks or completion markers are
    invented. Existing Cargo-generated .cargo-ok bytes are copied as metadata and
    labeled separately from the public archive/source proof.
    """
    locked = locked_registry_packages(source)
    fetched = registry_namespace_sets(cargo_home)
    for namespace in sorted(fetched):
        inventory_registry_view(cargo_home, locked, namespace)
        for kind in ["cache", "src", "index"]:
            rows = tree_hashes(cargo_home / "registry" / kind / namespace)
            if any("symlink" in row for row in rows.values()):
                raise ValueError("Fetched registry view contains links: " + namespace + "/" + kind)
    origin = REGISTRY_NAMESPACES[0] if REGISTRY_NAMESPACES[0] in fetched else sorted(fetched)[0]
    copies = []
    for namespace in REGISTRY_NAMESPACES:
        if namespace in fetched:
            continue
        for kind in ["cache", "src", "index"]:
            src = cargo_home / "registry" / kind / origin
            dst = cargo_home / "registry" / kind / namespace
            before = tree_hashes(src)
            shutil.copytree(src, dst)
            if tree_hashes(dst) != before or tree_hashes(src) != before:
                raise ValueError("Registry view copy differs: " + namespace + "/" + kind)
            copies.append({"kind": kind, "from_namespace": origin, "to_namespace": namespace,
                           "files": len(before), "tree_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()})
    if registry_namespace_sets(cargo_home) != set(REGISTRY_NAMESPACES):
        raise ValueError("Both Cargo-family registry views were not prepared")
    proof = {"fetched_namespaces": sorted(fetched), "required_namespaces": list(REGISTRY_NAMESPACES),
             "copied_views": copies, "public_registry_packages": len(locked),
             "scope": "Byte-identical real directory views of authentic locked public fetch; copied views are not claimed as native Cargo extraction.",
             "namespace_basis": "Retained host-Cargo 1.94 metadata and platform-tools v1.44 depfiles; no version search or compiler flags.",
             "source_lock_changed": False, "symlink_aliases_created": False, "metadata_markers_fabricated": False}
    write_json(evidence / "registry-view-preparation.json", proof)
    return proof


def dependency_inventory(cargo_home, source, evidence, suffix):
    locked = locked_registry_packages(source)
    if registry_namespace_sets(cargo_home) != set(REGISTRY_NAMESPACES):
        raise ValueError("Expected both verified Cargo-family registry views")
    views, metadata = {}, {}
    for namespace in REGISTRY_NAMESPACES:
        views[namespace], metadata[namespace] = inventory_registry_view(cargo_home, locked, namespace)
    inventory = []
    archives_dir = evidence / "crate-archives"
    archives_dir.mkdir(exist_ok=True)
    for index, package in enumerate(locked):
        rows = [views[n][index] for n in REGISTRY_NAMESPACES]
        for field in ["name", "version", "source", "lock_checksum", "archive_sha256", "archive_bytes", "archive_file_sha256", "files"]:
            if rows[0][field] != rows[1][field]:
                raise ValueError("Registry public bytes differ between namespaces: " + package["name"] + "/" + field)
        origin = cargo_home / rows[0]["archive"]
        copied = archives_dir / origin.name
        if not copied.exists():
            shutil.copy2(origin, copied)
        if digest(copied) != package["checksum"]:
            raise ValueError("Retained archive differs from lock: " + origin.name)
        inventory.append({"name": package["name"], "version": package["version"], "source": package["source"],
                          "lock_checksum": package["checksum"], "registry_views": rows})
    write_json(evidence / ("dependencies-" + suffix + ".json"), inventory)
    # Cargo bookkeeping is recorded, not confused with published source bytes.
    write_json(evidence / ("dependency-cargo-metadata-" + suffix + ".json"), metadata)
    # Record index/config inputs separately; no credentials are loaded into this fresh Cargo home.
    write_json(evidence / ("registry-index-" + suffix + ".json"), tree_hashes(cargo_home / "registry/index"))
    return inventory


def compare_after_build(repository, candidate, evidence):
    """First and only captured-ELF read; compilation has already returned zero."""
    original = git_blob(repository, ORIGINAL_PATH)
    candidate_bytes = candidate.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise ValueError("Unexpected captured original at frozen source revision")
    overlap = min(len(original), len(candidate_bytes))
    first = next((i for i in range(overlap) if original[i] != candidate_bytes[i]), None)
    if first is None and len(original) != len(candidate_bytes):
        first = overlap
    result = {"comparison_phase": "after successful single source compilation",
              "original_path_at_revision": ORIGINAL_PATH, "source_revision": REVISION,
              "original_sha256": ORIGINAL_SHA, "original_bytes": len(original),
              "candidate_sha256": digest(candidate), "candidate_bytes": len(candidate_bytes),
              "full_byte_equality": original == candidate_bytes,
              "first_difference": first,
              "different_positions_in_shared_length": sum(a != b for a, b in zip(original, candidate_bytes)),
              "length_difference": len(candidate_bytes) - len(original),
              "previous_darwin_candidate_sha256": DARWIN_SHA,
              "same_sha256_as_previous_darwin_candidate": digest(candidate) == DARWIN_SHA,
              "normalization_or_patching": False,
              "runtime_validation": "not performed; prior candidate runtime receipts are not transferred by this build"}
    write_json(evidence / "whole-file-comparison.json", result)
    return result


def build(args, attempt):
    output, evidence = attempt.output, attempt.evidence
    repository = args.repository.resolve()
    actual_rev = subprocess.check_output(["git", "-C", str(repository), "rev-parse", "HEAD"], text=True).strip()
    if actual_rev != REVISION:
        raise ValueError("The input checkout must be the exact frozen revision")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("This proposal permits one Linux x86_64 environment only")
    pins = json.loads(args.inputs.read_text())
    expected = pins["source_files_sha256"]
    if pins["revision"] != REVISION or len(expected) != 22:
        raise ValueError("Unexpected source pin manifest")
    shutil.copy2(args.inputs, evidence / "source-pins.json")
    shutil.copy2(Path(__file__).resolve(), evidence / "build-helper.py")
    write_json(evidence / "runner.json", {"uname": list(platform.uname()),
              "python": sys.version, "github_run_id": os.environ.get("GITHUB_RUN_ID"),
              "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
              "image_os": os.environ.get("ImageOS"), "image_version": os.environ.get("ImageVersion"),
              "home_unchanged": os.environ["HOME"]})
    if Path("/etc/os-release").exists():
        shutil.copy2("/etc/os-release", evidence / "os-release")
    source = output / "source"
    source.mkdir()
    for name, sha in expected.items():
        p = Path(name)
        if p.is_absolute() or ".." in p.parts or p.suffix in {".so", ".o", ".a"}:
            raise ValueError("Only frozen source/workspace/IDL inputs may enter the compiler workspace")
        content = git_blob(repository, name)
        if hashlib.sha256(content).hexdigest() != sha:
            raise ValueError(f"Frozen source mismatch: {name}")
        destination = source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    snapshot_source(source, expected, evidence)
    for parent in [source, *source.parents]:
        for name in [".cargo/config", ".cargo/config.toml", "rust-toolchain", "rust-toolchain.toml"]:
            if (parent / name).exists():
                raise ValueError(f"Unexpected ancestor Cargo/toolchain configuration: {parent/name}")
    # Fail on observer/SDK readiness before tool downloads or compiler counting.
    recorded_sdk = args.recorded_sdk.resolve()
    recorded = tree_hashes(recorded_sdk)
    if {k: v.get("sha256") for k, v in recorded.items()} != pins["recorded_sdk_source_sha256"] or len(recorded) != 53:
        raise ValueError("Recorded SDK does not contain exactly the frozen 53 files")
    if any("symlink" in row for row in recorded.values()):
        raise ValueError("Recorded SDK source may not contain links")
    check_sdk_executable_modes(recorded_sdk, evidence, "input")
    tracer = preflight_tracer(attempt, source, {"HOME": os.environ["HOME"], "PATH": SYSTEM_PATH,
                                               "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"})
    # HOME stays unchanged. Cache payloads are verified artifacts, not fake markers.
    phases = pins["pipeline_tools"]
    if phases["compile_version"] != "v1.44" or phases["strip_version"] != "v1.52" or phases["criterion_version"] != "v2.3.3":
        raise ValueError("This helper permits only the frozen recorded pipeline")
    cache = Path(os.environ["HOME"]) / ".cache/solana/v1.44/platform-tools"
    strip_cache = Path(os.environ["HOME"]) / ".cache/solana/v1.52/platform-tools"
    criterion_cache = Path(os.environ["HOME"]) / ".cache/solana/v2.3.3/criterion"
    for path in [cache, strip_cache, criterion_cache]:
        if os.path.lexists(path):
            raise ValueError("Expected absent owned cache in a fresh hosted runner: " + str(path))
    platform_archive = attempt.download("platform-tools-linux-x86_64.tar.bz2", PLATFORM_URL, PLATFORM_SHA, PLATFORM_SIZE)
    tools_dir = output / "platform-tools"
    unpack(platform_archive, tools_dir)
    for member, sha in pins["platform_selected_sha256"].items():
        if digest(tools_dir / member) != sha:
            raise ValueError(f"Official selected platform member mismatch: {member}")
    write_json(evidence / "platform-files.json", tree_hashes(tools_dir))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.symlink_to(tools_dir, target_is_directory=True)
    attempt.state["platform_cache"] = {"link": str(cache), "target": str(tools_dir), "home_environment_changed": False}
    attempt.save()
    strip_archive = attempt.download("platform-tools-v152-linux-x86_64.tar.bz2", phases["strip_url"], phases["strip_sha256"], phases["strip_bytes"])
    strip_tools = output / "strip-platform-tools"
    unpack(strip_archive, strip_tools)
    for member, sha in phases["strip_selected_sha256"].items():
        if digest(strip_tools / member) != sha:
            raise ValueError("Official stripper platform member mismatch: " + member)
    write_json(evidence / "strip-platform-files.json", tree_hashes(strip_tools))
    strip_cache.parent.mkdir(parents=True, exist_ok=True)
    strip_cache.symlink_to(strip_tools, target_is_directory=True)
    criterion_archive = attempt.download("criterion-v2.3.3-linux-x86_64.tar.bz2", phases["criterion_url"], phases["criterion_sha256"], phases["criterion_bytes"])
    criterion = output / "criterion-v2.3.3"
    unpack_criterion(criterion_archive, criterion)
    criterion_before = tree_hashes(criterion)
    write_json(evidence / "criterion-payload-before.json", criterion_before)
    criterion_cache.parent.mkdir(parents=True, exist_ok=True)
    criterion_cache.symlink_to(criterion, target_is_directory=True)
    attempt.state["pipeline_caches"] = {"compiler": str(cache), "stripper": str(strip_cache), "criterion": str(criterion_cache),
                                          "completion_markers_fabricated": False,
                                          "installer_not_prerun": True}
    attempt.save()
    cli_metadata = attempt.download("agave-release.json", "https://api.github.com/repos/anza-xyz/agave/releases/tags/v2.1.21")
    release = json.loads(cli_metadata.read_text())
    matches = [x for x in release["assets"] if x["id"] == CLI_ASSET_ID and x["browser_download_url"] == CLI_URL and x["size"] == CLI_SIZE]
    if release["tag_name"] != "v2.1.21" or len(matches) != 1:
        raise ValueError("Official CLI release asset identity changed")
    cli_version = attempt.download("agave-release.yml", "https://github.com/anza-xyz/agave/releases/download/v2.1.21/solana-release-x86_64-unknown-linux-gnu.yml", "aa8f5e66f5c9e79d671b6b3e15c11cec5204ae0055408dd9ed26dba71734580f")
    if CLI_COMMIT not in cli_version.read_text():
        raise ValueError("CLI release revision mismatch")
    cli_archive = attempt.download("solana-release-x86_64-unknown-linux-gnu.tar.bz2", CLI_URL, expected_sha=CLI_SHA, expected_size=CLI_SIZE)
    cli_root = output / "cli"
    unpack(cli_archive, cli_root)
    cli_bin = cli_root / "solana-release/bin"
    cli = cli_bin / "cargo-build-sbf"
    sdk_source = cli_bin / "sdk/sbf"
    if not cli.is_file() or not sdk_source.is_dir():
        raise ValueError("Unexpected official CLI archive layout")
    write_json(evidence / "cli-files.json", tree_hashes(cli_root))
    official_sdk = tree_hashes(sdk_source, exclude=lambda path: "dependencies" in path.parts)
    if {k: v.get("sha256") for k, v in official_sdk.items()} != pins["official_sdk_source_sha256"]:
        raise ValueError("Official Linux CLI SDK source differs from pinned official archive")
    recorded_sdk = args.recorded_sdk.resolve()
    recorded = tree_hashes(recorded_sdk)
    if {k: v.get("sha256") for k, v in recorded.items()} != pins["recorded_sdk_source_sha256"] or len(recorded) != 53:
        raise ValueError("Recorded SDK does not contain exactly the frozen 53 files")
    if any("symlink" in row for row in recorded.values()):
        raise ValueError("Recorded SDK source may not contain links")
    differing = [n for n in recorded if recorded[n]["sha256"] != official_sdk[n]["sha256"]]
    if differing != ["scripts/install.sh"]:
        raise ValueError("Unexpected recorded versus official SDK difference")
    official_install = (sdk_source / "scripts/install.sh").read_bytes()
    if (recorded_sdk / "scripts/install.sh").read_bytes() != official_install.replace(b"version=v1.43\n", b"version=v1.52\n"):
        raise ValueError("Recorded installer is not the already documented single-line difference")
    # Copy frozen bytes; never synthesize a patch or installation marker here.
    sdk = output / "sdk"
    shutil.copytree(recorded_sdk, sdk)
    check_sdk_executable_modes(sdk, evidence, "copied")
    sdk_before = tree_hashes(sdk)
    write_json(evidence / "official-sdk-source.json", official_sdk)
    write_json(evidence / "sdk-source-before.json", sdk_before)
    if (sdk / "dependencies").exists():
        raise ValueError("Installer dependencies and markers must initially be absent")
    rustup_init = attempt.download("rustup-init", RUSTUP_URL, RUSTUP_SHA)
    rustup_init.chmod(0o755)
    attempt.download("channel-rust-1.94.0.toml", HOST_CHANNEL_URL, HOST_CHANNEL_SHA)
    cargo_home, rustup_home, target, fetch_target = (output / n for n in ["cargo-home", "rustup-home", "target", "fetch-target"])
    for path in [cargo_home, rustup_home, target, fetch_target, output / "tmp", output / "artifacts"]:
        path.mkdir()
    env = {"HOME": os.environ["HOME"], "PATH": SYSTEM_PATH,
           "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TMPDIR": str(output / "tmp"),
           "CARGO_HOME": str(cargo_home), "RUSTUP_HOME": str(rustup_home),
           "CARGO_TARGET_DIR": str(fetch_target)}
    attempt.run("rustup-host-install", [str(rustup_init), "-y", "--no-modify-path", "--profile", "minimal", "--default-toolchain", "1.94.0"], source, env)
    env["PATH"] = str(cargo_home / "bin") + ":" + str(cli_bin) + ":" + SYSTEM_PATH
    write_json(evidence / "preparation-environment.json", env)
    for name, command in [("rustup-version", ["rustup", "--version"]),
                          ("host-cargo-version", ["cargo", "--version"]),
                          ("host-rustc-version", ["rustc", "--version", "--verbose"]),
                          ("cli-version", [str(cli), "--version"]),
                          ("sbf-rustc-version", [str(tools_dir / "rust/bin/rustc"), "--version", "--verbose"]),
                          ("sbf-cargo-version", [str(tools_dir / "rust/bin/cargo"), "--version"]),
                          ("strip-objcopy-version", [str(strip_tools / "llvm/bin/llvm-objcopy"), "--version"]),
                          ("system-cc-version", ["cc", "--version"]),
                          ("system-ld-version", ["ld", "--version"]),
                          ("system-libc-version", ["ldd", "--version"]),
                          ("system-packages", ["dpkg-query", "-W"])]:
        attempt.run(name, command, source, env)
    if "cargo 1.94.0 " not in (evidence / "logs/host-cargo-version.log").read_text():
        raise ValueError("Host Cargo is not frozen 1.94.0")
    if "rustup 1.29.0 " not in (evidence / "logs/rustup-version.log").read_text():
        raise ValueError("Host rustup is not frozen 1.29.0")
    if "solana-cargo-build-sbf 2.1.21" not in (evidence / "logs/cli-version.log").read_text():
        raise ValueError("CLI is not 2.1.21")
    write_json(evidence / "host-toolchain-files.json", tree_hashes(rustup_home))
    write_json(evidence / "cargo-launchers.json", tree_hashes(cargo_home / "bin"))
    manifest = source / "programs/pump-fees/Cargo.toml"
    # Fetch does not compile. Resolve the unchanged lock with the same host Cargo used
    # by cargo-build-sbf's metadata stage; the target build later selects +solana.
    attempt.run("public-locked-fetch", ["cargo", "fetch", "--manifest-path", str(manifest), "--locked"], source, env)
    prepare_registry_views(cargo_home, source, evidence)
    before_deps = dependency_inventory(cargo_home, source, evidence, "before")
    before_source = prepare_compile_inputs(source, expected, fetch_target, target, evidence, env)
    command = ["cargo", "build-sbf", "--manifest-path", str(manifest), "--tools-version", "v1.44", "--offline",
               "--sbf-sdk", str(sdk), "--sbf-out-dir", str(output / "artifacts"), "--", "--locked", "--offline"]
    before_phase = capture_tool_phase(evidence, "before-build", sdk, rustup_home, tools_dir, strip_tools, criterion, tracer)
    if before_phase["sdk_platform"]["exists"] or before_phase["sdk_criterion"]["exists"] or before_phase["sdk_dependencies"]:
        raise ValueError("Build must start with an empty SDK dependencies state")
    # Observe successful executable paths and link changes without changing
    # the compiler command, SDK scripts, flags or source bytes. Keep one file
    # per traced process so interleaved syscall lines remain reviewable.
    trace_prefix = evidence / "logs/build-process"
    observed_command = [str(tracer), "-ff", "-ttt", "-s", "4096", "-y", "-o", str(trace_prefix),
                        "-e", TRACE_FILTER, "--", *command]
    attempt.state.update(status="building", build_attempts=1,
                         source_before_sha256=before_source,
                         target_empty_before_build=True,
                         cli_default_note="Unchanged CLI 2.1.21 internally uses -Zremap-cwd-prefix= with an empty replacement. No additional compiler remapping or flags are passed.",
                         recorded_pipeline={"compile": "v1.44", "postprocess": "v1.52", "criterion": "v2.3.3"})
    attempt.save()
    attempt.state["unwrapped_build_command"] = command
    attempt.state["process_trace_scope"] = "Observer only; review actual exec and symlink transitions; no compiler argument edits"
    attempt.save()
    code = attempt.run("build", observed_command, source, env, check=False)
    after_phase = capture_tool_phase(evidence, "after-build", sdk, rustup_home, tools_dir, strip_tools, criterion, tracer)
    write_json(evidence / "platform-files-after.json", tree_hashes(tools_dir))
    write_json(evidence / "strip-platform-files-after.json", tree_hashes(strip_tools))
    write_json(evidence / "criterion-payload-after.json", tree_hashes(criterion))
    trace_files = sorted(p for p in (evidence / "logs").glob("build-process.*") if p.suffix[1:].isdigit())
    trace_index = [{"path": str(f.relative_to(evidence)), "bytes": f.stat().st_size, "sha256": digest(f)} for f in trace_files]
    write_json(evidence / "process-trace-index.json", {"files": trace_index, "requires_phase_review": True,
              "trace_selector": TRACE_FILTER, "observer_preflight": "tracer-preflight.json",
              "claim": "Retained executable and symlink syscalls; no automatic historical-toolchain claim"})
    if not trace_files:
        raise ValueError("No actual build process trace was retained")
    for key in ["compiler_rustc", "stripper_objcopy", "tracer", "criterion_payload"]:
        if before_phase[key] != after_phase[key]:
            raise ValueError("Tool bytes changed across build: " + key)
    after_source = source_hashes(source, expected)
    write_json(evidence / "source-after.json", after_source)
    candidate = output / "artifacts/pump_fees_candidate.so"
    if candidate.is_symlink():
        raise ValueError("Candidate must be a regular emitted file, not a symlink")
    if after_source != expected:
        raise ValueError("Compiler changed a frozen source input")
    after_deps = dependency_inventory(cargo_home, source, evidence, "after")
    if after_deps != before_deps:
        raise ValueError("Dependency source/archive bytes changed during build")
    if tree_hashes(tools_dir) != json.loads((evidence / "platform-files.json").read_text()):
        raise ValueError("Platform tool distribution changed during build")
    sdk_after = tree_hashes(sdk)
    write_json(evidence / "sdk-source-after.json", sdk_after)
    if {k: v for k, v in sdk_after.items() if not k.startswith("dependencies/")} != sdk_before:
        raise ValueError("SDK source changed during build")
    if code:
        raise RuntimeError(f"Single compiler attempt failed ({code}); no fallback/variant/retry is authorized")
    if not candidate.is_file():
        raise ValueError("Compiler returned zero without expected candidate")
    write_json(evidence / "rustup-after-build.json", tree_hashes(rustup_home))
    if tree_hashes(strip_tools) != json.loads((evidence / "strip-platform-files.json").read_text()):
        raise ValueError("Stripper platform distribution changed during build")
    if tree_hashes(criterion) != criterion_before:
        raise ValueError("Criterion cache payload changed during build")
    if (sdk / "dependencies/platform-tools").resolve() != strip_tools:
        raise ValueError("Recorded installer did not finish with verified v1.52 tools")
    if (sdk / "dependencies/criterion").resolve() != criterion:
        raise ValueError("Recorded installer did not legitimately link verified Criterion")
    if (rustup_home / "toolchains/solana").resolve() != strip_tools / "rust":
        raise ValueError("Final solana alias does not select the recorded v1.52 post-processing family")
    for name in ["platform-tools-v1.52.md", "criterion-v2.3.3.md"]:
        marker = sdk / "dependencies" / name
        if not marker.is_file() or marker.read_bytes() != b"":
            raise ValueError("Installer completion marker missing or unexpected: " + name)
    compare_strip_sections(target / "sbf-solana-solana/release/pump_fees_candidate.so", candidate, evidence)
    attempt.state.update(status="comparing", compiler_success=True)
    attempt.save()
    result = compare_after_build(repository, candidate, evidence)
    attempt.state.update(status="completed", comparison=result,
                         historical_toolchain_proven=False, runtime_tests_performed=0)
    attempt.save()
    print(json.dumps({"compiler_success": True, **result}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recorded-sdk", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("Use a new output directory; prior attempts may not be overwritten")
    output.mkdir(parents=True)
    attempt = Attempt(output)
    failed = False
    try:
        build(args, attempt)
    except BaseException as error:
        failed = True
        attempt.state.update(status="failed", error_type=type(error).__name__, error=str(error))
        (attempt.evidence / "exception.txt").write_text(traceback.format_exc())
        attempt.save()
        print(str(error), file=sys.stderr)
    finally:
        try:
            retain_generated_outputs(attempt)
        except BaseException as error:
            failed = True
            attempt.state.update(status="failed", retention_error_type=type(error).__name__, retention_error=str(error))
            (attempt.evidence / "retention-exception.txt").write_text(traceback.format_exc())
        attempt.state["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        seal_evidence(attempt)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
