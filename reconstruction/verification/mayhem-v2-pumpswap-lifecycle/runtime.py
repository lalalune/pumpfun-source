#!/usr/bin/env python3
"""Persistent signed Mayhem V2 and PumpSwap execution fixtures."""
from __future__ import annotations

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

import base64
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

import mayhem_buy_v2_fixture as v2_fixture  # noqa: E402
import mayhem_pump_swap_fixture as swap_fixture  # noqa: E402
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
AMM = Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
FEES = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN_2022 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSTEM = Pubkey.default()
TRADER = Keypair.from_seed(hashlib.sha256(b"mayhem-v2-pumpswap-lifecycle-trader-v1").digest())
PAYER = Keypair.from_seed(hashlib.sha256(b"mayhem-v2-pumpswap-lifecycle-payer-v1").digest())


def selector(name: str) -> bytes:
    return hashlib.sha256(f"global:{name}".encode()).digest()[:8]


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


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


def token_account(mint: Pubkey, owner: Pubkey, amount: int, native: bool = False) -> bytes:
    raw = bytearray(165)
    raw[:32] = bytes(mint)
    raw[32:64] = bytes(owner)
    struct.pack_into("<Q", raw, 64, amount)
    raw[108] = 1
    if native:
        struct.pack_into("<IQ", raw, 109, 1, 2_039_280)
    return bytes(raw)


def ata(owner: Pubkey, mint: Pubkey, program: Pubkey) -> Pubkey:
    return Pubkey.find_program_address([bytes(owner), bytes(program), bytes(mint)], ATA)[0]


class PersistentVM:
    """A single image and stateful VM; fixture accounts are written only at construction."""

    venue: str

    def __init__(self, image: Path):
        self.image = image.resolve()
        self.vm = LiteSVM().with_sigverify(True).with_blockhash_check(True).with_log_bytes_limit(None)
        self.vm.set_clock(Clock(100, 0, 0, 0, 100))
        self._index = 0
        self._last_blockhash = None

    def roles(self) -> dict[str, str]:
        return {
            "trader": str(TRADER.pubkey()),
            "payer": str(PAYER.pubkey()),
            "mayhem_program": str(MAYHEM),
            **{name: str(value) for name, value in self.keys.items()},
        }

    def snapshot(self) -> dict[str, dict | None]:
        return {str(key): account_snapshot(self.vm.get_account(key)) for key in self.watched}

    def build_instruction(self, name: str) -> Instruction:
        raise NotImplementedError

    def execute(self, lifecycle: str, step: dict) -> dict:
        if self._index:
            prior = self.vm.latest_blockhash()
            self.vm.expire_blockhash()
            assert self.vm.latest_blockhash() != prior
        blockhash = self.vm.latest_blockhash()
        assert blockhash != self._last_blockhash
        self._last_blockhash = blockhash
        instructions = [set_compute_unit_limit(1_400_000)]
        instructions.extend(self.build_instruction(name) for name in step["instructions"])
        tx = Transaction.new_signed_with_payer(
            instructions, PAYER.pubkey(), [PAYER, TRADER], blockhash
        )
        assert tx.signatures and all(tx.verify_with_results())
        before = self.snapshot()
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        metadata = result.meta() if failed else result
        raw_metadata = json.loads(metadata.to_json())
        after = self.snapshot()
        raw_tx = bytes(tx)
        receipt = {
            "venue": self.venue,
            "lifecycle": lifecycle,
            "step": step["name"],
            "instructions": step["instructions"],
            "expected": step["expect"],
            "transaction_index": self._index,
            "transaction_base64": base64.b64encode(raw_tx).decode(),
            "transaction_sha256": sha256_bytes(raw_tx),
            "signatures": [str(item) for item in tx.signatures],
            "signature_verification": tx.verify_with_results(),
            "recent_blockhash": str(blockhash),
            "account_roles": self.roles(),
            "error": str(result.err()) if failed else None,
            "before": before,
            "after": after,
            "events": [line for line in metadata.logs() if line.startswith("Program data: ")],
            "inner_instructions": raw_metadata["inner_instructions"],
            "return_data": raw_metadata["return_data"],
            "logs": metadata.logs(),
            "compute_units_consumed": metadata.compute_units_consumed(),
        }
        self._index += 1
        return receipt


class V2VM(PersistentVM):
    venue = "v2"

    def __init__(self, image: Path):
        super().__init__(image)
        f = v2_fixture.f
        for program, path in (
            (MAYHEM, self.image),
            (PUMP, ROOT / "evidence/original/pump/deployed.so"),
            (FEES, ROOT / "evidence/original/pump_fees/deployed.so"),
        ):
            self.vm.add_program_from_file(program, path)
        for name in ("spl_token", "spl_token_2022", "associated_token"):
            capture = json.loads((ROOT / f"evidence/dependencies/{name}/capture.json").read_text())
            self.vm.add_program_from_file(
                Pubkey.from_string(capture["program"]),
                ROOT / f"evidence/dependencies/{name}/deployed.so",
            )
        for key, account in v2_fixture.INITIAL.items():
            if account is not None and not account.executable:
                self.vm.set_account(key, account)
        for signer in (TRADER, PAYER):
            self.vm.set_account(signer.pubkey(), Account(10_000_000_000, b"", SYSTEM))

        global_params = Pubkey.find_program_address([b"global-params"], MAYHEM)[0]
        sol_vault = Pubkey.find_program_address([b"sol-vault"], MAYHEM)[0]
        event_authority = Pubkey.find_program_address([b"__event_authority"], MAYHEM)[0]
        self.vm.set_account(sol_vault, Account(10_000_000_000, b"", SYSTEM))
        v3 = f.ixs[-1].accounts
        mint, base_program = v3[1].pubkey, v3[3].pubkey
        mayhem_state = Pubkey.find_program_address([b"mayhem-state", bytes(mint)], MAYHEM)[0]
        base_vault = ata(sol_vault, mint, base_program)
        raw = bytearray(v2_fixture.INITIAL[v3[9].pubkey].data)
        raw[32:64] = bytes(sol_vault)
        struct.pack_into("<Q", raw, 64, 1_000_000_000_000)
        self.vm.set_account(base_vault, Account(100_000_000, bytes(raw), base_program))

        global_raw = bytearray(hashlib.sha256(b"account:GlobalParams").digest()[:8] + bytes(310))
        global_raw[49:81] = bytes(TRADER.pubkey())
        global_raw[81:113] = bytes(TRADER.pubkey())
        for offset in (32, 40, 190, 198):
            struct.pack_into("<Q", global_raw, offset, (1 << 64) - 1)
        self.vm.set_account(global_params, Account(100_000_000, bytes(global_raw), MAYHEM))
        state_raw = bytearray(hashlib.sha256(b"account:MayhemState").digest()[:8] + bytes(162))
        struct.pack_into("<q", state_raw, 16, 10_000)
        state_raw[24:56] = bytes(mint)
        state_raw[97] = 1
        self.vm.set_account(mayhem_state, Account(100_000_000, bytes(state_raw), MAYHEM))

        curve = v2_fixture.CURVE
        curve_raw = bytearray(v2_fixture.INITIAL[curve].data)
        curve_raw[81] = 1
        self.vm.set_account(curve, Account(v2_fixture.INITIAL[curve].lamports, bytes(curve_raw), PUMP))
        pump_global = v2_fixture.PGLOBAL
        creator = Pubkey(curve_raw[49:81])
        creator_vault = Pubkey.find_program_address([b"creator-vault", bytes(creator)], PUMP)[0]
        fee_recipient = Pubkey(v2_fixture.INITIAL[pump_global].data[483:515])
        pump_event = Pubkey.find_program_address([b"__event_authority"], PUMP)[0]
        curve_v2 = Pubkey.find_program_address([b"bonding-curve-v2", bytes(mint)], MAYHEM)[0]
        self.vm.set_account(curve_v2, Account(10_000_000, bytes(curve_raw), PUMP))
        for key in (creator_vault, fee_recipient):
            if self.vm.get_account(key) is None:
                self.vm.set_account(key, Account(10_000_000, b"", SYSTEM))

        quote = Pubkey.from_string("So11111111111111111111111111111111111111112")
        quote_program = TOKEN
        quote_mint = bytearray(82)
        struct.pack_into("<Q", quote_mint, 36, 10**15)
        quote_mint[44:46] = bytes((9, 1))
        self.vm.set_account(quote, Account(1_000_000_000, bytes(quote_mint), quote_program))
        global_volume = Pubkey.find_program_address([b"global_volume_accumulator"], PUMP)[0]
        volume = bytearray(600)
        volume[:8] = hashlib.sha256(b"account:GlobalVolumeAccumulator").digest()[:8]
        struct.pack_into("<qqq", volume, 8, 1000, 10000, 86400)
        self.vm.set_account(global_volume, Account(100_000_000, bytes(volume), PUMP))
        user_volume = Pubkey.find_program_address([b"user_volume_accumulator", bytes(sol_vault)], PUMP)[0]
        user_volume_raw = bytearray(137)
        user_volume_raw[:8] = hashlib.sha256(b"account:UserVolumeAccumulator").digest()[:8]
        user_volume_raw[8:40] = bytes(sol_vault)
        self.vm.set_account(user_volume, Account(100_000_000, bytes(user_volume_raw), PUMP))
        sharing = Pubkey.find_program_address([b"sharing-config", bytes(mint)], FEES)[0]
        self.vm.set_account(sharing, Account(10_000_000, b"", SYSTEM))
        quote_accounts = {}
        authorities = {
            "vault": sol_vault,
            "curve": curve,
            "fee": fee_recipient,
            "creator": creator_vault,
            "volume": user_volume,
            "buyback": v3[13].pubkey,
        }
        for name, authority in authorities.items():
            address = ata(authority, quote, quote_program)
            quote_accounts[name] = address
            self.vm.set_account(
                address,
                Account(1_000_000_000, token_account(quote, authority, 1_000_000_000_000), quote_program),
            )
        self.keys = {
            "global_params": global_params,
            "mayhem_state": mayhem_state,
            "mint": mint,
            "quote_mint": quote,
            "base_vault": base_vault,
            "quote_vault": quote_accounts["vault"],
            "sol_vault": sol_vault,
            "pump_global": pump_global,
            "bonding_curve": curve,
            "curve_quote_vault": quote_accounts["curve"],
            "fee_recipient": fee_recipient,
            "fee_quote_vault": quote_accounts["fee"],
            "curve_base_vault": v3[6].pubkey,
            "creator_vault": creator_vault,
            "creator_quote_vault": quote_accounts["creator"],
            "sharing_config": sharing,
            "pump_event_authority": pump_event,
            "global_volume": global_volume,
            "user_volume": user_volume,
            "volume_quote_vault": quote_accounts["volume"],
            "fee_config": Pubkey.from_string(f.x["accounts"]["fee_config"]),
            "event_authority": event_authority,
            "curve_v2": curve_v2,
            "buyback": v3[13].pubkey,
            "buyback_quote_vault": quote_accounts["buyback"],
        }
        self.base_program = base_program
        self.quote_program = quote_program
        self.watched = list(dict.fromkeys(
            [TRADER.pubkey(), PAYER.pubkey(), MAYHEM, PUMP, FEES, TOKEN, TOKEN_2022, ATA]
            + list(self.keys.values())
        ))

    def _reference(self) -> int:
        raw = self.vm.get_account(self.keys["bonding_curve"]).data
        virtual_tokens, virtual_quote = struct.unpack_from("<QQ", raw, 8)
        return virtual_quote * 10**15 // virtual_tokens

    def build_instruction(self, name: str) -> Instruction:
        invalid = name.endswith("_invalid_reference")
        actual = name.removesuffix("_invalid_reference")
        k = self.keys
        common = [
            TRADER.pubkey(), k["global_params"], k["mayhem_state"], k["mint"],
            k["quote_mint"], ATA, k["base_vault"], k["quote_vault"], k["sol_vault"],
            SYSTEM, self.base_program, self.quote_program, k["pump_global"],
            k["bonding_curve"], k["curve_quote_vault"], k["fee_recipient"],
            k["fee_quote_vault"], k["curve_base_vault"], k["creator_vault"],
            k["creator_quote_vault"], k["sharing_config"], k["pump_event_authority"],
            PUMP,
        ]
        if actual == "buy_v2":
            keys = common + [k["global_volume"], k["user_volume"], k["volume_quote_vault"]]
            keys += [k["fee_config"], FEES, k["event_authority"], MAYHEM, k["buyback"], k["buyback_quote_vault"]]
            writable = {0, 1, 2, 6, 7, 8, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25, 30, 31}
        elif actual == "sell_v2":
            keys = common + [k["user_volume"], k["volume_quote_vault"]]
            keys += [k["fee_config"], FEES, k["event_authority"], MAYHEM, k["buyback"], k["buyback_quote_vault"]]
            writable = {0, 1, 2, 6, 7, 8, 13, 14, 15, 16, 17, 18, 19, 23, 24, 29, 30}
        else:
            raise ValueError(f"unknown V2 instruction: {name}")
        reference = 0 if invalid else self._reference()
        tolerance = 0 if invalid else 2400
        data = selector(actual) + reference.to_bytes(16, "little") + struct.pack("<HH", tolerance, 9000)
        return Instruction(MAYHEM, data, [AccountMeta(key, i == 0, i in writable) for i, key in enumerate(keys)])


class PumpSwapVM(PersistentVM):
    venue = "pumpswap"

    def __init__(self, image: Path):
        super().__init__(image)
        f = swap_fixture
        for program, path in (
            (MAYHEM, self.image),
            (AMM, ROOT / "evidence/original/pump_amm/deployed.so"),
            (FEES, ROOT / "evidence/original/pump_fees/deployed.so"),
            (TOKEN, ROOT / "evidence/dependencies/spl_token/deployed.so"),
            (TOKEN_2022, ROOT / "evidence/dependencies/spl_token_2022/deployed.so"),
            (ATA, ROOT / "evidence/dependencies/associated_token/deployed.so"),
        ):
            self.vm.add_program_from_file(program, path)
        for row in f.F["accounts"].values():
            self.vm.set_account(
                Pubkey.from_string(row["address"]),
                Account(row["lamports"], base64.b64decode(row["data_base64"]), Pubkey.from_string(row["owner"])),
            )
        for signer in (TRADER, PAYER):
            self.vm.set_account(signer.pubkey(), Account(10_000_000_000, b"", SYSTEM))
        global_params = Pubkey.find_program_address([b"global-params"], MAYHEM)[0]
        sol_vault = Pubkey.find_program_address([b"sol-vault"], MAYHEM)[0]
        event_authority = Pubkey.find_program_address([b"__event_authority"], MAYHEM)[0]
        amm_event = Pubkey.find_program_address([b"__event_authority"], AMM)[0]
        for key in (sol_vault, event_authority, amm_event):
            self.vm.set_account(key, Account(10_000_000_000, b"", SYSTEM))
        base = Pubkey.from_string(f.F["keys"]["base_mint"])
        quote = Pubkey.from_string(f.F["keys"]["quote_mint"])
        pool = Pubkey.from_string(f.F["pool"])
        pool_base = Pubkey.from_string(f.F["keys"]["pool_base_token_account"])
        pool_quote = Pubkey.from_string(f.F["keys"]["pool_quote_token_account"])
        fee_config = Pubkey.from_string(f.F["keys"]["fee_config"])
        config = Pubkey.from_string(f.CONFIG["address"])
        base_program = TOKEN_2022
        quote_program = self.vm.get_account(quote).owner
        base_mint = self.vm.get_account(base)
        self.vm.set_account(base, Account(base_mint.lamports, base_mint.data, base_program))
        old_pool_base = self.vm.get_account(pool_base)
        pool_base = ata(pool, base, base_program)
        self.vm.set_account(pool_base, Account(old_pool_base.lamports, old_pool_base.data, base_program))
        pool_raw = bytearray(self.vm.get_account(pool).data)
        pool_raw[139:171] = bytes(pool_base)
        pool_raw[245:287] = bytes(42)
        self.vm.set_account(pool, Account(self.vm.get_account(pool).lamports, bytes(pool_raw), AMM))
        config_raw = bytearray(base64.b64decode(f.CONFIG["data_base64"]))
        config_raw[56] = 0
        self.vm.set_account(config, Account(f.CONFIG["lamports"], bytes(config_raw), AMM))
        protocol = Pubkey(config_raw[57:89])
        creator = Pubkey(pool_raw[211:243])
        creator_vault = Pubkey.find_program_address([b"creator_vault", bytes(creator)], AMM)[0]
        buyback = Pubkey(base64.b64decode(f.F["accounts"]["buyback_fee_recipient"]["data_base64"])[32:64])
        base_vault = ata(sol_vault, base, base_program)
        quote_vault = ata(sol_vault, quote, quote_program)
        protocol_quote = ata(protocol, quote, quote_program)
        creator_quote = ata(creator_vault, quote, quote_program)
        buyback_quote = ata(buyback, quote, quote_program)
        self.vm.set_account(base_vault, Account(100_000_000, token_account(base, sol_vault, 1_000_000_000_000), base_program))
        for address, owner, amount in (
            (quote_vault, sol_vault, 0),
            (protocol_quote, protocol, 0),
            (creator_quote, creator_vault, 0),
            (buyback_quote, buyback, 0),
        ):
            self.vm.set_account(address, Account(amount + 2_039_280, token_account(quote, owner, amount, True), quote_program))
        for key in (protocol, creator_vault, buyback):
            self.vm.set_account(key, Account(100_000_000, b"", SYSTEM))
        mayhem_state = Pubkey.find_program_address([b"mayhem-state", bytes(base)], MAYHEM)[0]
        global_raw = bytearray(hashlib.sha256(b"account:GlobalParams").digest()[:8] + bytes(310))
        global_raw[49:81] = bytes(TRADER.pubkey())
        global_raw[81:113] = bytes(TRADER.pubkey())
        for offset in (32, 40, 190, 198):
            struct.pack_into("<Q", global_raw, offset, (1 << 64) - 1)
        self.vm.set_account(global_params, Account(100_000_000, bytes(global_raw), MAYHEM))
        state_raw = bytearray(hashlib.sha256(b"account:MayhemState").digest()[:8] + bytes(162))
        struct.pack_into("<q", state_raw, 16, 10_000)
        state_raw[24:56] = bytes(base)
        state_raw[97] = 1
        self.vm.set_account(mayhem_state, Account(100_000_000, bytes(state_raw), MAYHEM))
        global_volume = Pubkey.find_program_address([b"global_volume_accumulator"], AMM)[0]
        user_volume = Pubkey.find_program_address([b"user_volume_accumulator", bytes(sol_vault)], AMM)[0]
        volume = hashlib.sha256(b"account:GlobalVolumeAccumulator").digest()[:8] + struct.pack("<qqq", 1000, 10000, 86400) + bytes(base) + bytes(480)
        self.vm.set_account(global_volume, Account(100_000_000, volume, AMM))
        self.vm.set_account(user_volume, Account(100_000_000, hashlib.sha256(b"account:UserVolumeAccumulator").digest()[:8] + bytes(sol_vault) + bytes(97), AMM))
        pool_v2 = Pubkey.find_program_address([b"pool-v2", bytes(base)], MAYHEM)[0]
        self.vm.set_account(pool_v2, Account(100_000_000, b"", SYSTEM))
        self.keys = {
            "global_params": global_params,
            "mayhem_state": mayhem_state,
            "base_mint": base,
            "base_vault": base_vault,
            "quote_vault": quote_vault,
            "sol_vault": sol_vault,
            "pool": pool,
            "global_config": config,
            "quote_mint": quote,
            "pool_base_vault": pool_base,
            "pool_quote_vault": pool_quote,
            "protocol": protocol,
            "protocol_quote_vault": protocol_quote,
            "amm_event_authority": amm_event,
            "creator_quote_vault": creator_quote,
            "creator_vault": creator_vault,
            "global_volume": global_volume,
            "user_volume": user_volume,
            "fee_config": fee_config,
            "event_authority": event_authority,
            "pool_v2": pool_v2,
            "buyback": buyback,
            "buyback_quote_vault": buyback_quote,
        }
        self.base_program = base_program
        self.quote_program = quote_program
        self.watched = list(dict.fromkeys(
            [TRADER.pubkey(), PAYER.pubkey(), MAYHEM, AMM, FEES, TOKEN, TOKEN_2022, ATA]
            + list(self.keys.values())
        ))

    def _reference(self) -> int:
        base = struct.unpack_from("<Q", self.vm.get_account(self.keys["pool_base_vault"]).data, 64)[0]
        quote = struct.unpack_from("<Q", self.vm.get_account(self.keys["pool_quote_vault"]).data, 64)[0]
        virtual = int.from_bytes(self.vm.get_account(self.keys["pool"]).data[245:261], "little", signed=True)
        return max(0, quote + virtual) * 10**15 // base

    def build_instruction(self, name: str) -> Instruction:
        invalid = name.endswith("_invalid_reference")
        actual = name.removesuffix("_invalid_reference")
        k = self.keys
        keys = [
            TRADER.pubkey(), k["global_params"], k["mayhem_state"], k["base_mint"],
            k["base_vault"], k["quote_vault"], k["sol_vault"], SYSTEM,
            self.quote_program, self.base_program, ATA, k["pool"], k["global_config"],
            k["quote_mint"], k["pool_base_vault"], k["pool_quote_vault"],
            k["protocol"], k["protocol_quote_vault"], k["amm_event_authority"], AMM,
            k["creator_quote_vault"], k["creator_vault"], k["global_volume"],
            k["user_volume"], k["fee_config"], FEES, k["event_authority"], MAYHEM,
            k["pool_v2"], k["buyback"], k["buyback_quote_vault"],
        ]
        writable = {0, 1, 2, 4, 5, 6, 11, 14, 15, 16, 17, 20, 22, 23, 30}
        if actual == "sell_pump_swap":
            keys = keys[:22] + keys[24:]
            writable = {i for i in writable if i < 22} | {i - 2 for i in writable if i >= 24}
        elif actual != "buy_pump_swap":
            raise ValueError(f"unknown PumpSwap instruction: {name}")
        reference = 0 if invalid else self._reference()
        tolerance = 0 if invalid else 2400
        payload = selector(actual) + reference.to_bytes(16, "little") + struct.pack("<HH", tolerance, 9000)
        return Instruction(MAYHEM, payload, [AccountMeta(key, i == 0, i in writable) for i, key in enumerate(keys)])


def plan() -> list[dict]:
    return json.loads((HERE / "plan.json").read_text())["lifecycles"]


def run_image(image: Path) -> list[dict]:
    digest = sha256_bytes(image.read_bytes())
    rows = []
    for lifecycle in plan():
        fixture = V2VM(image) if lifecycle["venue"] == "v2" else PumpSwapVM(image)
        rows.extend(fixture.execute(lifecycle["name"], step) for step in lifecycle["steps"])
    if sha256_bytes(image.read_bytes()) != digest:
        raise ValueError("program image changed during execution")
    return rows
