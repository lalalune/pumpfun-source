#!/usr/bin/env python3
"""Build the maintained Mayhem exact recipe twice on native x86_64 Linux.

The program sources, historical proc-macro sources, metadata/path maps, and linker
scripts are always taken from a freshly verified ``build_exact.py --stage-only``
snapshot.  The captured program is comparison data only and is never a compiler
input.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import resource
import shutil
import subprocess
import tarfile
import time


HERE = Path(__file__).resolve().parent
PLATFORM_ARCHIVE_SHA256 = "fcc41631c7f77561bf5412218bf297501dccf0305ea280f338f0ace2aab9f31e"
OFFICIAL_TOOLS = {
    "rust/bin/rustc": "fa2c61467ffa823dc1a64c28cba22c6ce24b2439ebe28fe546609d7fc638569a",
    "rust/bin/cargo": "638ab45125934a94e94980d5ae6aa3641257914f0882fcbf116d643fa7ec405b",
    "rust/bin/rustdoc": "5c88201be47010946fd363bd97dc79ff8698a15102e32f91256f0a565227ec09",
    "llvm/bin/clang": "cad3fd5da01c3db8ffb102f5ae405f477be78201a137e18c50d88ec3360355a3",
    "llvm/bin/llvm-ar": "baa43b60f27718df405ed3a12038a9a8a0945d1f79d3d59b0ad7627cc34e54ac",
    "llvm/bin/llvm-objcopy": "c69ce74d2c5068cb52675aabca60d981a26ddac173518cbc0cd893461db48a48",
    "llvm/bin/lld": "835a58c95dec82de9b415f1f2e46fce2f2ddd3ffa80a11c8e56e2915f5232267",
}
EXPECTED = {
    "symbols.so": "7b15bb1e5c7c9c53041322fa64d4a420906fffd96ff97a55d70d627bcb854960",
    "candidate.so": "9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d",
}
CAPTURE_SHA256 = "a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb"
PROGRAMDATA_SHA256 = "a556c21bbf54f1da76ada6bd6b809a8315e45a1af43f13ac7e2839dd5312cfa2"
MEANINGFUL_ELF_BYTES = 775416
ALLOCATION_TAIL_BYTES = 1992
VENDOR_CLOSURE_SHA256 = "c679e8263e597ef94ff3b0a518a6c56a5909188acee6693ccd554248d5746097"
PUBLISHED_BINDINGS_SHA256 = "2c77f22c3f464cbecc0124845baec601412adbeb283aabb32e305b27b716b038"
BUILD_JOBS = "6"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": sha256(path)}


def load(path: Path):
    data = path.read_bytes()
    if path.suffix == ".gz":
        data = gzip.decompress(data)
    return json.loads(data)


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def safe(name: str) -> str:
    path = PurePosixPath(name)
    require(
        bool(name)
        and not path.is_absolute()
        and ".." not in path.parts
        and ":" not in name
        and "\\" not in name
        and path.as_posix() == name,
        f"unsafe relative path: {name!r}",
    )
    return name


def snapshot(root: Path) -> dict[str, dict[str, object]]:
    return {
        path.relative_to(root).as_posix(): identity(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def extract_regular_files(data: bytes) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
        for member in archive:
            if member.isdir():
                continue
            require(member.isfile(), f"nonregular retained archive member: {member.name}")
            name = safe(member.name)
            require(name not in result, f"duplicate retained archive member: {name}")
            extracted = archive.extractfile(member)
            require(extracted is not None, f"unreadable retained archive member: {name}")
            result[name] = extracted.read()
    return result


def run_logged(command: list[str], *, cwd: Path, env: dict[str, str], prefix: Path) -> int:
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    with prefix.with_suffix(".stdout.log").open("wb") as stdout, prefix.with_suffix(
        ".stderr.log"
    ).open("wb") as stderr:
        returncode = subprocess.run(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr).returncode
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    save(
        prefix.with_suffix(".process.json"),
        {
            "command": command,
            "cwd": str(cwd),
            "returncode": returncode,
            "elapsed_seconds": time.monotonic() - started,
            "child_user_cpu_seconds": after.ru_utime - before.ru_utime,
            "child_system_cpu_seconds": after.ru_stime - before.ru_stime,
            "child_max_rss_kib_cumulative": after.ru_maxrss,
            "child_involuntary_context_switches": after.ru_nivcsw - before.ru_nivcsw,
        },
    )
    return returncode


def pin_files(root: Path, rows: list[dict[str, object]]) -> None:
    for row in rows:
        name = safe(str(row["path"]))
        path = root / name
        require(path.is_file() and not path.is_symlink(), f"nonregular pinned file: {name}")
        require(path.stat().st_size == row["bytes"], f"pinned file size differs: {name}")
        require(sha256(path) == row["sha256"], f"pinned file digest differs: {name}")


def pin_snapshot(root: Path, expected: dict[str, dict[str, object]], label: str) -> None:
    require(snapshot(root) == expected, f"{label} changed during build")


def pin_canonical_sources(repo: Path, expected: dict[str, str]) -> None:
    source = repo / "programs/mayhem"
    actual = {name: sha256(source / safe(name)) for name in expected}
    require(actual == expected, "canonical Mayhem source changed during build")


def verify_capture(repo: Path, candidate: Path) -> dict[str, object]:
    capture = repo / "evidence/original/mayhem/deployed.so"
    programdata = repo / "evidence/original/mayhem/programdata-account.bin"
    require(identity(capture) == {"bytes": 777408, "sha256": CAPTURE_SHA256}, "captured allocation differs")
    require(
        identity(programdata) == {"bytes": 777453, "sha256": PROGRAMDATA_SHA256},
        "captured ProgramData differs",
    )
    payload = capture.read_bytes()
    require(programdata.read_bytes()[45:] == payload, "ProgramData payload binding differs")
    require(
        len(payload) == MEANINGFUL_ELF_BYTES + ALLOCATION_TAIL_BYTES
        and payload[MEANINGFUL_ELF_BYTES:] == bytes(ALLOCATION_TAIL_BYTES),
        "captured allocation tail differs",
    )
    built = candidate.read_bytes()
    require(
        len(built) == MEANINGFUL_ELF_BYTES and built == payload[:MEANINGFUL_ELF_BYTES],
        "native Linux meaningful ELF differs from capture",
    )
    return {
        "programdata_header_bytes": 45,
        "programdata": identity(programdata),
        "captured_allocation": identity(capture),
        "meaningful_elf_bytes": MEANINGFUL_ELF_BYTES,
        "meaningful_elf_sha256": sha256(candidate),
        "excluded_zero_allocation_tail_bytes": ALLOCATION_TAIL_BYTES,
    }


def inspect_vendor(vendor: Path, controller: Path) -> dict[str, object]:
    """Validate package archives and source bytes, not host newline serialization."""
    records = load(controller / "vendor-inputs.json")["packages"]
    require(
        {path.name for path in vendor.iterdir()} == {record["directory"] for record in records},
        "vendor package set differs",
    )
    closure = []
    for record in records:
        directory = vendor / safe(record["directory"])
        checksum = directory / ".cargo-checksum.json"
        require(checksum.is_file() and not checksum.is_symlink(), f"missing vendor map: {directory.name}")
        data = load(checksum)
        require(data["package"] == record["package_sha256"], f"package digest differs: {directory.name}")
        require(len(data["files"]) == record["file_count"], f"file count differs: {directory.name}")
        actual = {
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*")
            if path.is_file() and path.name != ".cargo-checksum.json"
        }
        require(actual == set(data["files"]), f"vendor file set differs: {directory.name}")
        for name, digest in data["files"].items():
            path = directory / safe(name)
            require(not path.is_symlink() and sha256(path) == digest, f"vendor byte differs: {directory.name}/{name}")
        closure.append(
            {"directory": record["directory"], "package_sha256": data["package"], "files": data["files"]}
        )
    encoded = json.dumps(closure, sort_keys=True, separators=(",", ":")).encode()
    return {"packages": len(records), "closure_sha256": hashlib.sha256(encoded).hexdigest()}


def check_vendor(vendor: Path, controller: Path, expected: str = VENDOR_CLOSURE_SHA256) -> dict[str, object]:
    result = inspect_vendor(vendor, controller)
    require(result["closure_sha256"] == expected, "complete vendor source closure differs")
    return result


def unpack_sdk(archive: Path, destination: Path) -> None:
    require(sha256(archive) == PLATFORM_ARCHIVE_SHA256, "official platform-tools archive digest differs")
    destination.mkdir()
    with tarfile.open(archive, mode="r:bz2") as tar:
        tar.extractall(destination, filter="data")


def linux_environment(sdk: Path, cargo_home: Path, target: Path) -> dict[str, str]:
    system_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    return {
        "HOME": str(cargo_home.parent / "home"),
        "PATH": f"{sdk / 'rust/bin'}:{sdk / 'llvm/bin'}:{system_path}",
        "RUSTC": str(sdk / "rust/bin/rustc"),
        "RUSTDOC": str(sdk / "rust/bin/rustdoc"),
        "CARGO_HOME": str(cargo_home),
        "CARGO_TARGET_DIR": str(target),
        "CARGO_NET_OFFLINE": "true",
        "CC": str(sdk / "llvm/bin/clang"),
        "AR": str(sdk / "llvm/bin/llvm-ar"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "SOURCE_DATE_EPOCH": "0",
    }


def configure_cargo(home: Path, vendor: Path) -> None:
    home.mkdir()
    (home / "config.toml").write_text(
        '[source.crates-io]\nreplace-with = "locked-vendor"\n'
        '[source.locked-vendor]\ndirectory = '
        + json.dumps(str(vendor))
        + "\n[net]\noffline = true\n",
        encoding="utf-8",
    )


def build_historical_macro(recipe: Path, sdk: Path, vendor: Path, output: Path) -> dict[str, object]:
    output.mkdir()
    inputs = recipe / "host-inputs"
    pins = load(inputs / "inputs.json")
    expected_snapshot = dict(pins)
    expected_snapshot["inputs.json"] = identity(inputs / "inputs.json")
    require(snapshot(inputs) == expected_snapshot, "retained historical macro inputs differ")

    source_files = extract_regular_files((inputs / "historical-source.tar.gz").read_bytes())
    tree = load(inputs / "source-tree.json")
    require(tree["revision"] == "c0077c2a7de64361f451735ac89118bc89f1c277", "historical revision differs")
    require(len(source_files) == 121, "historical source count differs")
    for row in tree["files"]:
        data = source_files[row["path"]]
        git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        require(len(data) == row["size"] and git_blob == row["sha"], "historical source blob differs")

    original = source_files["Cargo.toml"]
    adapted, substitutions = re.subn(
        rb"members = \[.*?\]",
        b'members = ["lang/attribute/program", "lang/syn", "idl", "idl/spec"]',
        original,
        count=1,
        flags=re.S,
    )
    require(substitutions == 1 and adapted != original, "historical workspace adaptation failed")
    adapted += b"\n[patch.crates-io]\n"

    packages = load(inputs / "supplement-packages.json")
    receipts = {row["name"]: row for row in load(inputs / "supplement-receipts.json")}
    supplement_inputs: dict[str, dict[str, object]] = {}
    for row in packages:
        package_name = f"{row['name']}-{row['version']}"
        archive = inputs / "archives" / f"{package_name}.crate"
        require(sha256(archive) == row["checksum"] == receipts[package_name]["archive_sha256"], "supplement archive differs")
        files = extract_regular_files(archive.read_bytes())
        prefix = package_name + "/"
        files = {name[len(prefix) :]: data for name, data in files.items() if name.startswith(prefix)}
        observed = {
            name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in files.items()
        }
        require(observed == receipts[package_name]["files"], "supplement source inventory differs")
        for name, data in files.items():
            path = output / "supplements" / package_name / safe(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            supplement_inputs[path.relative_to(output).as_posix()] = identity(path)
        adapted += f'{row["name"]} = {{ path = "../supplements/{package_name}" }}\n'.encode()

    source_files["Cargo.toml"] = adapted
    source_files["Cargo.lock"] = (inputs / "resolved-Cargo.lock").read_bytes()
    source = output / "source"
    for name, data in source_files.items():
        path = source / safe(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    initial = snapshot(source)

    cargo_home = output / "cargo-home"
    configure_cargo(cargo_home, vendor)
    target = output / "target"
    env = linux_environment(sdk, cargo_home, target)
    command = [
        str(sdk / "rust/bin/cargo"),
        "build",
        "--locked",
        "--offline",
        "--manifest-path",
        str(source / "Cargo.toml"),
        "--release",
        "-p",
        "anchor-attribute-program",
        "--jobs",
        BUILD_JOBS,
        "--verbose",
    ]
    save(
        output / "launch.json",
        {
            "command": command,
            "cwd": str(source),
            "environment": env,
            "source_inputs": initial,
            "supplement_inputs": supplement_inputs,
            "target_directory_initially_absent": True,
        },
    )
    code = run_logged(command, cwd=source, env=env, prefix=output / "compiler")
    require(code == 0, "historical proc-macro build failed")
    require(snapshot(source) == initial, "historical proc-macro source changed during build")
    macro = target / "release/libanchor_attribute_program.so"
    require(macro.is_file(), "historical proc-macro output missing")
    deps = {
        path.relative_to(target / "release").as_posix(): sha256(path)
        for path in sorted((target / "release/deps").iterdir())
        if path.suffix in {".so", ".rlib", ".rmeta"}
    }
    binding = {
        "macro": {"path": str(macro), "sha256": sha256(macro)},
        "host_dependencies": deps,
    }
    save(output / "macro-binding.json", binding)
    return binding


def compile_controller(source: Path, destination: Path, sdk: Path, env: dict[str, str], crate: str) -> dict[str, object]:
    command = [
        str(sdk / "rust/bin/rustc"),
        "--crate-name",
        crate,
        "--edition=2021",
        "-C",
        "opt-level=2",
        str(source),
        "-o",
        str(destination),
    ]
    code = run_logged(command, cwd=source.parent, env=env, prefix=destination.parent / f"{crate}-compile")
    require(code == 0 and destination.is_file(), f"{crate} compilation failed")
    return {"command": command, "source_sha256": sha256(source), "output": identity(destination)}


def derive_linux_metadata_map(records: Path, output: Path) -> dict[str, object]:
    bindings_path = HERE / "published-metadata-bindings.json"
    require(sha256(bindings_path) == PUBLISHED_BINDINGS_SHA256, "published metadata bindings differ")
    evidence = load(bindings_path)
    require(evidence["schema"] == 1, "published metadata binding schema differs")
    require(
        evidence["selected_windows_build_zip_sha256"]
        == "eb93ee0f5208c5d51aa359c765b13cc71e11da5908dfc196182e096aa5a0ebfc",
        "selected Windows evidence binding differs",
    )
    require(evidence["selected_windows_wrapper_records"] == 176, "selected Windows wrapper count differs")
    bindings = {
        (row["crate"], row["source"]): row
        for row in evidence["target_compile_bindings"]
    }
    require(len(bindings) == 85, "published metadata binding count differs")
    registry = {source.split("/", 1)[1] for _, source in bindings if source.startswith("registry/")}

    observed = {}
    for path in sorted(records.glob("*.json")):
        record = load(path)
        arguments = record["before"]
        if "--target" not in arguments or "--crate-name" not in arguments:
            continue
        if arguments[arguments.index("--target") + 1] != "sbpf-solana-solana":
            continue
        metadata = [value.split("=", 1)[1] for value in arguments if value.startswith("metadata=")]
        if len(metadata) != 1:
            continue
        crate = arguments[arguments.index("--crate-name") + 1]
        source_arguments = [value for value in arguments if value.endswith(".rs") and not value.startswith("-")]
        require(len(source_arguments) == 1, f"ambiguous source locator for {crate}")
        source_path = source_arguments[0].replace("\\", "/")
        parts = PurePosixPath(source_path).parts
        package = next((part for part in parts if part in registry), None)
        if package is not None:
            source_key = "registry/" + package
        elif "curve-accounts" in parts:
            source_key = "local/curve-accounts"
        elif "vendor" in parts and "anchor-lang" in parts:
            source_key = "local/anchor-lang"
        else:
            source_key = "local/mayhem"
        key = (crate, source_key)
        require(key in bindings, f"unbound Linux target compile: {crate} from {source_key}")
        require(key not in observed, f"duplicate Linux target compile binding: {crate} from {source_key}")
        observed[key] = metadata[0]

    require(set(observed) == set(bindings), "Linux target compile set differs from selected Windows build")
    rows = sorted(
        (linux, bindings[key]["published_metadata"], key[0], key[1])
        for key, linux in observed.items()
    )
    require(len({(old, crate) for old, _, crate, _ in rows}) == len(rows), "ambiguous Linux Cargo metadata")
    output.write_text(
        "".join(f"{old}\t{published}\t{crate}\n" for old, published, crate, _ in rows),
        encoding="utf-8",
    )
    receipt = {
        "bindings_sha256": sha256(bindings_path),
        "probe_wrapper_records": len(list(records.glob("*.json"))),
        "target_compile_bindings": len(rows),
        "linux_metadata_map": identity(output),
        "bindings": [
            {"crate": crate, "source": source, "linux_cargo_metadata": old, "published_metadata": published}
            for old, published, crate, source in rows
        ],
    }
    save(output.with_suffix(".json"), receipt)
    return receipt


def build_target(
    recipe: Path,
    sdk: Path,
    vendor: Path,
    historical: dict[str, object],
    output: Path,
    *,
    metadata_mode: str,
    metadata_map: Path,
) -> dict[str, object]:
    output.mkdir()
    controller = recipe / "controller"
    source = output / "source/programs/mayhem"
    source.mkdir(parents=True)
    rows = load(controller / "source-inputs.json")["source_files"]
    declared = {}
    for row in rows:
        name = safe(row["path"])
        data = gzip.decompress((controller / "sources" / f"{name}.gz").read_bytes())
        require(len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"], f"staged source differs: {name}")
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        declared[name] = {"bytes": row["bytes"], "sha256": row["sha256"]}
    initial = snapshot(source)
    require(initial == declared, "staged current Mayhem sources differ")

    cargo_home = output / "cargo-home"
    configure_cargo(cargo_home, vendor)
    target = output / "target"
    env = linux_environment(sdk, cargo_home, target)
    env["CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS"] = f"-Zremap-cwd-prefix= --sysroot={sdk / 'rust'}"
    env["CC_sbpf_solana_solana"] = str(sdk / "llvm/bin/clang")
    env["AR_sbpf_solana_solana"] = str(sdk / "llvm/bin/llvm-ar")

    records = output / "wrapper-records"
    records.mkdir()
    wrapper = output / "metadata-relative-wrapper"
    linker = output / "qualified-linker-wrapper"
    wrapper_build = compile_controller(controller / "wrapper.rs", wrapper, sdk, env, "metadata_relative_wrapper")
    linker_build = compile_controller(controller / "linker.rs", linker, sdk, env, "qualified_linker_wrapper")
    link_records = output / "link"
    env.update(
        {
            "RUSTC_WRAPPER": str(wrapper),
            "MAYHEM_METADATA_MODE": metadata_mode,
            "MAYHEM_PATH_MAP": str(controller / "path-map.tsv"),
            "MAYHEM_METADATA_MAP": str(metadata_map),
            "MAYHEM_WRAPPER_RECORDS": str(records),
            "MAYHEM_LINKER_REAL": str(sdk / "llvm/bin/lld"),
            "MAYHEM_LINKER_DEFAULT": str(controller / "default.ld"),
            "MAYHEM_LINKER_SCRIPT": str(controller / "ordered-native.ld"),
            "MAYHEM_LINKER_OUTPUT": str(link_records),
            "MAYHEM_HISTORICAL_MACRO": str(historical["macro"]["path"]),
            "MAYHEM_HISTORICAL_DEPS": str(Path(historical["macro"]["path"]).parent / "deps"),
        }
    )
    command = [
        str(sdk / "rust/bin/cargo"),
        "rustc",
        "--manifest-path",
        str(source / "Cargo.toml"),
        "--release",
        "--target",
        "sbpf-solana-solana",
        "--locked",
        "--offline",
        "--jobs",
        BUILD_JOBS,
        "--verbose",
        "--",
        "--remap-path-prefix=src/=programs/mayhem-program/src/",
        "--remap-path-prefix=src/account_wrapper.rs=src/account_wrapper.rs",
        "-C",
        f"linker={linker}",
    ]
    save(
        output / "launch.json",
        {
            "command": command,
            "cwd": str(source.parents[1]),
            "environment_overrides": {key: env[key] for key in sorted(env) if key.startswith(("CARGO_", "MAYHEM_", "RUST"))},
            "source_inputs": initial,
            "metadata_mode": metadata_mode,
            "metadata_map": identity(metadata_map),
            "wrapper_build": wrapper_build,
            "linker_build": linker_build,
        },
    )
    started = time.monotonic()
    code = run_logged(command, cwd=source.parents[1], env=env, prefix=output / "compiler")
    elapsed = time.monotonic() - started
    require(code == 0, "target compiler build failed")
    require(snapshot(source) == initial, "current Mayhem source changed during build")
    symbols = output / "symbols.so"
    shutil.copyfile(target / "sbpf-solana-solana/release/mayhem_recovered.so", symbols)
    candidate = output / "candidate.so"
    strip_command = [str(sdk / "llvm/bin/llvm-objcopy"), "--strip-all", str(symbols), str(candidate)]
    strip_code = run_logged(strip_command, cwd=output, env=env, prefix=output / "strip")
    require(strip_code == 0, "target strip failed")
    result = {
        "returncode": code,
        "elapsed_seconds": elapsed,
        "source_unchanged": True,
        "wrapper_records": len(list(records.glob("*.json"))),
        "outputs": {path.name: identity(path) for path in (symbols, candidate)},
        "selected_exact": {
            name: result["sha256"] == EXPECTED[name]
            for name, result in {path.name: identity(path) for path in (symbols, candidate)}.items()
        },
        "target_cache_retained": False,
    }
    shutil.rmtree(target)
    save(output / "result.json", result)
    return result


def qualify(args: argparse.Namespace) -> dict[str, object]:
    require(platform.system() == "Linux", "native Linux host required")
    require(platform.machine() == "x86_64", "native x86_64 Linux host required")
    repo = args.repo.resolve()
    vendor = args.vendor.resolve()
    output = args.output.resolve()
    require(not output.exists(), "output directory must be absent")
    output.mkdir(parents=True)
    started = time.monotonic()
    overall: dict[str, object] = {"status": "STARTED", "started_at": datetime.now(timezone.utc).isoformat()}
    try:
        archive = args.sdk_archive.resolve()
        require(sha256(archive) == PLATFORM_ARCHIVE_SHA256, "official platform-tools archive digest differs")
        sdk = output / "sdk"
        unpack_sdk(archive, sdk)
        for name, digest in OFFICIAL_TOOLS.items():
            require(sha256(sdk / name) == digest, f"official tool differs: {name}")

        stage = output / "stage"
        stage_command = [
            "python3",
            str(repo / "programs/mayhem/build_exact.py"),
            "--stage-only",
            "--repo",
            str(repo),
            "--output",
            str(stage),
        ]
        stage_code = run_logged(stage_command, cwd=repo, env=dict(os.environ), prefix=output / "stage")
        require(stage_code == 0, "current exact recipe staging failed")
        recipe = stage / "recipe"
        stage_mapping = load(stage / "source-mapping.json")
        recipe_snapshot = snapshot(recipe)
        require(len(recipe_snapshot) == 98, "staged recipe file count differs")
        pin_canonical_sources(repo, stage_mapping["canonical_inputs"])
        pin_files(sdk, load(recipe / "controller/target-components.json")["files"])
        vendor_identity = check_vendor(vendor, recipe / "controller")

        macro = build_historical_macro(recipe, sdk, vendor, output / "historical-macro")
        probe = build_target(
            recipe,
            sdk,
            vendor,
            macro,
            output / "metadata-probe",
            metadata_mode="passthrough",
            metadata_map=recipe / "controller/metadata-map.tsv",
        )
        linux_metadata_map = output / "linux-metadata-map.tsv"
        linux_metadata = derive_linux_metadata_map(output / "metadata-probe/wrapper-records", linux_metadata_map)
        runs = [
            build_target(
                recipe,
                sdk,
                vendor,
                macro,
                output / name,
                metadata_mode="published-with-paths-relative",
                metadata_map=linux_metadata_map,
            )
            for name in ("build-01", "build-02")
        ]
        repeat_equal = runs[0]["outputs"] == runs[1]["outputs"]
        require(repeat_equal, "independent Linux builds differ")
        require(
            all(all(exact.values()) for exact in (run["selected_exact"] for run in runs)),
            "native Linux build differs from selected exact ELF",
        )
        capture = verify_capture(repo, output / "build-01/candidate.so")
        require(sha256(archive) == PLATFORM_ARCHIVE_SHA256, "official platform-tools archive changed during build")
        require(
            sha256(HERE / "published-metadata-bindings.json") == PUBLISHED_BINDINGS_SHA256,
            "published metadata bindings changed during build",
        )
        pin_snapshot(recipe, recipe_snapshot, "staged recipe")
        pin_canonical_sources(repo, stage_mapping["canonical_inputs"])
        check_vendor(vendor, recipe / "controller")
        pin_files(sdk, load(recipe / "controller/target-components.json")["files"])
        overall.update(
            {
                "status": "SUCCEEDED",
                "platform": {"system": platform.system(), "machine": platform.machine(), "release": platform.release()},
                "sdk_archive": identity(archive),
                "sdk_origin": "fresh authenticated archive extraction",
                "official_tools": {name: identity(sdk / name) for name in OFFICIAL_TOOLS},
                "vendor": vendor_identity,
                "stage_source_mapping": identity(stage / "source-mapping.json"),
                "historical_macro": macro["macro"],
                "metadata_probe": probe,
                "linux_metadata": linux_metadata,
                "runs": runs,
                "repeat_build_equal": repeat_equal,
                "capture_comparison": capture,
                "recipe_inputs_unchanged": True,
                "canonical_sources_unchanged": True,
                "meaningful_elf_bytes": MEANINGFUL_ELF_BYTES,
                "allocation_tail_emitted": False,
            }
        )
        shutil.rmtree(sdk)
        overall["sdk_extraction_retained"] = False
    except Exception as error:
        overall.update({"status": "FAILED", "error_type": type(error).__name__, "error": str(error)})
        raise
    finally:
        overall["elapsed_seconds"] = time.monotonic() - started
        overall["finished_at"] = datetime.now(timezone.utc).isoformat()
        save(output / "result.json", overall)
    return overall


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--sdk-archive", type=Path, required=True)
    parser.add_argument("--vendor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(qualify(parser.parse_args()), indent=2))


if __name__ == "__main__":
    main()
