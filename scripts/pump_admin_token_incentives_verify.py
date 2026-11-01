"""Independent signed offline replay of Pump incentive scheduler evidence."""

import argparse
import base64
import gzip
import json
from pathlib import Path

import pump_admin_token_incentives_differential as diff


def check(condition, message):
    """Fail closed under optimized Python, where assert statements vanish."""
    if not condition:
        raise AssertionError(message)


FINANCIAL_ACCOUNTS = (
    "global", "global_volume_accumulator", "mint",
    "global_incentive_token_account", "canonical_global",
    "canonical_volume", "canonical_vault",
)


def main(receipt_path=diff.OUTPUT, candidate_path=diff.CANDIDATE,
         build_path=diff.BUILD, expected_baseline="4ffe8bd88761059693e481ae972443c10204f7af"):
    receipt_path, candidate_path, build_path = map(Path,
                                                   (receipt_path, candidate_path, build_path))
    encoded = receipt_path.read_bytes()
    receipt = json.loads(gzip.decompress(encoded) if receipt_path.suffix == ".gz"
                         else encoded)
    check(receipt["baseline_commit"] == expected_baseline, "receipt baseline commit differs")
    check(receipt["target_sha256"] == diff.sha(diff.TARGET), "receipt target hash differs")
    check(receipt["candidate_sha256"] == diff.sha(candidate_path), "receipt candidate hash differs")
    check(receipt["build_comparison_sha256"] == diff.sha(build_path), "receipt build comparison hash differs")
    build = json.loads(build_path.read_text())
    check(build["selected_toolchain"] == "v1.44", "build toolchain must be v1.44")
    check(build["comparison"]["candidate_sha256"] == receipt["candidate_sha256"], "build candidate hash differs from receipt")
    # all() over an empty map is vacuously true; a comparison must name the
    # sources it was built from before their hashes can bind anything.
    check(isinstance(build.get("source_sha256"), dict) and build["source_sha256"],
          "build comparison binds no source")
    check(all(checksum == diff.sha(diff.ROOT / path)
               for path, checksum in build["source_sha256"].items()), "build source hash differs")
    check(build["build_log_sha256"] == diff.sha(gzip.decompress(
        (build_path.parent / "build.log.gz").read_bytes())), "build log hash differs")
    if receipt.get("second_clean_build") is not None:
        second = receipt["second_clean_build"]
        second_path = Path(second["comparison_path"])
        if not second_path.is_absolute():
            second_path = diff.ROOT / second_path
        check(diff.sha(second_path) == second["comparison_sha256"], "second clean build hash differs")
        first_build = build
        second_build = json.loads(second_path.read_text())
        check(first_build["source_sha256"] == second_build["source_sha256"], "second build source hashes differ")
        check(first_build["selected_toolchain"] == second_build["selected_toolchain"], "second build toolchain differs")
        check(first_build["comparison"]["candidate_sha256"] == second_build["comparison"]["candidate_sha256"], "second build candidate hash differs")
        check(second_build["build_log_sha256"] == diff.sha(gzip.decompress(
            (second_path.parent / "second-build.log.gz").read_bytes())), "second build log hash differs")
    check(receipt["idl_sha256"] == diff.sha(diff.IDL), "receipt IDL hash differs")
    check(receipt["global_snapshot_sha256"] == diff.sha(diff.SNAPSHOT), "receipt snapshot hash differs")
    check(isinstance(receipt.get("source_sha256"), dict) and receipt["source_sha256"],
          "receipt binds no source")
    for path, checksum in receipt["source_sha256"].items():
        check(checksum == diff.sha(diff.ROOT / path), path)
    for name, checksum in receipt["dependency_sha256"].items():
        check(checksum == diff.sha(diff.ROOT / "evidence/dependencies" / name / "deployed.so"), "dependency hash differs")
    if expected_baseline == "80990317bd9c0363e071646b892490886d7bf946":
        package = build_path.parent
        reproducibility = json.loads((package / "build-reproducibility.json").read_text())
        check(reproducibility["source_base_commit"] == expected_baseline, "reproducibility baseline differs")
        check(reproducibility["candidate_sha256"] == receipt["candidate_sha256"], "reproducibility candidate hash differs")
        check(reproducibility["builds_identical"] and not reproducibility["deployed_byte_match"], "reproducibility build identity differs")
        check(reproducibility["source_sha256"] == build["source_sha256"], "reproducibility source hashes differ")
        for filename in ("build-attempt.json", "second-build-attempt.json"):
            attempt = json.loads((package / filename).read_text())
            check(attempt["returncode"] == 0 and attempt["source_unchanged"], "build attempt was not a clean success")
            check(attempt["source_sha256"] == build["source_sha256"], "build attempt source hashes differ")
        regression = json.loads((package / "regression-summary.json").read_text())
        quote_file = package / "quote-control-regression.json.gz"
        curve_file = package / "multi-hop-regression.json.gz"
        quote = json.loads(gzip.decompress(quote_file.read_bytes()))
        curve = json.loads(gzip.decompress(curve_file.read_bytes()))
        check(regression["candidate_sha256"] == receipt["candidate_sha256"], "regression candidate hash differs")
        check(regression["quote_control"]["receipt_sha256"] == diff.sha(quote_file), "quote regression receipt hash differs")
        check(regression["multi_hop_curve"]["receipt_sha256"] == diff.sha(curve_file), "curve regression receipt hash differs")
        # The header alone says what the retained rows must say; a receipt whose
        # rows disagree with it is refused rather than published as clean.
        check(type(quote.get("cases")) is int and type(quote.get("mismatches")) is int
              and isinstance(quote.get("results"), list) and all(isinstance(row, dict) for row in quote["results"])
              and len(quote["results"]) == quote["cases"] == 507
              and quote["mismatches"] == 0
              and not any(row.get("matches") is not True for row in quote["results"]),
              "quote regression cases/mismatches differ")
        check(isinstance(quote.get("bound_inputs_sha256"), dict) and quote["bound_inputs_sha256"],
              "quote regression binds no input")
        check(all(checksum == diff.sha(diff.ROOT / path)
                   for path, checksum in quote["bound_inputs_sha256"].items()), "quote bound input hash differs")
        check(type(curve.get("case_count")) is int and type(curve.get("passed")) is int
              and isinstance(curve.get("cases"), list) and all(isinstance(row, dict) for row in curve["cases"])
              and len(curve["cases"]) == curve["case_count"] == curve["passed"] == 56
              and not any(row.get("mismatches") != [] for row in curve["cases"]),
              "curve regression case count differs")
        check(curve["candidate_sha256"] == receipt["candidate_sha256"], "curve regression candidate hash differs")
    idl = json.loads(diff.IDL.read_text(encoding="utf-8"))
    item = next(item for item in idl["instructions"]
                if item["name"] == "admin_update_token_incentives")
    event_disc = bytes(next(event for event in idl["events"]
                            if event["name"] == "AdminUpdateTokenIncentivesEvent")["discriminator"])
    global_fixture = next(row for row in json.loads(diff.SNAPSHOT.read_text())["accounts"]
                          if row["program_name"] == "pump")
    check(global_fixture["data_sha256"] == receipt["global_snapshot_account_data_sha256"], "snapshot account data hash differs")
    check(len(receipt["cases"]) == len(diff.variants()) == receipt["summary"]["cases"] == 98, "case count must be 98")
    successes = 0
    for row, (name, variant) in zip(receipt["cases"], diff.variants()):
        check(row["case"] == name and row["variant"] == variant, "case/variant identity differs")
        check(row["match"] and not row["differing_fields"], "case did not match")
        for binary, stored in ((diff.TARGET, row["target"]),
                               (candidate_path, row["candidate"])):
            observed = diff.run(binary, item, variant, global_fixture)
            check(observed == stored, (name, binary))
            check(observed["signature_verified"], "replayed signature was not verified")
        target, candidate = row["target"], row["candidate"]
        for field in ("error", "error_code", "before", "after",
                      "signed_transaction_base64", "signature", "events",
                      "state_debug_logs", "inner_instructions", "return_data_hex",
                      "args", "keys"):
            check(target[field] == candidate[field], (name, field))
        if target["error"] is None:
            successes += 1
            check(len(target["events"]) == 1, "success case must emit exactly one event")
            check(len(target["state_debug_logs"]) == 1, "success case must emit exactly one debug log")
            event = base64.b64decode(target["events"][0])
            check(len(event) == 88 and event[:8] == event_disc, "event length/discriminator differs")
            check(event[40:72] == bytes(diff.MINT), "event mint differs")
            check(bytes.fromhex(target["inner_instructions"][-1]["data_hex"])[8:] == event, "inner instruction event bytes differ")
        else:
            check(not target["state_debug_logs"], "error case must not emit debug logs")
            # The wrong self-CPI program errors after emit! wrote its log
            # event; transaction rollback still preserves every account.
            if name == "wrong_program":
                check(len(target["events"]) == 1 and not target["inner_instructions"], "wrong-program case must emit exactly one event and no inner instructions")
            else:
                check(not target["events"], "error case must not emit events")
            for account in FINANCIAL_ACCOUNTS:
                check(target["before"][account] == target["after"][account], (name, account))
    check(successes == receipt["summary"]["target_successes"] == 43, "success count must be 43")
    check(receipt["summary"]["matched"] == 98, "matched count must be 98")
    print(json.dumps({"verified": True, "signed_cases": len(receipt["cases"]),
                      "successes": successes, "rollbacks": len(receipt["cases"]) - successes,
                      "candidate_sha256": receipt["candidate_sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=diff.OUTPUT)
    parser.add_argument("--candidate", type=Path, default=diff.CANDIDATE)
    parser.add_argument("--build-comparison", type=Path, default=diff.BUILD)
    parser.add_argument("--expected-baseline", default="4ffe8bd88761059693e481ae972443c10204f7af")
    args = parser.parse_args()
    main(args.receipt, args.candidate, args.build_comparison, args.expected_baseline)
