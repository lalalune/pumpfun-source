#!/usr/bin/env python3
"""Build only the main Pump crate with the installed v1.44 SDK and bound inputs.

This creates a fresh target and records source/tool hashes and both ELF outputs.
It neither downloads a compiler nor uses the captured program as compiler input.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from pump_dependency_cache import DependencyCache
import pump_text_layout
import pump_target_library_profile
import pump_data_order

from source_manifest_guard import strict_manifest as source_manifest
from compare import compare

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def check(ok, message="build check failed"):
    # Explicit check instead of `assert`: `python -O` / `-OO` strips asserts,
    # which let a data-order build publish a "passed" receipt on a cache miss
    # and with changed staged source, primary source, or certificate.
    if not ok:
        raise AssertionError(message)


def compiler_overrides(env):
    """The dependency-cache key's flags beyond those the seed import compares."""
    return {k: v for k, v in env.items() if k == "RUSTC_BOOTSTRAP" or k.startswith("CARGO_PROFILE_")}


def workspace_manifests(text):
    """Split literal TOML tables without treating comments or values as headers."""
    parsed = tomllib.loads(text)
    check(parsed.get("workspace") == {} and set(parsed.get("profile", {})) == {
        "release"
    }, "unsupported source workspace/profile layout")

    def table_start(name):
        pattern = r'(?m)^[ \t]*\[' + re.escape(name) + r'\][ \t]*(?:#[^\n]*)?$'
        for match in re.finditer(pattern, text):
            try:
                # A header-looking line inside a multiline value leaves an
                # incomplete TOML prefix; a real table follows complete values.
                tomllib.loads(text[:match.start()])
            except tomllib.TOMLDecodeError:
                continue
            return match.start()
        raise AssertionError("missing literal manifest table: " + name)

    profile_start = table_start("profile.release")
    workspace_start = table_start("workspace")
    check(profile_start < workspace_start and
          tomllib.loads(text[workspace_start:]) == {"workspace": {}},
          "unexpected manifest tables after release profile")
    profile = text[profile_start:workspace_start].strip() + "\n"
    crate = text[:profile_start].rstrip() + "\n"
    return crate, '[workspace]\nmembers = ["programs/pump"]\nresolver = "2"\n\n' + profile


def finish_report(record, report, receipt, cache, target, log, data_order=False):
    """Publish the data-order receipt only after all cache checks succeed."""
    try:
        if cache and not data_order:
            report.write_text(json.dumps(record, indent=2) + "\n",encoding='utf-8',newline='\n')
        if cache:
            if data_order:
                check(cache.record["status"] == "hit", "data-order build must use a verified external cache")
            cache.finish(target, log, report)
            record["dependency_cache"] = cache.record
            record["dependency_cache"]["implementation_sha256"] = sha(
                Path(DependencyCache.__init__.__code__.co_filename)
            )
        if data_order:
            check(all(sha(ROOT / path) == value for path, value in record["source_sha256"].items()), "data-order staged source changed")
            check(all(sha(ROOT / path) == value for path, value in record["primary_source_sha256"].items()), "data-order primary source changed")
            certificate = record["text_layout"]["data_order_certificate"]
            check(sha(Path(certificate["path"])) == certificate["sha256"], "data-order certificate changed before acceptance")
            record["data_order"]["status"] = "passed"
        report.write_text(json.dumps(record, indent=2) + "\n",encoding='utf-8',newline='\n')
        if data_order:
            receipt.write_text(json.dumps(record, indent=2) + "\n",encoding='utf-8',newline='\n')
    except BaseException:
        if cache:
            report.unlink(missing_ok=True)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-directory", type=Path, default=ROOT / "programs/pump")
    p.add_argument(
        "--sdk", type=Path, default=Path.home() / ".cache/solana/v1.44/platform-tools"
    )
    p.add_argument(
        "--registry-home",
        type=Path,
        default=Path(os.environ.get("CARGO_HOME", Path.home() / ".cargo")),
    )
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--target", choices=["sbf-solana-solana", "sbpf-solana-solana"],
                   help="Native SDK target; must agree with an explicitly selected target-library profile.")
    p.add_argument("--data-order-certificate", type=Path,
                   help="Opt in to the two-object data-order certificate derived from this source's identity build.")
    p.add_argument("--target-library-profile", choices=["linux-v1.44-sbf", "linux-v1.44-sbpf"],
                   help="Opt in to a private native-host SDK with the pinned Linux v1.44 SBF libraries.")
    p.add_argument("--target-library-directory", type=Path,
                   help="Directory containing exactly the admitted profile's target libraries.")
    p.add_argument(
        "--text-section-order",
        type=Path,
        help="Optional validated SDK linker script changing only .text input order.",
    )
    p.add_argument(
        "--workspace-layout",
        action="store_true",
        help="Stage identical Rust sources in an actual programs/pump Cargo workspace; preserve release settings and lockfile.",
    )
    p.add_argument(
        "--dependency-cache",
        type=Path,
        help="Reuse verified external libraries only; regenerate the Cargo plan and always compile main Pump.",
    )
    p.add_argument(
        "--dependency-cache-seed",
        type=Path,
        help="Optional completed clean build whose external artifacts are verified before seeding an empty cache.",
    )
    a = p.parse_args()
    if a.dependency_cache_seed and not a.dependency_cache:
        p.error("--dependency-cache-seed requires --dependency-cache")
    if a.target_library_profile and a.target and a.target != pump_target_library_profile.PROFILE_TARGETS[a.target_library_profile]:
        p.error("--target disagrees with --target-library-profile")
    if a.target == "sbpf-solana-solana" and a.dependency_cache and not a.target_library_profile:
        p.error("native sbpf --target does not support --dependency-cache; use a target-library profile")
    if bool(a.target_library_profile) != bool(a.target_library_directory):
        p.error("--target-library-profile and --target-library-directory must be supplied together")
    if a.data_order_certificate and not (a.text_section_order and a.dependency_cache):
        p.error("--data-order-certificate requires --text-section-order and --dependency-cache")
    crate = a.source_directory.resolve()
    sdk = a.sdk.resolve()
    out = a.output.resolve()
    registry = a.registry_home.resolve()
    crate.relative_to(ROOT)
    data_certificate = None
    data_certificate_sha256 = None
    if a.data_order_certificate:
        data_certificate_sha256 = sha(a.data_order_certificate)
        data_certificate = pump_data_order.check_request(
            a.data_order_certificate, crate, sdk, a.target_library_profile,
            a.target_library_directory, registry, a.workspace_layout, a.text_section_order
        )
        check(sha(a.data_order_certificate) == data_certificate_sha256, "data-order certificate changed during admission")
    out.mkdir(parents=True, exist_ok=False)
    target_library_profile = None
    if a.target_library_profile:
        sdk, target_library_profile = pump_target_library_profile.prepare(
            a.target_library_profile, sdk, a.target_library_directory, out / "profile-sdk"
        )
    target = target_library_profile["cache_context"]["target"] if target_library_profile else (a.target or "sbf-solana-solana")
    if a.target and a.target != target:
        p.error("--target disagrees with --target-library-profile")
    target_flags_key = "CARGO_TARGET_" + target.upper().replace("-", "_") + "_RUSTFLAGS"
    target_libdir = sdk / "rust/lib/rustlib" / target / "lib"
    target_libraries_before = pump_target_library_profile.inventory(target_libdir)
    check(target_libraries_before, "selected SDK target libraries are missing")

    primary = crate
    primary_before = source_manifest(primary, primary, ROOT)
    workspace = crate
    if a.workspace_layout:
        check(not out.is_relative_to(primary),
              "workspace staging must be outside the input crate")
        text = (primary / "Cargo.toml").read_text()
        crate_text, workspace_text = workspace_manifests(text)
        workspace = out / "source"
        crate = workspace / "programs/pump"
        for source_path in primary_before:
            src = ROOT / source_path
            try:
                relative = src.relative_to(primary)
            except ValueError:
                raise AssertionError(
                    "staged inputs outside the main crate need explicit handling: "
                    + source_path
                )
            dest = crate / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        (crate / "Cargo.toml").write_text(crate_text,encoding='utf-8',newline='\n')
        shutil.move(crate / "Cargo.lock", workspace / "Cargo.lock")
        (workspace / "Cargo.toml").write_text(workspace_text,encoding='utf-8',newline='\n')
    tools = {
        "rustc": sdk / "rust/bin/rustc",
        "cargo": sdk / "rust/bin/cargo",
        "objcopy": sdk / "llvm/bin/llvm-objcopy",
    }
    check(all(p.is_file() for p in tools.values()), "installed SDK is incomplete")
    cargo_home = out / "cargo-home"
    (cargo_home / "registry").mkdir(parents=True)
    for name in ["src", "cache", "index"]:
        original = registry / "registry" / name
        if original.exists():
            (cargo_home / "registry" / name).symlink_to(
                original, target_is_directory=True
            )
    wrapper = ROOT / "scripts/pump_physical_source_wrapper.py"
    wrapper_launcher = wrapper.with_suffix(".sh")
    before = source_manifest(crate, workspace, ROOT, cwd=workspace)
    env = os.environ.copy()
    env.pop("PUMP_DATA_ORDER_CERTIFICATE", None)
    env.update(
        RUSTC_WRAPPER=str(wrapper_launcher),
        PUMP_VERIFIED_PYTHON=sys.executable,
        PUMP_LOGICAL_REGISTRY_SRC=str(cargo_home / "registry/src"),
        PUMP_SOURCE_WRAPPER_LOG=str(out / "physical-source-calls.jsonl"),
        CARGO_HOME=str(cargo_home),
        CARGO_TARGET_DIR=str(out / "target"),
        CARGO_BUILD_JOBS="2",
        RUSTC=str(tools["rustc"]),
        CC=str(sdk / "llvm/bin/clang"),
        AR=str(sdk / "llvm/bin/llvm-ar"),
        OBJDUMP=str(sdk / "llvm/bin/llvm-objdump"),
        OBJCOPY=str(tools["objcopy"]),
    )
    env[target_flags_key] = "-Zremap-cwd-prefix="
    command = [
        str(tools["cargo"]),
        "build",
        "--manifest-path",
        str(crate / "Cargo.toml"),
        "--release",
        "--target",
        target,
        "--locked",
        "--offline",
    ]
    if a.dependency_cache:
        env["CARGO_HOME"] = str(registry)
        env["PUMP_LOGICAL_REGISTRY_SRC"] = str(registry / "registry/src")
    cache = (
        DependencyCache(
            a.dependency_cache, ROOT, crate, workspace, sdk, env, wrapper, direct=True,
            target_library_profile=(target_library_profile["cache_context"] if target_library_profile else None),
            wrapper_launcher=wrapper_launcher,
        )
        if a.dependency_cache
        else None
    )
    if cache:
        if data_certificate:
            check(cache.context == data_certificate["payload"]["cache_context"], "data-order dependency/compiler context differs")
        if a.dependency_cache_seed and not cache.entry.exists():
            seed = json.loads((a.dependency_cache_seed.resolve() / "build-comparison.json").read_text())
            check(compiler_overrides(seed["environment"]) == compiler_overrides(env), "seed compiler overrides differ")
            cache.import_clean_build(a.dependency_cache_seed.resolve())
        cache.seed(out / "target")
        command += ["--message-format=json-render-diagnostics"]
    text_layout = None
    if a.text_section_order:
        if data_certificate:
            check(sha(a.data_order_certificate) == data_certificate_sha256, "data-order certificate changed")
        if cache:
            check(cache.record["status"] == "hit",
                  "prepare the ordinary external cache before an ordered build")
        name = tomllib.loads((crate / "Cargo.toml").read_text()).get("lib", {}).get(
            "name", tomllib.loads((crate / "Cargo.toml").read_text())["package"]["name"].replace("-", "_")
        )
        layout_env, text_layout = pump_text_layout.configure(
            a.text_section_order.resolve(), out, sdk, name, wrapper,
            data_certificate=a.data_order_certificate
        )
        env.update(layout_env)
        if data_certificate:
            check(sha(a.data_order_certificate) == data_certificate_sha256, "data-order certificate changed")
        if cache:
            # The external context/key above remains the ordinary physical
            # wrapper. Only the fresh main Cargo plan uses this root-only hook.
            cache.env = env.copy()
    tool_sha256 = {k: sha(v) for k, v in tools.items()}
    record = {
        "scope": __doc__,
        "workspace_layout": a.workspace_layout,
        "source_directory": str(crate),
        "primary_source_directory": str(primary),
        "primary_source_sha256": primary_before,
        "source_sha256": before,
        "source_wrapper_sha256": sha(wrapper),
        "source_wrapper_launcher_sha256": sha(wrapper_launcher),
        "builder_sha256": sha(Path(__file__)),
        "selected_toolchain": "v1.44",
        "target": target,
        "target_libraries_sha256": target_libraries_before,
        "tool_sha256": tool_sha256,
        "command": command,
        "environment": {
            k: env[k]
            for k in [
                "RUSTC_WRAPPER",
                "PUMP_VERIFIED_PYTHON",
                "PUMP_LOGICAL_REGISTRY_SRC",
                "PUMP_SOURCE_WRAPPER_LOG",
                "CARGO_HOME",
                "CARGO_TARGET_DIR",
                "CARGO_BUILD_JOBS",
                "RUSTC",
                "CC",
                "AR",
                "OBJDUMP",
                "OBJCOPY",
                target_flags_key,
                "RUSTFLAGS",
                "CARGO_ENCODED_RUSTFLAGS",
            ]
            if k in env
        } | compiler_overrides(env),
    }
    if cache:
        record["dependency_cache"] = cache.record
        record["dependency_cache"]["implementation_sha256"] = sha(
            Path(DependencyCache.__init__.__code__.co_filename)
        )
    if target_library_profile:
        record["target_library_profile"] = target_library_profile
    if text_layout:
        record["text_layout"] = text_layout
    if data_certificate:
        record["data_order"] = {"status": "pending", "certificate_sha256": data_certificate_sha256}
    receipt = out / "build-attempt.json"
    receipt.write_text(json.dumps(record, indent=2) + "\n",encoding='utf-8',newline='\n')
    with (out / "build.log").open("w") as f:
        result = (
            cache.compile_main(out / "target", f)
            if cache and cache.record["status"] == "hit"
            else subprocess.run(
                command, cwd=workspace, env=env, stdout=f, stderr=subprocess.STDOUT
            )
        )
    if cache and cache.record.get("main_command"):
        record["requested_cargo_command"] = record["command"]
        record["command"] = cache.record["main_command"]
    record.update(
        returncode=result.returncode,
        source_after_sha256=source_manifest(crate, workspace, ROOT, cwd=workspace),
    )
    record["build_log_sha256"] = sha(out / "build.log")
    record["stack_warnings"] = [
        line.strip() for line in (out / "build.log").read_text(encoding="utf-8").splitlines()
        if "exceeded max offset" in line
    ]
    record["stack_diagnostic_gate_passed"] = not record["stack_warnings"]
    record["target_libraries_unchanged"] = pump_target_library_profile.inventory(target_libdir) == target_libraries_before
    check(record["target_libraries_unchanged"], "selected SDK target libraries changed during compilation")
    record["source_unchanged"] = record[
        "source_after_sha256"
    ] == before and primary_before == source_manifest(primary, primary, ROOT)
    if target_library_profile:
        record["target_library_profile"] = pump_target_library_profile.finish(target_library_profile)
    receipt.write_text(json.dumps(record, indent=2) + "\n",encoding='utf-8',newline='\n')
    result.check_returncode()
    check(record["source_unchanged"])
    check(record["stack_diagnostic_gate_passed"], "compiler reported a stack offset exceeding its maximum; inspect build.log")
    if text_layout:
        record["text_layout"] = pump_text_layout.finish(text_layout)
    manifest = tomllib.loads((crate / "Cargo.toml").read_text())
    name = manifest.get("lib", {}).get(
        "name", manifest["package"]["name"].replace("-", "_")
    )
    built = out / "target" / target / "release" / f"{name}.so"
    shutil.copy2(built, out / "unstripped.so")
    subprocess.run(
        [str(tools["objcopy"]), "--strip-all", str(built), str(out / "candidate.so")],
        check=True,
    )
    # The record hashed the tool paths before the build; sources and target
    # libraries are already re-verified above. Bind the executables the same
    # way: a tool replaced at its path during the build must not let the
    # report name bytes that did not produce the artifact.
    record["tools_unchanged"] = {k: sha(v) for k, v in tools.items()} == tool_sha256
    check(record["tools_unchanged"], "selected SDK tools changed during compilation")
    record.update(
        unstripped_sha256=sha(out / "unstripped.so"),
        build_log_sha256=sha(out / "build.log"),
        comparison=compare(
            (ROOT / "evidence/original/pump/deployed.so").read_bytes(),
            (out / "candidate.so").read_bytes(),
        ),
    )
    if data_certificate:
        check(sha(a.data_order_certificate) == data_certificate_sha256, "data-order certificate changed")
        proof = pump_data_order.verify_transform(data_certificate, out)
        proof_path = out / "data-order-transformation.json"
        proof_path.write_text(json.dumps(proof, indent=2) + "\n",encoding='utf-8',newline='\n')
        record["data_order"] = {"status": "transform_verified", "certificate_sha256": data_certificate_sha256,
                                "transformation_sha256": sha(proof_path)}
        receipt.write_text(json.dumps(record, indent=2) + "\n",encoding='utf-8',newline='\n')
    report = out / "build-comparison.json"
    finish_report(record, report, receipt, cache, out / "target", out / "build.log", bool(data_certificate))
    print(json.dumps(record["comparison"], indent=2))


if __name__ == "__main__":
    main()
