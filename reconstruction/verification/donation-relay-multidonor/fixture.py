#!/usr/bin/env python3
"""Deterministic accounts and instructions for Donation Relay multi-donor runs."""
from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey


P = Pubkey.from_string
RELAY = P("RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu")
RELAYER = P("RLYRf96HAJSbbXCNS6ibQYnkxtb6kbfuFxqEkm9oQUc")
TOKEN = P("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ATA = P("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSTEM = Pubkey.default()
ORIGINAL_SHA256 = "367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563"
TOKEN_SHA256 = "8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697"
ATA_SHA256 = "6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d"
DONOR_NAMES = ("A", "B", "C")
MINT_NAMES = ("mint_x", "mint_y")
DOMAIN_NAMES = ("config_a_mint_x", "config_b_mint_x", "config_a_mint_y")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def owned_key(case: str, label: str) -> Keypair:
    seed = hashlib.sha256(f"relay-multidonor/{case}/{label}".encode()).digest()
    return Keypair.from_seed(seed)


def data_pubkey(case: str, label: str) -> Pubkey:
    return Pubkey.from_bytes(hashlib.sha256(f"relay-multidonor-data/{case}/{label}".encode()).digest())


def discriminator(namespace: str, name: str) -> bytes:
    return hashlib.sha256(f"{namespace}:{name}".encode()).digest()[:8]


def pda(*seeds: bytes) -> tuple[Pubkey, int]:
    return Pubkey.find_program_address(list(seeds), RELAY)


def associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def account(lamports: int, data: bytes = b"", owner: Pubkey = SYSTEM) -> Account:
    return Account(lamports, data, owner)


def mint_data(*, decimals: int = 6, supply: int = 10**15) -> bytes:
    data = bytearray(82)
    data[36:44] = supply.to_bytes(8, "little")
    data[44] = decimals
    data[45] = 1
    return bytes(data)


def token_data(mint: Pubkey, authority: Pubkey, amount: int) -> bytes:
    if not 0 <= amount <= (1 << 64) - 1:
        raise ValueError("token amount outside u64")
    data = bytearray(165)
    data[:32] = bytes(mint)
    data[32:64] = bytes(authority)
    data[64:72] = amount.to_bytes(8, "little")
    data[108] = 1
    return bytes(data)


def token_amount(row: dict[str, Any] | None) -> int | None:
    if row is None or "data_base64" not in row:
        return None
    data = base64.b64decode(row["data_base64"])
    return None if len(data) < 72 else int.from_bytes(data[64:72], "little")


def account_data(row: dict[str, Any] | None) -> bytes:
    return b"" if row is None else base64.b64decode(row.get("data_base64", ""))


@dataclass(frozen=True)
class Donor:
    name: str
    keypair: Keypair
    sources: dict[str, Pubkey]


@dataclass(frozen=True)
class Domain:
    name: str
    config_name: str
    mint_name: str
    config: bytes
    mint: Pubkey
    epoch: Pubkey
    debouncer: Pubkey
    destination: Pubkey


@dataclass
class Fixture:
    case: str
    fee: Keypair
    outsider: Keypair
    donors: dict[str, Donor]
    mints: dict[str, Pubkey]
    configs: dict[str, bytes]
    domains: dict[str, Domain]
    whitelist: Pubkey
    event: Pubkey
    accounts: dict[Pubkey, Account]

    @classmethod
    def create(cls, case: str, balances: dict[str, int] | None = None) -> "Fixture":
        balances = dict(balances or {})
        fee = owned_key(case, "fee-payer")
        outsider = owned_key(case, "outsider")
        mints = {name: data_pubkey(case, name) for name in MINT_NAMES}
        configs = {name: bytes(data_pubkey(case, name)) for name in ("config_a", "config_b")}
        domains: dict[str, Domain] = {}
        for name, config_name, mint_name in (
            ("config_a_mint_x", "config_a", "mint_x"),
            ("config_b_mint_x", "config_b", "mint_x"),
            ("config_a_mint_y", "config_a", "mint_y"),
        ):
            config, mint = configs[config_name], mints[mint_name]
            epoch = pda(b"epoch_tracker_v1", config, bytes(mint))[0]
            debouncer = pda(b"debouncer_v1", config, bytes(mint))[0]
            domains[name] = Domain(name, config_name, mint_name, config, mint, epoch,
                                   debouncer, associated_token_address(debouncer, mint))

        donors: dict[str, Donor] = {}
        for name in DONOR_NAMES:
            signer = owned_key(case, f"donor-{name}")
            sources = {mint_name: associated_token_address(signer.pubkey(), mint)
                       for mint_name, mint in mints.items()}
            donors[name] = Donor(name, signer, sources)

        whitelist, whitelist_bump = pda(b"mint_whitelist_v1")
        event = pda(b"__event_authority")[0]
        accounts: dict[Pubkey, Account] = {
            fee.pubkey(): account(50_000_000_000),
            outsider.pubkey(): account(50_000_000_000),
            whitelist: account(
                10**9,
                discriminator("account", "MintWhitelistV1") + bytes([whitelist_bump])
                + (0).to_bytes(4, "little") + bytes(1024),
                RELAY,
            ),
            event: account(0),
        }
        for mint in mints.values():
            accounts[mint] = account(10**9, mint_data(), TOKEN)
        for donor in donors.values():
            accounts[donor.keypair.pubkey()] = account(50_000_000_000)
            for mint_name, source in donor.sources.items():
                amount = balances.get(f"{donor.name}:{mint_name}", 10_000_000)
                accounts[source] = account(3_000_000, token_data(mints[mint_name], donor.keypair.pubkey(), amount), TOKEN)
        for domain in domains.values():
            accounts[domain.epoch] = account(0)
            accounts[domain.debouncer] = account(0)
            accounts[domain.destination] = account(0)
        return cls(case, fee, outsider, donors, mints, configs, domains,
                   whitelist, event, accounts)

    def watch(self) -> set[Pubkey]:
        return set(self.accounts) | {RELAY, TOKEN, ATA, SYSTEM}

    def donation(
        self,
        donor_name: str,
        amount: int,
        *,
        domain_name: str = "config_a_mint_x",
        message: bytes = b"multi-donor donation",
        tip_bps: int = 125,
        source_donor: str | None = None,
    ) -> Instruction:
        if not 0 <= amount <= (1 << 64) - 1:
            raise ValueError("donation amount outside u64")
        if not 0 <= tip_bps <= (1 << 16) - 1:
            raise ValueError("tip bps outside u16")
        donor = self.donors[donor_name]
        domain = self.domains[domain_name]
        source = self.donors[source_donor or donor_name].sources[domain.mint_name]
        metas = [
            AccountMeta(domain.epoch, False, True),
            AccountMeta(domain.debouncer, False, True),
            AccountMeta(domain.destination, False, True),
            AccountMeta(domain.mint, False, True),
            AccountMeta(source, False, True),
            AccountMeta(donor.keypair.pubkey(), True, True),
            AccountMeta(self.whitelist, False, False),
            AccountMeta(ATA, False, False),
            AccountMeta(TOKEN, False, False),
            AccountMeta(SYSTEM, False, False),
            AccountMeta(self.event, False, False),
            AccountMeta(RELAY, False, False),
        ]
        data = (
            discriminator("global", "donate_v1")
            + amount.to_bytes(8, "little")
            + domain.config
            + tip_bps.to_bytes(2, "little")
            + len(message).to_bytes(4, "little")
            + message
            + bytes(donor.keypair.pubkey())
        )
        return Instruction(RELAY, data, metas)

    def close_wrong_signer(self, domain_name: str = "config_a_mint_x") -> tuple[Instruction, set[Pubkey]]:
        domain = self.domains[domain_name]
        distribution = pda(
            b"distribution_v1", domain.config, bytes(domain.mint), (0).to_bytes(16, "little")
        )[0]
        vault = associated_token_address(distribution, domain.mint)
        for address in (distribution, vault):
            self.accounts.setdefault(address, account(0))
        data = discriminator("global", "close_donation_epoch_v1") + domain.config + (0).to_bytes(16, "little")
        metas = [
            AccountMeta(distribution, False, True),
            AccountMeta(vault, False, True),
            AccountMeta(domain.epoch, False, True),
            AccountMeta(domain.debouncer, False, True),
            AccountMeta(domain.destination, False, True),
            AccountMeta(domain.mint, False, True),
            AccountMeta(TOKEN, False, False),
            AccountMeta(self.outsider.pubkey(), True, True),
            AccountMeta(ATA, False, False),
            AccountMeta(SYSTEM, False, False),
            AccountMeta(self.event, False, False),
            AccountMeta(RELAY, False, False),
        ]
        return Instruction(RELAY, data, metas), {distribution, vault}

    def decode(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        domains = {}
        for name, domain in self.domains.items():
            epoch = account_data(snapshot.get(str(domain.epoch)))
            debouncer = account_data(snapshot.get(str(domain.debouncer)))
            domains[name] = {
                "epoch": None if len(epoch) < 90 else int.from_bytes(epoch[74:90], "little"),
                "epoch_state": None if len(epoch) < 10 else epoch[9],
                "debouncer_total": None if len(debouncer) < 82 else int.from_bytes(debouncer[74:82], "little"),
                "debouncer_state": None if len(debouncer) < 10 else debouncer[9],
                "destination_tokens": token_amount(snapshot.get(str(domain.destination))),
            }
        sources = {
            donor_name: {
                mint_name: token_amount(snapshot.get(str(source)))
                for mint_name, source in donor.sources.items()
            }
            for donor_name, donor in self.donors.items()
        }
        lamports = {
            "fee": snapshot[str(self.fee.pubkey())]["lamports"],
            **{name: snapshot[str(donor.keypair.pubkey())]["lamports"] for name, donor in self.donors.items()},
        }
        return {"domains": domains, "sources": sources, "lamports": lamports}


def unique_keypairs(values: Iterable[Keypair]) -> list[Keypair]:
    result: dict[str, Keypair] = {}
    for value in values:
        result[str(value.pubkey())] = value
    return list(result.values())
