"""Verify the 8099031-source claim build and signed offline differential."""

import gzip
import hashlib
import json
from pathlib import Path

import pump_claim_token_incentives_differential as diff
import pump_claim_token_incentives_verify as historical


def check(condition, message):
    """Fail closed under optimized Python, where assert statements vanish."""
    if not condition:
        raise AssertionError(message)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "repro/pump/claim-token-incentives-8099"
SOURCE_BASE = "80990317bd9c0363e071646b892490886d7bf946"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads(gzip.decompress((PACKAGE / "differential.json.gz").read_bytes()))
    first = json.loads((PACKAGE / "build-comparison.json").read_text())
    second = json.loads((PACKAGE / "second-build-comparison.json").read_text())
    reproducibility = json.loads((PACKAGE / "build-reproducibility.json").read_text())
    candidate = PACKAGE / "candidate.so"
    check(receipt["baseline_commit"] == reproducibility["source_base_commit"] == SOURCE_BASE, "claim verification failed: receipt['baseline_commit'] == reproducibility['source_base_commit'] ==")
    check(receipt["candidate_sha256"] == reproducibility["candidate_sha256"] == sha(candidate), "claim verification failed: receipt['candidate_sha256'] == reproducibility['candidate_sha256'] == ")
    check(receipt["candidate_path"] == str(candidate.relative_to(ROOT)), "claim verification failed: receipt['candidate_path'] == str(candidate.relative_to(ROOT))")
    check(receipt["build_receipt_sha256"] == sha(PACKAGE / "build-comparison.json"), "claim verification failed: receipt['build_receipt_sha256'] == sha(PACKAGE / 'build-comparison.jso")
    check(receipt["second_build_comparison_sha256"] == sha(PACKAGE / "second-build-comparison.json"), "claim verification failed: receipt['second_build_comparison_sha256'] == sha(PACKAGE / 'second-bui")
    check(reproducibility["build_comparison_sha256"] == [
        receipt["build_receipt_sha256"], receipt["second_build_comparison_sha256"]], "claim verification failed: reproducibility['build_comparison_sha256'] == [")
    check(first["source_sha256"] == second["source_sha256"] == reproducibility["source_sha256"], "claim verification failed: first['source_sha256'] == second['source_sha256'] == reproducibility['")
    check(first["selected_toolchain"] == second["selected_toolchain"] == "v1.44", "claim verification failed: first['selected_toolchain'] == second['selected_toolchain'] == 'v1.44'")
    check(first["comparison"]["candidate_sha256"] == second["comparison"]["candidate_sha256"] == sha(candidate), "claim verification failed: first['comparison']['candidate_sha256'] == second['comparison']['candi")
    check(not first["comparison"]["full_byte_equality"] and reproducibility["builds_identical"], "claim verification failed: not first['comparison']['full_byte_equality'] and reproducibility['bui")
    check(receipt["source_sha256"] == {
        **first["source_sha256"],
        "scripts/pump_claim_token_incentives_differential.py": sha(Path(diff.__file__)),
    }, "claim verification failed: receipt['source_sha256'] == {")
    check(all(sha(ROOT / path) == digest for path, digest in receipt["source_sha256"].items()), "claim verification failed: all(sha(ROOT / path) == digest for path, digest in receipt['source_sha")
    check(receipt["script_sha256"] == sha(Path(diff.__file__)), "claim verification failed: receipt['script_sha256'] == sha(Path(diff.__file__))")
    for attempt_name in ("build-attempt.json", "second-build-attempt.json"):
        attempt = json.loads((PACKAGE / attempt_name).read_text())
        check(attempt["returncode"] == 0 and attempt["source_unchanged"], "claim verification failed: attempt['returncode'] == 0 and attempt['source_unchanged']")
        check(attempt["source_sha256"] == first["source_sha256"], "claim verification failed: attempt['source_sha256'] == first['source_sha256']")
    for report, log_name in ((first, "build.log.gz"), (second, "second-build.log.gz")):
        check(hashlib.sha256(gzip.decompress((PACKAGE / log_name).read_bytes())).hexdigest() == report["build_log_sha256"], "claim verification failed: hashlib.sha256(gzip.decompress((PACKAGE / log_name).read_bytes())).hex")
    check(receipt["target_sha256"] == sha(diff.ORIGINAL), "claim verification failed: receipt['target_sha256'] == sha(diff.ORIGINAL)")
    check(receipt["idl_sha256"] == sha(diff.IDL), "claim verification failed: receipt['idl_sha256'] == sha(diff.IDL)")
    check(receipt["fixture_sha256"] == sha(diff.FIXTURE), "claim verification failed: receipt['fixture_sha256'] == sha(diff.FIXTURE)")
    check(receipt["dependency_sha256"] == {
        name: sha(ROOT / f"evidence/dependencies/{name}/deployed.so")
        for name in ("spl_token_2022", "associated_token")}, "claim verification failed: receipt['dependency_sha256'] == {")
    regressions = json.loads((PACKAGE / "regression-summary.json").read_text())
    check(regressions["candidate_sha256"] == sha(candidate), "claim verification failed: regressions['candidate_sha256'] == sha(candidate)")
    quote = json.loads(gzip.decompress((PACKAGE / "quote-control-regression.json.gz").read_bytes()))
    curve = json.loads(gzip.decompress((PACKAGE / "multi-hop-regression.json.gz").read_bytes()))
    check(regressions["quote_control"]["receipt_sha256"] == sha(PACKAGE / "quote-control-regression.json.gz"), "claim verification failed: regressions['quote_control']['receipt_sha256'] == sha(PACKAGE / 'quote")
    check(regressions["multi_hop_curve"]["receipt_sha256"] == sha(PACKAGE / "multi-hop-regression.json.gz"), "claim verification failed: regressions['multi_hop_curve']['receipt_sha256'] == sha(PACKAGE / 'mul")
    check(type(quote.get("cases")) is int and type(quote.get("mismatches")) is int
              and isinstance(quote.get("results"), list) and all(isinstance(row, dict) for row in quote["results"])
              and len(quote["results"]) == quote["cases"] == 507
          and quote["mismatches"] == 0
          and not any(row.get("matches") is not True for row in quote["results"]),
          "claim verification failed: quote['cases'] == 507 and quote['mismatches'] == 0")
    check(isinstance(quote.get("bound_inputs_sha256"), dict) and quote["bound_inputs_sha256"],
          "claim verification failed: quote-control receipt binds no input")
    check(all(sha(ROOT / path) == digest for path, digest in quote["bound_inputs_sha256"].items()), "claim verification failed: all(sha(ROOT / path) == digest for path, digest in quote['bound_inputs")
    check(type(curve.get("case_count")) is int and type(curve.get("passed")) is int
              and isinstance(curve.get("cases"), list) and all(isinstance(row, dict) for row in curve["cases"])
              and len(curve["cases"]) == curve["case_count"] == curve["passed"] == 56
          and not any(row.get("mismatches") != [] for row in curve["cases"]),
          "claim verification failed: curve['case_count'] == curve['passed'] == 56")
    check(curve["candidate_sha256"] == sha(candidate), "claim verification failed: curve['candidate_sha256'] == sha(candidate)")

    idl = json.loads(diff.IDL.read_text(encoding="utf-8"))
    event_discriminator = bytes(next(item for item in idl["events"]
        if item["name"] == "ClaimTokenIncentivesEvent")["discriminator"])
    _, keys, _, user_volume, global_ata = diff.fixture_data()
    keys["user_ata"] = keys["user_base"]
    keys["global_ata"] = global_ata
    check(user_volume == keys["volume"], "claim verification failed: user_volume == keys['volume']")
    check(len(receipt["cases"]) == len(diff.CASES) == 60, "claim verification failed: len(receipt['cases']) == len(diff.CASES) == 60")
    successes = events = 0
    for row, case in zip(receipt["cases"], diff.CASES):
        name = case["name"]
        check(row["case"] == case, "claim verification failed: row['case'] == case")
        target = diff.run_case(diff.ORIGINAL, case)
        current = diff.run_case(candidate, case)
        check(row["target"] == target and row["candidate"] == current, "claim verification failed: row['target'] == target and row['candidate'] == current")
        check(not row["differences"], "claim verification failed: not row['differences']")
        historical.assert_signature(target)
        historical.assert_signature(current)
        for field in ("error", "before", "after", "event_data_base64", "inner",
                      "signature", "transaction_base64"):
            check(target[field] == current[field], (name, field))
        check(target["error_code"] == historical.EXPECTED_ERRORS.get(name), "claim verification failed: target['error_code'] == historical.EXPECTED_ERRORS.get(name)")
        if target["success"]:
            successes += 1
            if target["event_data_base64"]:
                events += 1
                historical.assert_event_and_cpis(target, event_discriminator, keys)
        else:
            check(target["before"]["user_volume"] == target["after"]["user_volume"], "claim verification failed: target['before']['user_volume'] == target['after']['user_volume']")
            check(not target["event_data_base64"], "claim verification failed: not target['event_data_base64']")
    check(receipt["summary"] == {"cases": 60, "matched": 60, "target_successes": 48}, "claim verification failed: receipt['summary'] == {'cases': 60, 'matched': 60, 'target_successes':")
    check(successes == 48 and events == 31, "claim verification failed: successes == 48 and events == 31")
    print(json.dumps({"verified": True, "signed_cases": 60, "matches": 60,
                      "successes": successes, "payout_events": events,
                      "candidate_sha256": sha(candidate)}))


if __name__ == "__main__":
    main()
