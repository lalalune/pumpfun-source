"""Re-execute and verify the signed Pump token-incentive claim differential."""

import argparse
import base64
import gzip
import json
import struct
from pathlib import Path

from solders.transaction import Transaction

import pump_claim_token_incentives_differential as diff


def check(condition, message):
    """Fail closed under optimized Python, where assert statements vanish."""
    if not condition:
        raise AssertionError(message)


LOG = diff.ROOT / "repro/pump/claim-token-incentives/build.log.gz"
SECOND_BUILD = diff.ROOT / "repro/pump/claim-token-incentives/build-second-comparison.json"
SECOND_LOG = diff.ROOT / "repro/pump/claim-token-incentives/build-second.log.gz"
BUILD_REPRO = diff.ROOT / "repro/pump/claim-token-incentives/build-reproducibility.json"
INHERITED = diff.ROOT / "repro/pump/claim-token-incentives/inherited-regressions.json"
EXPECTED_ERRORS = {
    "vault_underfunded": 1,
    "wrong_global_owner": 3007,
    "wrong_user_owner": 3007,
    "wrong_global_pda": 2006,
    "wrong_user_pda": 2006,
    "wrong_mint": 3007,
    "wrong_token_program": 3008,
    "wrong_event_authority": 2006,
    "wrong_program_account": 3008,
    "read_only_user_volume": 2000,
}
EVENT_CPI_DISCRIMINATOR = bytes.fromhex("e445a52e51cb9a1d")


def account_bytes(row):
    data = base64.b64decode(row["data_base64"])
    check(diff.sha(data) == row["data_sha256"], "claim verification failed: diff.sha(data) == row['data_sha256']")
    return data


def token_amount(row):
    return struct.unpack_from("<Q", account_bytes(row), 64)[0]


def assert_signature(row):
    tx = Transaction.from_bytes(base64.b64decode(row["transaction_base64"]))
    check((tx.signatures and all(tx.verify_with_results())), "claim verification failed: (tx.signatures and all(tx.verify_with_results()))")
    check(str(tx.signatures[0]) == row["signature"], "claim verification failed: str(tx.signatures[0]) == row['signature']")


def assert_event_and_cpis(row, event_discriminator, keys):
    before, after = row["before"], row["after"]
    check(len(row["event_data_base64"]) == 1 and len(row["inner"]) == 2, "claim verification failed: len(row['event_data_base64']) == 1 and len(row['inner']) == 2")
    event = base64.b64decode(row["event_data_base64"][0])
    check(len(event) == 104 and event[:8] == event_discriminator, "claim verification failed: len(event) == 104 and event[:8] == event_discriminator")
    check(event[8:40] == bytes(keys["user"]), "claim verification failed: event[8:40] == bytes(keys['user'])")
    check(event[40:72] == bytes(keys["mint"]), "claim verification failed: event[40:72] == bytes(keys['mint'])")
    amount, timestamp, claimed, volume = struct.unpack_from("<QqQQ", event, 72)
    check(amount > 0 and timestamp == row["case"].get("now", 10), "claim verification failed: amount > 0 and timestamp == row['case'].get('now', 10)")
    check(claimed == row["user_after"][2] and volume == row["user_after"][3], "claim verification failed: claimed == row['user_after'][2] and volume == row['user_after'][3]")
    check(token_amount(after["user_ata"]) - token_amount(before["user_ata"]) == amount, "claim verification failed: token_amount(after['user_ata']) - token_amount(before['user_ata']) == ")
    check(token_amount(before["global_ata"]) - token_amount(after["global_ata"]) == amount, "claim verification failed: token_amount(before['global_ata']) - token_amount(after['global_ata'])")
    transfer, event_cpi = row["inner"]
    check(transfer["program"] == str(diff.TOKEN), "claim verification failed: transfer['program'] == str(diff.TOKEN)")
    check(transfer["accounts"] == [str(keys["global_ata"]), str(keys["mint"]),
                                     str(keys["user_ata"]), str(diff.GLOBAL_VOLUME)], "claim verification failed: transfer['accounts'] == [str(keys['global_ata']), str(keys['mint']),")
    check(bytes.fromhex(transfer["data_hex"]) == bytes([12]) + \
           struct.pack("<Q", amount) + bytes([6]), "claim verification failed: bytes.fromhex(transfer['data_hex']) == bytes([12]) + ...")
    check(event_cpi["program"] == str(diff.PROGRAM), "claim verification failed: event_cpi['program'] == str(diff.PROGRAM)")
    check(event_cpi["accounts"] == [str(diff.EVENT_AUTHORITY)], "claim verification failed: event_cpi['accounts'] == [str(diff.EVENT_AUTHORITY)]")
    check(bytes.fromhex(event_cpi["data_hex"]) == EVENT_CPI_DISCRIMINATOR + event, "claim verification failed: bytes.fromhex(event_cpi['data_hex']) == EVENT_CPI_DISCRIMINATOR + even")
    check(any("Instruction: TransferChecked" in line
               for line in row["relevant_logs"]), "claim verification failed: any('Instruction: TransferChecked' in line")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, default=diff.OUT)
    args = parser.parse_args()
    report = json.loads(args.receipt.read_text())
    build = json.loads(diff.BUILD.read_text())
    second_build = json.loads(SECOND_BUILD.read_text())
    repro = json.loads(BUILD_REPRO.read_text())
    check(report["baseline_commit"] == "4ffe8bd88761059693e481ae972443c10204f7af", "claim verification failed: report['baseline_commit'] == '4ffe8bd88761059693e481ae972443c10204f7af")
    check(report["target_sha256"] == diff.sha(diff.ORIGINAL.read_bytes()), "claim verification failed: report['target_sha256'] == diff.sha(diff.ORIGINAL.read_bytes())")
    check(report["candidate_sha256"] == diff.sha(args.candidate.read_bytes()), "claim verification failed: report['candidate_sha256'] == diff.sha(args.candidate.read_bytes())")
    check(report["build_receipt_sha256"] == diff.sha(diff.BUILD.read_bytes()), "claim verification failed: report['build_receipt_sha256'] == diff.sha(diff.BUILD.read_bytes())")
    check(report["idl_sha256"] == diff.sha(diff.IDL.read_bytes()), "claim verification failed: report['idl_sha256'] == diff.sha(diff.IDL.read_bytes())")
    check(report["fixture_sha256"] == diff.sha(diff.FIXTURE.read_bytes()), "claim verification failed: report['fixture_sha256'] == diff.sha(diff.FIXTURE.read_bytes())")
    check(report["script_sha256"] == diff.sha(Path(diff.__file__).read_bytes()), "claim verification failed: report['script_sha256'] == diff.sha(Path(diff.__file__).read_bytes())")
    check(report["dependency_sha256"] == {name: diff.sha((diff.ROOT /
        f"evidence/dependencies/{name}/deployed.so").read_bytes())
        for name in ("spl_token_2022", "associated_token")}, "claim verification failed: report['dependency_sha256'] == {name: diff.sha((diff.ROOT /")
    # all() over an empty map is vacuously true, and the equality check below
    # accepts {} == {}; the evidence must name the sources it binds.
    check(isinstance(report.get("source_sha256"), dict) and report["source_sha256"],
          "claim verification failed: report binds no source")
    check(isinstance(build.get("source_sha256"), dict) and build["source_sha256"],
          "claim verification failed: build comparison binds no source")
    check(all(diff.sha((diff.ROOT / path).read_bytes()) == expected
               for path, expected in report["source_sha256"].items()), "claim verification failed: all(diff.sha((diff.ROOT / path).read_bytes()) == expected")
    check(all(diff.sha((diff.ROOT / path).read_bytes()) == expected
               for path, expected in build["source_sha256"].items()), "claim verification failed: all(diff.sha((diff.ROOT / path).read_bytes()) == expected")
    check(diff.sha(gzip.decompress(LOG.read_bytes())) == build["build_log_sha256"], "claim verification failed: diff.sha(gzip.decompress(LOG.read_bytes())) == build['build_log_sha256")
    check(diff.sha(gzip.decompress(SECOND_LOG.read_bytes())) == second_build["build_log_sha256"], "claim verification failed: diff.sha(gzip.decompress(SECOND_LOG.read_bytes())) == second_build['bu")
    check(repro["build_receipt_sha256"] == [diff.sha(diff.BUILD.read_bytes()),
                                              diff.sha(SECOND_BUILD.read_bytes())], "claim verification failed: repro['build_receipt_sha256'] == [diff.sha(diff.BUILD.read_bytes()),")
    check(repro["source_sha256"] == build["source_sha256"] == second_build["source_sha256"], "claim verification failed: repro['source_sha256'] == build['source_sha256'] == second_build['sour")
    check(repro["candidate_sha256"] == [report["candidate_sha256"]] * 2, "claim verification failed: repro['candidate_sha256'] == [report['candidate_sha256']] * 2")
    check(repro["builds_identical"] and not repro["deployed_byte_match"], "claim verification failed: repro['builds_identical'] and not repro['deployed_byte_match']")
    inherited = json.loads(INHERITED.read_text())
    check(inherited["baseline_commit"] == report["baseline_commit"], "claim verification failed: inherited['baseline_commit'] == report['baseline_commit']")
    check(inherited["candidate_sha256"] == report["candidate_sha256"], "claim verification failed: inherited['candidate_sha256'] == report['candidate_sha256']")
    check(inherited["target_sha256"] == report["target_sha256"], "claim verification failed: inherited['target_sha256'] == report['target_sha256']")
    check(inherited["total_cases"] == 9161 and inherited["suite_count"] == 36, "claim verification failed: inherited['total_cases'] == 9161 and inherited['suite_count'] == 36")
    check([entry["name"] for entry in inherited["receipts"]] == [
        "maintained", "holder_distribution", "nested_create", "quote_control"], "claim verification failed: [entry['name'] for entry in inherited['receipts']] == [")
    check([entry["cases"] for entry in inherited["receipts"]] == \
        [7957, 649, 48, 507], "claim verification failed: [entry['cases'] for entry in inherited['receipts']] == ...")
    for entry in inherited["receipts"]:
        compressed = (INHERITED.parent / entry["file"]).read_bytes()
        raw = gzip.decompress(compressed)
        check(diff.sha(compressed) == entry["compressed_sha256"], "claim verification failed: diff.sha(compressed) == entry['compressed_sha256']")
        check(diff.sha(raw) == entry["json_sha256"] and len(raw) == entry["json_bytes"], "claim verification failed: diff.sha(raw) == entry['json_sha256'] and len(raw) == entry['json_byte")
        selected = json.loads(raw)
        if entry["name"] == "quote_control":
            check(type(selected.get("cases")) is int and type(entry.get("cases")) is int
                  and isinstance(selected.get("results"), list)
                  and selected["cases"] == entry["cases"] == len(selected["results"]), "claim verification failed: selected['cases'] == entry['cases'] == len(selected['results'])")
            check(type(selected.get("mismatches")) is int and selected["mismatches"] == 0, "claim verification failed: selected['mismatches'] == 0")
            # The header is only admitted when the retained rows say the same.
            check(all(isinstance(row, dict) for row in selected["results"])
                  and not any(row.get("matches") is not True for row in selected["results"]),
                  "claim verification failed: not any(row.get('matches') is not True for row in selected['results'])")
            check(isinstance(selected.get("bound_inputs_sha256"), dict) and selected["bound_inputs_sha256"],
                  "claim verification failed: quote-control receipt binds no input")
            for path, expected in selected["bound_inputs_sha256"].items():
                if path == "work/claim-pr-candidate/pump_recovered.so":
                    check(expected == report["candidate_sha256"], "claim verification failed: expected == report['candidate_sha256']")
                else:
                    check(diff.sha((diff.ROOT / path).read_bytes()) == expected, "claim verification failed: diff.sha((diff.ROOT / path).read_bytes()) == expected")
        else:
            check(selected["candidate_sha256"] == report["candidate_sha256"], "claim verification failed: selected['candidate_sha256'] == report['candidate_sha256']")
            check(selected["original_sha256"] == report["target_sha256"], "claim verification failed: selected['original_sha256'] == report['target_sha256']")
            check(selected["case_count"] == entry["cases"] and not selected["mismatches"], "claim verification failed: selected['case_count'] == entry['cases'] and not selected['mismatches'")
            if entry["name"] == "maintained":
                check(len(selected["suites"]) == 33, "claim verification failed: len(selected['suites']) == 33")
                check(sum(suite["case_count"] for suite in selected["suites"].values()) == 7957, "claim verification failed: sum(suite['case_count'] for suite in selected['suites'].values()) == 7")
                check(all(not suite.get("mismatches", suite.get("failures", []))
                           for suite in selected["suites"].values()), "claim verification failed: all(not suite.get('mismatches', suite.get('failures', []))")
                check(isinstance(selected.get("script_sha256"), dict) and selected["script_sha256"],
                      "claim verification failed: maintained receipt binds no script")
                check(all(diff.sha((diff.ROOT / "scripts" / name).read_bytes()) == digest
                           for name, digest in selected["script_sha256"].items()), "claim verification failed: all(diff.sha((diff.ROOT / 'scripts' / name).read_bytes()) == digest")
            else:
                check(len(selected["cases"]) == entry["cases"], "claim verification failed: len(selected['cases']) == entry['cases']")
    check(build["selected_toolchain"] == "v1.44", "claim verification failed: build['selected_toolchain'] == 'v1.44'")
    check(build["comparison"]["candidate_sha256"] == report["candidate_sha256"], "claim verification failed: build['comparison']['candidate_sha256'] == report['candidate_sha256']")
    check(build["comparison"]["original_sha256"] == report["target_sha256"], "claim verification failed: build['comparison']['original_sha256'] == report['target_sha256']")
    check(not build["comparison"]["full_byte_equality"], "claim verification failed: not build['comparison']['full_byte_equality']")
    check(report["signed_local"] and report["offline_only"], "claim verification failed: report['signed_local'] and report['offline_only']")
    idl = json.loads(diff.IDL.read_text(encoding="utf-8"))
    event_discriminator = bytes(next(item for item in idl["events"]
        if item["name"] == "ClaimTokenIncentivesEvent")["discriminator"])
    _, keys, _, user_volume, global_ata = diff.fixture_data()
    keys["user_ata"] = keys["user_base"]
    keys["global_ata"] = global_ata
    check(user_volume == keys["volume"], "claim verification failed: user_volume == keys['volume']")
    rows = report["cases"]
    check(len(rows) == report["summary"]["cases"] == len(diff.CASES) == 60, "claim verification failed: len(rows) == report['summary']['cases'] == len(diff.CASES) == 60")
    check([row["case"] for row in rows] == list(diff.CASES), "claim verification failed: [row['case'] for row in rows] == list(diff.CASES)")
    successes = 0
    events = 0
    for row in rows:
        case = row["case"]
        target = diff.run_case(diff.ORIGINAL, case)
        candidate = diff.run_case(args.candidate, case)
        check(target == row["target"] and candidate == row["candidate"], "claim verification failed: target == row['target'] and candidate == row['candidate']")
        assert_signature(target)
        assert_signature(candidate)
        check(not row["differences"], "claim verification failed: not row['differences']")
        for field in ("error", "before", "after", "event_data_base64", "inner",
                      "signature", "transaction_base64"):
            check(target[field] == candidate[field], (case["name"], field))
        check(target["error_code"] == EXPECTED_ERRORS.get(case["name"]), "claim verification failed: target['error_code'] == EXPECTED_ERRORS.get(case['name'])")
        check(target["before"]["payer"]["lamports"] - \
               target["after"]["payer"]["lamports"] == 5_000, "claim verification failed: target['before']['payer']['lamports'] - ...")
        check(target["before"]["global_volume"] == \
               target["after"]["global_volume"], "claim verification failed: target['before']['global_volume'] == ...")
        check(target["before"]["mint"] == target["after"]["mint"], "claim verification failed: target['before']['mint'] == target['after']['mint']")
        check(any("Instruction: ClaimTokenIncentives" in line
                   for line in target["relevant_logs"]), "claim verification failed: any('Instruction: ClaimTokenIncentives' in line")
        if target["success"]:
            successes += 1
            if target["event_data_base64"]:
                events += 1
                assert_event_and_cpis(target, event_discriminator, keys)
            else:
                check(not target["inner"], "claim verification failed: not target['inner']")
                check(target["before"]["user_ata"] == target["after"]["user_ata"], "claim verification failed: target['before']['user_ata'] == target['after']['user_ata']")
                check(target["before"]["global_ata"] == target["after"]["global_ata"], "claim verification failed: target['before']['global_ata'] == target['after']['global_ata']")
        else:
            check(target["before"]["user_ata"] == target["after"]["user_ata"], "claim verification failed: target['before']['user_ata'] == target['after']['user_ata']")
            check(target["before"]["global_ata"] == target["after"]["global_ata"], "claim verification failed: target['before']['global_ata'] == target['after']['global_ata']")
            check(target["before"]["user_volume"] == target["after"]["user_volume"], "claim verification failed: target['before']['user_volume'] == target['after']['user_volume']")
            check(not target["event_data_base64"], "claim verification failed: not target['event_data_base64']")
            if case["name"] in ("now_day_30", "now_day_31"):
                check("Fieldless(ProgramFailedToComplete)" in target["error"], "claim verification failed: 'Fieldless(ProgramFailedToComplete)' in target['error']")
            elif case["name"] == "vault_underfunded":
                check(len(target["inner"]) == 1, "claim verification failed: len(target['inner']) == 1")
            else:
                check(not target["inner"], "claim verification failed: not target['inner']")
    check(successes == report["summary"]["target_successes"] == 48, "claim verification failed: successes == report['summary']['target_successes'] == 48")
    check(report["summary"]["matched"] == 60, "claim verification failed: report['summary']['matched'] == 60")
    print(json.dumps({"verified": True, "signed_cases": len(rows),
                      "successes": successes, "payout_events": events,
                      "rollbacks": len(rows) - successes,
                      "candidate_sha256": report["candidate_sha256"]}))


if __name__ == "__main__":
    main()
