#!/usr/bin/env python3
"""Persistent Pump Main/PumpSwap creator-fee lifecycle differential."""
from __future__ import annotations

import argparse
import base64
import copy
import gzip
import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.message import Message
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[3]
BASE_PATH = ROOT / "reconstruction/verification/pump-admin-cto-stateful/lifecycle.py"
def source_module(name: str, path: Path):
    """Execute admitted source bytes; -B alone still permits reading a .pyc."""
    raw = path.read_bytes()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    module.__dict__["_ADMITTED_SOURCE_BYTES"] = raw
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module, raw


# Load both execution-bearing dependencies from the bytes we bind, so an old
# or injected timestamp-valid bytecode cache cannot change this producer.
_output, OUTPUT_SOURCE_BYTES = source_module(
    "pump_differential_output", ROOT / "scripts/pump_differential_output.py"
)
base, BASE_SOURCE_BYTES = source_module("pump_admin_cto_stateful_base", BASE_PATH)

AMM_IDL_PATH = ROOT / "evidence/upstream/pump_amm.json"
TRADE_FIXTURE_PATH = ROOT / "research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json"
CANDIDATE_PROVENANCE_PATH = Path(__file__).resolve().parent / "candidate-provenance.json"
VERIFIER_PATH = Path(__file__).resolve().parent / "verify.py"
TEST_PATH = Path(__file__).resolve().parent / "test_lifecycle.py"
AMM_IDL_BYTES = AMM_IDL_PATH.read_bytes()
AMM_IDL = json.loads(AMM_IDL_BYTES)
TRADE_FIXTURE_BYTES = TRADE_FIXTURE_PATH.read_bytes()
TRADE_FIXTURE = json.loads(TRADE_FIXTURE_BYTES)
CANDIDATE_PROVENANCE_BYTES = CANDIDATE_PROVENANCE_PATH.read_bytes()
CANDIDATE_PROVENANCE = json.loads(CANDIDATE_PROVENANCE_BYTES)
AMM_BUY = next(row for row in AMM_IDL["instructions"] if row["name"] == "buy_v2")
AMM_SWEEP = next(row for row in AMM_IDL["instructions"] if row["name"] == "sweep_creator_fee")
AMM_COLLECT = next(row for row in AMM_IDL["instructions"] if row["name"] == "collect_coin_creator_fee")

PAYER = base.PAYER
ADMIN = base.ADMIN
CREATORS = base.CREATORS
PUMP = base.PUMP
AMM = base.AMM
FEES = base.FEES
TOKEN = base.TOKEN
ATA = base.ATA
SYSTEM = base.SYSTEM
WSOL = base.WSOL
AMM_EVENT = base.AMM_EVENT
PUMP_EVENT = base.PUMP_EVENT

FEE_CONFIG = base.P(TRADE_FIXTURE["keys"]["fee_config"])
BUYBACK_RECIPIENT = base.P(TRADE_FIXTURE["accounts"]["buyback_fee_recipient"]["address"])
TRADE_POOL_TEMPLATE = bytearray(base64.b64decode(TRADE_FIXTURE["accounts"]["pool"]["data_base64"]))
POOL_BASE_AMOUNT = int(TRADE_FIXTURE["pool_base_vault_amount_raw"])
POOL_QUOTE_AMOUNT = int(TRADE_FIXTURE["pool_quote_vault_amount_raw"])
USER_QUOTE_AMOUNT = 10**15
TRADE_BASE_AMOUNT = 10**10
TRADE_MAX_QUOTE = 10**9

PRODUCER_PATHS = (
    Path(__file__).resolve(),
    BASE_PATH,
    ROOT / "scripts/pump_differential_output.py",
    base.IDL_PATH,
    base.CONFIG_PATH,
    AMM_IDL_PATH,
    TRADE_FIXTURE_PATH,
    CANDIDATE_PROVENANCE_PATH,
    VERIFIER_PATH,
    TEST_PATH,
)

LOADED_INPUT_SHA256 = {
    path.relative_to(ROOT).as_posix(): base.file_sha(path) for path in PRODUCER_PATHS
}
LOADED_INPUT_SHA256[BASE_PATH.relative_to(ROOT).as_posix()] = base.sha(BASE_SOURCE_BYTES)
LOADED_INPUT_SHA256["scripts/pump_differential_output.py"] = base.sha(OUTPUT_SOURCE_BYTES)
if "_ADMITTED_SOURCE_BYTES" in globals():
    LOADED_INPUT_SHA256[Path(__file__).resolve().relative_to(ROOT).as_posix()] = base.sha(_ADMITTED_SOURCE_BYTES)
# The base module records the bytes it admitted when it was loaded. Its decoded
# IDL/config values must agree with this closure as well as with current files.
for _name, _digest in base.LOADED_INPUT_SHA256.items():
    if _name in LOADED_INPUT_SHA256 and LOADED_INPUT_SHA256[_name] != _digest:
        raise ValueError("producer input changed during import: " + _name)

STRICT_FIELDS = base.STRICT_FIELDS


def same_json(left, right) -> bool:
    """Compare saved claims without Python's bool/int/float coercions."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def recheck_inputs() -> None:
    for name, digest in LOADED_INPUT_SHA256.items():
        if base.file_sha(ROOT / name) != digest:
            raise ValueError("producer input changed after import: " + name)
    if base.sha(base.IDL_BYTES) != LOADED_INPUT_SHA256[base.IDL_PATH.relative_to(ROOT).as_posix()]:
        raise ValueError("loaded Pump IDL differs from admitted bytes")
    if base.sha(base.CONFIG_BYTES) != LOADED_INPUT_SHA256[base.CONFIG_PATH.relative_to(ROOT).as_posix()]:
        raise ValueError("loaded config differs from admitted bytes")


def instruction(name: str):
    return next(row for row in AMM_IDL["instructions"] if row["name"] == name)


def native_token_data(mint, owner, amount: int, rent: int) -> bytes:
    data = bytearray(base.token_data(mint, owner, amount))
    data[109:113] = (1).to_bytes(4, "little")
    data[113:121] = rent.to_bytes(8, "little")
    return bytes(data)


def token_amount(account: dict | None) -> int | None:
    if account is None:
        return None
    raw = base64.b64decode(account["data_base64"], validate=True)
    return int.from_bytes(raw[64:72], "little") if len(raw) >= 72 else None


def pool_u64(account: dict | None, offset: int) -> int | None:
    if account is None:
        return None
    raw = base64.b64decode(account["data_base64"], validate=True)
    return int.from_bytes(raw[offset:offset + 8], "little") if len(raw) >= offset + 8 else None


class Harness(base.Harness):
    """Merged Admin CTO fixture extended with a canonical tradable PumpSwap pool."""

    def __init__(self, pump_image: Path, images=None, case_index: int = 0):
        super().__init__(pump_image, {
            "name": "cross-program/creator-fee-lifecycle",
            "mints": ["native"],
            "complete": True,
            "native_vault_lamports": 890_880,
        }, images, case_index)

    def _seed(self) -> None:
        super()._seed()
        fixture = self.mints[0]
        self.vm.set_clock(Clock(1_000, 0, 0, 0, 1_700_000_000))

        # Keep the captured config bytes and fee table, but make the retained
        # pool canonical for this deterministic mint and index zero.
        amm_config = bytearray(self.vm.get_account(base.AMM_CONFIG_KEY).data)
        amm_config[56] = 0
        self.put(base.AMM_CONFIG_KEY, Account(10**9, bytes(amm_config), AMM))
        fee_row = TRADE_FIXTURE["accounts"]["fee_config"]
        self.put(FEE_CONFIG, Account(fee_row["lamports"], base64.b64decode(fee_row["data_base64"]), FEES))
        buyback_row = TRADE_FIXTURE["accounts"]["buyback_fee_recipient"]
        self.put(BUYBACK_RECIPIENT, Account(
            buyback_row["lamports"], base64.b64decode(buyback_row["data_base64"]),
            base.P(buyback_row["owner"]),
        ))

        pool_base = base.ata(fixture.pool, fixture.mint, TOKEN)
        pool_quote = base.ata(fixture.pool, fixture.quote, TOKEN)
        user_base = base.ata(PAYER.pubkey(), fixture.mint, TOKEN)
        user_quote = base.ata(PAYER.pubkey(), fixture.quote, TOKEN)
        volume = base.pda(b"user_volume_accumulator", bytes(PAYER.pubkey()), program=AMM)
        self.pool_base = pool_base
        self.pool_quote = pool_quote
        self.user_base = user_base
        self.user_quote = user_quote
        self.volume = volume

        pool = bytearray(TRADE_POOL_TEMPLATE)
        pool.extend(bytes(max(0, 301 - len(pool))))
        bump = base.Pubkey.find_program_address(
            [b"pool", bytes(2), bytes(fixture.pool_authority), bytes(fixture.mint), bytes(fixture.quote)], AMM
        )[1]
        pool[8] = bump
        pool[9:11] = bytes(2)
        pool[11:43] = bytes(fixture.pool_authority)
        pool[43:75] = bytes(fixture.mint)
        pool[75:107] = bytes(fixture.quote)
        pool[139:171] = bytes(pool_base)
        pool[171:203] = bytes(pool_quote)
        pool[211:243] = bytes(CREATORS[0].pubkey())
        pool[243:245] = bytes(2)
        pool[261:263] = bytes(2)
        pool[271:287] = bytes(16)
        pool[287:303] = bytes(16)
        self.put(fixture.pool, Account(10**9, bytes(pool), AMM))

        rent = self.vm.minimum_balance_for_rent_exemption(165)
        self.put(pool_base, Account(rent, base.token_data(fixture.mint, fixture.pool, POOL_BASE_AMOUNT), TOKEN))
        self.put(pool_quote, Account(
            rent + POOL_QUOTE_AMOUNT,
            native_token_data(fixture.quote, fixture.pool, POOL_QUOTE_AMOUNT, rent), TOKEN,
        ))
        self.put(user_base, Account(rent, base.token_data(fixture.mint, PAYER.pubkey(), 0), TOKEN))
        self.put(user_quote, Account(
            rent + USER_QUOTE_AMOUNT,
            native_token_data(fixture.quote, PAYER.pubkey(), USER_QUOTE_AMOUNT, rent), TOKEN,
        ))
        self.put(volume, Account(0, b"", SYSTEM))

        # Pre-create every canonical native token account. This keeps rent
        # creation out of the accounting oracle while retaining real SPL CPI.
        for creator in (kp.pubkey() for kp in CREATORS):
            amm_vault = base.pda(b"creator_vault", bytes(creator), program=AMM)
            for owner in (creator, amm_vault):
                self.put(base.ata(owner, fixture.quote, TOKEN), Account(
                    rent, native_token_data(fixture.quote, owner, 0, rent), TOKEN,
                ))

    @property
    def fixture(self):
        return self.mints[0]

    def trade_instruction(self, amount: int = TRADE_BASE_AMOUNT, limit: int = TRADE_MAX_QUOTE) -> Instruction:
        names = {
            "pool": self.fixture.pool,
            "user": PAYER.pubkey(),
            "global_config": base.AMM_CONFIG_KEY,
            "base_mint": self.fixture.mint,
            "quote_mint": self.fixture.quote,
            "user_base_token_account": self.user_base,
            "user_quote_token_account": self.user_quote,
            "pool_base_token_account": self.pool_base,
            "pool_quote_token_account": self.pool_quote,
            "base_token_program": TOKEN,
            "quote_token_program": TOKEN,
            "system_program": SYSTEM,
            "user_volume_accumulator": self.volume,
            "fee_config": FEE_CONFIG,
            "buyback_fee_recipient": BUYBACK_RECIPIENT,
            "event_authority": AMM_EVENT,
            "program": AMM,
        }
        metas = [AccountMeta(names[row["name"]], bool(row.get("signer")), bool(row.get("writable")))
                 for row in AMM_BUY["accounts"]]
        return Instruction(AMM, bytes(AMM_BUY["discriminator"]) + struct.pack("<QQ", amount, limit), metas)

    def sweep_instruction(self) -> Instruction:
        creator = base.Pubkey.from_bytes(self.vm.get_account(self.fixture.pool).data[211:243])
        recipient = base.pda(b"creator_vault", bytes(creator), program=AMM)
        names = {
            "payer": PAYER.pubkey(),
            "global_config": base.AMM_CONFIG_KEY,
            "pool": self.fixture.pool,
            "quote_mint": self.fixture.quote,
            "quote_token_program": TOKEN,
            "pool_quote_token_account": self.pool_quote,
            "recipient": recipient,
            "recipient_token_account": base.ata(recipient, self.fixture.quote, TOKEN),
            "system_program": SYSTEM,
            "associated_token_program": ATA,
            "event_authority": AMM_EVENT,
            "program": AMM,
        }
        metas = [AccountMeta(names[row["name"]], bool(row.get("signer")), bool(row.get("writable")))
                 for row in AMM_SWEEP["accounts"]]
        return Instruction(AMM, bytes(AMM_SWEEP["discriminator"]), metas)

    def amm_collect_instruction(self, creator_index: int) -> Instruction:
        creator = CREATORS[creator_index].pubkey()
        authority = base.pda(b"creator_vault", bytes(creator), program=AMM)
        names = {
            "quote_mint": self.fixture.quote,
            "quote_token_program": TOKEN,
            "coin_creator": creator,
            "coin_creator_vault_authority": authority,
            "coin_creator_vault_ata": base.ata(authority, self.fixture.quote, TOKEN),
            "coin_creator_token_account": base.ata(creator, self.fixture.quote, TOKEN),
            "event_authority": AMM_EVENT,
            "program": AMM,
        }
        metas = [AccountMeta(names[row["name"]], bool(row.get("signer")), bool(row.get("writable")))
                 for row in AMM_COLLECT["accounts"]]
        return Instruction(AMM, bytes(AMM_COLLECT["discriminator"]), metas)

    def instructions_for(self, step: dict) -> list[Instruction]:
        result = []
        for operation in step["operations"]:
            name = operation["op"]
            if name == "amm_buy_v2":
                result.append(self.trade_instruction(operation.get("amount", TRADE_BASE_AMOUNT),
                                                     operation.get("limit", TRADE_MAX_QUOTE)))
            elif name == "amm_sweep_creator_fee":
                result.append(self.sweep_instruction())
            elif name == "amm_collect_creator_fee":
                result.append(self.amm_collect_instruction(operation["creator"]))
            elif name == "pump_admin_cto":
                result.append(self.admin_instruction({"op": "admin_cto", "new": operation["new"],
                                                      "name": step["name"]}))
            elif name == "pump_collect_creator_fee":
                result.append(self.collect_instruction({"op": "collect", "creator": operation["creator"],
                                                        "name": step["name"]}))
            else:
                raise ValueError(f"unknown operation {name}")
        return result

    def execute_step(self, step: dict, index: int) -> dict:
        self.vm.expire_blockhash()
        self.vm.set_clock(Clock(1_000 + index, 0, 0, 0, 1_700_000_000 + index))
        before = self.snapshot()
        instructions = self.instructions_for(step)
        needs_admin = any(item["op"] == "pump_admin_cto" for item in step["operations"])
        signers = [PAYER, ADMIN] if needs_admin else [PAYER]
        blockhash = self.vm.latest_blockhash()
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), *instructions], PAYER.pubkey(), signers, blockhash
        )
        checks = list(tx.verify_with_results())
        if checks != [True] * len(signers):
            raise ValueError("locally constructed transaction failed signature verification")
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        raw = json.loads(meta.to_json())
        logs = list(meta.logs())
        after = self.snapshot()
        nonfee = lambda state: {key: value for key, value in state.items() if key != str(PAYER.pubkey())}
        error = str(result.err()) if failed else None
        return {
            "step": step["name"],
            "operation": "+".join(item["op"] for item in step["operations"]),
            "operations": copy.deepcopy(step["operations"]),
            "recent_blockhash": str(blockhash),
            "transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "signature": str(tx.signatures[0]),
            "signature_verification": checks,
            "message_sha256": base.sha(bytes(tx.message)),
            "error": error,
            "outcome": base.outcome(logs, error),
            "failure_class": base.failure_class(error),
            "compute_units": meta.compute_units_consumed(),
            "logs": logs,
            "semantic_logs": base.semantic_logs(logs),
            "events": [line[14:] for line in logs if line.startswith("Program data: ")],
            "inner_instructions": raw.get("inner_instructions"),
            "return_data": raw.get("return_data"),
            "before_hash": base.canonical_hash(before),
            "after_hash": base.canonical_hash(after),
            "before": before,
            "after": after,
            "rollback_nonfee_equal": None if not failed else nonfee(before) == nonfee(after),
        }


STEPS = [
    {"name": "trade-A", "operations": [{"op": "amm_buy_v2"}]},
    {"name": "sweep-A", "operations": [{"op": "amm_sweep_creator_fee"}]},
    {"name": "collect-A", "operations": [{"op": "amm_collect_creator_fee", "creator": 0}]},
    {"name": "admin-A-to-B", "operations": [{"op": "pump_admin_cto", "new": 1}]},
    {"name": "trade-B", "operations": [{"op": "amm_buy_v2"}]},
    {"name": "atomic-unswept-B-to-C", "operations": [
        {"op": "amm_buy_v2"}, {"op": "pump_admin_cto", "new": 2},
    ]},
    {"name": "atomic-sweep-B-to-C-retry", "operations": [
        {"op": "amm_sweep_creator_fee"}, {"op": "pump_admin_cto", "new": 2},
    ]},
    {"name": "collect-B-empty-after-cto", "operations": [{"op": "amm_collect_creator_fee", "creator": 1}]},
    {"name": "trade-C", "operations": [{"op": "amm_buy_v2"}]},
    {"name": "sweep-C", "operations": [{"op": "amm_sweep_creator_fee"}]},
    {"name": "collect-C", "operations": [{"op": "amm_collect_creator_fee", "creator": 2}]},
]


# Retain one immutable plan contract per loaded producer. A caller must not
# shorten the mutable public list while retaining the old declared case count.
PLAN_SHA256 = base.canonical_hash(STEPS)
EXPECTED_TRANSACTION_COUNT = 11


def checked_steps() -> list[dict]:
    if len(STEPS) != EXPECTED_TRANSACTION_COUNT or base.canonical_hash(STEPS) != PLAN_SHA256:
        raise ValueError("lifecycle plan changed after import")
    return copy.deepcopy(STEPS)


def canonical_accounts() -> dict[str, str]:
    fixture = Harness._mint_fixture(0, "native")
    return {
        "pool": str(fixture.pool), "curve": str(fixture.curve),
        "pool_base": str(base.ata(fixture.pool, fixture.mint, TOKEN)),
        "pool_quote": str(base.ata(fixture.pool, fixture.quote, TOKEN)),
        "user_base": str(base.ata(PAYER.pubkey(), fixture.mint, TOKEN)),
        "user_quote": str(base.ata(PAYER.pubkey(), fixture.quote, TOKEN)),
        "user_volume": str(base.pda(b"user_volume_accumulator", bytes(PAYER.pubkey()), program=AMM)),
    }


def expected_snapshot_keys() -> set[str]:
    """Every account constructed by this one fixed fixture, including no-ops."""
    fixture = Harness._mint_fixture(0, "native")
    keys = {base.GLOBAL, base.AMM_CONFIG_KEY, PAYER.pubkey(), ADMIN.pubkey(),
            *(kp.pubkey() for kp in CREATORS), PUMP_EVENT, AMM_EVENT, base.FEES_EVENT,
            fixture.mint, fixture.quote, fixture.curve, fixture.sharing, fixture.pool,
            fixture.pool_authority, FEE_CONFIG, BUYBACK_RECIPIENT}
    keys.update(base.P(value) for value in canonical_accounts().values())
    for creator in (fixture.sharing, fixture.holder, *(kp.pubkey() for kp in CREATORS)):
        vault = base.pda(b"creator-vault", bytes(creator))
        amm_vault = base.pda(b"creator_vault", bytes(creator), program=AMM)
        keys.update((vault, amm_vault, base.ata(creator, fixture.quote, TOKEN),
                     base.ata(vault, fixture.quote, TOKEN), base.ata(amm_vault, fixture.quote, TOKEN)))
    holder_vault = base.pda(b"creator-vault", bytes(fixture.holder))
    keys.add(base.ata(holder_vault, fixture.quote, TOKEN))
    return {str(key) for key in keys}


def planned_message(row: dict, plan: dict, blockhash) -> Message:
    """Reconstruct exact instructions/accounts without executing a VM.

    The two instructions that select a current creator read only the declared
    before-state, already covered by state continuity and creator invariants.
    """
    class Snapshot:
        def get_account(self, key):
            saved = row["before"][str(key)]
            if saved is None:
                raise ValueError("planned instruction needs an absent account")
            return Account(saved["lamports"], base64.b64decode(saved["data_base64"], validate=True),
                           base.P(saved["owner"]), saved["executable"], saved["rent_epoch"])
    harness = object.__new__(Harness)
    harness.mints = [Harness._mint_fixture(0, "native")]
    harness.vm = Snapshot()
    for field, key in canonical_accounts().items():
        if field in ("pool_base", "pool_quote", "user_base", "user_quote"):
            setattr(harness, field, base.P(key))
    harness.volume = base.P(canonical_accounts()["user_volume"])
    instructions = [set_compute_unit_limit(1_400_000), *harness.instructions_for(plan)]
    return Message.new_with_blockhash(instructions, PAYER.pubkey(), blockhash)


def run_image(image: Path, images=None, case_index: int = 0) -> dict:
    harness = Harness(image, images, case_index)
    initial = harness.snapshot()
    receipts = [harness.execute_step(step, index) for index, step in enumerate(checked_steps(), 1)]
    return {
        "initial_state_hash": base.canonical_hash(initial),
        "receipts": receipts,
        "accounts": {
            "pool": str(harness.fixture.pool),
            "curve": str(harness.fixture.curve),
            "pool_base": str(harness.pool_base),
            "pool_quote": str(harness.pool_quote),
            "user_base": str(harness.user_base),
            "user_quote": str(harness.user_quote),
            "user_volume": str(harness.volume),
        },
    }


def compare_runs(original: dict, candidate: dict) -> tuple[list[str], list[dict]]:
    mismatches = []
    if original["initial_state_hash"] != candidate["initial_state_hash"]:
        mismatches.append("initial_state_hash")
    if len(original["receipts"]) != len(candidate["receipts"]):
        return mismatches + ["receipt_count"], []
    comparison = []
    for left, right in zip(original["receipts"], candidate["receipts"]):
        strict = [field for field in STRICT_FIELDS
                  if base.canonical_hash(left.get(field)) != base.canonical_hash(right.get(field))]
        diagnostic = [field for field in ("logs", "compute_units")
                      if base.canonical_hash(left.get(field)) != base.canonical_hash(right.get(field))]
        comparison.append({"step": left["step"], "mismatch_fields": strict,
                           "diagnostic_difference_fields": diagnostic})
        mismatches.extend(f"{left['step']}:{field}" for field in strict)
    return mismatches, comparison


def validate_run(run: dict) -> list[str]:
    failures = []
    previous = None
    signatures = []
    try:
        plans = checked_steps()
        if len(run["receipts"]) != EXPECTED_TRANSACTION_COUNT:
            return ["receipt-count"]
        if not same_json(run["accounts"], canonical_accounts()):
            failures.append("canonical-accounts")
        for row, plan in zip(run["receipts"], plans):
            tag = row["step"]
            if tag != plan["name"] or not same_json(row["operations"], plan["operations"]):
                failures.append(tag + ":operation-plan")
            raw = base64.b64decode(row["transaction_base64"], validate=True)
            tx = Transaction.from_bytes(raw)
            required = tx.message.header.num_required_signatures
            checked = list(tx.verify_with_results())
            if (bytes(tx) != raw or required < 1 or len(tx.signatures) != required
                    or checked != [True] * required
                    or not same_json(row["signature_verification"], checked)
                    or row["signature"] != str(tx.signatures[0])
                    or row["message_sha256"] != base.sha(bytes(tx.message))
                    or row["recent_blockhash"] != str(tx.message.recent_blockhash)
                    or tx.message.account_keys[0] != PAYER.pubkey()):
                failures.append(tag + ":signature-verification")
            expected_signers = {PAYER.pubkey()}
            if any(op["op"] == "pump_admin_cto" for op in plan["operations"]):
                expected_signers.add(ADMIN.pubkey())
            signers = set(tx.message.account_keys[:required])
            if signers != expected_signers or bytes(tx.message) != bytes(planned_message(row, plan, tx.message.recent_blockhash)):
                failures.append(tag + ":signed-instruction-plan")
            signatures.append(str(tx.signatures[0]))
            for stage in ("before", "after"):
                state = row[stage]
                if set(state) != expected_snapshot_keys():
                    failures.append(tag + ":" + stage + "-membership")
                if row[stage + "_hash"] != base.canonical_hash(state):
                    failures.append(tag + ":" + stage + "-hash")
                for key, account in state.items():
                    base.P(key)
                    if account is None:
                        continue
                    data = base64.b64decode(account["data_base64"], validate=True)
                    base.P(account["owner"])
                    if (len(data) != account["data_len"] or base.sha(data) != account["data_sha256"]
                            or type(account["lamports"]) is not int or account["lamports"] < 0
                            or type(account["data_len"]) is not int
                            or type(account["rent_epoch"]) is not int or account["rent_epoch"] < 0
                            or type(account["executable"]) is not bool):
                        failures.append(tag + ":account-snapshot")
            if previous is None:
                if run["initial_state_hash"] != base.canonical_hash(row["before"]):
                    failures.append(tag + ":initial-state")
            elif base.canonical_hash(previous) != base.canonical_hash(row["before"]):
                failures.append(tag + ":state-continuity")
            previous = row["after"]
            nonfee = lambda state: {key: value for key, value in state.items() if key != str(PAYER.pubkey())}
            rollback = None if row["error"] is None else nonfee(row["before"]) == nonfee(row["after"])
            if not same_json(rollback, row["rollback_nonfee_equal"]) or rollback is False:
                failures.append(tag + ":atomic-rollback")
            if (row["outcome"] != base.outcome(row["logs"], row["error"])
                    or row["failure_class"] != base.failure_class(row["error"])
                    or row["semantic_logs"] != base.semantic_logs(row["logs"])
                    or row["events"] != [line[14:] for line in row["logs"] if line.startswith("Program data: ")]):
                failures.append(tag + ":derived-fields")
        if len(signatures) != len(set(signatures)):
            failures.append("duplicate-signature")
    except (KeyError, TypeError, ValueError, IndexError) as error:
        failures.append("malformed-receipt:" + type(error).__name__)
    return failures


def lifecycle_invariants(run: dict) -> list[str]:
    failures = []
    rows = {row["step"]: row for row in run["receipts"]}
    keys = run["accounts"]
    pool = keys["pool"]
    user_base = keys["user_base"]
    pool_base = keys["pool_base"]
    user_quote = keys["user_quote"]
    pool_quote = keys["pool_quote"]

    expected_success = {step["name"] for step in STEPS} - {"atomic-unswept-B-to-C"}
    for name, row in rows.items():
        if (name in expected_success) != (row["error"] is None):
            failures.append(name + ":unexpected-outcome")
        expected_fee = 10_000 if any(op["op"] == "pump_admin_cto" for op in row["operations"]) else 5_000
        payer_before = row["before"][str(PAYER.pubkey())]["lamports"]
        payer_after = row["after"][str(PAYER.pubkey())]["lamports"]
        volume_before_account = row["before"][keys["user_volume"]]
        volume_after_account = row["after"][keys["user_volume"]]
        volume_before = 0 if volume_before_account is None else volume_before_account["lamports"]
        volume_after = 0 if volume_after_account is None else volume_after_account["lamports"]
        if payer_before - payer_after != expected_fee + volume_after - volume_before:
            failures.append(name + ":payer-fee")
        # All tracked lamports conserve except the transaction fee. This also
        # covers ATA closures and the first trade's real accumulator creation.
        before_total = sum(account["lamports"] for account in row["before"].values() if account is not None)
        after_total = sum(account["lamports"] for account in row["after"].values() if account is not None)
        if before_total - after_total != expected_fee:
            failures.append(name + ":tracked-lamport-conservation")

    for name in ("trade-A", "trade-B", "trade-C"):
        row = rows[name]
        if (token_amount(row["after"][user_base]) - token_amount(row["before"][user_base]) <= 0
                or token_amount(row["after"][pool_base]) - token_amount(row["before"][pool_base]) >= 0
                or token_amount(row["after"][user_quote]) - token_amount(row["before"][user_quote]) >= 0
                or token_amount(row["after"][pool_quote]) - token_amount(row["before"][pool_quote]) <= 0
                or pool_u64(row["after"][pool], 279) <= pool_u64(row["before"][pool], 279)):
            failures.append(name + ":trade-accounting")

    if rows["atomic-unswept-B-to-C"]["rollback_nonfee_equal"] is not True:
        failures.append("atomic-unswept-B-to-C:not-rolled-back")
    failed = rows["atomic-unswept-B-to-C"]
    if (failed["outcome"] != "error:CreatorFeesNotSwept"
            or failed["error"] != "TransactionErrorInstructionError((2, Tagged(InstructionErrorCustom(6081))))"):
        failures.append("atomic-unswept-B-to-C:wrong-error")

    for name in ("sweep-A", "atomic-sweep-B-to-C-retry", "sweep-C"):
        row = rows[name]
        if pool_u64(row["after"][pool], 279) != 0:
            failures.append(name + ":creator-fees-not-zero")

    curve = keys["curve"]
    for name, creator_index in (("admin-A-to-B", 1), ("atomic-sweep-B-to-C-retry", 2)):
        row = rows[name]
        curve_bytes = base64.b64decode(row["after"][curve]["data_base64"], validate=True)
        pool_bytes = base64.b64decode(row["after"][pool]["data_base64"], validate=True)
        if curve_bytes[49:81] != bytes(CREATORS[creator_index].pubkey()) or pool_bytes[211:243] != bytes(CREATORS[creator_index].pubkey()):
            failures.append(name + ":creator-transition")
    retry = rows["atomic-sweep-B-to-C-retry"]
    curve_data = base64.b64decode(retry["after"][curve]["data_base64"])
    pool_data = base64.b64decode(retry["after"][pool]["data_base64"])
    if curve_data[49:81] != bytes(CREATORS[2].pubkey()) or pool_data[211:243] != bytes(CREATORS[2].pubkey()):
        failures.append("atomic-sweep-B-to-C-retry:creator-not-C")
    creator_b_destination = str(base.ata(CREATORS[1].pubkey(), WSOL, TOKEN))
    if token_amount(retry["after"][creator_b_destination]) <= token_amount(retry["before"][creator_b_destination]):
        failures.append("atomic-sweep-B-to-C-retry:B-fees-not-forwarded")

    for name, creator_index in (("collect-A", 0), ("collect-C", 2)):
        row = rows[name]
        creator = CREATORS[creator_index].pubkey()
        destination = str(base.ata(creator, WSOL, TOKEN))
        if token_amount(row["after"][destination]) <= token_amount(row["before"][destination]):
            failures.append(name + ":token-collection")
    empty = rows["collect-B-empty-after-cto"]
    if (token_amount(empty["after"][creator_b_destination])
            != token_amount(empty["before"][creator_b_destination]) or empty["events"]):
        failures.append("collect-B-empty-after-cto:not-empty")

    # Every native-token amount delta must be mirrored by its account lamports.
    for row in run["receipts"]:
        for key in (user_quote, pool_quote, *(str(base.ata(CREATORS[i].pubkey(), WSOL, TOKEN)) for i in range(3))):
            before, after = row["before"].get(key), row["after"].get(key)
            if before is None or after is None or token_amount(before) is None or token_amount(after) is None:
                continue
            if ((after["lamports"] - before["lamports"])
                    != (token_amount(after) - token_amount(before))):
                failures.append(row["step"] + ":native-lamport-token-delta:" + key)
    return failures


def source_manifest() -> tuple[dict, str]:
    rows = {}
    for path in sorted((ROOT / "programs/pump").rglob("*")):
        if path.is_file() and "target" not in path.parts:
            rows[path.relative_to(ROOT).as_posix()] = base.file_sha(path)
    return rows, base.canonical_hash(rows)


def candidate_binding(candidate_sha256: str) -> tuple[dict, dict]:
    if candidate_sha256 == CANDIDATE_PROVENANCE["candidate_sha256"]:
        return CANDIDATE_PROVENANCE, {
            "candidate_source_revision": CANDIDATE_PROVENANCE["source_revision"],
            "current_source_manifest_role": "review_context_only",
        }
    if candidate_sha256 == base.file_sha(base.CAPTURED["pump_original"]):
        return {"schema": "captured-original-control-v1", "candidate_sha256": candidate_sha256}, {
            "candidate_source_revision": None,
            "current_source_manifest_role": "original-vs-original control only",
        }
    return {"schema": "supplied-candidate-input-v1", "candidate_sha256": candidate_sha256,
            "limits": "Supplied immutable binary only; this packet establishes no source/build linkage."}, {
        "candidate_source_revision": None,
        "current_source_manifest_role": "review_context_only",
    }


def run_suite(candidate: Path) -> dict:
    recheck_inputs()
    checked_steps()
    source_files, source_digest = source_manifest()
    snapshots = {name: path.read_bytes() for name, path in base.CAPTURED.items()}
    snapshots["pump_candidate"] = candidate.read_bytes()
    with tempfile.TemporaryDirectory(prefix="pump-cross-program-lifecycle-") as scratch:
        images = {name: Path(scratch) / (name + ".so") for name in snapshots}
        for name, raw in snapshots.items():
            images[name].write_bytes(raw)
        original = run_image(images["pump_original"], images)
        rebuilt = run_image(images["pump_candidate"], images)
    mismatches, comparison = compare_runs(original, rebuilt)
    original_receipt_failures = validate_run(original)
    candidate_receipt_failures = validate_run(rebuilt)
    original_invariants = lifecycle_invariants(original)
    candidate_invariants = lifecycle_invariants(rebuilt)
    infrastructure = [
        f"{side}:{row['step']}"
        for side, run in (("original", original), ("candidate", rebuilt))
        for row in run["receipts"] if row["failure_class"] == "infrastructure"
    ]
    hashes = {name: base.sha(raw) for name, raw in snapshots.items()}
    provenance, source_binding = candidate_binding(hashes["pump_candidate"])
    recheck_inputs()
    if source_manifest() != (source_files, source_digest):
        raise ValueError("source review context changed during run")
    return {
        "schema": "pump-cross-program-fee-lifecycle-v1",
        "scope": "Persistent signed Pump Main/PumpSwap creator-fee lifecycle in independent LiteSVM instances.",
        "classification": (
            "infrastructure_failure" if infrastructure else
            "unsupported_fixture" if original_invariants or original_receipt_failures else
            "different_behavior" if mismatches or candidate_invariants or candidate_receipt_failures else
            "equal_observed_behavior"
        ),
        "program_ids": {
            "pump": str(PUMP), "pump_amm": str(AMM), "pump_fees": str(FEES),
            "spl_token": str(TOKEN), "associated_token": str(ATA),
        },
        "program_sha256": hashes,
        "idl_sha256": {"pump": base.sha(base.IDL_BYTES), "pump_amm": base.sha(AMM_IDL_BYTES)},
        "fixture_sha256": base.sha(TRADE_FIXTURE_BYTES),
        "candidate_provenance": provenance,
        "candidate_provenance_sha256": base.sha(CANDIDATE_PROVENANCE_BYTES),
        "source_binding": source_binding,
        "producer_input_sha256": dict(LOADED_INPUT_SHA256),
        "source_manifest_sha256": source_digest,
        "source_files": source_files,
        "transaction_count_per_image": len(STEPS),
        "multi_instruction_transactions_per_image": sum(len(step["operations"]) > 1 for step in STEPS),
        "original": original,
        "candidate": rebuilt,
        "comparison": comparison,
        "mismatch_fields": mismatches,
        "receipt_failures": {"original": original_receipt_failures, "candidate": candidate_receipt_failures},
        "invariant_failures": {"original": original_invariants, "candidate": candidate_invariants},
        "infrastructure_failures": infrastructure,
    }


def negative_controls(report: dict) -> dict:
    checks = {}
    for field, mutate in (
        ("error", lambda row: row.update(error="negative-control")),
        ("after", lambda row: row["after"].update({"negative-control": None})),
        ("events", lambda row: row["events"].append("negative-control")),
        ("inner_instructions", lambda row: row.update(inner_instructions=[])),
    ):
        changed = copy.deepcopy(report["candidate"])
        mutate(changed["receipts"][0])
        differences, _ = compare_runs(report["original"], changed)
        checks[field] = any(item.endswith(":" + field) for item in differences)
    return checks


def write_report(path: Path, report: dict, publisher=None) -> None:
    raw = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if publisher is None:
        publisher = base.PumpReport(path, ROOT, None, __file__, overwrite=False,
                                    extra_inputs=[*base.CAPTURED.values(), *PRODUCER_PATHS, ROOT / "programs/pump"])
    publisher.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-mismatches", action="store_true")
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit(f"refusing to overwrite existing report: {args.output}")
    publisher = base.PumpReport(
        args.output, ROOT, args.candidate, __file__, overwrite=False,
        extra_inputs=[*base.CAPTURED.values(), *PRODUCER_PATHS, ROOT / "programs/pump"],
    )
    report = run_suite(args.candidate.resolve())
    report["negative_controls"] = negative_controls(report)
    write_report(args.output, report, publisher)
    summary = {key: report[key] for key in (
        "classification", "transaction_count_per_image", "multi_instruction_transactions_per_image",
        "mismatch_fields", "receipt_failures", "invariant_failures", "infrastructure_failures",
        "negative_controls",
    )}
    print(json.dumps(summary, indent=2))
    failed = (report["classification"] != "equal_observed_behavior"
              or not all(report["negative_controls"].values()))
    return 0 if args.allow_mismatches or not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
