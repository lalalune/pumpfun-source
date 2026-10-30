"""Isolated, hash-bound target-library profiles for the verified main builder."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from pump_dependency_cache import clone_file, digest, sha

HERE = Path(__file__).resolve().parent
TARGET_LIB = Path("rust/lib/rustlib/sbf-solana-solana/lib")
PROFILE_TARGETS = {"linux-v1.44-sbf": "sbf-solana-solana", "linux-v1.44-sbpf": "sbpf-solana-solana"}


def specification(name):
    assert name in PROFILE_TARGETS, "unknown target-library profile"
    suffix = "sbpf" if name == "linux-v1.44-sbpf" else "sbf"
    path = HERE / ("pump_linux_v144_" + suffix + "_libraries.json")
    spec = json.loads(path.read_text())
    assert spec["name"] == name and spec["target"] == PROFILE_TARGETS[name]
    return path, spec


def target_library_path(target):
    assert target in PROFILE_TARGETS.values(), "unsupported target triple"
    return Path("rust/lib/rustlib") / target / "lib"


def inventory(root):
    root = root.resolve()
    result = {}
    for path in sorted(root.rglob("*")):
        name = str(path.relative_to(root))
        if path.is_symlink():
            assert path.resolve().is_relative_to(root), "SDK symlink resolves outside the copied tree"
            result[name] = {"symlink": os.readlink(path)}
        elif path.is_file():
            result[name] = {"sha256": sha(path), "mode": path.stat().st_mode & 0o777}
    return result


def validate_libraries(directory, expected, empty_directories=("self-contained",)):
    assert directory.is_dir() and not directory.is_symlink(), "library directory must be an ordinary directory"
    entries = list(directory.iterdir())
    assert not any(path.is_symlink() for path in entries), "library symlinks/subdirectories are not admitted"
    directories = [path for path in entries if path.is_dir()]
    assert {path.name for path in directories} == set(empty_directories) and all(not list(path.iterdir()) for path in directories), "unadmitted or nonempty target-library directory"
    assert all(path.is_file() or path in directories for path in entries), "non-file target-library input"
    actual = {path.name: sha(path) for path in entries if path.is_file()}
    assert actual == expected, "target-library set or hashes differ from the admitted profile"
    return actual


def prepare(name, native_sdk, libraries, output):
    spec_path, spec = specification(name)
    target_lib = target_library_path(spec["target"])
    libraries = Path(libraries).resolve()
    native_sdk = Path(native_sdk).resolve()
    output = Path(output).resolve()
    assert not output.exists() and not output.is_relative_to(native_sdk), "profile SDK must be a fresh isolated directory"
    actual = validate_libraries(libraries, spec["target_libraries"], spec["empty_directories"])
    for tool, expected in spec["native_tools"].items():
        assert sha(native_sdk / tool) == expected, "native compiler/Cargo differs from the admitted v1.44 tools"
    before = inventory(native_sdk)
    methods = Counter()

    def copy(source, target):
        methods[clone_file(Path(source), Path(target))] += 1
        return target

    shutil.copytree(native_sdk, output, copy_function=copy, symlinks=True)
    assert not (output / target_lib).is_symlink()
    shutil.rmtree(output / target_lib)
    shutil.copytree(libraries, output / target_lib, copy_function=copy)
    after = inventory(output)
    changed = [path for path in sorted(before.keys() | after.keys()) if before.get(path) != after.get(path)]
    assert changed and all(path.startswith(str(target_lib) + "/") for path in changed), "profile changed a host/compiler file"
    assert validate_libraries(output / target_lib, spec["target_libraries"]) == actual
    identity = {"name": name, "target": spec["target"], "profile_spec_sha256": sha(spec_path),
                "native_sdk_manifest_sha256": digest(before), "prepared_sdk_manifest_sha256": digest(after),
                "target_libraries": actual, "empty_directories": spec["empty_directories"]}
    record = {"scope": spec["scope"], "name": name, "native_sdk": str(native_sdk),
              "prepared_sdk": str(output), "library_source": str(libraries),
              "profile_spec": str(spec_path), "profile_spec_sha256": sha(spec_path),
              "implementation": str(Path(__file__)), "implementation_sha256": sha(Path(__file__)),
              "cache_context": identity, "changed_paths": changed,
              "file_manifest": str(output.parent / "target-library-profile-files.json"),
              "copy_methods": dict(methods), "native_host_files_unchanged": True}
    return output, finish(record)


def finish(record):
    target = record["cache_context"]["target"]
    target_lib = target_library_path(target)
    assert sha(record["profile_spec"]) == record["profile_spec_sha256"]
    assert sha(record["implementation"]) == record["implementation_sha256"]
    native, prepared = Path(record["native_sdk"]), Path(record["prepared_sdk"])
    native_files, prepared_files = inventory(native), inventory(prepared)
    assert digest(native_files) == record["cache_context"]["native_sdk_manifest_sha256"]
    assert digest(prepared_files) == record["cache_context"]["prepared_sdk_manifest_sha256"]
    validate_libraries(Path(record["library_source"]), record["cache_context"]["target_libraries"])
    queries = []
    for args in [["--print", "sysroot"], ["--print", "target-libdir", "--target", target]]:
        command = [str(prepared / "rust/bin/rustc"), *args]
        output = subprocess.check_output(command, text=True).strip()
        queries.append({"command": command, "stdout": output})
    assert queries[0]["stdout"] == str(prepared / "rust")
    assert queries[1]["stdout"] == str(prepared / target_lib)
    contents = {"native": native_files, "prepared": prepared_files}
    manifest = Path(record["file_manifest"])
    if "file_manifest_sha256" in record:
        assert sha(manifest) == record["file_manifest_sha256"]
        assert json.loads(manifest.read_text()) == contents, "profile manifest content changed"
    else:
        assert not manifest.exists(), "profile manifest already exists"
        temporary = manifest.with_name(manifest.name + ".tmp")
        try:
            temporary.write_text(json.dumps(contents, indent=2) + "\n")
            assert json.loads(temporary.read_text()) == contents
            os.replace(temporary, manifest)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        record = dict(record, file_manifest_sha256=sha(manifest))
    return dict(record, status="verified", compiler_queries=queries)
