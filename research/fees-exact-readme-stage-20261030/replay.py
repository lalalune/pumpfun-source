#!/usr/bin/env python3
"""Replay the retained Fees staging failure and the one-pin correction offline."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import traceback

sys.dont_write_bytecode = True
PACKET = Path(__file__).resolve().parent
BUILDER_SHA256 = "6fffc0c2d0eedf2e84541445c6a388092accb6bf3371e159acc851bc397a92b8"
README = "programs/pump-fees/README.md"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): digest(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def load_builder(path, source):
    require(digest(path) == BUILDER_SHA256, "retained staging controller changed")
    spec = importlib.util.spec_from_file_location("fees_stage_replay", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = source
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=PACKET.parents[1])
    parser.add_argument("--output", type=Path, required=True,
                        help="new task-owned directory; existing output is never overwritten")
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    source = repo / "programs/pump-fees"
    require(not output.is_relative_to(source), "output must be outside program source")
    output.mkdir(parents=True, exist_ok=False)
    old_bytes = (PACKET / "ORIGINAL-PINS.json").read_bytes()
    old = json.loads(old_bytes)
    fixed = json.loads((source / "exact/qualified-source-inputs.json").read_bytes())
    require(set(old) == set(fixed) and len(fixed) == 65, "65-input cohort changed")
    require([name for name in old if old[name] != fixed[name]] == [README],
            "expected only the retained README pin correction")
    require(fixed[README] == digest(source / "exact/research-README.md"),
            "corrected README is not the current source")
    before = inventory(source)
    baseline = output / "baseline-inputs"
    shutil.copytree(source, baseline, ignore=shutil.ignore_patterns("__pycache__"))
    (baseline / "exact/qualified-source-inputs.json").write_bytes(old_bytes)
    original_output = output / "original-stage"
    original_output.mkdir()
    try:
        load_builder(source / "build_exact.py", baseline).stage(original_output)
    except ValueError as error:
        require(str(error) == "canonical input changed: " + README,
                "unexpected original staging failure: " + str(error))
        (output / "original-stage.log").write_text(traceback.format_exc(), encoding="utf-8")
        original_error = str(error)
    else:
        raise ValueError("original pin unexpectedly staged successfully")
    fixed_output = output / "fixed-stage"
    fixed_output.mkdir()
    module = load_builder(source / "build_exact.py", source)
    workspace, mapping, expected = module.stage(fixed_output)
    require(expected == fixed, "unexpected stage input inventory")
    require(set(inventory(workspace)) == set(fixed), "unexpected staged files")
    for name, value in fixed.items():
        require(digest(source / mapping[name]["canonical"]) == value, "input changed: " + name)
        if name != "Cargo.toml":
            require(digest(workspace / name) == value, "staged input changed: " + name)
    text = (source / "exact/workspace-Cargo.toml").read_text(encoding="utf-8")
    locator = 'anchor-attribute-program = { path = "vendor/used-public" }'
    require(text.count(locator) == 1, "unexpected original macro locator")
    require((workspace / "Cargo.toml").read_text(encoding="utf-8") == text.replace(
        locator, 'anchor-attribute-program = { path = "' + module.MACRO + '" }'),
        "unexpected existing workspace path adaptation")
    require(inventory(source) == before, "repository source was modified")
    result = {"scope": "source staging only; no SDK, Cargo, linker or ELF invocation",
              "builderSHA256": BUILDER_SHA256, "originalError": original_error,
              "oldReadmePin": old[README], "currentReadmePin": fixed[README],
              "inputs": mapping, "inputCount": len(fixed), "unchangedPins": 64,
              "sourceUnchanged": True, "staged": inventory(workspace),
              "compilerInvocations": 0, "newElfReceipts": 0}
    (output / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "originalError", "inputCount", "unchangedPins", "sourceUnchanged", "compilerInvocations")}, indent=2))


if __name__ == "__main__":
    main()
