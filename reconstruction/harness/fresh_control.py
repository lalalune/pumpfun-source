#!/usr/bin/env python3
"""Build and score fresh Pump base/candidate sources with fail-closed receipts."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
import types
from pathlib import Path

import build_score_pair
import compare_scores
import fastbuild
import score as official_score
from original_input import copy_original_inputs
from source_inputs import assert_unchanged, snapshot


H = Path(__file__).resolve().parent
SC = H.parent


def qualified_module(name):
    path = H / "fresh_control_inputs.py"
    raw = path.read_bytes()
    admission = types.ModuleType("_fresh_control_admission")
    admission.__file__ = str(path)
    admission.__dict__["_ADMITTED_SOURCE_BYTES"] = raw
    exec(compile(raw, str(path), "exec", dont_inherit=True), admission.__dict__)
    return admission.load_context().load(name)


def same_json(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def valid_build(result):
    build_score_pair.require_valid_build(result)
    if (result.get("ok") is not True or result.get("runtime_valid") is not True
            or not same_json(result.get("stack_warnings"), [])
            or result.get("timed_out", False) is not False
            or result.get("recipe") != "identity" or result.get("triple") != "sbpf-solana-solana"):
        raise ValueError("build flags or recipe are not admissible")
    for field in ("source_sha256", "unstripped_sha256", "candidate_sha256"):
        value = result.get(field)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("build digest is not admissible: " + field)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def publish_json(path: Path, document: dict) -> None:
    """Atomically publish deterministic JSON while preserving an older receipt."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    for _ in range(100):
        temporary = path.parent / f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}"
        try:
            stream = temporary.open("x", encoding="utf-8", newline="\n")
        except FileExistsError:
            continue
        break
    else:
        raise FileExistsError("could not create fresh-control report staging file")
    metadata = os.fstat(stream.fileno())
    identity = metadata.st_dev, metadata.st_ino
    try:
        with stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                current = temporary.lstat()
            except FileNotFoundError:
                pass
            else:
                if (current.st_dev, current.st_ino) == identity:
                    temporary.unlink()


def public_build(result: dict) -> dict:
    """Remove host paths and timings while retaining all acceptance fields."""
    fields = (
        "ok",
        "timed_out",
        "runtime_valid",
        "stack_warnings",
        "source_sha256",
        "recipe",
        "triple",
        "unstripped_sha256",
        "candidate_sha256",
        "link_order",
    )
    return {name: result[name] for name in fields if name in result}


def artifact_inventory(root: Path) -> dict[str, dict]:
    result = {}
    for path in sorted(root.rglob("*")):
        metadata = path.lstat()
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("linked retained artifacts are unsupported")
        if stat.S_ISREG(metadata.st_mode):
            result[path.relative_to(root).as_posix()] = {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        elif stat.S_ISDIR(metadata.st_mode):
            result[path.relative_to(root).as_posix() + "/"] = {"directory": True}
        else:
            raise ValueError("special retained artifacts are unsupported")
    return result


def retain_artifacts(receipt: dict, root: Path) -> None:
    """Bind retained artifacts without attempting to hash the receipt itself."""
    receipt["artifacts"] = artifact_inventory(root)
    receipt["artifacts"].pop("receipt.json", None)


def score_summary(windows: dict[int, dict]) -> dict:
    ambiguous = sorted(start for start, row in windows.items() if len(row.get("symbols", [])) > 1)
    return {
        "total": len(windows),
        "normalized": sum(row["normalized"] for row in windows.values()),
        "raw": sum(row["raw"] for row in windows.values()),
        "matched_text_bytes": sum(row["bytes"] for row in windows.values() if row["normalized"]),
        "ambiguous": [hex(start) for start in ambiguous],
    }


def write_score(path: Path, image_sha256: str, windows: dict[int, dict]) -> None:
    publish_json(
        path,
        {
            "candidate_sha256": image_sha256,
            "summary": score_summary(windows),
            "windows": {str(start): row for start, row in sorted(windows.items())},
        },
    )


def _binding(scoring_inputs: Path, sdk: Path, hybrid: Path) -> dict:
    if "_SOURCE_CONTEXT" in globals():
        _SOURCE_CONTEXT.recheck()
    result = build_score_pair.bound_inputs(scoring_inputs, sdk, hybrid)
    result["fresh_control_tools"] = {
        name: sha256_file(H / name) for name in
        ("fresh_control.py", "integrate.py", "verify_fresh_control.py", "fresh_control_inputs.py")
    }
    if "_SOURCE_CONTEXT" in globals():
        result["executed_python_source_sha256"] = dict(_SOURCE_CONTEXT.hashes)
    return result


def _reject(reason: str, detail: str | None = None) -> dict:
    result = {"accepted": False, "rejection_reasons": [reason]}
    if detail:
        result["detail"] = detail
    return result


def run_pair(
    base_source: Path,
    candidate_source: Path,
    output: Path,
    *,
    sdk: Path | None = None,
    hybrid: Path | None = None,
    timeout: float | None = None,
) -> dict:
    """Build/score admitted sources sequentially and return a final receipt.

    The caller owns source composition. This function owns a new output tree,
    private scoring inputs, separate cold build workspaces, and all receipts.
    Expected build/score rejection is returned as an unaccepted receipt;
    preflight output/source errors are raised before a misleading receipt exists.
    """
    if "_SOURCE_CONTEXT" not in globals():
        return qualified_module("fresh_control").run_pair(
            base_source, candidate_source, output, sdk=sdk, hybrid=hybrid, timeout=timeout)
    _SOURCE_CONTEXT.recheck()
    for path in (base_source, candidate_source, output):
        path = Path(path)
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("linked fresh-control inputs or output are unsupported")
    base_source = Path(base_source).resolve(strict=True)
    candidate_source = Path(candidate_source).resolve(strict=True)
    output = Path(output).resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"fresh-control output already exists: {output}")
    for source in (base_source, candidate_source):
        if fastbuild.contains_path(source, output) or fastbuild.contains_path(output, source):
            raise ValueError("fresh-control output must not overlap a source tree")
    sdk = Path(sdk or fastbuild.SDK).resolve()
    hybrid = Path(
        hybrid
        or Path(os.environ.get("PUMP_RECON_HOME", str(Path.home() / ".cache/pumpfun-reconstruction")))
        / "toolchains/hybrid144"
    ).resolve()
    fastbuild.validate_timeout(timeout)

    sources = {"base": snapshot(base_source), "candidate": snapshot(candidate_source)}
    output.mkdir(parents=True)
    scoring_inputs = output / "scoring-inputs"
    scoring_inputs.mkdir()

    receipt = {
        "schema": "pump-fresh-control-v1",
        "mode": "fresh_control",
        "sources": sources,
        "build_order": ["base", "candidate"],
        "isolated_workspaces": True,
        "cold_targets": True,
        "builds": {},
        "scores": {},
        "qualification": _reject("incomplete"),
    }
    receipt_path = output / "receipt.json"
    saved_fastbuild_sdk = fastbuild.SDK
    saved_fastbuild_lockdir = fastbuild.LOCKDIR
    saved_recipe = fastbuild.RECIPES["identity"]
    saved_score_base = official_score.BASE
    missing = object()
    saved_objdump = getattr(official_score, "OBJDUMP", missing)

    try:
        copy_original_inputs(SC / "base", scoring_inputs)
        fastbuild.SDK = sdk
        fastbuild.LOCKDIR = output / "locks"
        fastbuild.RECIPES["identity"] = {
            "triple": "sbpf-solana-solana",
            "rustc": hybrid / "rust/bin/rustc",
            "template": output / "no-template",
        }
        official_score.BASE = scoring_inputs
        official_score.OBJDUMP = str(sdk / "llvm/bin/llvm-objdump")
        bound = _binding(scoring_inputs, sdk, hybrid)
        receipt["provenance"] = bound
        publish_json(receipt_path, receipt)

        score_windows = {}
        for side, source in (("base", base_source), ("candidate", candidate_source)):
            with _SOURCE_CONTEXT.hook_cache():
                result = fastbuild.build(
                    source, output / f"{side}-work", output / f"{side}-build",
                    quiet=True, recipe="identity", timeout=timeout,
                )
            receipt["builds"][side] = public_build(result)
            publish_json(receipt_path, receipt)
            try:
                valid_build(result)
            except ValueError as error:
                receipt["qualification"] = _reject(f"{side}_build_invalid", str(error))
                retain_artifacts(receipt, output)
                publish_json(receipt_path, receipt)
                return receipt
            if result.get("source_sha256") != sources[side]["sha256"]:
                receipt["qualification"] = _reject(f"{side}_build_source_mismatch")
                retain_artifacts(receipt, output)
                publish_json(receipt_path, receipt)
                return receipt
            for artifact, field in (("unstripped.so", "unstripped_sha256"),
                                    ("candidate.so", "candidate_sha256")):
                path = output / f"{side}-build" / artifact
                if not path.is_file() or sha256_file(path) != result.get(field):
                    receipt["qualification"] = _reject(f"{side}_build_artifact_mismatch")
                    retain_artifacts(receipt, output)
                    publish_json(receipt_path, receipt)
                    return receipt
            assert_unchanged(source, sources[side], phase=f"{side} build")
            if _binding(scoring_inputs, sdk, hybrid) != bound:
                receipt["qualification"] = _reject("toolchain_or_scorer_input_mutation")
                retain_artifacts(receipt, output)
                publish_json(receipt_path, receipt)
                return receipt

            image = output / f"{side}-build/unstripped.so"
            windows, scored_sha256 = official_score.score_with_hash(image, result["unstripped_sha256"])
            score_path = output / f"{side}-score.json"
            write_score(score_path, scored_sha256, windows)
            # Parse the just-produced score through the independent saved-report
            # admission path before it can participate in acceptance.
            admitted = compare_scores.load_report(score_path)
            score_windows[side] = admitted
            receipt["scores"][side] = {
                "image_sha256": scored_sha256,
                **score_summary(windows),
                "report_sha256": sha256_file(score_path),
            }
            publish_json(receipt_path, receipt)

        for side, source in (("base", base_source), ("candidate", candidate_source)):
            assert_unchanged(source, sources[side], phase="paired qualification")
            for artifact, field in (("unstripped.so", "unstripped_sha256"),
                                    ("candidate.so", "candidate_sha256")):
                if sha256_file(output / f"{side}-build" / artifact) != receipt["builds"][side][field]:
                    raise ValueError(side + " earlier build artifact changed")
            if sha256_file(output / f"{side}-score.json") != receipt["scores"][side]["report_sha256"]:
                raise ValueError(side + " earlier score report changed")
        if _binding(scoring_inputs, sdk, hybrid) != bound:
            receipt["qualification"] = _reject("toolchain_or_scorer_input_mutation")
        else:
            comparison = compare_scores.compare(score_windows["base"], score_windows["candidate"])
            receipt["comparison"] = comparison
            reasons = []
            if comparison["missing"]:
                reasons.append("missing_windows")
            if comparison["added"]:
                reasons.append("added_windows")
            if comparison["resized"]:
                reasons.append("resized_windows")
            if comparison["normalized_losses"]:
                reasons.append("normalized_match_regression")
            if comparison["raw_losses"]:
                reasons.append("raw_match_regression")
            receipt["qualification"] = {
                "accepted": not reasons,
                "rejection_reasons": reasons,
                "base_source_sha256": sources["base"]["sha256"],
                "candidate_source_sha256": sources["candidate"]["sha256"],
                "same_original_evidence": True,
                "source_inputs_unchanged": True,
                "toolchain_and_scorer_inputs_unchanged": True,
            }
        retain_artifacts(receipt, output)
        publish_json(receipt_path, receipt)
        return receipt
    except Exception as error:
        receipt["qualification"] = _reject("infrastructure_failure", str(error))
        receipt["error_type"] = type(error).__name__
        retain_artifacts(receipt, output)
        publish_json(receipt_path, receipt)
        return receipt
    finally:
        fastbuild.SDK = saved_fastbuild_sdk
        fastbuild.LOCKDIR = saved_fastbuild_lockdir
        fastbuild.RECIPES["identity"] = saved_recipe
        official_score.BASE = saved_score_base
        if saved_objdump is missing:
            official_score.__dict__.pop("OBJDUMP", None)
        else:
            official_score.OBJDUMP = saved_objdump
