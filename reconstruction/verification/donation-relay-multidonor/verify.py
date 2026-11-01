#!/usr/bin/env python3
"""Independently admit finite Donation Relay multi-donor runtime receipts."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import re
import tempfile
import types
from pathlib import Path
from typing import Any
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solders.hash import Hash
from solders.compute_budget import set_compute_unit_limit

_SELF_SOURCE_SHA256 = globals().get("__source_sha256__")
if _SELF_SOURCE_SHA256 is None:
    _SELF_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if "_ADMISSION" in globals():
    A = _ADMISSION
else:
    _path = HERE / "admission.py"
    if _path.is_symlink():
        raise ValueError("admission source must be regular")
    _raw = _path.read_bytes()
    A = types.ModuleType("_relay_multidonor_admission")
    A.__file__ = str(_path)
    A.__source_sha256__ = hashlib.sha256(_raw).hexdigest()
    exec(compile(_raw, str(_path), "exec", dont_inherit=True), A.__dict__)
F = A.source_module("fixture", HERE / "fixture.py")
D = A.source_module("producer", HERE / "producer.py", bindings={"_ADMISSION": A, "_FIXTURE": F})
A.LOADED[str(Path(__file__).resolve())] = _SELF_SOURCE_SHA256

P = Pubkey.from_string
RELAY = P("RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu")
RELAYER = P("RLYRf96HAJSbbXCNS6ibQYnkxtb6kbfuFxqEkm9oQUc")
TOKEN = P("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ATA = P("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
ORIGINAL_SHA256 = "367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563"
TOKEN_SHA256 = "8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697"
ATA_SHA256 = "6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d"
COMPUTE_RE = re.compile(r"Program \S+ consumed \d+ of \d+ compute units")
CASE_NAMES = (
    "same_epoch_a_then_b", "interleaved_a_b_a", "three_donors_one_transaction",
    "a_success_b_fail_c_success", "atomic_rollback_invalid_third",
    "different_balance_boundaries", "authority_substitution", "separate_configurations",
    "separate_mints", "zero_and_u64_boundary", "rejected_close_between_donors",
    "failed_donor_retry",
)
EXPECTED_ERRORS = {
    "same_epoch_a_then_b": [None, None],
    "interleaved_a_b_a": [None, None, None],
    "three_donors_one_transaction": [None],
    "a_success_b_fail_c_success": [None, "Custom(6009)", None],
    "atomic_rollback_invalid_third": ["Custom(6009)"],
    "different_balance_boundaries": [None, "Custom(1)", None],
    "authority_substitution": ["Custom(2015)", None],
    "separate_configurations": [None, None],
    "separate_mints": [None, None],
    "zero_and_u64_boundary": [None, "Custom(1)", None],
    "rejected_close_between_donors": [None, "Custom(2012)", None],
    "failed_donor_retry": [None, "Custom(1)", None],
}
EXPECTED_SHAPES = {
    "same_epoch_a_then_b": [[("A", 1_000_000, "config_a_mint_x", None)],
                              [("B", 2_000_000, "config_a_mint_x", None)]],
    "interleaved_a_b_a": [[("A", 100, "config_a_mint_x", None)],
                            [("B", 200, "config_a_mint_x", None)],
                            [("A", 300, "config_a_mint_x", None)]],
    "three_donors_one_transaction": [[("A", 1_000, "config_a_mint_x", None),
                                        ("B", 2_000, "config_a_mint_x", None),
                                        ("C", 3_000, "config_a_mint_x", None)]],
    "a_success_b_fail_c_success": [[("A", 1_000, "config_a_mint_x", None)],
                                     [("B", 1, "config_a_mint_x", None)],
                                     [("C", 3_000, "config_a_mint_x", None)]],
    "atomic_rollback_invalid_third": [[("A", 100, "config_a_mint_x", None),
                                         ("B", 200, "config_a_mint_x", None),
                                         ("C", 1, "config_a_mint_x", None)]],
    "different_balance_boundaries": [[("A", 5, "config_a_mint_x", None)],
                                       [("B", 11, "config_a_mint_x", None)],
                                       [("C", 0, "config_a_mint_x", None)]],
    "authority_substitution": [[("B", 7, "config_a_mint_x", "A")],
                                 [("B", 17, "config_a_mint_x", None)]],
    "separate_configurations": [[("A", 111, "config_a_mint_x", None)],
                                  [("B", 222, "config_b_mint_x", None)]],
    "separate_mints": [[("A", 333, "config_a_mint_x", None)],
                         [("B", 444, "config_a_mint_y", None)]],
    "zero_and_u64_boundary": [[("A", 0, "config_a_mint_x", None)],
                                [("B", (1 << 64) - 1, "config_a_mint_x", None)],
                                [("C", 1, "config_a_mint_x", None)]],
    "rejected_close_between_donors": [[("A", 777, "config_a_mint_x", None)],
                                        "close_wrong_signer",
                                        [("B", 223, "config_a_mint_x", None)]],
    "failed_donor_retry": [[("A", 10, "config_a_mint_x", None)],
                             [("B", 101, "config_a_mint_x", None)],
                             [("B", 100, "config_a_mint_x", None)]],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    return sha(A.regular_bytes(path))


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def canonical(document):
    return (json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def data(row):
    return b"" if row is None else base64.b64decode(row.get("data_base64", ""), validate=True)


def token_amount(row):
    raw = data(row)
    return 0 if len(raw) < 72 else int.from_bytes(raw[64:72], "little")


def nullable_token_amount(row):
    raw = data(row)
    return None if len(raw) < 72 else int.from_bytes(raw[64:72], "little")


def lamports(row):
    return 0 if row is None else row["lamports"]


def pda(*seeds):
    return Pubkey.find_program_address(list(seeds), RELAY)[0]


def ata(owner, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def fixture_info(value):
    return {
        "donors": {name: str(donor.keypair.pubkey()) for name, donor in value.donors.items()},
        "fee_payer": str(value.fee.pubkey()), "outsider": str(value.outsider.pubkey()),
        "production_relayer": str(F.RELAYER),
        "domains": {name: {"config_hex": domain.config.hex(), "mint": str(domain.mint),
                            "epoch": str(domain.epoch), "debouncer": str(domain.debouncer),
                            "destination": str(domain.destination)} for name, domain in value.domains.items()},
        "sources": {name: {mint: str(address) for mint, address in donor.sources.items()}
                    for name, donor in value.donors.items()},
    }


def validate_snapshot(rows, expected_initial):
    if type(rows) is not dict or set(rows) != set(expected_initial):
        raise ValueError("snapshot exact watched key set")
    for key, row in rows.items():
        if str(P(key)) != key:
            raise ValueError("snapshot public key")
        expected = expected_initial[key]
        # Executable membership and metadata remain exact even when saved None.
        if expected is not None and expected["executable"]:
            if not A.same_json(row, expected):
                raise ValueError("snapshot executable identity")
            continue
        if row is None:
            continue
        if type(row) is not dict or set(row) != {"lamports", "owner", "executable", "rent_epoch", "data_len", "data_sha256", "data_base64"}:
            raise ValueError("snapshot account fields")
        if (type(row["executable"]) is not bool or row["executable"]
                or type(row["data_len"]) is not int or not 0 <= row["data_len"] <= 16 * 1024 * 1024):
            raise ValueError("snapshot account types")
        for field in ("lamports", "rent_epoch"):
            if type(row[field]) is not int or not 0 <= row[field] < 2**64:
                raise ValueError("snapshot u64 metadata")
        raw = base64.b64decode(row["data_base64"], validate=True)
        if (len(raw) != row["data_len"] or sha(raw) != row["data_sha256"]
                or base64.b64encode(raw).decode() != row["data_base64"]
                or str(P(row["owner"])) != row["owner"]):
            raise ValueError("snapshot account bytes")

def domain_maps(case):
    return case["fixture"]["domains"], case["fixture"]["sources"]


def token_total(state: dict[str, Any], domains: dict[str, dict[str, str]],
                sources: dict[str, dict[str, str]], mint: str) -> int:
    source_total = sum(token_amount(state[address]) for donor in sources.values()
                       for _mint_name, address in donor.items()
                       if data(state[address])[:32] == bytes(P(mint)))
    destination_total = sum(token_amount(state[row["destination"]])
                            for row in domains.values() if row["mint"] == mint)
    return source_total + destination_total


def validate_invariants(case: dict[str, Any], step: dict[str, Any]) -> list[str]:
    problems = []
    row = step["original"]
    before, after = row["before"], row["after"]
    domains, sources = domain_maps(case)
    if row.get("transaction_fee_lamports", 0) <= 0:
        problems.append("fee")
    for mint in {domain["mint"] for domain in domains.values()}:
        if token_total(before, domains, sources, mint) != token_total(after, domains, sources, mint):
            problems.append("token_conservation")
    if row["error"] is not None:
        fee = case["fixture"]["fee_payer"]
        if any(before[key] != after[key] for key in before if key != fee):
            problems.append("rollback")
        return problems

    source_delta: dict[str, int] = {}
    destination_delta: dict[str, int] = {}
    touched = set()
    for donation in step["donations"]:
        domain = domains[donation["domain"]]
        source_owner = donation.get("source_donor") or donation["donor"]
        mint_name = "mint_x" if donation["domain"].endswith("mint_x") else "mint_y"
        source_address = sources[source_owner][mint_name]
        source_delta[source_address] = source_delta.get(source_address, 0) + donation["amount"]
        destination_delta[donation["domain"]] = destination_delta.get(donation["domain"], 0) + donation["amount"]
        touched.add(donation["domain"])
    for donor in sources.values():
        for address in donor.values():
            if token_amount(before[address]) - token_amount(after[address]) != source_delta.get(address, 0):
                problems.append("source_delta")
    for name, domain in domains.items():
        expected = destination_delta.get(name, 0)
        if token_amount(after[domain["destination"]]) - token_amount(before[domain["destination"]]) != expected:
            problems.append("destination_delta")
        before_debouncer, after_debouncer = data(before[domain["debouncer"]]), data(after[domain["debouncer"]])
        before_total = 0 if len(before_debouncer) < 82 else int.from_bytes(before_debouncer[74:82], "little")
        after_total = 0 if len(after_debouncer) < 82 else int.from_bytes(after_debouncer[74:82], "little")
        if after_total - before_total != expected:
            problems.append("debouncer_delta")
        if name not in touched and any(before[address] != after[address] for address in
                                       (domain["epoch"], domain["debouncer"], domain["destination"])):
            problems.append("domain_isolation")
    donor_loss = sum(lamports(before[pubkey]) - lamports(after[pubkey])
                     for pubkey in case["fixture"]["donors"].values())
    rent_gain = sum(lamports(after[address]) - lamports(before[address])
                    for domain in domains.values()
                    for address in (domain["epoch"], domain["debouncer"], domain["destination"]))
    if donor_loss != rent_gain:
        problems.append("rent_conservation")
    return sorted(set(problems))


def decode_final(case: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    domains, sources = domain_maps(case)
    decoded_domains = {}
    for name, domain in domains.items():
        epoch, debouncer = data(state[domain["epoch"]]), data(state[domain["debouncer"]])
        decoded_domains[name] = {
            "epoch": None if len(epoch) < 90 else int.from_bytes(epoch[74:90], "little"),
            "epoch_state": None if len(epoch) < 10 else epoch[9],
            "debouncer_total": None if len(debouncer) < 82 else int.from_bytes(debouncer[74:82], "little"),
            "debouncer_state": None if len(debouncer) < 10 else debouncer[9],
            "destination_tokens": nullable_token_amount(state[domain["destination"]]),
        }
    decoded_sources = {donor: {mint: token_amount(state[address])
                               for mint, address in donor_sources.items()}
                       for donor, donor_sources in sources.items()}
    return {"domains": decoded_domains, "sources": decoded_sources,
            "lamports": {"fee": state[case["fixture"]["fee_payer"]]["lamports"],
                          **{name: state[pubkey]["lamports"]
                             for name, pubkey in case["fixture"]["donors"].items()}}}


def _validate(report, root, candidate, admitted, images):
    problems = []
    top = {"schema", "program", "authority_boundary", "inputs", "runtime", "case_count",
           "fixture_identity_sha256", "transaction_count", "individual_signature_count",
           "transaction_identity", "classification_counts", "original_positive_cases",
           "strict_mismatches", "unsupported", "cases"}
    if type(report) is not dict or set(report) != top or report["schema"] != "donation-relay-multidonor-v2":
        raise ValueError("report schema/fields")
    if report["program"] != str(RELAY) or not A.same_json(report["authority_boundary"], {
            "production_relayer": str(RELAYER), "private_key_retained": False,
            "privileged_signer_injection": False}):
        raise ValueError("authority boundary")
    inputs = report["inputs"]
    fields = {"original", "spl_token", "associated_token", "candidate", "candidate_provenance",
              "source_snapshot_context_only", "admitted_input_sha256", "source_manifest_sha256",
              "source_files", "package_files"}
    if type(inputs) is not dict or set(inputs) != fields:
        raise ValueError("input fields; source-build claims are not admitted")
    for name, path, expected in (("original", "donation_relay", ORIGINAL_SHA256),
                                 ("spl_token", "spl_token", TOKEN_SHA256),
                                 ("associated_token", "associated_token", ATA_SHA256)):
        if sha(images[name]) != expected or not A.same_json(inputs[name], {
                "path": f"evidence/dependencies/{path}/deployed.so", "sha256": expected}):
            raise ValueError("captured executable identity: " + name)
    if not A.same_json(inputs["candidate"], {"sha256": sha(images["candidate"]), "bytes": len(images["candidate"])}):
        raise ValueError("candidate identity")
    if (not A.same_json(inputs["candidate_provenance"], {"mode": "supplied_binary_only", "source_build_verified_by_this_suite": False})
            or inputs["source_snapshot_context_only"] is not True
            or not A.same_json(inputs["admitted_input_sha256"], admitted)):
        raise ValueError("runtime-only source/input provenance")
    source_files, source_digest = D.source_manifest(root)
    if (not A.same_json(inputs["source_files"], source_files)
            or inputs["source_manifest_sha256"] != source_digest
            or not A.same_json(inputs["package_files"], D.package_manifest(root))):
        raise ValueError("source/package context")
    clock = D.FIXED_CLOCK
    if not A.same_json(report["runtime"], {"engine": "LiteSVM through solders 0.27.1", "clock": {
            "slot": clock.slot, "epoch_start_timestamp": clock.epoch_start_timestamp,
            "epoch": clock.epoch, "leader_schedule_epoch": clock.leader_schedule_epoch,
            "unix_timestamp": clock.unix_timestamp}, "signature_verification": True,
            "blockhash_verification": True, "public_rpc": False}):
        raise ValueError("runtime admission")
    cases = report["cases"]
    if type(cases) is not list or [c["name"] for c in cases] != list(CASE_NAMES):
        raise ValueError("exact case membership/order")
    for name in ("case_count", "transaction_count", "individual_signature_count", "original_positive_cases"):
        if type(report[name]) is not int or report[name] < 0:
            raise ValueError("typed report count")
    identities, hashes, signatures, positive = [], [], [], 0
    evidence = []
    with tempfile.TemporaryDirectory(prefix="relay-multidonor-reader-inputs-") as temp:
        private = {}
        for name, raw in images.items():
            path = Path(temp) / (name + ".so")
            path.write_bytes(raw)
            private[name] = path
        for case in cases:
            if type(case) is not dict or set(case) != {"name", "classification", "problems", "fixture", "initial_balances", "plan", "expected_errors", "final_state", "steps"}:
                raise ValueError("case fields")
            name, spec = case["name"], D.CASES[case["name"]]
            value = F.Fixture.create(name, spec.get("balances"))
            if any("close_wrong_signer" in s for s in spec["steps"]):
                value.close_wrong_signer()
            if (not A.same_json(case["fixture"], fixture_info(value))
                    or not A.same_json(case["initial_balances"], spec.get("balances", {}))
                    or not A.same_json(case["plan"], spec["steps"])
                    or not A.same_json(case["expected_errors"], EXPECTED_ERRORS[name])):
                raise ValueError("canonical fixture/plan: " + name)
            evidence.append({k: case[k] for k in ("name", "fixture", "initial_balances", "plan", "expected_errors")})
            # Constructor-only canonical state, independently of saved receipts.
            pair = D.Pair(private["original"], private["candidate"], value,
                          private["spl_token"], private["associated_token"])
            watch = value.watch() | {set_compute_unit_limit(1_400_000).program_id}
            initial = {side: D.snapshot(vm, watch) for side, vm in pair.vms.items()}
            steps = case["steps"]
            if type(steps) is not list or len(steps) != len(spec["steps"]):
                raise ValueError("nonempty exact step count")
            previous = dict(initial)
            case_problems = []
            for index, (step, plan) in enumerate(zip(steps, spec["steps"])):
                if type(step) is not dict or set(step) != {"transaction_base64", "transaction_sha256", "message_base64", "message_sha256", "recent_blockhash", "signatures", "signature_verification", "required_signer_pubkeys", "donor_signers", "donations", "mismatches", "original", "candidate", "index", "expected_error", "original_state", "candidate_state", "invariant_problems"}:
                    raise ValueError("step fields")
                if type(step["index"]) is not int or step["index"] != index or not A.same_json(step["expected_error"], plan["error"]):
                    raise ValueError("step plan index/error")
                instructions, keypairs, records = D.build_step(value, plan)
                if not A.same_json(step["donations"], records) or not A.same_json(step["donor_signers"], sorted({r["donor"] for r in records})):
                    raise ValueError("donation records/signers")
                blockhash = Hash.from_string(step["recent_blockhash"])
                expected_message = Message.new_with_blockhash(
                    [set_compute_unit_limit(1_400_000), *instructions], value.fee.pubkey(), blockhash)
                raw = base64.b64decode(step["transaction_base64"], validate=True)
                tx = Transaction.from_bytes(raw)
                checked = list(tx.verify_with_results())
                flags = step["signature_verification"]
                required = expected_message.header.num_required_signatures
                signer_keys = [str(k) for k in expected_message.account_keys[:required]]
                if (bytes(tx) != raw or base64.b64encode(raw).decode() != step["transaction_base64"]
                        or bytes(tx.message) != bytes(expected_message)
                        or len(tx.signatures) != required or not checked or checked != [True] * required
                        or type(flags) is not list or any(type(v) is not bool for v in flags) or flags != checked
                        or not A.same_json(step["required_signer_pubkeys"], signer_keys)
                        or set(signer_keys) != {str(k.pubkey()) for k in F.unique_keypairs([value.fee, *keypairs])}
                        or not A.same_json(step["signatures"], [str(s) for s in tx.signatures])
                        or step["transaction_sha256"] != sha(raw)
                        or step["message_sha256"] != sha(bytes(tx.message))
                        or step["message_base64"] != base64.b64encode(bytes(tx.message)).decode()):
                    raise ValueError("canonical complete signed message: " + name)
                identities.append(step["transaction_sha256"])
                hashes.append(step["recent_blockhash"])
                signatures.extend(step["signatures"])
                for side in ("original", "candidate"):
                    row = step[side]
                    if type(row) is not dict or set(row) != {"error", "compute_units", "transaction_fee_lamports", "logs", "events", "inner_instructions", "return_data", "rollback_non_fee_changes", "before", "after"}:
                        raise ValueError("receipt outcome fields")
                    for stage in ("before", "after"):
                        validate_snapshot(row[stage], initial[side])
                    if not A.same_json(previous[side], row["before"]):
                        raise ValueError("constructor prestate or continuity")
                    if (type(row["logs"]) is not list or any(type(line) is not str for line in row["logs"])
                            or row["error"] is not None and type(row["error"]) is not str
                            or type(row["compute_units"]) is not int or row["compute_units"] < 0):
                        raise ValueError("typed outcome")
                    expected_error = plan["error"]
                    if not D.error_matches(row["error"], expected_error, 3 if name == "atomic_rollback_invalid_third" else 1):
                        raise ValueError("exact error code/instruction index")
                    if not A.same_json(row["events"], [line for line in row["logs"] if line.startswith("Program data: ")]):
                        raise ValueError("event/log binding")
                    payer = str(value.fee.pubkey())
                    fee = row["before"][payer]["lamports"] - row["after"][payer]["lamports"]
                    if type(row["transaction_fee_lamports"]) is not int or row["transaction_fee_lamports"] != fee or fee != 5000 * required:
                        raise ValueError("payer fee/signature delta")
                    rollback = [] if row["error"] is None else [k for k in row["before"] if k != payer and not A.same_json(row["before"][k], row["after"][k])]
                    if rollback or not A.same_json(rollback, row["rollback_non_fee_changes"]):
                        raise ValueError("rollback")
                    # Use independent accounting for each side, not only original.
                    single_side = dict(step, original=row)
                    if validate_invariants(case, single_side):
                        raise ValueError("donor/domain accounting")
                    decoded = value.decode(row["after"])
                    if not A.same_json(step[side + "_state"], decoded):
                        raise ValueError("derived per-side state")
                    previous[side] = row["after"]
                if (not A.same_json(D.Pair.comparable(step["original"]), D.Pair.comparable(step["candidate"]))
                        or not A.same_json(step["mismatches"], []) or not A.same_json(step["invariant_problems"], [])):
                    case_problems.append("differential-or-invariant")
            if (case_problems or case["classification"] != "equal_observed_behavior" or not A.same_json(case["problems"], [])
                    or not A.same_json(case["final_state"], value.decode(previous["original"]))):
                problems.append("case comparison/final state: " + name)
            positive += int(any(step["original"]["error"] is None for step in steps))
    if report["fixture_identity_sha256"] != sha(json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()):
        problems.append("fixture evidence hash")
    expected_counts = {"equal_observed_behavior": len(cases), "different_behavior": 0,
                       "unsupported_fixture": 0, "infrastructure_failure": 0}
    if (report["case_count"] != len(cases) or report["transaction_count"] != len(identities)
            or len(set(identities)) != len(identities) or len(set(hashes)) != len(hashes)
            or report["individual_signature_count"] != len(signatures)
            or report["original_positive_cases"] != positive
            or not A.same_json(report["transaction_identity"], {"unique_transaction_count": len(identities),
                        "unique_blockhash_count": len(hashes), "all_signatures_verified": True})
            or not A.same_json(report["classification_counts"], expected_counts)
            or not A.same_json(report["strict_mismatches"], [])):
        problems.append("typed complete summary")
    unsupported = [{"family": "production-relayer epoch closure and distribution", "classification": "unsupported_fixture",
                    "reason": "production relayer private key is not retained"},
                   {"family": "Jupiter swap settlement", "classification": "unsupported_fixture",
                    "reason": "cannot legitimately cross the same relayer gate"}]
    if not A.same_json(report["unsupported"], unsupported):
        problems.append("unsupported boundary")
    return problems


def validate(report, root, candidate):
    try:
        if root.resolve() != ROOT:
            raise ValueError("root must be this admitted source checkout")
        admitted = A.snapshot_inputs()
        images = {"original": A.regular_bytes(root / "evidence/dependencies/donation_relay/deployed.so", root=ROOT),
                  "spl_token": A.regular_bytes(root / "evidence/dependencies/spl_token/deployed.so", root=ROOT),
                  "associated_token": A.regular_bytes(root / "evidence/dependencies/associated_token/deployed.so", root=ROOT),
                  "candidate": A.regular_bytes(candidate)}
        result = _validate(report, root, candidate, admitted, images)
        A.recheck_inputs(admitted)
        if A.regular_bytes(candidate) != images["candidate"]:
            raise ValueError("candidate changed during verification")
        return sorted(set(result))
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError) as error:
        return ["invalid_report:" + type(error).__name__ + ":" + str(error)]


def verify_file(root, candidate, report_path):
    raw = None
    try:
        raw = A.regular_bytes(report_path)
        report = A.json_bytes(raw)
        problems = validate(report, root.resolve(), candidate.absolute())
        if raw != canonical(report):
            problems.append("noncanonical JSON")
        if A.regular_bytes(report_path) != raw:
            problems.append("report changed during verification")
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError) as error:
        problems = ["invalid_report:" + type(error).__name__ + ":" + str(error)]
    return {"accepted": not problems, "problems": sorted(set(problems)),
            "report_sha256": None if raw is None else sha(raw),
            "verification_scope": "supplied-binary-only finite runtime receipts; no source-build authentication"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = verify_file(args.root, args.candidate, args.report)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["accepted"] else 1)


if __name__ == "__main__":
    main()
