#!/usr/bin/env python3
"""Independently recompute a fresh-control receipt's acceptance decision."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import types

if "_SOURCE_CONTEXT" not in globals():
    _path = Path(__file__).resolve().with_name("fresh_control_inputs.py")
    _raw = _path.read_bytes()
    _admission = types.ModuleType("_fresh_control_admission")
    _admission.__file__ = str(_path)
    _admission.__dict__["_ADMITTED_SOURCE_BYTES"] = _raw
    exec(compile(_raw, str(_path), "exec", dont_inherit=True), _admission.__dict__)
    _SOURCE_CONTEXT = _admission.load_context()
compare_scores = _SOURCE_CONTEXT.load("compare_scores")
fastbuild = _SOURCE_CONTEXT.load("fastbuild")
fresh_control = _SOURCE_CONTEXT.load("fresh_control")
snapshot = _SOURCE_CONTEXT.load("source_inputs").snapshot


def load_document(path: Path, *, raw: bytes | None = None) -> dict:
    def reject_constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    document = json.loads(path.read_bytes() if raw is None else raw,
                          object_pairs_hook=compare_scores.unique_fields,
                          parse_constant=reject_constant)
    if not isinstance(document, dict):
        raise ValueError(f"{path.name} must contain an object")
    return document


def expected_reasons(comparison: dict) -> list[str]:
    checks = (
        ("missing", "missing_windows"),
        ("added", "added_windows"),
        ("resized", "resized_windows"),
        ("normalized_losses", "normalized_match_regression"),
        ("raw_losses", "raw_match_regression"),
    )
    return [reason for field, reason in checks if comparison[field]]


def source_matches(path: Path, admitted: dict) -> bool:
    try:
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            return False
        return fresh_control.same_json(snapshot(path), admitted)
    except (OSError, ValueError):
        return False


def find_sources(root: Path, receipt: dict, base_source: Path | None,
                 candidate_source: Path | None) -> dict[str, Path]:
    result = {}
    supplied = {"base": base_source, "candidate": candidate_source}
    for side, path in supplied.items():
        if path is not None:
            if Path(path).is_symlink() or (hasattr(Path(path), "is_junction") and Path(path).is_junction()):
                raise ValueError("linked source snapshots are unsupported")
            path = Path(path).resolve(strict=True)
            if not source_matches(path, receipt["sources"][side]):
                raise ValueError(f"{side} source does not match admitted source receipt")
            result[side] = path

    integration = root.parent
    if "candidate" not in result:
        candidate = integration / "src"
        if source_matches(candidate, receipt["sources"]["candidate"]):
            result["candidate"] = candidate
    if "base" not in result:
        inputs = integration / "inputs"
        if inputs.is_symlink() or (hasattr(inputs, "is_junction") and inputs.is_junction()):
            raise ValueError("linked source inventory is unsupported")
        matches = [path for path in sorted(inputs.iterdir())
                   if path.is_dir() and source_matches(path, receipt["sources"]["base"])] \
            if inputs.is_dir() else []
        if len(matches) == 1:
            result["base"] = matches[0]
        elif len(matches) > 1:
            # Identical owned snapshots are equivalent, but select deterministically.
            result["base"] = matches[0]
    missing = {"base", "candidate"} - result.keys()
    if missing:
        raise ValueError("cannot locate admitted source snapshot: " + ", ".join(sorted(missing)))
    return result


def verify(root: Path, *, sdk: Path | None = None, hybrid: Path | None = None,
           base_source: Path | None = None, candidate_source: Path | None = None) -> dict:
    if Path(root).is_symlink() or (hasattr(Path(root), "is_junction") and Path(root).is_junction()):
        raise ValueError("linked receipt root is unsupported")
    root = Path(root).resolve(strict=True)
    receipt_path = root / "receipt.json"
    admitted_receipt = receipt_path.read_bytes()
    admitted_receipt_sha256 = hashlib.sha256(admitted_receipt).hexdigest()
    receipt = load_document(receipt_path, raw=admitted_receipt)
    if receipt_path.read_bytes() != admitted_receipt:
        raise ValueError("receipt changed during parsing")
    if receipt.get("schema") != "pump-fresh-control-v1" or receipt.get("mode") != "fresh_control":
        raise ValueError("unsupported fresh-control receipt schema")
    if (not fresh_control.same_json(receipt.get("build_order"), ["base", "candidate"])
            or receipt.get("cold_targets") is not True
            or receipt.get("isolated_workspaces") is not True):
        raise ValueError("fresh isolated build claims are not admissible")

    retained = fresh_control.artifact_inventory(root)
    retained.pop("receipt.json", None)
    if not fresh_control.same_json(receipt.get("artifacts"), retained):
        raise ValueError("retained artifact inventory does not match receipt")

    sdk = Path(sdk or fastbuild.SDK).resolve()
    hybrid = Path(
        hybrid
        or Path(os.environ.get("PUMP_RECON_HOME", str(Path.home() / ".cache/pumpfun-reconstruction")))
        / "toolchains/hybrid144"
    ).resolve()
    actual_binding = fresh_control._binding(root / "scoring-inputs", sdk, hybrid)
    if not fresh_control.same_json(receipt.get("provenance"), actual_binding):
        raise ValueError("toolchain, scorer, or captured evidence provenance mismatch")

    sources = find_sources(root, receipt, base_source, candidate_source)
    scores = {}
    for side in ("base", "candidate"):
        build = receipt.get("builds", {}).get(side)
        if type(build) is not dict:
            raise ValueError(f"{side} build is not admissible")
        fresh_control.valid_build(build)
        if build.get("source_sha256") != receipt["sources"][side]["sha256"]:
            raise ValueError(f"{side} build source digest mismatch")
        for artifact, field in (("unstripped.so", "unstripped_sha256"),
                                ("candidate.so", "candidate_sha256")):
            image = root / f"{side}-build" / artifact
            if not image.is_file() or fresh_control.sha256_file(image) != build.get(field):
                raise ValueError(f"{side} {artifact} digest mismatch")

        score_path = root / f"{side}-score.json"
        score_document = load_document(score_path)
        if score_document.get("candidate_sha256") != build["unstripped_sha256"]:
            raise ValueError(f"{side} score is bound to the wrong image")
        raw_windows = {int(start): row for start, row in score_document.get("windows", {}).items()}
        summary = fresh_control.score_summary(raw_windows)
        if not fresh_control.same_json(score_document.get("summary"), summary):
            raise ValueError(f"{side} score summary does not match its windows")
        report_sha256 = fresh_control.sha256_file(score_path)
        expected_score = {
            "image_sha256": build["unstripped_sha256"],
            **summary,
            "report_sha256": report_sha256,
        }
        if not fresh_control.same_json(receipt.get("scores", {}).get(side), expected_score):
            raise ValueError(f"{side} receipt score summary or digest mismatch")
        scores[side] = compare_scores.load_report(score_path)
        # A saved hash binds supplied bytes, not the truth of match claims.
        # Independently score the actual admitted ELF with the frozen official
        # source graph and the retained captured evidence on both sides.
        scorer = fresh_control.official_score
        previous_base = scorer.BASE
        try:
            scorer.BASE = root / "scoring-inputs"
            actual_windows, actual_image = scorer.score_with_hash(
                root / f"{side}-build/unstripped.so", build["unstripped_sha256"])
        finally:
            scorer.BASE = previous_base
        expected_rows = {str(start): row for start, row in sorted(actual_windows.items())}
        if (actual_image != build["unstripped_sha256"]
                or not fresh_control.same_json(score_document.get("windows"), expected_rows)
                or not fresh_control.same_json(summary, fresh_control.score_summary(actual_windows))):
            raise ValueError(f"{side} score differs from actual ELF rescoring")

    comparison = compare_scores.compare(scores["base"], scores["candidate"])
    if not fresh_control.same_json(receipt.get("comparison"), comparison):
        raise ValueError("recorded comparison differs from independent recomputation")
    reasons = expected_reasons(comparison)
    qualification = receipt.get("qualification")
    if not isinstance(qualification, dict):
        raise ValueError("missing qualification")
    if qualification.get("accepted") is not (not reasons):
        raise ValueError("producer acceptance boolean differs from recomputation")
    if not fresh_control.same_json(qualification.get("rejection_reasons"), reasons):
        raise ValueError("producer rejection reasons differ from recomputation")
    if qualification.get("base_source_sha256") != receipt["sources"]["base"]["sha256"] \
            or qualification.get("candidate_source_sha256") \
            != receipt["sources"]["candidate"]["sha256"]:
        raise ValueError("qualification source binding mismatch")
    if not all(qualification.get(field) is True for field in
               ("same_original_evidence", "source_inputs_unchanged",
                "toolchain_and_scorer_inputs_unchanged")):
        raise ValueError("qualification does not attest immutable inputs")
    _SOURCE_CONTEXT.recheck()
    if not fresh_control.same_json(actual_binding, fresh_control._binding(root / "scoring-inputs", sdk, hybrid)):
        raise ValueError("inputs changed during independent rescoring")
    for side in ("base", "candidate"):
        if not source_matches(sources[side], receipt["sources"][side]):
            raise ValueError(side + " source changed during verification")
    final_inventory = fresh_control.artifact_inventory(root)
    final_inventory.pop("receipt.json", None)
    if not fresh_control.same_json(retained, final_inventory):
        raise ValueError("retained artifacts changed during verification")
    if receipt_path.read_bytes() != admitted_receipt:
        raise ValueError("receipt changed during verification")

    return {
        "accepted": not reasons,
        "artifact_count": len(retained),
        "base_source": str(sources["base"]),
        "candidate_source": str(sources["candidate"]),
        "comparison": comparison,
        "receipt_sha256": admitted_receipt_sha256,
        "schema": "pump-fresh-control-verification-v1",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="directory containing receipt.json")
    parser.add_argument("--sdk", type=Path, default=fastbuild.SDK)
    parser.add_argument("--hybrid", type=Path,
                        default=Path(os.environ.get("PUMP_RECON_HOME", str(Path.home() / ".cache/pumpfun-reconstruction"))) / "toolchains/hybrid144")
    parser.add_argument("--base-source", type=Path)
    parser.add_argument("--candidate-source", type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify(args.root, sdk=args.sdk, hybrid=args.hybrid,
                        base_source=args.base_source, candidate_source=args.candidate_source)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"fresh-control receipt invalid: {error}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
