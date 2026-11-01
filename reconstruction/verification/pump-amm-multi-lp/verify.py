#!/usr/bin/env python3
"""Admit fixed PumpSwap LP receipts against canonical signed fixture messages."""
from __future__ import annotations
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O, -OO or PYTHONOPTIMIZE.")
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import types

from solders.hash import Hash
from solders.instruction import CompiledInstruction
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_status import TransactionErrorInstructionError, InstructionErrorCustom

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
_SELF_SHA = globals().get("__source_sha256__")
if _SELF_SHA is None:
    _SELF_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if "_ADMISSION" in globals():
    A = _ADMISSION
else:
    _path = HERE / "admission.py"
    if _path.is_symlink():
        raise ValueError("admission source must be regular")
    _raw = _path.read_bytes()
    A = types.ModuleType("_amm_lp_reader_admission")
    A.__file__ = str(_path)
    A.__source_sha256__ = hashlib.sha256(_raw).hexdigest()
    exec(compile(_raw, str(_path), "exec", dont_inherit=True), A.__dict__)
A.LOADED[str(Path(__file__).resolve())] = _SELF_SHA
L = A.source_module("lifecycle", HERE / "lifecycle.py", bindings={"_ADMISSION": A})
lifecycle = L  # Public compatibility for existing callers.
_ELF = A.source_module("elf_admission", ROOT / "reconstruction/harness/score_admission.py")

CAPTURED_HASHES = {
    "original": "6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7",
    "spl_token": "8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697",
    "spl_token_2022": "15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d",
    "associated_token": "6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d",
    "pump_fees": "4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e",
}
COMMON_ACCOUNT = {"lamports", "owner", "executable", "rent_epoch", "data_len", "data_sha256",
                  "token_amount", "mint_supply", "pool_lp_supply"}
RECEIPT_FIELDS = {
    "step", "operation", "transaction_base64", "signatures", "message_sha256", "blockhash",
    "blockhash_sha256", "signer_pubkeys", "instruction_count", "pool_label", "error", "error_detail",
    "outcome", "failure_class", "raw_logs", "semantic_logs", "events", "inner_instructions",
    "return_data", "compute_units", "before", "after", "rollback_nonfee_equal", "accounting",
}
STRICT_FIELDS = ("transaction_base64", "signatures", "message_sha256", "pool_label", "error",
                 "error_detail", "outcome", "failure_class", "semantic_logs", "events",
                 "inner_instructions", "return_data", "before", "after", "rollback_nonfee_equal", "accounting")
TOP_FIELDS = {"schema", "upstream_commit", "source_snapshot_context_only", "program_ids", "program_sha256",
              "candidate_build", "producer_input_sha256", "candidate_source_sha256",
              "candidate_source_manifest_sha256", "case_count", "transaction_count_per_image",
              "cases", "classification_counts"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, *, raw=None):
    if raw is None:
        raw = A.regular_bytes(path)
    if raw.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            raw = stream.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("report decompression limit")
    return A.json_bytes(raw)


def uint(value, bits=64):
    return type(value) is int and 0 <= value < 1 << bits


def scalar_json(value):
    if value is None or type(value) in (str, bool, int):
        return True
    if type(value) is list:
        return all(scalar_json(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and scalar_json(item) for key, item in value.items())
    return False


def raw_account(snapshot, address):
    record = snapshot.get(address)
    return None if record is None or record.get("data_omitted") is True else base64.b64decode(record["data_base64"], validate=True)


def token_amount(snapshot, address):
    raw = raw_account(snapshot, address)
    return None if raw is None or len(raw) < 72 else struct.unpack_from("<Q", raw, 64)[0]


def mint_supply(snapshot, address):
    raw = raw_account(snapshot, address)
    return None if raw is None or len(raw) < 44 else struct.unpack_from("<Q", raw, 36)[0]


def pool_supply(snapshot, address):
    raw = raw_account(snapshot, address)
    return None if raw is None or len(raw) < 211 else struct.unpack_from("<Q", raw, 203)[0]


def economic_state(snapshot, fixture):
    a, b = fixture["provider_a_accounts"], fixture["provider_b_accounts"]
    state = {
        "provider_a_base": token_amount(snapshot, a["base"]),
        "provider_a_quote": token_amount(snapshot, a["quote"]),
        "provider_a_lp": token_amount(snapshot, a["lp"]),
        "provider_b_base": token_amount(snapshot, b["base"]),
        "provider_b_quote": token_amount(snapshot, b["quote"]),
        "provider_b_lp": token_amount(snapshot, b["lp"]),
        "pool_base": token_amount(snapshot, fixture["vault_base"]),
        "pool_quote": token_amount(snapshot, fixture["vault_quote"]),
        "buyback_quote": token_amount(snapshot, str(L.BUYBACK)),
        "lp_mint_supply": mint_supply(snapshot, fixture["lp_mint"]),
        "pool_reported_lp_supply": pool_supply(snapshot, fixture["pool"]),
    }
    lp = state["provider_a_lp"], state["provider_b_lp"]
    state["provider_lp_total"] = None if None in lp else sum(lp)
    state["locked_lp_difference"] = (None if state["pool_reported_lp_supply"] is None or state["lp_mint_supply"] is None
                                     else state["pool_reported_lp_supply"] - state["lp_mint_supply"])
    base = state["provider_a_base"], state["provider_b_base"], state["pool_base"]
    quote = state["provider_a_quote"], state["provider_b_quote"], state["pool_quote"], state["buyback_quote"]
    state["base_total"] = None if None in base else sum(base)
    state["quote_total_with_fee_recipient"] = None if None in quote else sum(quote)
    return state


def accounting(before, after, fixture):
    left, right = economic_state(before, fixture), economic_state(after, fixture)
    delta = {name: None if left[name] is None or right[name] is None else right[name] - left[name]
             for name in left if type(left[name]) is int or type(right[name]) is int}
    payer = fixture["fee_payer"]
    return {"before": left, "after": right, "delta": delta,
            "fee_payer_lamport_delta": after[payer]["lamports"] - before[payer]["lamports"]}


def owner_roles(harness):
    result = {str(pair.pubkey()): str(L.SYSTEM) for pair in (L.FEE_PAYER, L.PROVIDER_A, L.PROVIDER_B, L.MINT_AUTHORITY)}
    result.update({str(L.CONFIG): str(L.AMM), str(L.EVENT): str(L.SYSTEM),
                   str(L.FEE_CONFIG): L.FEE_CONFIG_ROW["owner"], str(L.BUYBACK): L.BUYBACK_ROW["owner"]})
    for pool in harness.pools.values():
        result.update({str(pool.base): str(pool.base_program), str(pool.quote): str(pool.quote_program),
                       str(pool.pool): str(L.AMM), str(pool.lp): str(L.TOKEN22),
                       str(pool.vault_base): str(pool.base_program), str(pool.vault_quote): str(pool.quote_program)})
        for pair in (L.PROVIDER_A, L.PROVIDER_B):
            keys = pool.provider_accounts(pair)
            result.update({str(keys["base"]): str(pool.base_program), str(keys["quote"]): str(pool.quote_program),
                           str(keys["lp"]): str(L.TOKEN22)})
    for pair in (L.PROVIDER_A, L.PROVIDER_B):
        volume = Pubkey.find_program_address([b"user_volume_accumulator", bytes(pair.pubkey())], L.AMM)[0]
        result[str(volume)] = str(L.AMM)
    return result


def validate_snapshot(snapshot, initial, roles, prefix, problems):
    if type(snapshot) is not dict or set(snapshot) != set(initial):
        problems.append(prefix + ":watch_membership")
        return False
    for address, record in snapshot.items():
        if record is None:
            if initial[address] is not None and initial[address].get("executable") is True:
                problems.append(prefix + ":missing_program:" + address)
            continue
        if type(record) is not dict or type(record.get("executable")) is not bool:
            problems.append(prefix + ":account_record_type:" + address)
            continue
        executable = record["executable"]
        if set(record) != COMMON_ACCOUNT | ({"data_omitted"} if executable else {"data_base64"}):
            problems.append(prefix + ":account_record_fields:" + address)
            continue
        if (not uint(record["lamports"]) or not uint(record["rent_epoch"]) or not uint(record["data_len"])
                or type(record["owner"]) is not str or str(Pubkey.from_string(record["owner"])) != record["owner"]
                or type(record["data_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", record["data_sha256"])):
            problems.append(prefix + ":account_metadata:" + address)
            continue
        for field in ("token_amount", "mint_supply", "pool_lp_supply"):
            if record[field] is not None and not uint(record[field]):
                problems.append(prefix + ":account_scalar_type:" + field)
        if initial[address] is not None and initial[address].get("executable") is True:
            if not A.same_json(record, initial[address]):
                problems.append(prefix + ":program_identity:" + address)
            continue
        if executable:
            problems.append(prefix + ":unexpected_executable:" + address)
            continue
        if address in roles and record["owner"] != roles[address]:
            problems.append(prefix + ":owner_role:" + address)
        if type(record["data_base64"]) is not str:
            problems.append(prefix + ":account_data_type:" + address)
            continue
        raw = base64.b64decode(record["data_base64"], validate=True)
        if base64.b64encode(raw).decode() != record["data_base64"] or len(raw) != record["data_len"] or sha(raw) != record["data_sha256"]:
            problems.append(prefix + ":account_data_identity:" + address)
        token = struct.unpack_from("<Q", raw, 64)[0] if record["owner"] in (str(L.TOKEN), str(L.TOKEN22)) and len(raw) >= 165 else None
        mint = struct.unpack_from("<Q", raw, 36)[0] if record["owner"] in (str(L.TOKEN), str(L.TOKEN22)) and 82 <= len(raw) < 165 else None
        pool = struct.unpack_from("<Q", raw, 203)[0] if record["owner"] == str(L.AMM) and len(raw) >= 211 else None
        if not A.same_json([record[k] for k in ("token_amount", "mint_supply", "pool_lp_supply")], [token, mint, pool]):
            problems.append(prefix + ":cached_account_fields:" + address)
    return not any(item.startswith(prefix + ":") for item in problems)


def validate_metadata(receipt, transaction, instruction_count, prefix, problems):
    if any(type(receipt[name]) is not list or any(type(v) is not str for v in receipt[name])
           for name in ("raw_logs", "semantic_logs", "events", "signatures", "signer_pubkeys")):
        problems.append(prefix + ":list_metadata_type")
        return
    if not uint(receipt["compute_units"]) or type(receipt["outcome"]) is not str:
        problems.append(prefix + ":execution_metadata_type")
    detail = receipt["error_detail"]
    if detail is None:
        expected_error = None
    elif (type(detail) is dict and set(detail) == {"instruction_index", "error_kind", "custom_code"}
          and uint(detail["instruction_index"], 8) and detail["instruction_index"] < instruction_count
          and detail["error_kind"] == "Custom" and uint(detail["custom_code"], 32)):
        expected_error = str(TransactionErrorInstructionError(detail["instruction_index"], InstructionErrorCustom(detail["custom_code"])))
    else:
        problems.append(prefix + ":error_detail")
        return
    if not A.same_json(receipt["error"], expected_error):
        problems.append(prefix + ":error_display")
    if not A.same_json(receipt["outcome"], L.outcome(receipt["raw_logs"], expected_error)):
        problems.append(prefix + ":outcome")
    if not A.same_json(receipt["failure_class"], L.failure_class(expected_error)):
        problems.append(prefix + ":failure_class")
    if not A.same_json(receipt["semantic_logs"], L.semantic_logs(receipt["raw_logs"])):
        problems.append(prefix + ":semantic_logs")
    if not A.same_json(receipt["events"], [s for s in receipt["raw_logs"] if s.startswith("Program data: ")]):
        problems.append(prefix + ":events")
    inner = receipt["inner_instructions"]
    if type(inner) is not list or len(inner) > instruction_count:
        problems.append(prefix + ":inner_instruction_groups")
    else:
        for group in inner:
            if type(group) is not list:
                problems.append(prefix + ":inner_instruction_group")
                continue
            for row in group:
                if type(row) is not dict or set(row) != {"instruction", "stackHeight"} or not uint(row["stackHeight"], 8) or not row["stackHeight"]:
                    problems.append(prefix + ":inner_instruction_row")
                    continue
                instruction = CompiledInstruction.from_json(json.dumps(row["instruction"]))
                if not A.same_json(json.loads(instruction.to_json()), row["instruction"]):
                    problems.append(prefix + ":inner_instruction_encoding")
                if instruction.program_id_index >= len(transaction.message.account_keys) or any(i >= len(transaction.message.account_keys) for i in instruction.accounts):
                    problems.append(prefix + ":inner_instruction_indices")
    returned = receipt["return_data"]
    if returned is not None:
        if (type(returned) is not dict or set(returned) != {"program_id", "data"}
                or type(returned["program_id"]) is not list or len(returned["program_id"]) != 32
                or type(returned["data"]) is not list
                or any(not uint(v, 8) for v in returned["program_id"] + returned["data"])):
            problems.append(prefix + ":return_data")


def validate_account_roles(snapshot, initial, harness, prefix, problems):
    """Bind decoded SPL and fixed Pool identity fields to their fixture roles."""
    token_roles = {}
    mint_roles = {}
    discriminator = bytes(next(row["discriminator"] for row in L.IDL["accounts"] if row["name"] == "Pool"))
    for pool in harness.pools.values():
        mint_roles.update({str(pool.base): (L.MINT_AUTHORITY.pubkey(), 6),
                           str(pool.quote): (L.MINT_AUTHORITY.pubkey(), 9),
                           str(pool.lp): (pool.pool, 9)})
        token_roles.update({str(pool.vault_base): (pool.base, pool.pool),
                            str(pool.vault_quote): (pool.quote, pool.pool)})
        for pair in (L.PROVIDER_A, L.PROVIDER_B):
            keys = pool.provider_accounts(pair)
            token_roles.update({str(keys["base"]): (pool.base, pair.pubkey()),
                                str(keys["quote"]): (pool.quote, pair.pubkey()),
                                str(keys["lp"]): (pool.lp, pair.pubkey())})
        raw = raw_account(snapshot, str(pool.pool))
        if raw is not None:
            _, bump = Pubkey.find_program_address([b"pool", struct.pack("<H", pool.index),
                                                   bytes(L.PROVIDER_A.pubkey()), bytes(pool.base), bytes(pool.quote)], L.AMM)
            identities = (L.PROVIDER_A.pubkey(), pool.base, pool.quote, pool.lp, pool.vault_base, pool.vault_quote)
            if (len(raw) != 287 or raw[:8] != discriminator or raw[8] != bump
                    or struct.unpack_from("<H", raw, 9)[0] != pool.index
                    or any(raw[offset:offset + 32] != bytes(key) for offset, key in zip((11, 43, 75, 107, 139, 171), identities))
                    # This fixture's real Ed25519 creator is on-curve, hence
                    # differs from Pump's off-curve pool_authority PDA. Only
                    # canonical Pump pools copy the supplied coin_creator.
                    or not L.PROVIDER_A.pubkey().is_on_curve()
                    or raw[211:243] != bytes(L.SYSTEM)
                    or any(raw[offset] not in (0, 1) for offset in (243, 244, 269, 270))):
                problems.append(prefix + ":pool_raw_identity:" + str(pool.pool))
    for address, (authority, decimals) in mint_roles.items():
        raw = raw_account(snapshot, address)
        if raw is not None and (len(raw) != 82 or struct.unpack_from("<I", raw)[0] != 1
                                or raw[4:36] != bytes(authority) or raw[44] != decimals or raw[45] != 1
                                or struct.unpack_from("<I", raw, 46)[0] != 0):
            problems.append(prefix + ":mint_raw_identity:" + address)
    for address, (mint, authority) in token_roles.items():
        raw = raw_account(snapshot, address)
        if raw is not None and (len(raw) < 165 or raw[:32] != bytes(mint) or raw[32:64] != bytes(authority)
                                or raw[108] not in (0, 1, 2)
                                or any(struct.unpack_from("<I", raw, offset)[0] not in (0, 1) for offset in (72, 109, 129))):
            problems.append(prefix + ":token_raw_identity:" + address)
    buyback = str(L.BUYBACK)
    old, new = raw_account(initial, buyback), raw_account(snapshot, buyback)
    if old is not None and new is not None and old[:64] != new[:64]:
        problems.append(prefix + ":fee_recipient_token_identity")


def comparable(value, field):
    if field in {"before", "after"}:
        return {key: item for key, item in value.items() if key != str(L.AMM)}
    return value


def verify(report, candidate):
    problems = []
    inputs = None
    images_before = None
    candidate = Path(candidate)
    try:
        inputs = A.snapshot_inputs()
        blobs = {name: A.regular_bytes(path) for name, path in L.CAPTURED.items()}
        blobs["candidate"] = A.regular_bytes(candidate)
        for name, raw in blobs.items():
            _ELF.sections(raw)
            if struct.unpack_from("<H", raw, 18)[0] not in (247, 263) or struct.unpack_from("<I", raw, 0x30)[0] not in (0, 1):
                raise ValueError("unsupported ELF machine/layout: " + name)
        images_before = {name: sha(raw) for name, raw in blobs.items()}
        if any(images_before[name] != digest for name, digest in CAPTURED_HASHES.items()):
            raise ValueError("captured executable identity changed")
        if type(report) is not dict or set(report) != TOP_FIELDS or not scalar_json(report):
            raise ValueError("report fields/types")
        if report["schema"] != "pump-amm-multi-lp-v2" or report["source_snapshot_context_only"] is not True:
            raise ValueError("report version/source context")
        upstream = report["upstream_commit"]
        if type(upstream) is not str or not re.fullmatch(r"[0-9a-f]{40}", upstream):
            raise ValueError("upstream commit must be a full object id")
        if subprocess.run(["git", "merge-base", "--is-ancestor", upstream, "HEAD"], cwd=ROOT, capture_output=True).returncode:
            raise ValueError("upstream context is not current ancestry")
        expected_ids = {"pump_amm": str(L.AMM), "spl_token": str(L.TOKEN), "spl_token_2022": str(L.TOKEN22), "associated_token": str(L.ATA)}
        if not A.same_json(report["program_ids"], expected_ids):
            problems.append("program_ids")
        if not A.same_json(report["program_sha256"], images_before):
            problems.append("program_sha256")
        if not A.same_json(report["producer_input_sha256"], inputs):
            problems.append("producer_input_sha256")
        sources, source_digest = L.source_manifest()
        if not A.same_json(report["candidate_source_sha256"], sources) or report["candidate_source_manifest_sha256"] != source_digest:
            problems.append("source_snapshot_context")
        if not A.same_json(report["candidate_build"], {"kind": "supplied_binary_only", "source_build_verified_by_this_suite": False}):
            problems.append("unsupported_source_build_claim")
        planned = L.plans()
        rows = report["cases"]
        if type(rows) is not list or len(rows) != len(planned) or [r.get("case") for r in rows] != [p["name"] for p in planned]:
            raise ValueError("case membership/order")
        if type(report["case_count"]) is not int or report["case_count"] != len(planned):
            problems.append("case_count")
        classifications = {name: 0 for name in ("equal_observed_behavior", "different_behavior", "unsupported_fixture", "infrastructure_failure")}
        signatures = {"original": [], "candidate": []}
        transactions = {"original": [], "candidate": []}
        count = 0
        # The constructor loads/validates supplied program bytes, but executes
        # no transactions. Immutable copies prevent path mutation during it.
        with tempfile.TemporaryDirectory(prefix="amm-lp-reader-images-") as temporary:
            copied = {}
            for name, raw in blobs.items():
                path = Path(temporary) / (name + ".so")
                path.write_bytes(raw)
                copied[name] = path
            captured = {name: copied[name] for name in L.CAPTURED}
            for index, (row, plan) in enumerate(zip(rows, planned)):
                prefix = plan["name"]
                if type(row) is not dict or set(row) != {"case", "plan", "fixture", "original", "candidate", "mismatch_fields", "expected_original_outcomes", "observed_original_outcomes", "oracle_mismatches", "classification"}:
                    raise ValueError("case fields")
                if not A.same_json(row["plan"], plan):
                    problems.append(prefix + ":plan")
                harness = L.fixture_only(copied["candidate"], index, plan, images=captured)
                fixture = L.expected_fixture(harness)
                roles = owner_roles(harness)
                if not A.same_json(row["fixture"], fixture):
                    problems.append(prefix + ":fixture")
                initials = {side: harness.snapshot(side) for side in ("original", "candidate")}
                canonical = []
                for number, step in enumerate(plan["steps"]):
                    for vm in harness.vms.values():
                        vm.expire_blockhash()
                    blockhash = harness.vms["original"].latest_blockhash()
                    if harness.vms["candidate"].latest_blockhash() != blockhash:
                        raise ValueError("constructor blockhash divergence")
                    canonical.append((*L.plan_step(harness, step, number), blockhash))
                if any(not A.same_json(harness.snapshot(side), initials[side]) for side in initials):
                    raise ValueError("instruction construction changed initial fixture")
                for side in ("original", "candidate"):
                    if type(row[side]) is not dict or set(row[side]) != {"receipts"}:
                        raise ValueError("side fields")
                    receipts = row[side]["receipts"]
                    if type(receipts) is not list or len(receipts) != len(canonical):
                        raise ValueError("receipt membership/count")
                    previous = initials[side]
                    for number, (receipt, step, construction) in enumerate(zip(receipts, plan["steps"], canonical)):
                        point = f"{prefix}:{side}:{number}"
                        if type(receipt) is not dict or set(receipt) != RECEIPT_FIELDS:
                            raise ValueError("receipt fields")
                        label, instructions, signers, operation, expected_blockhash = construction
                        if (receipt["step"], receipt["operation"], receipt["pool_label"]) != (label, operation, step.get("pool", "primary")):
                            problems.append(point + ":step_identity")
                        if type(receipt["instruction_count"]) is not int or receipt["instruction_count"] != len(instructions):
                            problems.append(point + ":instruction_count")
                        if type(receipt["transaction_base64"]) is not str:
                            raise ValueError("transaction base64 type")
                        raw = base64.b64decode(receipt["transaction_base64"], validate=True)
                        if base64.b64encode(raw).decode() != receipt["transaction_base64"]:
                            problems.append(point + ":transaction_encoding")
                        tx = Transaction.from_bytes(raw)
                        if bytes(tx) != raw:
                            problems.append(point + ":transaction_wire_roundtrip")
                        message = Message.new_with_blockhash(instructions, L.FEE_PAYER.pubkey(), expected_blockhash)
                        if tx.message.recent_blockhash != expected_blockhash:
                            problems.append(point + ":blockhash_sequence")
                        if bytes(tx.message) != bytes(message):
                            problems.append(point + ":canonical_message")
                        required = message.header.num_required_signatures
                        verified = tx.verify_with_results()
                        expected_keys = [str(key) for key in message.account_keys[:required]]
                        if not required or len(tx.signatures) != len(verified) or len(verified) != required or any(type(v) is not bool or v is not True for v in verified):
                            problems.append(point + ":nonempty_complete_signatures")
                        if set(expected_keys) != {str(key.pubkey()) for key in signers} or len(expected_keys) != len(signers):
                            raise ValueError("constructor signer roles")
                        if any(str(pool.pool) in expected_keys for pool in harness.pools.values()):
                            raise ValueError("pool PDA must not sign")
                        if not A.same_json(receipt["signer_pubkeys"], expected_keys) or not A.same_json(receipt["signatures"], [str(s) for s in tx.signatures]):
                            problems.append(point + ":signature_metadata")
                        if (receipt["message_sha256"] != sha(bytes(tx.message)) or receipt["blockhash"] != str(tx.message.recent_blockhash)
                                or receipt["blockhash_sha256"] != sha(bytes(tx.message.recent_blockhash))):
                            problems.append(point + ":message_metadata")
                        signatures[side].extend(receipt["signatures"])
                        transactions[side].append(sha(raw))
                        validate_metadata(receipt, tx, len(instructions), point, problems)
                        before, after = receipt["before"], receipt["after"]
                        valid_before = validate_snapshot(before, initials[side], roles, point + ":before", problems)
                        valid_after = validate_snapshot(after, initials[side], roles, point + ":after", problems)
                        if not A.same_json(before, previous):
                            problems.append(point + (":initial_fixture" if number == 0 else ":state_continuity"))
                        previous = after
                        if not valid_before or not valid_after:
                            continue
                        validate_account_roles(before, initials[side], harness, point + ":before", problems)
                        validate_account_roles(after, initials[side], harness, point + ":after", problems)
                        readonly = set()
                        writable = set()
                        for key_index, key in enumerate(message.account_keys):
                            allowed = (key_index < required - message.header.num_readonly_signed_accounts if key_index < required
                                       else key_index < len(message.account_keys) - message.header.num_readonly_unsigned_accounts)
                            (writable if allowed else readonly).add(str(key))
                        if not writable.issubset(set(initials[side])):
                            problems.append(point + ":unwatched_writable_account")
                        # Rent/funding are transfers among watched writable
                        # accounts. With this fixture's ordinary signed messages,
                        # the only lamport sink is LiteSVM's 5000/signature fee.
                        total_before = sum(value["lamports"] for value in before.values() if value is not None)
                        total_after = sum(value["lamports"] for value in after.values() if value is not None)
                        if total_before - total_after != 5000 * required:
                            problems.append(point + ":lamport_fee_conservation")
                        if any(not A.same_json(before[key], after[key]) for key in before if key not in writable):
                            problems.append(point + ":unreferenced_or_readonly_write")
                        expected_rollback = None
                        if receipt["error_detail"] is not None:
                            expected_rollback = A.same_json({k: v for k, v in before.items() if k != fixture["fee_payer"]},
                                                           {k: v for k, v in after.items() if k != fixture["fee_payer"]})
                            if expected_rollback is not True:
                                problems.append(point + ":failed_rollback")
                            payer = fixture["fee_payer"]
                            if not A.same_json({k: v for k, v in before[payer].items() if k != "lamports"},
                                               {k: v for k, v in after[payer].items() if k != "lamports"}):
                                problems.append(point + ":failed_payer_metadata")
                        if not A.same_json(receipt["rollback_nonfee_equal"], expected_rollback):
                            problems.append(point + ":rollback_claim")
                        if side == "original" and not A.same_json(receipt["error_detail"], L.expected_error_detail(prefix, number)):
                            problems.append(point + ":original_error_oracle")
                        active = fixture if step.get("pool", "primary") == "primary" else fixture["secondary"]
                        if not A.same_json(receipt["accounting"], accounting(before, after, active)):
                            problems.append(point + ":accounting")
                        state = economic_state(after, active)
                        if state["pool_reported_lp_supply"] is not None:
                            if state["locked_lp_difference"] != active["minimum_locked_lp"]:
                                problems.append(point + ":locked_lp")
                            lp_addresses = (active["provider_a_accounts"]["lp"], active["provider_b_accounts"]["lp"])
                            # A provider ATA is absent until its signed creation
                            # step; absence means zero shares, not an unknown
                            # balance. Present malformed accounts remain invalid.
                            lp_balances = [0 if after[address] is None else token_amount(after, address)
                                           for address in lp_addresses]
                            if None in lp_balances or sum(lp_balances) != state["lp_mint_supply"]:
                                problems.append(point + ":provider_lp_conservation")
                            if state["base_total"] != 2 * 10**12:
                                problems.append(point + ":base_conservation")
                    if side == "original":
                        count += len(receipts)
                differences = [f"{number}:{field}" for number, (left, right) in enumerate(zip(row["original"]["receipts"], row["candidate"]["receipts"]))
                               for field in STRICT_FIELDS if not A.same_json(comparable(left[field], field), comparable(right[field], field))]
                if not A.same_json(row["mismatch_fields"], differences):
                    problems.append(prefix + ":mismatch_fields")
                observed = [r["outcome"] for r in row["original"]["receipts"]]
                expected = L.EXPECTED_OUTCOMES[prefix]
                oracle = [] if A.same_json(observed, expected) else [{"expected": expected, "observed": observed}]
                if not A.same_json(row["expected_original_outcomes"], expected) or not A.same_json(row["observed_original_outcomes"], observed) or not A.same_json(row["oracle_mismatches"], oracle):
                    problems.append(prefix + ":original_oracle")
                infra = any(r["failure_class"] == "infrastructure" for side in ("original", "candidate") for r in row[side]["receipts"])
                classification = "infrastructure_failure" if infra else "unsupported_fixture" if oracle else "different_behavior" if differences else "equal_observed_behavior"
                if row["classification"] != classification:
                    problems.append(prefix + ":classification")
                classifications[classification] += 1
        for side in signatures:
            if not signatures[side] or len(signatures[side]) != len(set(signatures[side])):
                problems.append(side + ":signature_identity")
            if len(transactions[side]) != len(set(transactions[side])):
                problems.append(side + ":transaction_identity")
        if type(report["transaction_count_per_image"]) is not int or report["transaction_count_per_image"] != count:
            problems.append("transaction_count_per_image")
        if not A.same_json(report["classification_counts"], classifications):
            problems.append("classification_counts")
        if classifications != {"equal_observed_behavior": len(planned), "different_behavior": 0, "unsupported_fixture": 0, "infrastructure_failure": 0}:
            problems.append("qualification_failures")
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, struct.error) as error:
        problems.append("receipt_admission:" + type(error).__name__ + ":" + str(error))
    finally:
        if inputs is not None:
            try:
                A.recheck_inputs(inputs)
            except (OSError, ValueError) as error:
                problems.append("inputs_changed:" + str(error))
        if images_before is not None:
            try:
                images_after = {name: sha(A.regular_bytes(path)) for name, path in L.CAPTURED.items()}
                images_after["candidate"] = sha(A.regular_bytes(candidate))
                if images_after != images_before:
                    problems.append("images_changed_during_verification")
            except (OSError, ValueError) as error:
                problems.append("images_changed:" + str(error))
    return sorted(set(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--build-receipt", type=Path)
    args = parser.parse_args()
    if args.build_receipt is not None:
        parser.error("source-build receipts are not admitted by this supplied-binary fixture")
    raw = A.regular_bytes(args.report)
    report = read(args.report, raw=raw)
    problems = verify(report, args.candidate)
    replay_equal = None
    replay_context = None
    if args.replay and not problems:
        replayed = L.run_suite(args.candidate)
        replay_context = replayed["upstream_commit"]
        # A later evidence commit or merge changes descriptive Git context;
        # actual code/data/image identities remain exact admission gates.
        replay_equal = A.same_json({k: v for k, v in replayed.items() if k != "upstream_commit"},
                                  {k: v for k, v in report.items() if k != "upstream_commit"})
        if not replay_equal:
            problems.append("deterministic_replay")
    if A.regular_bytes(args.report) != raw:
        problems.append("report_changed_during_verification")
    print(json.dumps({"verified": not problems, "problems": sorted(set(problems)),
                      "deterministic_replay_equal": replay_equal,
                      "report_upstream_commit": report.get("upstream_commit") if type(report) is dict else None,
                      "replay_upstream_commit": replay_context,
                      "replay_comparison_scope": "all fields except descriptive upstream_commit; ancestry and exact input/image bindings remain required",
                      "scope": "fixed canonical signed receipts; supplied binary only, no source-build or whole-program-equivalence claim"}, indent=2))
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
