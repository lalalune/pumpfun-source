#!/usr/bin/env python3
"""Persistent, authenticated PumpSwap multi-provider LP differential."""
from __future__ import annotations

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

import argparse
import base64
import gzip
import hashlib
import json
import os
import re
import struct
import tempfile
import types
import subprocess
from dataclasses import dataclass
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from solders.transaction_status import TransactionErrorInstructionError, InstructionErrorCustom

_SELF_SOURCE_SHA256 = globals().get("__source_sha256__")
if _SELF_SOURCE_SHA256 is None:
    _SELF_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if "_ADMISSION" in globals():
    A = _ADMISSION
elif "A" in globals():
    pass  # A private source loader may provide this same admitted graph.
else:
    _path = HERE / "admission.py"
    if _path.is_symlink():
        raise ValueError("admission source must be regular")
    _raw = _path.read_bytes()
    A = types.ModuleType("_amm_multi_lp_admission")
    A.__file__ = str(_path)
    A.__source_sha256__ = hashlib.sha256(_raw).hexdigest()
    exec(compile(_raw, str(_path), "exec", dont_inherit=True), A.__dict__)
A.LOADED[str(Path(__file__).resolve())] = _SELF_SOURCE_SHA256
_OUTPUT = A.source_module("output", ROOT / "scripts/pump_differential_output.py")

IDL_PATH = ROOT / "evidence/upstream/pump_amm.json"
CONFIG_PATH = ROOT / "research/imported-lab/analysis/pump_fun/config-snapshot.json"
TRADE_FIXTURE_PATH = ROOT / "research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json"
IDL_BYTES = A.regular_bytes(IDL_PATH, root=ROOT)
A.bind_bytes(IDL_PATH, IDL_BYTES)
IDL = A.json_bytes(IDL_BYTES)

P = Pubkey.from_string
AMM = P(IDL["address"])
TOKEN = P("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = P("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = P("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
FEES = P("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
SYSTEM = Pubkey.default()
EVENT = Pubkey.find_program_address([b"__event_authority"], AMM)[0]

CAPTURED = {
    "original": ROOT / "evidence/original/pump_amm/deployed.so",
    "spl_token": ROOT / "evidence/dependencies/spl_token/deployed.so",
    "spl_token_2022": ROOT / "evidence/dependencies/spl_token_2022/deployed.so",
    "associated_token": ROOT / "evidence/dependencies/associated_token/deployed.so",
    "pump_fees": ROOT / "evidence/original/pump_fees/deployed.so",
}

FEE_PAYER = Keypair.from_seed(hashlib.sha256(b"pump-amm-multi-lp/fee-payer").digest())
PROVIDER_A = Keypair.from_seed(hashlib.sha256(b"pump-amm-multi-lp/provider-a").digest())
PROVIDER_B = Keypair.from_seed(hashlib.sha256(b"pump-amm-multi-lp/provider-b").digest())
MINT_AUTHORITY = Keypair.from_seed(hashlib.sha256(b"pump-amm-multi-lp/mint-authority").digest())

CONFIG_BYTES = A.regular_bytes(CONFIG_PATH, root=ROOT)
A.bind_bytes(CONFIG_PATH, CONFIG_BYTES)
CONFIG_ROW = next(row for row in A.json_bytes(CONFIG_BYTES)["accounts"]
                  if row["program_name"] == "pump_amm")
CONFIG = P(CONFIG_ROW["address"])
CONFIG_DATA = bytearray(base64.b64decode(CONFIG_ROW["data_base64"]))
CONFIG_DATA[56] = 0

TRADE_FIXTURE_BYTES = A.regular_bytes(TRADE_FIXTURE_PATH, root=ROOT)
A.bind_bytes(TRADE_FIXTURE_PATH, TRADE_FIXTURE_BYTES)
TRADE_FIXTURE = A.json_bytes(TRADE_FIXTURE_BYTES)
FEE_CONFIG_ROW = TRADE_FIXTURE["accounts"]["fee_config"]
BUYBACK_ROW = TRADE_FIXTURE["accounts"]["buyback_fee_recipient"]
FEE_CONFIG = P(FEE_CONFIG_ROW["address"])
BUYBACK = P(BUYBACK_ROW["address"])

IX = {row["name"]: row for row in IDL["instructions"]}
INPUT_PATHS = (Path(__file__), IDL_PATH, CONFIG_PATH, TRADE_FIXTURE_PATH)
U64_MAX = 2**64 - 1
EXPECTED_OUTCOMES = {
    "two-provider-independent-withdrawals": ["ok"] * 7,
    "deposit-trade-independent-withdraw": ["ok"] * 7,
    "atomic-two-provider-deposits": ["ok"] * 5,
    "atomic-valid-deposit-invalid-withdraw-rollback": [
        "ok", "ok", "ok", "ok", "ok",
        "error:TransactionErrorInstructionError((1, Tagged(InstructionErrorCustom(1))))",
    ],
    "foreign-lp-authority-refused-then-owner-withdraws": [
        "ok", "ok", "ok", "ok", "ok", "error:ConstraintTokenOwner", "ok",
    ],
    "over-withdraw-refused-then-partial-chain": [
        "ok", "ok", "ok", "ok", "ok",
        "error:TransactionErrorInstructionError((0, Tagged(InstructionErrorCustom(1))))", "ok", "ok",
    ],
    "tiny-deposits-and-rounding": ["ok"] * 8,
    "token2022-base-multi-provider": ["ok"] * 6,
    "two-pool-provider-state-isolation": ["ok"] * 11,
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_sha(path: Path) -> str:
    return sha(A.regular_bytes(path))


def canonical_hash(value) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def key(label: str) -> Pubkey:
    return Pubkey.from_bytes(hashlib.sha256(("pump-amm-multi-lp/" + label).encode()).digest())


def ata(owner: Pubkey, mint: Pubkey, token_program: Pubkey) -> Pubkey:
    return Pubkey.find_program_address(
        [bytes(owner), bytes(token_program), bytes(mint)], ATA)[0]


def mint_data(authority: Pubkey, decimals: int = 6, supply: int = 0) -> bytes:
    data = bytearray(82)
    struct.pack_into("<I", data, 0, 1)
    data[4:36] = bytes(authority)
    struct.pack_into("<Q", data, 36, supply)
    data[44] = decimals
    data[45] = 1
    return bytes(data)


def token_amount(account: Account | None) -> int | None:
    if account is None or len(account.data) < 72:
        return None
    return struct.unpack_from("<Q", account.data, 64)[0]


def mint_supply(account: Account | None) -> int | None:
    if account is None or len(account.data) < 44:
        return None
    return struct.unpack_from("<Q", account.data, 36)[0]


def pool_supply(account: Account | None) -> int | None:
    if account is None or len(account.data) < 211:
        return None
    return struct.unpack_from("<Q", account.data, 203)[0]


def account_record(account: Account | None) -> dict | None:
    if account is None:
        return None
    common = {
        "lamports": account.lamports, "owner": str(account.owner), "executable": account.executable,
        "rent_epoch": account.rent_epoch, "data_len": len(account.data), "data_sha256": sha(bytes(account.data)),
        "token_amount": token_amount(account) if account.owner in (TOKEN, TOKEN22) and len(account.data) >= 165 else None,
        "mint_supply": mint_supply(account) if account.owner in (TOKEN, TOKEN22) and 82 <= len(account.data) < 165 else None,
        "pool_lp_supply": pool_supply(account) if account.owner == AMM else None,
    }
    if account.executable:
        return dict(common, data_omitted=True)
    return dict(common, data_base64=base64.b64encode(bytes(account.data)).decode())


def instruction(name: str, keys: list[Pubkey], data: bytes) -> Instruction:
    spec = IX[name]
    if len(keys) != len(spec["accounts"]):
        raise ValueError(f"{name}: expected {len(spec['accounts'])} accounts, got {len(keys)}")
    metas = [AccountMeta(pubkey, bool(account.get("signer")), bool(account.get("writable")))
             for pubkey, account in zip(keys, spec["accounts"])]
    return Instruction(AMM, bytes(spec["discriminator"]) + data, metas)


def ata_create(owner: Pubkey, mint: Pubkey, token_program: Pubkey) -> Instruction:
    destination = ata(owner, mint, token_program)
    return Instruction(ATA, b"\x01", [
        AccountMeta(FEE_PAYER.pubkey(), True, True),
        AccountMeta(destination, False, True),
        AccountMeta(owner, False, False),
        AccountMeta(mint, False, False),
        AccountMeta(SYSTEM, False, False),
        AccountMeta(token_program, False, False),
    ])


def mint_to(mint: Pubkey, destination: Pubkey, amount: int, token_program: Pubkey) -> Instruction:
    return Instruction(token_program, bytes([7]) + struct.pack("<Q", amount), [
        AccountMeta(mint, False, True),
        AccountMeta(destination, False, True),
        AccountMeta(MINT_AUTHORITY.pubkey(), True, False),
    ])


def system_transfer(destination: Pubkey, amount: int) -> Instruction:
    return Instruction(SYSTEM, struct.pack("<IQ", 2, amount), [
        AccountMeta(FEE_PAYER.pubkey(), True, True),
        AccountMeta(destination, False, True),
    ])


def sync_native(account: Pubkey) -> Instruction:
    return Instruction(TOKEN, bytes([17]), [AccountMeta(account, False, True)])


def semantic_logs(logs: list[str]) -> list[str]:
    result = []
    for line in logs:
        if re.fullmatch(r"Program [1-9A-HJ-NP-Za-km-z]+ consumed \d+ of \d+ compute units", line):
            continue
        if line.startswith("Program ") and (" invoke [" in line or line.endswith((" success", " failed"))):
            continue
        result.append(line.replace("programs/pump-amm/src/", "src/"))
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
    infrastructure = ("BlockhashNotFound", "AlreadyProcessed", "SignatureFailure")
    return "infrastructure" if any(item in error for item in infrastructure) else "program"


@dataclass(frozen=True)
class PoolFixture:
    label: str
    index: int
    base: Pubkey
    quote: Pubkey
    base_program: Pubkey
    quote_program: Pubkey
    pool: Pubkey
    lp: Pubkey
    vault_base: Pubkey
    vault_quote: Pubkey

    @classmethod
    def derive(cls, label: str, index: int = 0, base_program: Pubkey = TOKEN,
               quote_program: Pubkey = TOKEN) -> "PoolFixture":
        # The captured quote allowlist recognizes wrapped SOL.  The account is
        # a deterministic local mint fixture; no RPC state is consulted.
        quote = P("So11111111111111111111111111111111111111112")
        base = key(f"{label}/base")
        pool = Pubkey.find_program_address([
            b"pool", struct.pack("<H", index), bytes(PROVIDER_A.pubkey()), bytes(base), bytes(quote)
        ], AMM)[0]
        lp = Pubkey.find_program_address([b"pool_lp_mint", bytes(pool)], AMM)[0]
        return cls(label, index, base, quote, base_program, quote_program, pool, lp,
                   ata(pool, base, base_program), ata(pool, quote, quote_program))

    def provider_accounts(self, provider: Keypair) -> dict[str, Pubkey]:
        return {
            "base": ata(provider.pubkey(), self.base, self.base_program),
            "quote": ata(provider.pubkey(), self.quote, self.quote_program),
            "lp": ata(provider.pubkey(), self.lp, TOKEN22),
        }


class DualHarness:
    """Two independent VMs receiving byte-identical signed transactions."""

    def __init__(self, candidate: Path, *, case_index: int = 0, token22_base: bool = False,
                 cross_pool: bool = False, images=None):
        self.input_images = CAPTURED if images is None else images
        self.images = {"original": self.input_images["original"], "candidate": candidate}
        self.vms = {side: self._vm(image, case_index, self.input_images) for side, image in self.images.items()}
        primary = PoolFixture.derive(
            f"case-{case_index}", index=case_index,
            base_program=TOKEN22 if token22_base else TOKEN)
        self.pools = {"primary": primary}
        if cross_pool:
            self.pools["secondary"] = PoolFixture.derive(
                f"case-{case_index}-secondary", index=case_index + 100)
        self.pool_label = "primary"
        self.pool = primary
        self.tracked: set[Pubkey] = set()
        self.receipts = {"original": [], "candidate": []}
        self._seed()
        self.tracked.update((AMM, TOKEN, TOKEN22, ATA, FEES, SYSTEM))
        for provider in (PROVIDER_A, PROVIDER_B):
            volume = Pubkey.find_program_address([b"user_volume_accumulator", bytes(provider.pubkey())], AMM)[0]
            self.put(volume, Account(0, b"", SYSTEM))

    @staticmethod
    def _vm(image: Path, case_index: int, images=None) -> LiteSVM:
        vm = (LiteSVM().with_sigverify(True).with_blockhash_check(True)
              .with_transaction_history(128).with_log_bytes_limit(None))
        for _ in range(case_index * 16):
            vm.expire_blockhash()
        vm.set_clock(Clock(1_000, 0, 0, 0, 1_700_000_000))
        inputs = CAPTURED if images is None else images
        for address, path in ((AMM, image), (TOKEN, inputs["spl_token"]),
                              (TOKEN22, inputs["spl_token_2022"]),
                              (ATA, inputs["associated_token"]),
                              (FEES, inputs["pump_fees"])):
            vm.add_program_from_file(address, path)
        return vm

    def put(self, pubkey: Pubkey, account: Account) -> None:
        self.tracked.add(pubkey)
        for vm in self.vms.values():
            # LiteSVM copies the solders value into each bank; Account itself
            # is immutable and deliberately does not implement Python pickle.
            vm.set_account(pubkey, account)

    def _seed(self) -> None:
        for signer in (FEE_PAYER, PROVIDER_A, PROVIDER_B, MINT_AUTHORITY):
            self.put(signer.pubkey(), Account(10**15, b"", SYSTEM))
        self.put(CONFIG, Account(CONFIG_ROW["lamports"], bytes(CONFIG_DATA), AMM))
        self.put(EVENT, Account(0, b"", SYSTEM))
        self.put(self.pool.quote, Account(10**9, mint_data(MINT_AUTHORITY.pubkey(), 9), self.pool.quote_program))
        self.put(FEE_CONFIG, Account(FEE_CONFIG_ROW["lamports"], base64.b64decode(FEE_CONFIG_ROW["data_base64"]), P(FEE_CONFIG_ROW["owner"])))
        self.put(BUYBACK, Account(BUYBACK_ROW["lamports"], base64.b64decode(BUYBACK_ROW["data_base64"]), P(BUYBACK_ROW["owner"])))
        for pool in self.pools.values():
            self.put(pool.base, Account(10**9, mint_data(MINT_AUTHORITY.pubkey(), 6), pool.base_program))
            for provider in (PROVIDER_A, PROVIDER_B):
                self.tracked.update(pool.provider_accounts(provider).values())
            self.tracked.update((pool.pool, pool.lp, pool.vault_base, pool.vault_quote))

    def select_pool(self, label: str) -> None:
        self.pool_label = label
        self.pool = self.pools[label]

    def snapshot(self, side: str) -> dict:
        vm = self.vms[side]
        return {str(pubkey): account_record(vm.get_account(pubkey)) for pubkey in sorted(self.tracked, key=str)}

    @staticmethod
    def _amount(snapshot: dict, pubkey: Pubkey) -> int | None:
        record = snapshot.get(str(pubkey))
        return None if record is None else record.get("token_amount")

    @staticmethod
    def _supply(snapshot: dict, pubkey: Pubkey, field: str) -> int | None:
        record = snapshot.get(str(pubkey))
        return None if record is None else record.get(field)

    def accounting(self, before: dict, after: dict) -> dict:
        a_accounts = self.pool.provider_accounts(PROVIDER_A)
        b_accounts = self.pool.provider_accounts(PROVIDER_B)

        def state(snapshot):
            result = {
                "provider_a_base": self._amount(snapshot, a_accounts["base"]),
                "provider_a_quote": self._amount(snapshot, a_accounts["quote"]),
                "provider_a_lp": self._amount(snapshot, a_accounts["lp"]),
                "provider_b_base": self._amount(snapshot, b_accounts["base"]),
                "provider_b_quote": self._amount(snapshot, b_accounts["quote"]),
                "provider_b_lp": self._amount(snapshot, b_accounts["lp"]),
                "pool_base": self._amount(snapshot, self.pool.vault_base),
                "pool_quote": self._amount(snapshot, self.pool.vault_quote),
                "buyback_quote": self._amount(snapshot, BUYBACK),
                "lp_mint_supply": self._supply(snapshot, self.pool.lp, "mint_supply"),
                "pool_reported_lp_supply": self._supply(snapshot, self.pool.pool, "pool_lp_supply"),
            }
            lp_values = (result["provider_a_lp"], result["provider_b_lp"])
            result["provider_lp_total"] = None if None in lp_values else sum(lp_values)
            result["locked_lp_difference"] = (
                None if result["pool_reported_lp_supply"] is None or result["lp_mint_supply"] is None
                else result["pool_reported_lp_supply"] - result["lp_mint_supply"])
            base_values = (result["provider_a_base"], result["provider_b_base"], result["pool_base"])
            quote_values = (result["provider_a_quote"], result["provider_b_quote"],
                            result["pool_quote"], result["buyback_quote"])
            result["base_total"] = None if None in base_values else sum(base_values)
            result["quote_total_with_fee_recipient"] = None if None in quote_values else sum(quote_values)
            return result

        left, right = state(before), state(after)
        delta = {name: None if left[name] is None or right[name] is None else right[name] - left[name]
                 for name in left if isinstance(left[name], int) or isinstance(right[name], int)}
        fee_before = before[str(FEE_PAYER.pubkey())]["lamports"]
        fee_after = after[str(FEE_PAYER.pubkey())]["lamports"]
        return {"before": left, "after": right, "delta": delta,
                "fee_payer_lamport_delta": fee_after - fee_before}

    def execute(self, step: str, instructions: list[Instruction], signers: list[Keypair], operation: str) -> None:
        left, right = self.vms["original"], self.vms["candidate"]
        left.expire_blockhash()
        right.expire_blockhash()
        blockhash = left.latest_blockhash()
        if blockhash != right.latest_blockhash():
            raise RuntimeError("VM blockhash divergence")
        unique = {signer.pubkey(): signer for signer in [FEE_PAYER, *signers]}
        tx = Transaction.new_signed_with_payer(
            instructions, FEE_PAYER.pubkey(), list(unique.values()), blockhash)
        checked = list(tx.verify_with_results())
        required = tx.message.header.num_required_signatures
        if not checked or len(tx.signatures) != required or checked != [True] * required:
            raise RuntimeError("locally generated transaction failed complete Ed25519 verification")
        raw = bytes(tx)
        message = bytes(tx.message)
        common = {
            "step": step,
            "operation": operation,
            "transaction_base64": base64.b64encode(raw).decode(),
            "signatures": [str(value) for value in tx.signatures],
            "message_sha256": sha(message),
            "blockhash": str(blockhash),
            "blockhash_sha256": sha(bytes(blockhash)),
            "signer_pubkeys": [str(pubkey) for pubkey in tx.message.account_keys[:required]],
            "instruction_count": len(instructions),
            "pool_label": self.pool_label,
        }
        for side, vm in self.vms.items():
            before = self.snapshot(side)
            result = vm.send_transaction(tx)
            failed = isinstance(result, FailedTransactionMetadata)
            meta = result.meta() if failed else result
            raw_meta = json.loads(meta.to_json())
            error = str(result.err()) if failed else None
            after = self.snapshot(side)
            nonfee_before = {k: v for k, v in before.items() if k != str(FEE_PAYER.pubkey())}
            nonfee_after = {k: v for k, v in after.items() if k != str(FEE_PAYER.pubkey())}
            receipt = {
                **common,
                "error": error,
                "error_detail": error_detail(result.err()) if failed else None,
                "outcome": outcome(meta.logs(), error),
                "failure_class": failure_class(error),
                "raw_logs": meta.logs(),
                "semantic_logs": semantic_logs(meta.logs()),
                "events": [line for line in meta.logs() if line.startswith("Program data: ")],
                "inner_instructions": raw_meta.get("inner_instructions", []),
                "return_data": raw_meta.get("return_data"),
                "compute_units": raw_meta.get("compute_units_consumed"),
                "before": before,
                "after": after,
                "rollback_nonfee_equal": nonfee_before == nonfee_after if failed else None,
                "accounting": self.accounting(before, after),
            }
            self.receipts[side].append(receipt)

    def fund_provider(self, provider: Keypair, amount: int = 10**12) -> None:
        accounts = self.pool.provider_accounts(provider)
        self.execute(f"setup-{str(provider.pubkey())[:8]}", [
            ata_create(provider.pubkey(), self.pool.base, self.pool.base_program),
            ata_create(provider.pubkey(), self.pool.quote, self.pool.quote_program),
            mint_to(self.pool.base, accounts["base"], amount, self.pool.base_program),
            # Wrapped SOL is the captured config's supported quote mint.  It
            # cannot be MintTo'd: fund the genuine ATA and invoke SyncNative.
            system_transfer(accounts["quote"], amount),
            sync_native(accounts["quote"]),
        ], [MINT_AUTHORITY], "setup_provider")

    def create_pool(self, base_amount: int = 10**9, quote_amount: int = 10**9) -> None:
        accounts = self.pool.provider_accounts(PROVIDER_A)
        keys = [self.pool.pool, CONFIG, PROVIDER_A.pubkey(), self.pool.base, self.pool.quote,
                self.pool.lp, accounts["base"], accounts["quote"], accounts["lp"],
                self.pool.vault_base, self.pool.vault_quote, SYSTEM, TOKEN22,
                self.pool.base_program, self.pool.quote_program, ATA, EVENT, AMM]
        args = (struct.pack("<HQQ", self.pool.index, base_amount, quote_amount)
                + bytes(PROVIDER_A.pubkey()) + b"\0")
        self.execute("create-pool", [instruction("create_pool", keys, args)], [PROVIDER_A], "create_pool")

    def create_lp_account(self, provider: Keypair) -> None:
        self.execute(f"create-lp-{str(provider.pubkey())[:8]}", [
            ata_create(provider.pubkey(), self.pool.lp, TOKEN22)
        ], [], "create_lp_account")

    def liquidity_ix(self, name: str, provider: Keypair, amount: int,
                     base_limit: int, quote_limit: int,
                     lp_owner: Keypair | None = None) -> Instruction:
        provider_accounts = self.pool.provider_accounts(provider)
        lp_accounts = self.pool.provider_accounts(lp_owner or provider)
        keys = [self.pool.pool, CONFIG, provider.pubkey(), self.pool.base, self.pool.quote,
                self.pool.lp, provider_accounts["base"], provider_accounts["quote"], lp_accounts["lp"],
                self.pool.vault_base, self.pool.vault_quote, TOKEN, TOKEN22, EVENT, AMM]
        return instruction(name, keys, struct.pack("<QQQ", amount, base_limit, quote_limit))

    def trade_ix(self, name: str, provider: Keypair, amount: int, limit: int) -> Instruction:
        accounts = self.pool.provider_accounts(provider)
        volume = Pubkey.find_program_address(
            [b"user_volume_accumulator", bytes(provider.pubkey())], AMM)[0]
        keys = [self.pool.pool, provider.pubkey(), CONFIG, self.pool.base, self.pool.quote,
                accounts["base"], accounts["quote"], self.pool.vault_base, self.pool.vault_quote,
                self.pool.base_program, self.pool.quote_program, SYSTEM, volume, FEE_CONFIG,
                BUYBACK, EVENT, AMM]
        return instruction(name, keys, struct.pack("<QQ", amount, limit))

    def deposit(self, provider: Keypair, amount: int, step: str = "deposit") -> None:
        self.execute(step, [self.liquidity_ix("deposit", provider, amount, U64_MAX, U64_MAX)],
                     [provider], "deposit")

    def withdraw(self, provider: Keypair, amount: int, step: str = "withdraw",
                 lp_owner: Keypair | None = None) -> None:
        self.execute(step, [self.liquidity_ix("withdraw", provider, amount, 0, 0, lp_owner)],
                     [provider], "withdraw")

    def trade(self, name: str, provider: Keypair, amount: int, limit: int, step: str) -> None:
        self.execute(step, [self.trade_ix(name, provider, amount, limit)], [provider], name)

    def atomic(self, step: str, operations: list[dict]) -> None:
        instructions, signers = [], []
        providers = {"A": PROVIDER_A, "B": PROVIDER_B}
        for operation in operations:
            provider = providers[operation["provider"]]
            name = operation["op"]
            instructions.append(self.liquidity_ix(
                name, provider, operation["amount"],
                U64_MAX if name == "deposit" else 0,
                U64_MAX if name == "deposit" else 0,
                providers.get(operation.get("lp_owner"))))
            signers.append(provider)
        self.execute(step, instructions, signers, "atomic_liquidity")


def common_steps() -> list[dict]:
    return [
        {"op": "fund", "provider": "A"},
        {"op": "fund", "provider": "B"},
        {"op": "create_pool", "base": 10**9, "quote": 10**9},
        {"op": "create_lp", "provider": "B"},
    ]


def plans() -> list[dict]:
    return [{
        "name": "two-provider-independent-withdrawals",
        "token22_base": False,
        "steps": common_steps() + [
            {"op": "deposit", "provider": "B", "amount": 100_000_000},
            {"op": "withdraw", "provider": "A", "amount": 100_000_000},
            {"op": "withdraw", "provider": "B", "amount": 50_000_000},
        ],
    }, {
        "name": "deposit-trade-independent-withdraw",
        "token22_base": False,
        "steps": common_steps() + [
            {"op": "deposit", "provider": "B", "amount": 100_000_000},
            {"op": "trade", "name": "buy_v2", "provider": "A", "amount": 10_000_000,
             "limit": U64_MAX},
            {"op": "withdraw", "provider": "A", "amount": 100_000_000},
        ],
    }, {
        "name": "atomic-two-provider-deposits",
        "token22_base": False,
        "steps": common_steps() + [{"op": "atomic", "operations": [
            {"op": "deposit", "provider": "A", "amount": 20_000_000},
            {"op": "deposit", "provider": "B", "amount": 30_000_000},
        ]}],
    }, {
        "name": "atomic-valid-deposit-invalid-withdraw-rollback",
        "token22_base": False,
        "steps": common_steps() + [
            {"op": "deposit", "provider": "B", "amount": 20_000_000},
            {"op": "atomic", "operations": [
                {"op": "deposit", "provider": "A", "amount": 10_000_000},
                {"op": "withdraw", "provider": "B", "amount": 20_000_001},
            ]},
        ],
    }, {
        "name": "foreign-lp-authority-refused-then-owner-withdraws",
        "token22_base": False,
        "steps": common_steps() + [
            {"op": "deposit", "provider": "B", "amount": 40_000_000},
            {"op": "withdraw", "provider": "B", "lp_owner": "A", "amount": 1_000_000},
            {"op": "withdraw", "provider": "B", "amount": 20_000_000},
        ],
    }, {
        "name": "over-withdraw-refused-then-partial-chain",
        "token22_base": False,
        "steps": common_steps() + [
            {"op": "deposit", "provider": "B", "amount": 40_000_000},
            {"op": "withdraw", "provider": "B", "amount": 40_000_001},
            {"op": "withdraw", "provider": "B", "amount": 10_000_000},
            {"op": "withdraw", "provider": "B", "amount": 10_000_000},
        ],
    }, {
        "name": "tiny-deposits-and-rounding",
        "token22_base": False,
        "steps": common_steps() + [
            {"op": "deposit", "provider": "A", "amount": 1},
            {"op": "deposit", "provider": "B", "amount": 2},
            {"op": "withdraw", "provider": "A", "amount": 1},
            {"op": "withdraw", "provider": "B", "amount": 1},
        ],
    }, {
        "name": "token2022-base-multi-provider",
        "token22_base": True,
        "steps": common_steps() + [
            {"op": "deposit", "provider": "B", "amount": 25_000_000},
            {"op": "withdraw", "provider": "B", "amount": 10_000_000},
        ],
    }, {
        "name": "two-pool-provider-state-isolation",
        "token22_base": False,
        "cross_pool": True,
        "steps": common_steps() + [
            {"op": "deposit", "provider": "B", "amount": 25_000_000},
            {"op": "fund", "provider": "A", "pool": "secondary"},
            {"op": "fund", "provider": "B", "pool": "secondary"},
            {"op": "create_pool", "base": 2 * 10**9, "quote": 10**9, "pool": "secondary"},
            {"op": "create_lp", "provider": "B", "pool": "secondary"},
            {"op": "deposit", "provider": "B", "amount": 40_000_000, "pool": "secondary"},
            {"op": "withdraw", "provider": "A", "amount": 100_000_000, "pool": "secondary"},
        ],
    }]


def error_detail(error):
    if isinstance(error, TransactionErrorInstructionError):
        if isinstance(error.err, InstructionErrorCustom):
            return {"instruction_index": error.index, "error_kind": "Custom", "custom_code": error.err.code}
        return {"instruction_index": error.index, "error_kind": type(error.err).__name__, "description": str(error.err)}
    return {"error_kind": type(error).__name__, "description": str(error)}


def expected_error_detail(case_name, number):
    failures = {("atomic-valid-deposit-invalid-withdraw-rollback", 5): (1, 1),
                ("foreign-lp-authority-refused-then-owner-withdraws", 5): (0, 2015),
                ("over-withdraw-refused-then-partial-chain", 5): (0, 1)}
    value = failures.get((case_name, number))
    return None if value is None else {"instruction_index": value[0], "error_kind": "Custom", "custom_code": value[1]}


def fixture_only(candidate: Path, index: int, plan: dict, images=None):
    """Seed the canonical accounts and fixed watches; execute zero transactions."""
    return DualHarness(candidate, case_index=index, token22_base=plan.get("token22_base", False),
                       cross_pool=plan.get("cross_pool", False), images=images)


def plan_step(harness, step, number):
    """Capture existing instruction constructors without invoking the VM.

    This fixed fixture is created internally, never from report-controlled code.
    The original execute method is restored before any actual transaction runs.
    """
    harness.select_pool(step.get("pool", "primary"))
    providers = {"A": PROVIDER_A, "B": PROVIDER_B}
    op = step["op"]
    label = f"{number:02d}-{op}"
    captured = []
    original_execute = harness.execute
    def capture(name, instructions, signers, operation):
        unique = {pair.pubkey(): pair for pair in (FEE_PAYER, *signers)}
        captured.append((name, instructions, list(unique.values()), operation))
    harness.execute = capture
    try:
        if op == "fund":
            harness.fund_provider(providers[step["provider"]], step.get("amount", 10**12))
        elif op == "create_pool":
            harness.create_pool(step["base"], step["quote"])
        elif op == "create_lp":
            harness.create_lp_account(providers[step["provider"]])
        elif op == "deposit":
            harness.deposit(providers[step["provider"]], step["amount"], label)
        elif op == "withdraw":
            harness.withdraw(providers[step["provider"]], step["amount"], label,
                             providers.get(step.get("lp_owner")))
        elif op == "trade":
            harness.trade(step["name"], providers[step["provider"]], step["amount"], step["limit"], label)
        elif op == "atomic":
            harness.atomic(label, step["operations"])
        else:
            raise ValueError("unknown operation: " + str(op))
    finally:
        harness.execute = original_execute
    if len(captured) != 1:
        raise ValueError("canonical plan must create exactly one transaction")
    return captured[0]


def expected_fixture(harness):
    def record(pool):
        return {
            "pool": str(pool.pool), "lp_mint": str(pool.lp),
            "base_mint": str(pool.base), "quote_mint": str(pool.quote),
            "provider_a": str(PROVIDER_A.pubkey()), "provider_b": str(PROVIDER_B.pubkey()),
            "fee_payer": str(FEE_PAYER.pubkey()),
            "base_token_program": str(pool.base_program), "quote_token_program": str(pool.quote_program),
            "vault_base": str(pool.vault_base), "vault_quote": str(pool.vault_quote),
            "provider_a_accounts": {k: str(v) for k, v in pool.provider_accounts(PROVIDER_A).items()},
            "provider_b_accounts": {k: str(v) for k, v in pool.provider_accounts(PROVIDER_B).items()},
            "minimum_locked_lp": 100,
        }
    value = record(harness.pools["primary"])
    if "secondary" in harness.pools:
        value["secondary"] = record(harness.pools["secondary"])
    return value


def run_plan(candidate: Path, plan: dict, index: int = 0, images=None) -> dict:
    harness = fixture_only(candidate, index, plan, images)
    for number, step in enumerate(plan["steps"]):
        name, instructions, signers, operation = plan_step(harness, step, number)
        harness.execute(name, instructions, signers, operation)
    return {"case": plan["name"], "plan": plan, "fixture": expected_fixture(harness),
            "original": {"receipts": harness.receipts["original"]},
            "candidate": {"receipts": harness.receipts["candidate"]}}


def compare_case(row: dict) -> list[str]:
    fields = ("transaction_base64", "signatures", "message_sha256", "pool_label", "error", "error_detail", "outcome",
              "failure_class", "semantic_logs", "events", "inner_instructions", "return_data",
              "before", "after", "rollback_nonfee_equal", "accounting")
    differences = []
    left = row["original"]["receipts"]
    right = row["candidate"]["receipts"]
    if len(left) != len(right):
        return ["receipt_count"]
    for index, (a, b) in enumerate(zip(left, right)):
        for field in fields:
            if field in {"before", "after"}:
                left_state = {k: v for k, v in a[field].items() if k != str(AMM)}
                right_state = {k: v for k, v in b[field].items() if k != str(AMM)}
                equal = A.same_json(left_state, right_state)
            else:
                equal = A.same_json(a.get(field), b.get(field))
            if not equal:
                differences.append(f"{index}:{field}")
    return differences


def input_hashes() -> dict:
    return A.snapshot_inputs()


def source_manifest() -> tuple[dict, str]:
    roots = (ROOT / "programs/pump-amm", ROOT / "crates/native-transfer-fee")
    paths = [ROOT / "Cargo.lock", ROOT / "Cargo.toml"]
    for source_root in roots:
        paths.extend(path for path in source_root.rglob("*")
                     if path.is_file() and "target" not in path.relative_to(source_root).parts)
    manifest = {str(path.relative_to(ROOT)): file_sha(path) for path in sorted(set(paths))}
    return manifest, canonical_hash(manifest)


def program_hashes(candidate: Path) -> dict:
    return {"original": file_sha(CAPTURED["original"]), "candidate": file_sha(candidate),
            **{name: file_sha(path) for name, path in CAPTURED.items() if name != "original"}}


CAPTURED_SHA256 = {
    "original": "6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7",
    "spl_token": "8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697",
    "spl_token_2022": "15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d",
    "associated_token": "6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d",
    "pump_fees": "4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e",
}


def build_provenance(candidate: Path, receipt_path: Path | None) -> dict:
    if receipt_path is not None:
        raise ValueError("This runtime suite does not authenticate source-build receipts")
    return {"kind": "supplied_binary_only", "source_build_verified_by_this_suite": False}


def revision_context():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run_suite(candidate: Path, build_receipt: Path | None = None) -> dict:
    provenance = build_provenance(candidate, build_receipt)
    admitted = input_hashes()
    source_files, source_digest = source_manifest()
    images = {name: A.regular_bytes(path, root=ROOT) for name, path in CAPTURED.items()}
    images["candidate"] = A.regular_bytes(candidate)
    for name, digest in CAPTURED_SHA256.items():
        if sha(images[name]) != digest:
            raise ValueError("captured executable identity: " + name)
    cases = []
    with tempfile.TemporaryDirectory(prefix="amm-multi-lp-inputs-") as directory:
        private = {}
        for name, raw in images.items():
            path = Path(directory) / (name + ".so")
            path.write_bytes(raw)
            private[name] = path
        for index, plan in enumerate(plans()):
            row = run_plan(private["candidate"], plan, index, private)
            row["mismatch_fields"] = compare_case(row)
            observed = [receipt["outcome"] for receipt in row["original"]["receipts"]]
            row["expected_original_outcomes"] = EXPECTED_OUTCOMES[plan["name"]]
            row["observed_original_outcomes"] = observed
            row["oracle_mismatches"] = [] if observed == row["expected_original_outcomes"] else [{
                "expected": row["expected_original_outcomes"], "observed": observed}]
            infrastructure = any(receipt["failure_class"] == "infrastructure" for side in ("original", "candidate")
                                 for receipt in row[side]["receipts"])
            row["classification"] = ("infrastructure_failure" if infrastructure else
                                     "unsupported_fixture" if row["oracle_mismatches"] else
                                     "different_behavior" if row["mismatch_fields"] else "equal_observed_behavior")
            cases.append(row)
    A.recheck_inputs(admitted)
    if A.regular_bytes(candidate) != images["candidate"]:
        raise ValueError("candidate changed during execution")
    return {
        "schema": "pump-amm-multi-lp-v2", "upstream_commit": revision_context(),
        "source_snapshot_context_only": True,
        "program_ids": {"pump_amm": str(AMM), "spl_token": str(TOKEN), "spl_token_2022": str(TOKEN22), "associated_token": str(ATA)},
        "program_sha256": {name: sha(raw) for name, raw in images.items()},
        "candidate_build": provenance, "producer_input_sha256": admitted,
        "candidate_source_sha256": source_files, "candidate_source_manifest_sha256": source_digest,
        "case_count": len(cases), "transaction_count_per_image": sum(len(row["plan"]["steps"]) for row in cases),
        "cases": cases, "classification_counts": {name: sum(row["classification"] == name for row in cases)
            for name in ("equal_observed_behavior", "different_behavior", "unsupported_fixture", "infrastructure_failure")},
    }


def write_report(path: Path, report: dict) -> None:
    A.outside_repository(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError("retain prior report: " + str(path))
    publisher = _OUTPUT.PumpReport(path, ROOT, None, __file__, overwrite=False)
    raw = (json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    publisher.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def produce(candidate: Path, output: Path, build_receipt: Path | None = None):
    A.outside_repository(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain prior report: " + str(output))
    publisher = _OUTPUT.PumpReport(output, ROOT, candidate, __file__, overwrite=False)
    report = run_suite(candidate, build_receipt)
    A.recheck_inputs(report["producer_input_sha256"])
    if file_sha(candidate) != report["program_sha256"]["candidate"]:
        raise ValueError("candidate changed before publication")
    raw = (json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    publisher.write(gzip.compress(raw, mtime=0) if output.suffix == ".gz" else raw)
    A.recheck_inputs(report["producer_input_sha256"])
    if file_sha(candidate) != report["program_sha256"]["candidate"]:
        raise ValueError("candidate changed during publication")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-receipt", type=Path,
                        help="unsupported: runtime reports do not authenticate source-build receipts")
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    report = produce(candidate, args.output.absolute(), args.build_receipt.resolve() if args.build_receipt else None)
    print(json.dumps({"cases": report["case_count"],
                      "transactions_per_image": report["transaction_count_per_image"],
                      "classification_counts": report["classification_counts"]}, indent=2))
    return report["classification_counts"] != {"equal_observed_behavior": len(plans()),
             "different_behavior": 0, "unsupported_fixture": 0, "infrastructure_failure": 0}


if __name__ == "__main__":
    raise SystemExit(main())
