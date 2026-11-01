#!/usr/bin/env python3
"""Persistent, authenticated Pump ``admin_cto`` differential qualification."""
from __future__ import annotations

import argparse
import base64
import copy
import gzip
import hashlib
import json
import struct
import sys
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from pump_differential_output import PumpReport  # noqa: E402

IDL_PATH = ROOT / "evidence/upstream/pump.json"
IDL_BYTES = IDL_PATH.read_bytes()
IDL = json.loads(IDL_BYTES)
ADMIN_CTO = next(row for row in IDL["instructions"] if row["name"] == "admin_cto")
COLLECT = next(row for row in IDL["instructions"] if row["name"] == "collect_creator_fee")

P = Pubkey.from_string
PUMP = P(IDL["address"])
AMM = P("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
FEES = P("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
TOKEN = P("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = P("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = P("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
WSOL = P("So11111111111111111111111111111111111111112")
SYSTEM = Pubkey.default()
GLOBAL = Pubkey.find_program_address([b"global"], PUMP)[0]
PUMP_EVENT = Pubkey.find_program_address([b"__event_authority"], PUMP)[0]
AMM_EVENT = Pubkey.find_program_address([b"__event_authority"], AMM)[0]
FEES_EVENT = Pubkey.find_program_address([b"__event_authority"], FEES)[0]

ADMIN = Keypair.from_seed(hashlib.sha256(b"pump-admin-cto-stateful/admin").digest())
PAYER = Keypair.from_seed(hashlib.sha256(b"pump-admin-cto-stateful/payer").digest())
CREATORS = [Keypair.from_seed(hashlib.sha256(f"pump-admin-cto-stateful/creator/{i}".encode()).digest()) for i in range(4)]

CAPTURED = {
    "pump_original": ROOT / "evidence/original/pump/deployed.so",
    "pump_amm": ROOT / "evidence/original/pump_amm/deployed.so",
    "pump_fees": ROOT / "evidence/original/pump_fees/deployed.so",
    "spl_token": ROOT / "evidence/dependencies/spl_token/deployed.so",
    "spl_token_2022": ROOT / "evidence/dependencies/spl_token_2022/deployed.so",
    "associated_token": ROOT / "evidence/dependencies/associated_token/deployed.so",
}

CONFIG_PATH = ROOT / "research/imported-lab/analysis/pump_fun/config-snapshot.json"
CONFIG_BYTES = CONFIG_PATH.read_bytes()
CONFIG_ACCOUNTS = json.loads(CONFIG_BYTES)["accounts"]
PUMP_CONFIG = next(row for row in CONFIG_ACCOUNTS if row["program_name"] == "pump")
AMM_CONFIG = next(row for row in CONFIG_ACCOUNTS if row["program_name"] == "pump_amm")
# Same captured templates used by the maintained fixture helpers; decode these
# exact retained bytes directly, without executing the unrelated suite modules.
PUMP_GLOBAL_TEMPLATE = bytearray(base64.b64decode(PUMP_CONFIG["data_base64"]))
PUMP_GLOBAL_TEMPLATE[9:41] = bytes(Keypair.from_seed(bytes([201]) * 32).pubkey())
AMM_GLOBAL_TEMPLATE = bytearray(base64.b64decode(AMM_CONFIG["data_base64"]))
AMM_GLOBAL_TEMPLATE[8:40] = bytes(Keypair.from_seed(bytes([201]) * 32).pubkey())
AMM_CONFIG_KEY = P(AMM_CONFIG["address"])
PRODUCER_PATHS = (Path(__file__), ROOT / "scripts/pump_differential_output.py", IDL_PATH, CONFIG_PATH)
LOADED_INPUT_SHA256 = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in PRODUCER_PATHS}

STRICT_FIELDS = (
    "transaction_base64", "signature", "message_sha256", "error", "outcome",
    "failure_class", "events", "semantic_logs", "inner_instructions",
    "return_data", "before", "after", "rollback_nonfee_equal",
)
EXPECTED_OUTCOMES = {
    "native/reassign-fail-retry-collect": ["ok", "error:CtoNewCreatorRequired", "ok", "ok"],
    "native/holder-transition-idempotent-retry": ["ok", "error:HolderRewardCreatorImmutable", "ok"],
    "spl/wallet-collection-and-reassign": ["ok", "ok"],
    "spl/frozen-wallet-leaves-fees": ["ok"],
    "spl/frozen-shared-vault-rollback": ["error:TransactionErrorInstructionError((1, Tagged(InstructionErrorCustom(17))))", "ok"],
    "spl/sharing-config-A-B-C": ["ok", "ok"],
    "token22/reassign": ["ok"],
    "cross-mint/isolation": ["ok", "ok", "ok"],
    "atomic/wrong-fees-event-then-retry": ["error:ConstraintSeeds", "ok"],
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def canonical_hash(value) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def pda(*seeds: bytes, program: Pubkey = PUMP) -> Pubkey:
    return Pubkey.find_program_address(list(seeds), program)[0]


def ata(owner: Pubkey, mint: Pubkey, token: Pubkey = TOKEN) -> Pubkey:
    return pda(bytes(owner), bytes(token), bytes(mint), program=ATA)


def mint_data(decimals: int) -> bytes:
    data = bytearray(82)
    data[36:44] = (10**15).to_bytes(8, "little")
    data[44] = decimals
    data[45] = 1
    return bytes(data)


def token_data(mint: Pubkey, owner: Pubkey, amount: int, state: int = 1) -> bytes:
    data = bytearray(165)
    data[:32], data[32:64] = bytes(mint), bytes(owner)
    data[64:72] = amount.to_bytes(8, "little")
    data[108] = state
    return bytes(data)


def semantic_logs(logs: list[str]) -> list[str]:
    result = []
    for line in logs:
        if re.fullmatch(r"Program [1-9A-HJ-NP-Za-km-z]+ consumed \d+ of \d+ compute units", line):
            continue
        if line.startswith("Program ") and (" invoke [" in line or line.endswith((" success", " failed"))):
            continue
        result.append(line.replace("programs/pump/src/", "src/"))
    return result


def outcome(logs: list[str], error: str | None) -> str:
    if error is None:
        return "ok"
    for line in logs:
        if "Error Code: " in line:
            return "error:" + line.split("Error Code: ", 1)[1].split(".", 1)[0]
    return "error:" + error


def failure_class(error: str | None) -> str | None:
    if error is None:
        return None
    infra = ("ComputationalBudgetExceeded", "ProgramFailedToComplete", "BlockhashNotFound", "AlreadyProcessed", "SignatureFailure")
    return "infrastructure" if any(item in error for item in infra) else "program"


@dataclass(frozen=True)
class MintFixture:
    label: str
    mint: Pubkey
    quote: Pubkey
    token_program: Pubkey
    curve: Pubkey
    pool_authority: Pubkey
    pool: Pubkey
    sharing: Pubkey
    holder: Pubkey


class Harness:
    def __init__(self, pump_image: Path, config: dict, images=None, case_index=0):
        self.config = copy.deepcopy(config)
        self.vm = (LiteSVM().with_sigverify(True).with_blockhash_check(True)
                   .with_transaction_history(128).with_log_bytes_limit(None))
        for _ in range(case_index * 8):
            self.vm.expire_blockhash()
        self.vm.set_clock(Clock(1_000, 0, 0, 0, 1_700_000_000))
        images = CAPTURED if images is None else images
        for address, image in ((PUMP, pump_image), (AMM, images["pump_amm"]),
                               (FEES, images["pump_fees"]), (TOKEN, images["spl_token"]),
                               (TOKEN22, images["spl_token_2022"]), (ATA, images["associated_token"])):
            self.vm.add_program_from_file(address, image)
        self.tracked: set[Pubkey] = set()
        self.mints = [self._mint_fixture(i, mode) for i, mode in enumerate(config.get("mints", ["native"]))]
        self._seed()

    def put(self, key: Pubkey, value: Account) -> None:
        self.tracked.add(key)
        self.vm.set_account(key, value)

    @staticmethod
    def _mint_fixture(index: int, mode: str) -> MintFixture:
        mint = Pubkey.from_bytes(hashlib.sha256(f"pump-admin-cto-stateful/mint/{index}".encode()).digest())
        quote = WSOL if mode == "native" else Pubkey.from_bytes(hashlib.sha256(f"pump-admin-cto-stateful/quote/{index}".encode()).digest())
        token = TOKEN22 if mode == "token22" else TOKEN
        curve = pda(b"bonding-curve", bytes(mint))
        pool_authority = pda(b"pool-authority", bytes(mint))
        pool = pda(b"pool", bytes(2), bytes(pool_authority), bytes(mint), bytes(quote), program=AMM)
        sharing = pda(b"sharing-config", bytes(mint), program=FEES)
        holder = pda(b"holder-rewards", bytes(mint))
        return MintFixture(f"mint-{index}", mint, quote, token, curve, pool_authority, pool, sharing, holder)

    def _seed(self) -> None:
        global_data = bytearray(PUMP_GLOBAL_TEMPLATE)
        global_data[418:450] = bytes(ADMIN.pubkey())
        global_data[1045] = 1
        global_data[1046:1054] = (300).to_bytes(8, "little")
        global_data[1086] = 1
        self.put(GLOBAL, Account(10**9, bytes(global_data), PUMP))
        amm_data = bytearray(AMM_GLOBAL_TEMPLATE)
        self.put(AMM_CONFIG_KEY, Account(10**9, bytes(amm_data), AMM))
        for keypair in [PAYER, ADMIN, *CREATORS]:
            self.put(keypair.pubkey(), Account(10**12, b"", SYSTEM))
        for event in (PUMP_EVENT, AMM_EVENT, FEES_EVENT):
            self.put(event, Account(0, b"", SYSTEM))
        for index, fixture in enumerate(self.mints):
            self.put(fixture.mint, Account(10**9, mint_data(6), TOKEN))
            self.put(fixture.quote, Account(10**9, mint_data(9), fixture.token_program))
            initial = fixture.sharing if self.config.get("shared") else CREATORS[0].pubkey()
            curve = bytearray(hashlib.sha256(b"account:BondingCurve").digest()[:8] + bytes(158))
            curve[8:16] = (1_000_000).to_bytes(8, "little")
            curve[16:24] = (1_000_000).to_bytes(8, "little")
            curve[24:32] = (1_000).to_bytes(8, "little")
            curve[32:40] = (1_000_000).to_bytes(8, "little")
            curve[48] = int(self.config.get("complete", False))
            curve[49:81] = bytes(initial)
            curve[83:115] = bytes(fixture.quote if fixture.quote != WSOL else Pubkey.default())
            curve[115:123] = (100).to_bytes(8, "little")
            curve[124] = int(self.config.get("holder_initial", False))
            self.put(fixture.curve, Account(10**9, bytes(curve), PUMP))
            sharing = (hashlib.sha256(b"account:SharingConfig").digest()[:8]
                       + bytes([Pubkey.find_program_address([b"sharing-config", bytes(fixture.mint)], FEES)[1], 2, 1])
                       + bytes(fixture.mint) + bytes(CREATORS[0].pubkey()) + b"\0"
                       + (1).to_bytes(4, "little") + bytes(CREATORS[0].pubkey()) + (10_000).to_bytes(2, "little"))
            self.put(fixture.sharing, Account(10**9, sharing.ljust(1024, b"\0"), FEES))
            pool = (hashlib.sha256(b"account:Pool").digest()[:8] + bytes([Pubkey.find_program_address(
                    [b"pool", bytes(2), bytes(fixture.pool_authority), bytes(fixture.mint), bytes(fixture.quote)], AMM)[1]])
                    + bytes(2) + bytes(fixture.pool_authority) + bytes(fixture.mint) + bytes(fixture.quote)
                    + bytes(96) + bytes(8) + bytes(initial) + bytes(2) + bytes(16))
            self.put(fixture.pool, Account(10**9, pool.ljust(301, b"\0"), AMM))
            self.put(fixture.pool_authority, Account(0, b"", SYSTEM))
            for creator in [fixture.sharing, fixture.holder, *(kp.pubkey() for kp in CREATORS)]:
                vault = pda(b"creator-vault", bytes(creator))
                amm_vault = pda(b"creator_vault", bytes(creator), program=AMM)
                native_amount = self.config.get("native_vault_lamports", 890_880) if creator == initial else 0
                self.put(vault, Account(native_amount, b"", SYSTEM))
                self.put(amm_vault, Account(0, b"", SYSTEM))
                self.put(ata(creator, fixture.quote, fixture.token_program), Account(0, b"", SYSTEM))
                self.put(ata(vault, fixture.quote, fixture.token_program), Account(0, b"", SYSTEM))
                self.put(ata(amm_vault, fixture.quote, fixture.token_program), Account(0, b"", SYSTEM))
            holder_vault = pda(b"creator-vault", bytes(fixture.holder))
            self.put(ata(holder_vault, fixture.quote, fixture.token_program), Account(0, b"", SYSTEM))
            if fixture.quote != WSOL:
                old = initial
                old_vault = pda(b"creator-vault", bytes(old))
                state = 2 if self.config.get("frozen_pump") else 1
                self.put(ata(old_vault, fixture.quote, fixture.token_program),
                         Account(2_039_280, token_data(fixture.quote, old_vault, self.config.get("spl_vault_tokens", 0), state), fixture.token_program))
                self.put(ata(old, fixture.quote, fixture.token_program),
                         Account(2_039_280, token_data(fixture.quote, old, 0, 2 if self.config.get("frozen_wallet") else 1), fixture.token_program))
                amm_vault = pda(b"creator_vault", bytes(old), program=AMM)
                self.put(ata(amm_vault, fixture.quote, fixture.token_program),
                         Account(2_039_280, token_data(fixture.quote, amm_vault, self.config.get("amm_tokens", 0), 2 if self.config.get("frozen_amm") else 1), fixture.token_program))

    def snapshot(self) -> dict:
        rows = {}
        for key in sorted(self.tracked, key=str):
            value = self.vm.get_account(key)
            if value is not None and value.executable:
                continue
            rows[str(key)] = None if value is None else {
                "lamports": value.lamports, "owner": str(value.owner),
                "data_len": len(value.data), "data_sha256": sha(bytes(value.data)),
                "executable": value.executable, "rent_epoch": value.rent_epoch,
                "data_base64": base64.b64encode(bytes(value.data)).decode(),
            }
        return rows

    def curve_creator(self, fixture: MintFixture) -> Pubkey:
        return Pubkey.from_bytes(bytes(self.vm.get_account(fixture.curve).data[49:81]))

    def admin_instruction(self, step: dict) -> Instruction:
        fixture = self.mints[step.get("mint", 0)]
        current = self.curve_creator(fixture)
        vault = pda(b"creator-vault", bytes(current))
        holder_vault = pda(b"creator-vault", bytes(fixture.holder))
        amm_vault = pda(b"creator_vault", bytes(current), program=AMM)
        names = {
            "admin_set_creator_authority": ADMIN.pubkey(), "global": GLOBAL, "mint": fixture.mint,
            "quote_mint": fixture.quote, "quote_token_program": fixture.token_program,
            "associated_token_program": ATA, "system_program": SYSTEM, "bonding_curve": fixture.curve,
            "current_creator": current, "current_creator_quote_token_account": ata(current, fixture.quote, fixture.token_program),
            "creator_vault": vault, "creator_vault_quote_token_account": ata(vault, fixture.quote, fixture.token_program),
            "holder_creator_vault": holder_vault,
            "holder_creator_vault_quote_token_account": ata(holder_vault, fixture.quote, fixture.token_program),
            "pump_amm": AMM, "amm_global_config": AMM_CONFIG_KEY, "pool_authority": fixture.pool_authority,
            "pool": fixture.pool, "pump_amm_event_authority": AMM_EVENT,
            "coin_creator_vault_authority": amm_vault,
            "coin_creator_vault_ata": ata(amm_vault, fixture.quote, fixture.token_program),
            "sharing_config": fixture.sharing, "pump_fees": FEES, "pump_fees_event_authority": FEES_EVENT,
            "event_authority": PUMP_EVENT, "program": PUMP,
        }
        wrong = step.get("wrong")
        if wrong:
            names[wrong] = CREATORS[3].pubkey()
        metas = [AccountMeta(names[row["name"]], bool(row.get("signer")), bool(row.get("writable"))) for row in ADMIN_CTO["accounts"]]
        # The recovered handler requires an ordinary wallet recipient to be
        # writable when it opportunistically settles the old creator vault.
        metas[8] = AccountMeta(metas[8].pubkey, False, True)
        holder = b"\0" if "holder" not in step else bytes([1, int(step["holder"])])
        fee = b"\0" if "fee" not in step else b"\1" + struct.pack("<Q", step["fee"])
        if step.get("new_none"):
            new = b"\0"
        else:
            target = CREATORS[step.get("new", 1)].pubkey()
            new = b"\1" + bytes(target)
        return Instruction(PUMP, bytes(ADMIN_CTO["discriminator"]) + holder + fee + new, metas)

    def collect_instruction(self, step: dict) -> Instruction:
        creator = CREATORS[step.get("creator", 0)].pubkey()
        vault = pda(b"creator-vault", bytes(creator))
        names = {"creator": creator, "creator_vault": vault, "system_program": SYSTEM,
                 "event_authority": PUMP_EVENT, "program": PUMP}
        metas = [AccountMeta(names[row["name"]], False, bool(row.get("writable"))) for row in COLLECT["accounts"]]
        return Instruction(PUMP, bytes(COLLECT["discriminator"]), metas)

    def execute(self, step: dict, index: int) -> dict:
        self.vm.expire_blockhash()
        self.vm.set_clock(Clock(1_000 + index, 0, 0, 0, 1_700_000_000 + index))
        before = self.snapshot()
        instruction = self.collect_instruction(step) if step["op"] == "collect" else self.admin_instruction(step)
        blockhash = self.vm.latest_blockhash()
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), instruction],
                                               PAYER.pubkey(), [PAYER, ADMIN] if step["op"] == "admin_cto" else [PAYER], blockhash)
        checks = list(tx.verify_with_results())
        if not checks or not all(checks):
            raise ValueError("locally constructed transaction failed signature verification")
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        raw = json.loads(meta.to_json())
        logs = list(meta.logs())
        after = self.snapshot()
        nonfee_before = {k: v for k, v in before.items() if k != str(PAYER.pubkey())}
        nonfee_after = {k: v for k, v in after.items() if k != str(PAYER.pubkey())}
        error = str(result.err()) if failed else None
        return {
            "step": step["name"], "operation": step["op"], "recent_blockhash": str(blockhash),
            "mint_index": step.get("mint", 0),
            "transaction_base64": base64.b64encode(bytes(tx)).decode(), "signature": str(tx.signatures[0]),
            "signature_verification": checks, "message_sha256": sha(bytes(tx.message)), "error": error,
            "outcome": outcome(logs, error), "failure_class": failure_class(error),
            "compute_units": meta.compute_units_consumed(), "logs": logs, "semantic_logs": semantic_logs(logs),
            "events": [line[14:] for line in logs if line.startswith("Program data: ")],
            "inner_instructions": raw.get("inner_instructions"), "return_data": raw.get("return_data"),
            "before_hash": canonical_hash(before), "after_hash": canonical_hash(after), "before": before, "after": after,
            "rollback_nonfee_equal": None if not failed else nonfee_before == nonfee_after,
        }


def scenarios() -> list[dict]:
    return [
        {"name": "native/reassign-fail-retry-collect", "mints": ["native"], "native_vault_lamports": 1_890_880,
         "steps": [{"name": "A-to-B", "op": "admin_cto", "new": 1},
                   {"name": "missing-new", "op": "admin_cto", "new_none": True},
                   {"name": "B-to-C-retry", "op": "admin_cto", "new": 2},
                   {"name": "collect-old-A", "op": "collect", "creator": 0}]},
        {"name": "native/holder-transition-idempotent-retry", "mints": ["native"], "native_vault_lamports": 1_890_880,
         "steps": [{"name": "enable-holder", "op": "admin_cto", "holder": True, "new_none": True},
                   {"name": "invalid-disable-holder", "op": "admin_cto", "new": 1},
                   {"name": "holder-retry", "op": "admin_cto", "holder": True, "new_none": True}]},
        {"name": "spl/wallet-collection-and-reassign", "mints": ["spl"], "spl_vault_tokens": 1_000_000, "amm_tokens": 500_000,
         "steps": [{"name": "A-to-B-with-collection", "op": "admin_cto", "new": 1},
                   {"name": "B-to-C", "op": "admin_cto", "new": 2}]},
        {"name": "spl/frozen-wallet-leaves-fees", "mints": ["spl"], "spl_vault_tokens": 1_000_000, "frozen_wallet": True,
         "steps": [{"name": "A-to-B-frozen-wallet", "op": "admin_cto", "new": 1}]},
        {"name": "spl/frozen-shared-vault-rollback", "mints": ["spl"], "shared": True, "spl_vault_tokens": 1_000_000, "frozen_pump": True,
         "steps": [{"name": "holder-frozen-fails", "op": "admin_cto", "holder": True, "new_none": True},
                   {"name": "nonholder-sharing-update-retry", "op": "admin_cto", "new": 1}]},
        {"name": "spl/sharing-config-A-B-C", "mints": ["spl"], "shared": True,
         "steps": [{"name": "sharing-A-to-B", "op": "admin_cto", "new": 1},
                   {"name": "sharing-B-to-C", "op": "admin_cto", "new": 2}]},
        {"name": "token22/reassign", "mints": ["token22"], "spl_vault_tokens": 777,
         "steps": [{"name": "token22-A-to-B", "op": "admin_cto", "new": 1}]},
        {"name": "cross-mint/isolation", "mints": ["native", "spl"], "spl_vault_tokens": 333,
         "steps": [{"name": "mint0-A-to-B", "op": "admin_cto", "mint": 0, "new": 1},
                   {"name": "mint1-A-to-C", "op": "admin_cto", "mint": 1, "new": 2},
                   {"name": "mint0-B-to-C", "op": "admin_cto", "mint": 0, "new": 2}]},
        {"name": "atomic/wrong-fees-event-then-retry", "mints": ["spl"], "shared": True,
         "steps": [{"name": "wrong-fees-event", "op": "admin_cto", "new": 1, "wrong": "pump_fees_event_authority"},
                   {"name": "valid-after-failure", "op": "admin_cto", "new": 1}]},
    ]


def run_image(image: Path, scenario: dict, images=None, case_index=0) -> dict:
    harness = Harness(image, scenario, images, case_index)
    initial = harness.snapshot()
    receipts = [harness.execute(step, index) for index, step in enumerate(scenario["steps"], 1)]
    signatures = [row["signature"] for row in receipts]
    if len(signatures) != len(set(signatures)):
        raise ValueError(f"duplicate signature in {scenario['name']}")
    return {"initial_state_hash": canonical_hash(initial), "receipts": receipts,
            "mint_accounts": [{"mint": str(m.mint), "curve": str(m.curve), "pool": str(m.pool), "sharing": str(m.sharing)} for m in harness.mints]}


def compare_runs(original: dict, candidate: dict) -> tuple[list[str], list[dict]]:
    mismatches = []
    if original["initial_state_hash"] != candidate["initial_state_hash"]:
        mismatches.append("initial_state_hash")
    if len(original["receipts"]) != len(candidate["receipts"]):
        return mismatches + ["receipt_count"], []
    comparison = []
    for left, right in zip(original["receipts"], candidate["receipts"]):
        strict = [field for field in STRICT_FIELDS if canonical_hash(left.get(field)) != canonical_hash(right.get(field))]
        diagnostic = [field for field in ("logs", "compute_units") if canonical_hash(left.get(field)) != canonical_hash(right.get(field))]
        comparison.append({"step": left["step"], "mismatch_fields": strict, "diagnostic_difference_fields": diagnostic})
        mismatches.extend(f"{left['step']}:{field}" for field in strict)
    return mismatches, comparison


def source_manifest() -> tuple[dict, str]:
    rows = {}
    for path in sorted((ROOT / "programs/pump").rglob("*")):
        if path.is_file() and "target" not in path.parts:
            rows[path.relative_to(ROOT).as_posix()] = file_sha(path)
    return rows, canonical_hash(rows)


def input_hashes():
    actual = {str(path.relative_to(ROOT)): file_sha(path) for path in PRODUCER_PATHS}
    if actual != LOADED_INPUT_SHA256:
        raise ValueError("loaded producer input changed")
    return actual


def validate_run(run: dict) -> list[str]:
    """Recompute signature, state, log and continuity evidence from raw records."""
    failures = []
    previous = None
    signatures = []
    try:
        for row in run["receipts"]:
            tag = row["step"]
            raw = base64.b64decode(row["transaction_base64"], validate=True)
            tx = Transaction.from_bytes(raw)
            required = tx.message.header.num_required_signatures
            checked = list(tx.verify_with_results())
            if (bytes(tx) != raw or required < 1 or len(tx.signatures) != required
                    or checked != [True] * required or canonical_hash(row["signature_verification"]) != canonical_hash(checked)
                    or row["signature"] != str(tx.signatures[0])
                    or row["message_sha256"] != sha(bytes(tx.message))
                    or row["recent_blockhash"] != str(tx.message.recent_blockhash)
                    or tx.message.account_keys[0] != PAYER.pubkey()
                    or [str(key) for key in tx.message.account_keys[:required]] !=
                       [str(PAYER.pubkey()), *([str(ADMIN.pubkey())] if row["operation"] == "admin_cto" else [])]
                    or tx.message.account_keys[tx.message.instructions[-1].program_id_index] != PUMP
                    or bytes(tx.message.instructions[-1].data[:8]) != bytes((ADMIN_CTO if row["operation"] == "admin_cto" else COLLECT)["discriminator"])):
                failures.append(tag + ":signature-verification")
            signatures.append(str(tx.signatures[0]) if tx.signatures else "unsigned")
            for stage in ("before", "after"):
                state = row[stage]
                if row[stage + "_hash"] != canonical_hash(state):
                    failures.append(tag + ":" + stage + "-hash")
                for key, account in state.items():
                    P(key)
                    if account is None:
                        continue
                    data = base64.b64decode(account["data_base64"], validate=True)
                    P(account["owner"])
                    if (type(account["lamports"]) is not int or account["lamports"] < 0
                            or account["lamports"] >= 2**64
                            or type(account["rent_epoch"]) is not int or not 0 <= account["rent_epoch"] < 2**64
                            or type(account["executable"]) is not bool
                            or type(account["data_len"]) is not int
                            or len(data) != account["data_len"] or sha(data) != account["data_sha256"]):
                        failures.append(tag + ":account-snapshot")
            before, after = row["before"], row["after"]
            if previous is None:
                if run["initial_state_hash"] != canonical_hash(before):
                    failures.append(tag + ":initial-state")
            elif canonical_hash(previous) != canonical_hash(before):
                failures.append(tag + ":state-continuity")
            previous = after
            nonfee = lambda stage: {key: value for key, value in stage.items() if key != str(PAYER.pubkey())}
            rollback = None if row["error"] is None else canonical_hash(nonfee(before)) == canonical_hash(nonfee(after))
            if rollback != row["rollback_nonfee_equal"] or rollback is False:
                failures.append(tag + ":non-atomic-failure")
            if (row["outcome"] != outcome(row["logs"], row["error"])
                    or row["failure_class"] != failure_class(row["error"])
                    or row["semantic_logs"] != semantic_logs(row["logs"])
                    or row["events"] != [line[14:] for line in row["logs"] if line.startswith("Program data: ")]):
                failures.append(tag + ":derived-receipt-fields")
            for index, mint in enumerate(run["mint_accounts"]):
                if index != row["mint_index"]:
                    for name in ("curve", "pool", "sharing"):
                        if canonical_hash(before.get(mint[name])) != canonical_hash(after.get(mint[name])):
                            failures.append(tag + f":cross-mint-{index}-{name}")
        if len(signatures) != len(set(signatures)):
            failures.append("duplicate-signature")
    except (KeyError, TypeError, ValueError, IndexError) as error:
        failures.append("malformed-receipt:" + type(error).__name__)
    return failures


def program_hashes(candidate: Path) -> dict:
    rows = {name: file_sha(path) for name, path in CAPTURED.items()}
    rows["pump_candidate"] = file_sha(candidate)
    return rows


def run_suite(candidate: Path) -> dict:
    sources, source_digest = source_manifest()
    inputs = input_hashes()
    snapshots = {name: path.read_bytes() for name, path in CAPTURED.items()}
    snapshots["pump_candidate"] = candidate.read_bytes()
    hashes = {name: sha(raw) for name, raw in snapshots.items()}
    rows = []
    with tempfile.TemporaryDirectory(prefix="pump-cto-stateful-") as scratch:
        images = {name: Path(scratch) / (name + ".so") for name in snapshots}
        for name, raw in snapshots.items():
            images[name].write_bytes(raw)
        for case_index, scenario in enumerate(scenarios()):
            original = run_image(images["pump_original"], scenario, images, case_index)
            rebuilt = run_image(images["pump_candidate"], scenario, images, case_index)
            mismatches, comparison = compare_runs(original, rebuilt)
            invariants = {"original": validate_run(original), "candidate": validate_run(rebuilt)}
            observed = [receipt["outcome"] for receipt in original["receipts"]]
            expected = EXPECTED_OUTCOMES[scenario["name"]]
            infrastructure = [f"{side}:{receipt['step']}" for side, run in (("original", original), ("candidate", rebuilt))
                              for receipt in run["receipts"] if receipt["failure_class"] == "infrastructure"]
            rows.append({"case": scenario["name"], "config": {k: v for k, v in scenario.items() if k != "steps"},
                         "steps": scenario["steps"], "original": original, "candidate": rebuilt,
                         "comparison": comparison, "mismatch_fields": mismatches,
                         "expected_original_outcomes": expected, "observed_original_outcomes": observed,
                         "oracle_mismatches": [] if observed == expected else [{"expected": expected, "observed": observed}],
                         "invariant_failures": invariants, "infrastructure_failures": infrastructure})
    for side in ("original", "candidate"):
        signatures = [receipt["signature"] for row in rows for receipt in row[side]["receipts"]]
        if len(signatures) != len(set(signatures)):
            raise ValueError("suite reused a transaction signature")
    return {"schema": "pump-admin-cto-stateful-v1", "scope": "Persistent signed admin_cto lifecycle differential; synthetic state, captured on-chain programs, no network.",
            "program_ids": {"pump": str(PUMP), "pump_amm": str(AMM), "pump_fees": str(FEES), "spl_token": str(TOKEN), "spl_token_2022": str(TOKEN22), "associated_token": str(ATA)},
            "program_sha256": hashes, "idl_sha256": sha(IDL_BYTES), "producer_input_sha256": inputs, "source_manifest_sha256": source_digest,
            "source_files": sources, "case_count": len(rows),
            "transaction_count_per_image": sum(len(row["original"]["receipts"]) for row in rows),
            "mismatch_cases": [row["case"] for row in rows if row["mismatch_fields"]],
            "oracle_mismatch_cases": [row["case"] for row in rows if row["oracle_mismatches"]],
            "invariant_failure_cases": [row["case"] for row in rows if any(row["invariant_failures"].values())],
            "infrastructure_failure_cases": [row["case"] for row in rows if row["infrastructure_failures"]], "cases": rows}


def negative_control(report: dict) -> dict:
    base = report["cases"][0]
    checks = {}
    for field, mutate in (("error", lambda row: row.update(error="negative-control")),
                          ("after", lambda row: row["after"].update({"negative-control": None})),
                          ("events", lambda row: row["events"].append("negative-control"))):
        changed = copy.deepcopy(base["candidate"])
        mutate(changed["receipts"][0])
        differences, _ = compare_runs(base["original"], changed)
        checks[field] = any(item.endswith(":" + field) for item in differences)
    return checks


def write_report(path: Path, report: dict, publisher=None) -> None:
    raw = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if publisher is None:
        publisher = PumpReport(path, ROOT, None, __file__, overwrite=False, extra_inputs=[*CAPTURED.values(), *PRODUCER_PATHS])
    publisher.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-mismatches", action="store_true")
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit(f"refusing to overwrite existing report: {args.output}")
    publisher = PumpReport(args.output, ROOT, args.candidate, __file__, overwrite=False,
                           extra_inputs=[*CAPTURED.values(), *PRODUCER_PATHS,
                                         *[ROOT / name for name in source_manifest()[0]]])
    report = run_suite(args.candidate.resolve())
    report["negative_controls"] = negative_control(report)
    write_report(args.output, report, publisher)
    summary_keys = ("case_count", "transaction_count_per_image", "mismatch_cases", "oracle_mismatch_cases", "invariant_failure_cases", "infrastructure_failure_cases", "negative_controls")
    print(json.dumps({key: report[key] for key in summary_keys}, indent=2))
    failed = report["mismatch_cases"] or report["oracle_mismatch_cases"] or report["invariant_failure_cases"] or report["infrastructure_failure_cases"] or not all(report["negative_controls"].values())
    return 0 if args.allow_mismatches or not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
