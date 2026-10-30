#!/usr/bin/env python3
"""Stage current Mayhem inputs into the qualified fresh-host Windows recipe.

--stage-only validates the complete source mapping without compiling. A real
build requires the exact pinned Windows toolchain and never reuses a host macro.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stage(output, repository):
    qualified = repository / "research/mayhem-fresh-host-20261028"
    records = json.loads((qualified / "controller/source-inputs.json").read_text())["source_files"]
    expected = {row["path"]:row["sha256"] for row in records}
    actual = {}
    for path in HERE.rglob("*"):
        rel = path.relative_to(HERE)
        if {"target", ".git", "__pycache__"}.intersection(rel.parts):
            continue
        require(not path.is_symlink() and (path.is_file() or path.is_dir()), "special canonical input")
        if path.is_file() and str(rel) not in ("build_exact.py", "README.md"):
            actual[rel.as_posix()] = digest(path.read_bytes())
    require(actual == expected and len(actual) == 67, "current Mayhem inputs differ from qualified67-source recipe")
    output.mkdir(parents=True, exist_ok=False)
    recipe = output / "recipe"
    recipe.mkdir()
    for name in ("build.py", "host_build.py"):
        shutil.copy2(qualified / name, recipe / name)
    for name in ("controller", "host-inputs"):
        shutil.copytree(qualified / name, recipe / name)
    mapping = {}
    for row in records:
        name = row["path"]
        data = (HERE / name).read_bytes()
        require(len(data) == row["bytes"] and digest(data) == row["sha256"], "canonical source changed while staging")
        target = recipe / "controller/sources" / (name + ".gz")
        target.write_bytes(gzip.compress(data, mtime=0))
        require(gzip.decompress(target.read_bytes()) == data, "staged source differs")
        mapping[name] = {"canonical_sha256": digest(data), "staged_raw_sha256": digest(gzip.decompress(target.read_bytes()))}
    record = {"schema": "MAYHEM_CURRENT_SOURCE_TO_QUALIFIED_RECIPE_V1", "current_source": str(HERE),
              "qualified_recipe": str(qualified.relative_to(repository)), "source_files": 67,
              "mapping": mapping, "canonical_inputs": actual,
              "wrapper_sha256": digest(Path(__file__).read_bytes()),
              "copied_recipe_inputs": {p.relative_to(recipe).as_posix():digest(p.read_bytes()) for p in sorted(recipe.rglob("*")) if p.is_file()},
              "stage_only": True, "compiler_executed": False, "target_executed": False,
              "allocation_tail_emitted": False}
    (output / "source-mapping.json").write_text(json.dumps(record, indent=2) + "\n")
    return recipe, record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--stage-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    for name in ("sdk", "target-sysroot", "vendor", "msvc", "windows-sdk"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--kit-version", default="10.0.26100.0")
    args = parser.parse_args()
    repository = args.repo.resolve() if args.repo else next(p for p in HERE.parents if (p / "research/mayhem-fresh-host-20261028/build.py").is_file())
    if not args.stage_only:
        require(os.name == "nt", "actual qualified Mayhem build requires Windows")
        require(all(getattr(args, name.replace("-", "_")) for name in ("sdk", "target-sysroot", "vendor", "msvc", "windows-sdk")), "all pinned Windows build inputs are required")
    output = args.output.resolve()
    recipe, record = stage(output, repository)
    if args.stage_only:
        print(json.dumps({"source_files":67, "stage_only":True, "compiler_executed":False}, indent=2))
        return
    command = [sys.executable, "-I", "-B", str(recipe / "build.py")]
    for name in ("sdk", "target-sysroot", "vendor", "msvc", "windows-sdk"):
        command += ["--" + name, str(getattr(args, name.replace("-", "_")).resolve())]
    command += ["--kit-version", args.kit_version, "--output", str(output / "build")]
    (output / "launch.json").write_text(json.dumps({"command":command, "mapping_sha256":digest((output / "source-mapping.json").read_bytes())}, indent=2) + "\n")
    with (output / "driver.log").open("wb") as log:
        run = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    require(run.returncode == 0, "fresh Windows host/target build failed; inspect driver.log")
    require(all(digest((HERE / name).read_bytes()) == value for name, value in record["canonical_inputs"].items()), "canonical source changed during build")
    expected = {"symbols.so":"7b15bb1e5c7c9c53041322fa64d4a420906fffd96ff97a55d70d627bcb854960",
                "candidate-v154-strip.so":"9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d"}
    for name, value in expected.items():
        require(digest((output / "build/target" / name).read_bytes()) == value, "fresh exact output differs: " + name)
    (output / "current-build-result.json").write_text(json.dumps({"status":"SUCCEEDED", "source_files":67,
        "source_unchanged":True, "outputs":expected, "target_executions":0,
        "meaningful_elf_bytes":775416, "allocation_tail_emitted":False}, indent=2) + "\n")
    print("Verified fresh current-source Windows host+target output; meaningful ELF775416B exact")


if __name__ == "__main__":
    main()
