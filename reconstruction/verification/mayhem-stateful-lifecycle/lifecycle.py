#!/usr/bin/env python3
"""Deterministic persistent Mayhem LiteSVM fixture and signed transaction executor."""
from __future__ import annotations

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

import base64
import hashlib
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
# Execute the exact source we bind; Python -B still permits reading a .pyc.
_admission_path = HERE / "admission.py"
_admission_raw = _admission_path.read_bytes()
_admission = {"__file__": str(_admission_path), "__name__": "mayhem_admission"}
exec(compile(_admission_raw, str(_admission_path), "exec", dont_inherit=True), _admission)
LOADED_INPUT_SHA256 = _admission["snapshot_inputs"]()
LOADED_INPUT_SHA256[_admission_path.relative_to(ROOT).as_posix()] = hashlib.sha256(_admission_raw).hexdigest()
if "_ADMITTED_SOURCE_BYTES" in globals():
    LOADED_INPUT_SHA256[Path(__file__).resolve().relative_to(ROOT).as_posix()] = hashlib.sha256(_ADMITTED_SOURCE_BYTES).hexdigest()
recheck_inputs = lambda: _admission["recheck_inputs"](LOADED_INPUT_SHA256)
same_json = _admission["same_json"]
source_module = _admission["source_module"]

pump_fixture = source_module("mayhem_pump_trade_fixture", ROOT / "scripts/pump_trade_fixture.py")
LOADED_INPUT_SHA256["scripts/pump_trade_fixture.py"] = hashlib.sha256(pump_fixture._ADMITTED_SOURCE_BYTES).hexdigest()
recheck_inputs()
from solders.account import Account  # noqa: E402
from solders.clock import Clock  # noqa: E402
from solders.compute_budget import set_compute_unit_limit  # noqa: E402
from solders.instruction import AccountMeta, Instruction  # noqa: E402
from solders.keypair import Keypair  # noqa: E402
from solders.litesvm import LiteSVM  # noqa: E402
from solders.pubkey import Pubkey  # noqa: E402
from solders.transaction import Transaction  # noqa: E402
from solders.transaction_metadata import FailedTransactionMetadata  # noqa: E402

MAYHEM = Pubkey.from_string("MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e")
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
PUMP_FEES = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSTEM = Pubkey.default()
TOKEN_2022 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")

ADMIN = Keypair.from_seed(hashlib.sha256(b"mayhem-stateful-admin-v1").digest())
PAYER = Keypair.from_seed(hashlib.sha256(b"mayhem-stateful-payer-v1").digest())
INTRUDER = Keypair.from_seed(hashlib.sha256(b"mayhem-stateful-intruder-v1").digest())


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def selector(name: str) -> bytes:
    return hashlib.sha256(f"global:{name}".encode()).digest()[:8]


def account_snapshot(account: Account | None) -> dict | None:
    if account is None:
        return None
    return {
        "lamports": account.lamports,
        "owner": str(account.owner),
        "executable": account.executable,
        "rent_epoch": account.rent_epoch,
        "data_bytes": len(account.data),
        "data_sha256": sha256_bytes(account.data),
        "data_base64": None if account.executable else base64.b64encode(account.data).decode(),
    }


@dataclass(frozen=True)
class FixtureKeys:
    global_params: Pubkey
    mayhem_state: Pubkey
    sol_vault: Pubkey
    mint: Pubkey
    mayhem_token_vault: Pubkey
    pump_global: Pubkey
    bonding_curve: Pubkey
    fee_recipient: Pubkey
    associated_bonding_curve: Pubkey
    creator_vault: Pubkey
    pump_event_authority: Pubkey
    global_volume_accumulator: Pubkey
    user_volume_accumulator: Pubkey
    fee_config: Pubkey
    event_authority: Pubkey
    bonding_curve_v2: Pubkey
    buyback_recipient: Pubkey


class LifecycleVM:
    """One image, one persistent VM, and no account writes after construction."""

    def __init__(self, image: Path):
        recheck_inputs()
        self.image = image.resolve()
        self.spec = json.loads((HERE / "fixture.json").read_text())
        self.vm = LiteSVM().with_sigverify(True).with_blockhash_check(True).with_log_bytes_limit(None)
        self._load_programs()
        self.keys = self._install_fixture()
        self._transaction_index = 0
        self._last_blockhash = None
        self.watched = self._watched_keys()

    def account_roles(self):
        return {"admin_trader": str(ADMIN.pubkey()), "payer": str(PAYER.pubkey()),
                "intruder": str(INTRUDER.pubkey()), "mayhem_program": str(MAYHEM),
                **{name: str(value) for name, value in self.keys.__dict__.items()}}

    def _load_programs(self) -> None:
        for program, path in (
            (MAYHEM, self.image),
            (PUMP, ROOT / "evidence/original/pump/deployed.so"),
            (PUMP_FEES, ROOT / "evidence/original/pump_fees/deployed.so"),
        ):
            self.vm.add_program_from_file(program, path)
        for name in ("spl_token", "spl_token_2022", "associated_token"):
            capture = json.loads((ROOT / f"evidence/dependencies/{name}/capture.json").read_text())
            self.vm.add_program_from_file(
                Pubkey.from_string(capture["program"]),
                ROOT / f"evidence/dependencies/{name}/deployed.so",
            )

    def _install_fixture(self) -> FixtureKeys:
        source_vm = pump_fixture.vm
        source_tx = pump_fixture.ixs[-1]
        initial = {key: source_vm.get_account(key) for key in pump_fixture.msg.account_keys}
        for key, account in initial.items():
            if account is not None and not account.executable:
                self.vm.set_account(key, account)

        self.vm.set_clock(Clock(100, 0, 0, 0, self.spec["clock_unix_timestamp"]))
        for signer in (ADMIN, PAYER, INTRUDER):
            assert signer.pubkey().is_on_curve()
            self.vm.set_account(signer.pubkey(), Account(10_000_000_000, b"", SYSTEM))

        global_params = Pubkey.find_program_address([b"global-params"], MAYHEM)[0]
        sol_vault = Pubkey.find_program_address([b"sol-vault"], MAYHEM)[0]
        event_authority = Pubkey.find_program_address([b"__event_authority"], MAYHEM)[0]
        self.vm.set_account(sol_vault, Account(self.spec["initial_sol_vault_lamports"], b"", SYSTEM))

        v3 = source_tx.accounts
        mint = v3[1].pubkey
        token_program = v3[3].pubkey
        mayhem_state = Pubkey.find_program_address([b"mayhem-state", bytes(mint)], MAYHEM)[0]
        mayhem_token_vault = Pubkey.find_program_address(
            [bytes(sol_vault), bytes(token_program), bytes(mint)], ATA
        )[0]
        token_data = bytearray(initial[v3[9].pubkey].data)
        token_data[32:64] = bytes(sol_vault)
        struct.pack_into("<Q", token_data, 64, self.spec["initial_mayhem_token_vault_amount"])
        self.vm.set_account(mayhem_token_vault, Account(100_000_000, bytes(token_data), token_program))

        global_data = bytearray(hashlib.sha256(b"account:GlobalParams").digest()[:8] + bytes(310))
        global_data[49:81] = bytes(ADMIN.pubkey())
        global_data[81:113] = bytes(ADMIN.pubkey())
        struct.pack_into("<Q", global_data, 32, (1 << 64) - 1)
        struct.pack_into("<Q", global_data, 40, (1 << 64) - 1)
        self.vm.set_account(global_params, Account(100_000_000, bytes(global_data), MAYHEM))

        state_data = bytearray(hashlib.sha256(b"account:MayhemState").digest()[:8] + bytes(162))
        struct.pack_into("<q", state_data, 16, 10_000)
        state_data[24:56] = bytes(mint)
        state_data[97] = 1
        self.vm.set_account(mayhem_state, Account(100_000_000, bytes(state_data), MAYHEM))

        bonding_curve = Pubkey.from_string(pump_fixture.x["accounts"]["curve"])
        pump_global = Pubkey.from_string(pump_fixture.x["accounts"]["global"])
        curve_data = bytearray(initial[bonding_curve].data)
        curve_data[81] = 1
        self.vm.set_account(
            bonding_curve,
            Account(initial[bonding_curve].lamports, bytes(curve_data), PUMP),
        )
        creator = Pubkey(curve_data[49:81])
        creator_vault = Pubkey.find_program_address([b"creator-vault", bytes(creator)], PUMP)[0]
        fee_recipient = Pubkey(initial[pump_global].data[483:515])
        pump_event_authority = Pubkey.find_program_address([b"__event_authority"], PUMP)[0]
        bonding_curve_v2 = Pubkey.find_program_address([b"bonding-curve-v2", bytes(mint)], MAYHEM)[0]
        self.vm.set_account(bonding_curve_v2, Account(10_000_000, bytes(curve_data), PUMP))
        for key in (creator_vault, fee_recipient):
            if self.vm.get_account(key) is None:
                self.vm.set_account(key, Account(10_000_000, b"", SYSTEM))

        global_volume = Pubkey.find_program_address([b"global_volume_accumulator"], PUMP)[0]
        user_volume = Pubkey.find_program_address([b"user_volume_accumulator", bytes(sol_vault)], PUMP)[0]
        volume_data = bytearray(600)
        volume_data[:8] = hashlib.sha256(b"account:GlobalVolumeAccumulator").digest()[:8]
        struct.pack_into("<qqq", volume_data, 8, 1000, 10000, 86400)
        user_volume_data = bytearray(137)
        user_volume_data[:8] = hashlib.sha256(b"account:UserVolumeAccumulator").digest()[:8]
        user_volume_data[8:40] = bytes(sol_vault)
        self.vm.set_account(global_volume, Account(100_000_000, bytes(volume_data), PUMP))
        self.vm.set_account(user_volume, Account(100_000_000, bytes(user_volume_data), PUMP))

        return FixtureKeys(
            global_params=global_params,
            mayhem_state=mayhem_state,
            sol_vault=sol_vault,
            mint=mint,
            mayhem_token_vault=mayhem_token_vault,
            pump_global=pump_global,
            bonding_curve=bonding_curve,
            fee_recipient=fee_recipient,
            associated_bonding_curve=v3[6].pubkey,
            creator_vault=creator_vault,
            pump_event_authority=pump_event_authority,
            global_volume_accumulator=global_volume,
            user_volume_accumulator=user_volume,
            fee_config=Pubkey.from_string(pump_fixture.x["accounts"]["fee_config"]),
            event_authority=event_authority,
            bonding_curve_v2=bonding_curve_v2,
            buyback_recipient=v3[13].pubkey,
        )

    def _watched_keys(self) -> list[Pubkey]:
        values = [ADMIN.pubkey(), PAYER.pubkey(), INTRUDER.pubkey(), MAYHEM, PUMP, PUMP_FEES]
        values.extend(self.keys.__dict__.values())
        values.extend((SYSTEM, TOKEN_2022, ATA))
        return list(dict.fromkeys(values))

    def snapshot(self) -> dict[str, dict | None]:
        return {str(key): account_snapshot(self.vm.get_account(key)) for key in self.watched}

    def _trade_reference(self) -> int:
        curve = self.vm.get_account(self.keys.bonding_curve)
        virtual_tokens, virtual_sol = struct.unpack_from("<QQ", curve.data, 8)
        return virtual_sol * 10**15 // virtual_tokens

    def trade_instruction(self, name: str) -> Instruction:
        k = self.keys
        if name == "buy":
            keys = [
                ADMIN.pubkey(), k.global_params, k.mayhem_state, k.mint, k.mayhem_token_vault,
                k.sol_vault, SYSTEM, TOKEN_2022, k.pump_global, k.bonding_curve,
                k.fee_recipient, k.associated_bonding_curve, k.creator_vault,
                k.pump_event_authority, PUMP, k.global_volume_accumulator,
                k.user_volume_accumulator, k.fee_config, PUMP_FEES, k.event_authority,
                MAYHEM, k.bonding_curve_v2, k.buyback_recipient,
            ]
            writable = {0, 1, 2, 4, 5, 9, 10, 11, 12, 15, 16, 22}
        elif name == "sell":
            keys = [
                ADMIN.pubkey(), k.global_params, k.mayhem_state, k.sol_vault, k.mint,
                k.mayhem_token_vault, TOKEN_2022, SYSTEM, k.pump_global, k.bonding_curve,
                k.fee_recipient, k.associated_bonding_curve, k.creator_vault,
                k.pump_event_authority, PUMP, k.fee_config, PUMP_FEES, k.event_authority,
                MAYHEM, k.bonding_curve_v2, k.buyback_recipient,
            ]
            writable = {0, 1, 2, 3, 5, 9, 10, 11, 12, 20}
        else:
            raise ValueError(f"unknown trade instruction: {name}")
        args = self.spec["trade_arguments"]
        data = (
            selector(name)
            + self._trade_reference().to_bytes(16, "little")
            + struct.pack("<HH", args["tolerance_bps"], args["retained_reserve_bps"])
        )
        metas = [AccountMeta(key, index == 0, index in writable) for index, key in enumerate(keys)]
        return Instruction(MAYHEM, data, metas)

    def admin_instruction(self, name: str, unauthorized: bool = False) -> Instruction:
        authority = INTRUDER.pubkey() if unauthorized else ADMIN.pubkey()
        metas = [
            AccountMeta(authority, True, True),
            AccountMeta(self.keys.global_params, False, True),
            AccountMeta(SYSTEM, False, False),
            AccountMeta(self.keys.event_authority, False, False),
            AccountMeta(MAYHEM, False, False),
        ]
        return Instruction(MAYHEM, selector(name), metas)

    def named_instruction(self, name: str) -> tuple[Instruction, Keypair]:
        if name in ("buy", "sell"):
            return self.trade_instruction(name), ADMIN
        if name == "resume_trading_unauthorized":
            return self.admin_instruction("resume_trading", unauthorized=True), INTRUDER
        if name in ("stop_trading", "resume_trading"):
            return self.admin_instruction(name), ADMIN
        raise ValueError(f"unknown planned instruction: {name}")

    def execute(self, lifecycle: str, step: dict) -> dict:
        if self._transaction_index:
            previous = self.vm.latest_blockhash()
            self.vm.expire_blockhash()
            assert self.vm.latest_blockhash() != previous
        blockhash = self.vm.latest_blockhash()
        assert blockhash != self._last_blockhash
        self._last_blockhash = blockhash

        instructions = [set_compute_unit_limit(1_400_000)]
        signers = [PAYER]
        for name in step["instructions"]:
            instruction, signer = self.named_instruction(name)
            instructions.append(instruction)
            if signer.pubkey() not in {item.pubkey() for item in signers}:
                signers.append(signer)

        before = self.snapshot()
        tx = Transaction.new_signed_with_payer(instructions, PAYER.pubkey(), signers, blockhash)
        assert tx.signatures and all(tx.verify_with_results())
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        metadata = result.meta() if failed else result
        raw_metadata = json.loads(metadata.to_json())
        raw_tx = bytes(tx)
        after = self.snapshot()
        self._transaction_index += 1
        return {
            "lifecycle": lifecycle,
            "step": step["name"],
            "instructions": step["instructions"],
            "expected": step["expect"],
            "transaction_index": self._transaction_index - 1,
            "transaction_sha256": sha256_bytes(raw_tx),
            "transaction_base64": base64.b64encode(raw_tx).decode(),
            "signatures": [str(value) for value in tx.signatures],
            "signature_verification": tx.verify_with_results(),
            "recent_blockhash": str(blockhash),
            "account_roles": self.account_roles(),
            "error": str(result.err()) if failed else None,
            "before": before,
            "after": after,
            "events": [line for line in metadata.logs() if line.startswith("Program data: ")],
            "inner_instructions": raw_metadata["inner_instructions"],
            "return_data": raw_metadata["return_data"],
            "logs": metadata.logs(),
            "compute_units_consumed": metadata.compute_units_consumed(),
        }

    def run_lifecycle(self, lifecycle: dict) -> list[dict]:
        return [self.execute(lifecycle["name"], step) for step in lifecycle["steps"]]


def lifecycle_plan() -> list[dict]:
    recheck_inputs()
    return json.loads((HERE / "fixture.json").read_text())["lifecycles"]


def run_image(image: Path) -> list[dict]:
    recheck_inputs()
    image_digest = sha256_bytes(image.read_bytes())
    receipts = []
    for lifecycle in lifecycle_plan():
        receipts.extend(LifecycleVM(image).run_lifecycle(lifecycle))
    recheck_inputs()
    if sha256_bytes(image.read_bytes()) != image_digest:
        raise ValueError("image changed during execution")
    return receipts
