#!/usr/bin/env python3
"""Verify current tracked inputs; historical scratch paths use exact published copies.

Run the immutable package verifier separately for saved receipts and signatures.
The historical Darwin Surfpool executable is identified, not installed or executed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "pump": "repro/pump/bonding-curve-serializer-fortyeight",
    "fees": "repro/pump_fees/solana-family-221-v144",
}
HISTORICAL_COPIES = {
    "work/pump-multi-hop-curve-recovery/differential.py": "repro/pump/native-curve-partial-fortyeight/harness/pump_multi_hop_curve_differential.py",
    "work/pump-multi-hop-curve-recovery/verify_saved.py": "repro/pump/native-curve-partial-fortyeight/isolated-partial-checkpoint/verify_saved.py",
    "work/fees-update-admin-dataflow/signed_transfers.py": "repro/pump_fees/fee-config-serialization-v144/signed_transfers.py",
    "work/fees-config-serialization/serialization_error.py": "repro/pump_fees/fee-config-serialization-v144/serialization_error.py",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(root, name):
    """Read one tracked file through a non-symlinked regular path."""
    root = Path(os.path.abspath(root))
    path = Path(os.path.abspath(root / name))
    try:
        path.relative_to(root)
    except ValueError:
        raise AssertionError(("Input outside root", name))
    current = path
    while True:
        if current.is_symlink():
            raise AssertionError(("Symlink ancestry", str(current)))
        if current == root:
            break
        current = current.parent
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise AssertionError(("Nonregular input", name))
        data = stream.read()
        after = os.fstat(stream.fileno())
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    current = os.stat(path, follow_symlinks=False)
    if (not stat.S_ISREG(current.st_mode)
            or identity(current) != identity(before)
            or identity(before) != identity(after)):
        raise AssertionError(("Input changed during read", name))
    return data


def verify_maps(root, groups, tracked):
    checked, historical = 0, []
    for group, entries in groups.items():
        for name, expected in entries.items():
            target = HISTORICAL_COPIES.get(name, name)
            if target not in tracked:
                raise AssertionError(("Unpublished input", group, name, target))
            if sha(read_regular(root, target)) != expected:
                raise AssertionError(("Binding mismatch", group, name, target))
            checked += 1
            if target != name:
                historical.append({"recorded_path": name, "published_copy": target, "sha256": expected})
    return checked, historical


def current_pump_groups(package):
    """Bind live published inputs without treating scratch origins as live files."""
    read = lambda name: json.loads((package / name).read_text())
    maps = read("source-harness-sha256.json")
    scratch = read("scratch-inputs-before.json")
    assert maps["source"] == read("source-sha256.json")
    assert len(maps["source"]) == 36
    assert len(scratch["harness_sha256"]) == 94
    assert len(scratch["repository_fixture_snapshot_sha256"]) == 28
    assert len(maps["canonical_harness"]) == 2
    groups = {
        "source": maps["source"],
        "harness": scratch["harness_sha256"],
        "runtime": scratch["repository_fixture_snapshot_sha256"],
        "build_helpers": read("build-helper-sha256.json"),
        "canonical_harness": maps["canonical_harness"],
        "static_and_saved_verifiers": maps["static_and_saved_verifiers"],
        "documentation": maps["owned_documentation"],
        "candidate": {str((package / "candidate.so").relative_to(ROOT)):
                      read("manifest-sha256.json")["candidate.so"]["sha256"]},
    }
    # The old single-curve runner and verifier have exact published aliases in
    # HISTORICAL_COPIES. The adapted new runner has its own canonical hashes;
    # scratch orchestration remains historical evidence inside the package.
    assert len(groups["build_helpers"]) == 3
    return groups


def verify_pump_body(root, package):
    # Same complete-body/call/literal checks as immutable verify-package.py:112-125.
    spec = importlib.util.spec_from_file_location("pump_binding_elf", package / "elf_reader.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = module.Elf(root / "evidence/original/pump/deployed.so")
    candidate = module.Elf(package / "candidate.so")
    symbols = module.Elf(package / "unstripped.so")
    match = json.loads((package / "function-match.json").read_text())
    assert sha(original.b) == "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
    assert sha(candidate.b) == "92575cd082bf76b332044a7d09371a9764db8b2cc40180bf1418f261945bbd6a"
    assert candidate.b[candidate.lo:candidate.hi] == symbols.b[symbols.lo:symbols.hi]
    assert candidate.pattern(candidate.lo, candidate.hi-candidate.lo) == symbols.pattern(symbols.lo, symbols.hi-symbols.lo)
    start, origin, size = match["candidate_body"]["start"], match["original_body"]["start"], 1840
    assert original.normalized[origin:origin+size] == candidate.normalized[start:start+size]
    assert original.pattern(origin, size) == candidate.pattern(start, size)
    functions = {(f["start"], f["size"]) for f in symbols.funcs}
    ranges = {p: (original.entries[i+1] if i+1 < len(original.entries) else original.hi)-p for i, p in enumerate(original.entries)}
    calls = candidate.callsites(start, size)
    assert len(calls) == 25
    for call in calls:
        dest = original.calls[origin+call["offset"]]
        sizes = [n for at, n in functions if at == call["target"]]
        assert len(sizes) == 1
        n = sizes[0]
        assert ranges[dest] == n
        assert original.normalized[dest:dest+n] == candidate.normalized[call["target"]:call["target"]+n]
        assert original.pattern(dest, n) == candidate.pattern(call["target"], n)
    assert candidate.pattern(start, size) == [{"offset": 248, "type": 8, "symbol": ""}]
    for elf, at in [(original, origin), (candidate, start)]:
        at += 248
        ptr = struct.unpack_from("<I", elf.b, at+4)[0] | struct.unpack_from("<I", elf.b, at+12)[0] << 32
        assert elf.b[ptr:ptr+8] == bytes.fromhex("17b7f83760d8ac60")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", choices=PACKAGES)
    args = parser.parse_args()
    status = json.loads((ROOT / "repro/status.json").read_text())
    key = "pump" if args.program == "pump" else "pump_fees"
    artifact = status[key]["candidate_artifact"]
    if args.program == 'fees' and artifact == 'research/all-contract-completion-20261028/fees-built/canonical-01/candidate.so':
        subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/verify_current_checkpoint.py'), 'pump_fees'], check=True)
        return
    if args.program == "pump" and artifact in ["repro/pump/main-contract-round47-20261027/candidate.so", "repro/pump/canonical-frontier-20261028/candidate.so", "research/pump-create-used-boundaries-20261028/artifacts/candidate.so", "research/pump-final-composition-673-20261028/artifacts/candidate.so", "research/pump-multihop-accrual-qualification-20261028/artifacts/candidate.so", "research/pump-program-creator-notice-qualification-20261028/artifacts/candidate.so"]:
        subprocess.run([sys.executable, "-B", str(ROOT / "scripts/verify_pump_main_checkpoint.py")], check=True)
        return
    if artifact == "repro/pump/remaining-guards-main-fortyeight/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "scripts/verify_pump_remaining_checkpoint.py")], check=True)
        return
    if artifact == "repro/pump/admin-cto-compared-errors-main-fortyeight/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "scripts/verify_pump_compared_checkpoint.py")], check=True)
        return
    if artifact in ("repro/pump_fees/sharing-authorize-main-v144/main/candidate.so", "repro/pump/admin-cto-error-batch-main-fortyeight/main/candidate.so", "repro/pump_fees/sharing-fourth-cpi-main-v144/main/candidate.so"):
        subprocess.run([sys.executable, "-B", str(ROOT / "scripts/verify_current_checkpoint.py"), key], check=True)
        return
    if args.program == "pump" and artifact == "repro/pump/buy-fee-basis-main-fortyeight/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump/buy-fee-basis-main-fortyeight/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "pump" and artifact == "repro/pump/admin-cto-owned6083-main-fortyeight/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "scripts/verify_current_checkpoint.py"), "pump"], check=True)
        return
    if args.program == "pump" and artifact == "repro/pump/admin-cto-owned-main-fortyeight/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump/admin-cto-owned-main-fortyeight/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "pump" and artifact == "repro/pump/admin-cto-typed-main-fortyeight/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump/admin-cto-typed-main-fortyeight/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "pump" and artifact == "repro/pump/creator-full-curve-main-fortyeight/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump/creator-full-curve-main-fortyeight/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "pump" and artifact == "repro/pump/buy-mode-order-main-fortyeight/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump/buy-mode-order-main-fortyeight/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "fees" and artifact == "repro/pump_fees/sharing-second-pump-cpi-main-v144/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "scripts/verify_current_checkpoint.py"), "pump_fees"], check=True)
        return
    if args.program == "fees" and artifact == "repro/pump_fees/sharing-pump-extend-main-v144/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump_fees/sharing-pump-extend-main-v144/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "fees" and artifact == "repro/pump_fees/sharing-option-order-main-v144/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump_fees/sharing-option-order-main-v144/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "fees" and artifact == "repro/pump_fees/graduation-zero-main-v144/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump_fees/graduation-zero-main-v144/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "fees" and artifact == "repro/pump_fees/sharing-owned-error-main-v144/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump_fees/sharing-owned-error-main-v144/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "fees" and artifact == "repro/pump_fees/withdraw-owned-error-main-v144/main/candidate.so":
        subprocess.run([sys.executable, "-B", str(ROOT / "repro/pump_fees/withdraw-owned-error-main-v144/verify.py"), "--current-main", str(ROOT)], check=True)
        return
    if args.program == "fees" and artifact in ("repro/pump_fees/donation-business-v144/pump_fees_candidate.so", "repro/pump_fees/donation-borrow-v144/pump_fees_candidate.so", "repro/pump_fees/legacy-social-admission-v144/pump_fees_candidate.so", "repro/pump_fees/legacy-caller-v144/pump_fees_candidate.so", "repro/pump_fees/legacy-value-v144/pump_fees_candidate.so", "repro/pump_fees/v2-caller-v144/pump_fees_candidate.so"):
        subprocess.run([sys.executable, "-B", str((ROOT / artifact).parent / "verify.py"),
                        "--current-main", "--repo", str(ROOT)], check=True)
        return
    if args.program == "pump" and artifact in ("repro/pump/nested-general-route-fortyeight/candidate.so", "repro/pump/final-error-metadata-fortyeight/candidate.so", "repro/pump/curve-preparation-fortyeight/candidate.so"):
        subprocess.run([sys.executable, "-B", str((ROOT / artifact).parent / "verify.py"),
                        "--current-main", "--repo", str(ROOT)], check=True)
        return
    if args.program == "pump" and artifact == "repro/pump/nested-ancestry-fortyeight/candidate.so":
        subprocess.run([sys.executable, "-B", str((ROOT / artifact).parent / "verify-package.py"),
                        "--current-main"], check=True)
        return
    current = {
        "pump": "repro/pump/tokenkeg-two-curve-fortyeight/candidate.so",
        "fees": "repro/pump_fees/donation-event-account-v144/pump_fees_candidate.so",
    }
    if artifact == current[args.program]:
        directory = (ROOT / artifact).parent
        if args.program == "pump":
            tracked = set(subprocess.check_output(
                ["git", "-C", str(ROOT), "ls-files", "-z"]).decode().split("\0"))
            groups = current_pump_groups(directory)
            count, historical = verify_maps(ROOT, groups, tracked)
            assert len(historical) == 2
        command = ([sys.executable, str(directory / "verify-package.py"), "--current-main"]
                   if args.program == "pump" else
                   [sys.executable, str(directory / "verify_current_bindings.py"), "--repo", str(ROOT)])
        subprocess.run(command, check=True)
        if args.program == "pump":
            print(json.dumps({"verified": True, "program": "pump",
                              "current_tracked_bindings": count,
                              "tracked_bindings_by_group": {k: len(v) for k, v in groups.items()},
                              "historical_exact_copy_bindings": historical,
                              "saved_package_verified": True,
                              "runtime_replayed_by_this_script": False}, indent=2))
        return
    expected_old = PACKAGES[args.program] + ("/candidate.so" if args.program == "pump" else "/pump_fees_candidate.so")
    assert artifact == expected_old, ("No reviewed binding verifier for current candidate", artifact)
    package = ROOT / PACKAGES[args.program]
    read = lambda name: json.loads((package / name).read_text())
    tracked = set(subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"]).decode().split("\0"))
    if args.program == "pump":
        maps = read("source-harness-sha256.json")
        groups = {k: maps[k] for k in ["source", "harness", "runtime", "documentation", "build_helpers"]}
        assert len(groups["source"]) == 36
    else:
        groups = {n: read(n) for n in ["source-sha256.json", "build-helper-sha256.json", "documentation-sha256.json", "harness-source-sha256.json", "runtime-inputs.json"]}
        assert len(groups["source-sha256.json"]) == 22
    count, historical = verify_maps(ROOT, groups, tracked)
    assert len(historical) == 2
    if args.program == "pump":
        verify_pump_body(ROOT, package)
    result = {"verified": True, "program": args.program, "current_tracked_bindings": count,
              "historical_exact_copy_bindings": historical,
              "saved_package_verifier_required_separately": True, "runtime_replayed_by_this_script": False}
    if args.program == "pump":
        result.update(historical_surfpool_identity=maps["surfpool"], local_surfpool_binary_checked=False,
                      complete_serializer_and_25_calls_checked=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
