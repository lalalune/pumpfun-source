#!/usr/bin/env python3
"""Signed Surfpool reproductions of five Fees findings on the original ELF."""
from __future__ import annotations

import base64
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))

from solders.account import Account
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.transaction import Transaction

import fees_admin_differential as admin
import fees_config_differential as config
import fees_donation_create_differential as create
import fees_donation_crank_probe as crank
import fees_extend_differential as extend
import fees_social_claim_v2_differential as social
from surfpool_rpc import Surfpool, RecordingVM, dependency, original, install_fixture, resign

OUT = HERE / "results"
FEES = original("pump_fees")
TOKEN = crank.TOKEN
TOKEN22 = social.TOKEN22
ATA = crank.ATA
USDC = social.USDC
P = admin.PROGRAM
PAYER = admin.PAYER
AUTH = admin.AUTH
OTHER = admin.OTHER


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def disc(name: str) -> bytes:
    return bytes(next(x["discriminator"] for x in admin.IDL["instructions"]
                      if x["name"] == name))


def account_rows(pool: Surfpool, addresses: dict[str, Pubkey]) -> dict:
    return {name: pool.get_account(key) for name, key in addresses.items()}


def send(pool: Surfpool, label: str, tx: Transaction, signers, addresses: dict[str, Pubkey]):
    tx = resign(tx, PAYER.pubkey(), signers, pool.latest_blockhash())
    before = account_rows(pool, addresses)
    result = pool.send(tx)
    result.update(label=label, before=before, after=account_rows(pool, addresses),
                  transaction_base64=base64.b64encode(bytes(tx)).decode())
    return result


def replay_fixture(pool: Surfpool, module, case: dict, signers, label: str,
                   addresses: dict[str, Pubkey], setup=None):
    recorded = []
    original_type = module.LiteSVM
    admin_original_type = admin.LiteSVM

    def factory():
        vm = RecordingVM()
        recorded.append(vm)
        return vm

    module.LiteSVM = factory
    admin.LiteSVM = factory
    try:
        fixture_type = (extend.ExtendFixture if module is extend else
                        create.Fixture if module is create else None)
        lite = fixture_type(FEES).run(case) if fixture_type else module.run(case)
        vm = recorded[0]
        if setup:
            setup(vm)
    finally:
        module.LiteSVM = original_type
        admin.LiteSVM = admin_original_type
    install_fixture(pool, vm)
    result = send(pool, label, vm.transaction, signers, addresses)
    result["litesvm_error"] = lite["error"]
    return result


def fees_fixture(pool: Surfpool):
    pool.load_program(P, FEES)
    pool.set_account(admin.GLOBAL, Account(10**9, admin.BASE, P))
    pool.set_account(config.CONFIG_PROGRAM, Account(10**9, b"", Pubkey.default()))
    for kp in (PAYER, AUTH, OTHER):
        pool.set_account(kp.pubkey(), Account(10**12, b"", Pubkey.default()))


def config_state(normal, stable, allocation=2512):
    return Account(10**9, config.encode(normal, stable).ljust(allocation, b"\0"), P)


def query_tx(name: str, payload: bytes):
    return Transaction.new_signed_with_payer([
        Instruction(P, disc(name) + payload, [
            AccountMeta(config.CONFIG, False, False),
            AccountMeta(config.CONFIG_PROGRAM, False, False),
        ])], PAYER.pubkey(), [PAYER], admin.Hash.default() if hasattr(admin, "Hash") else __import__("solders.hash", fromlist=["Hash"]).Hash.default())


def test_l07():
    rows = []
    with Surfpool(OUT / "fees-l07", binary=HERE / "tools/surfpool") as pool:
        fees_fixture(pool)
        pool.set_account(config.CONFIG, config_state([], []))
        addresses = {"fee_config": config.CONFIG}
        rows.append(send(pool, "fresh-empty-get-fees", query_tx(
            "get_fees", b"\1" + bytes(16) + struct.pack("<Q", 1000) + b"\0"),
            [PAYER], addresses))
        rows.append(send(pool, "legacy-empty-stable-get-fees-with-quote-mint", query_tx(
            "get_fees_with_quote_mint", b"\1" + bytes(16) + bytes(USDC)),
            [PAYER], addresses))
        loaded = pool.loaded_programs
    confirmed = all(r["error"] is not None and any("index out of bounds" in x for x in r["logs"])
                    for r in rows)
    return {"status": "CONFIRMED" if confirmed else "INCONCLUSIVE", "loaded_programs": loaded,
            "observation": "Both public query paths reverted with an index-out-of-bounds panic on empty tiers."
            if confirmed else "Expected empty-tier panic was not observed on both paths.", "transactions": rows}


def authority_tx(instruction: str, authority, arg: bytes):
    metas = [AccountMeta(authority.pubkey(), True, True),
             AccountMeta(admin.GLOBAL, False, True),
             AccountMeta(admin.EVENT, False, False), AccountMeta(P, False, False)]
    return Transaction.new_signed_with_payer([Instruction(P, disc(instruction) + arg, metas)],
        PAYER.pubkey(), [PAYER, authority], __import__("solders.hash", fromlist=["Hash"]).Hash.default())


def test_l08():
    rows = []
    with Surfpool(OUT / "fees-l08", binary=HERE / "tools/surfpool") as pool:
        fees_fixture(pool)
        addresses = {"fee_program_global": admin.GLOBAL, "old_authority": AUTH.pubkey(),
                     "new_authority": OTHER.pubkey()}
        rows.append(send(pool, "old-authority-rotates-without-new-signature",
                         authority_tx("set_authority", AUTH, bytes(OTHER.pubkey())), [PAYER, AUTH], addresses))
        rows.append(send(pool, "old-authority-rejected-after-rotation",
                         authority_tx("set_disable_flags", AUTH, b"\0"), [PAYER, AUTH], addresses))
        rows.append(send(pool, "new-authority-can-administer",
                         authority_tx("set_disable_flags", OTHER, b"\0"), [PAYER, OTHER], addresses))
        loaded = pool.loaded_programs
    confirmed = (rows[0]["error"] is None and rows[1]["error"] is not None and rows[2]["error"] is None
                 and rows[0]["after"]["fee_program_global"]["data"][18:82] == bytes(OTHER.pubkey()).hex())
    return {"status": "CONFIRMED" if confirmed else "INCONCLUSIVE", "loaded_programs": loaded,
            "observation": "One old-admin signature transferred authority; the old admin was then rejected and the new admin accepted."
            if confirmed else "The expected rotation and subsequent authority results were not observed.", "transactions": rows}


def stable_update_tx(tiers):
    metas = [AccountMeta(config.CONFIG, False, True), AccountMeta(AUTH.pubkey(), True, False),
             AccountMeta(config.CONFIG_PROGRAM, False, False), AccountMeta(admin.EVENT, False, False),
             AccountMeta(P, False, False)]
    return Transaction.new_signed_with_payer([Instruction(P, disc("update_stable_fee_config") + config.tiers(tiers), metas)],
        PAYER.pubkey(), [PAYER, AUTH], __import__("solders.hash", fromlist=["Hash"]).Hash.default())


def test_m07():
    rows = []
    with Surfpool(OUT / "fees-m07", binary=HERE / "tools/surfpool") as pool:
        fees_fixture(pool)
        pool.set_account(config.CONFIG, config_state([(0, (1, 2, 3))], []))
        addresses = {"fee_config": config.CONFIG}
        rows.append(send(pool, "legacy-sized-stable-update",
                         stable_update_tx([(0, (7, 8, 9))]), [PAYER, AUTH], addresses))
        rows.append(send(pool, "reload-query-after-successful-stable-update", query_tx(
            "get_fees_with_quote_mint", b"\1" + bytes(16) + bytes(USDC)), [PAYER], addresses))
        loaded = pool.loaded_programs
    changed = rows[0]["before"]["fee_config"]["data"] != rows[0]["after"]["fee_config"]["data"]
    confirmed = (rows[0]["error"] is None and changed and rows[1]["error"] is not None
                 and any("index out of bounds" in x for x in rows[1]["logs"]))
    return {"status": "CONFIRMED" if confirmed else "INCONCLUSIVE", "loaded_programs": loaded,
            "observation": "The legacy-sized stable update committed bytes and returned success, but reload/query still saw no stable tiers and panicked."
            if confirmed else "Successful update followed by empty stable decode was not established.", "transactions": rows}


def test_l15():
    rows = []
    with Surfpool(OUT / "fees-l15-extend", binary=HERE / "tools/surfpool") as pool:
        pool.load_program(P, FEES)
        addresses = {"fee_config": config.CONFIG, "funding_user": AUTH.pubkey(),
                     "distinct_transaction_payer": PAYER.pubkey()}
        row = replay_fixture(pool, extend, {"name": "legacy-readonly-user", "allocation": 2512},
                             [PAYER, AUTH], "readonly-user-funds-extend", addresses)
        rows.append(row)
        extend_loaded = pool.loaded_programs
    with Surfpool(OUT / "fees-l15-social", binary=HERE / "tools/surfpool") as pool:
        pool.load_program(P, FEES)
        pool.load_program(TOKEN, dependency("spl_token"))
        pool.load_program(ATA, dependency("associated_token"))
        case = {"name": "readonly-authority-creates-recipient-ata", "quote": str(USDC),
                "destination_exists": False}
        source_social = Pubkey.find_program_address([b"social-fee-pda", b"12345", b"\0"], P)[0]
        destination = Pubkey.find_program_address([bytes(OTHER.pubkey()), bytes(TOKEN), bytes(USDC)], ATA)[0]
        addresses = {"social_fee_pda": source_social, "associated_recipient": destination,
                     "funding_authority": AUTH.pubkey(), "distinct_transaction_payer": PAYER.pubkey()}
        row = replay_fixture(pool, social, case, [PAYER, AUTH], "readonly-authority-funds-recipient-ata", addresses)
        rows.append(row)
        social_loaded = pool.loaded_programs
    extend_ok = (rows[0]["error"] is None and rows[0]["after"]["funding_user"]["lamports"]
                 < rows[0]["before"]["funding_user"]["lamports"])
    social_ok = (rows[1]["error"] is not None
                 and any("writable privilege escalated" in line for line in rows[1]["logs"])
                 and (rows[1]["after"]["associated_recipient"] is None
                      or rows[1]["after"]["associated_recipient"]["lamports"] == 0))
    confirmed = extend_ok and social_ok
    return {"status": "CONFIRMED" if confirmed else "INCONCLUSIVE",
            "loaded_programs": {**extend_loaded, **social_loaded},
            "observation": "With a distinct transaction fee payer, readonly ExtendFeeConfig.user still funded resizing, but readonly social_claim_authority caused PrivilegeEscalation when creating the recipient ATA."
            if confirmed else "The two readonly funding branches did not produce the expected distinct outcomes.", "transactions": rows}


def test_m12():
    rows = []
    with Surfpool(OUT / "fees-m12", binary=HERE / "tools/surfpool") as pool:
        for key, name in [(P, None), (crank.RELAY, "donation_relay"), (TOKEN, "spl_token"),
                          (TOKEN22, "spl_token_2022"), (ATA, "associated_token")]:
            pool.load_program(key, FEES if name is None else dependency(name))

        def token22_quote(vm):
            md = bytearray(82)
            md[44] = 9
            md[45] = 1
            vm.set_account(create.QUOTE, Account(10**9, bytes(md), TOKEN22))

        addresses = {"donation_fee_pda": create.DONATION, "quote_mint": create.QUOTE,
                     "payer": AUTH.pubkey()}
        rows.append(replay_fixture(pool, create, {"name": "token2022-quote-create"},
                                   [PAYER, AUTH], "create-donation-with-token2022-quote", addresses,
                                   setup=token22_quote))
        whitelist = hashlib.sha256(b"account:MintWhitelistV1").digest()[:8] + bytes([crank.WB]) + bytes(4)
        pool.set_account(crank.WHITELIST, Account(10**9, whitelist, crank.RELAY))
        for key in (crank.RELAY_EVENT, crank.EPOCH, crank.DEBOUNCER, crank.D_ATA, crank.B_ATA):
            pool.set_account(key, Account(0, b"", Pubkey.default()))
        metas = [AccountMeta(crank.create.PAYER.pubkey() if False else {
            "event_authority": create.EVENT, "program": P, "payer": AUTH.pubkey(),
            "system_program": Pubkey.default(), "token_program": TOKEN,
            "associated_token_program": ATA, "rent": Pubkey.from_string("SysvarRent111111111111111111111111111111111"),
            "fee_program_global": create.GLOBAL, "donation_fee_pda": create.DONATION,
            "quote_mint": create.QUOTE, "donation_fee_pda_ata": crank.D_ATA,
            "donation_relay_program": crank.RELAY, "donation_relay_event_authority": crank.RELAY_EVENT,
            "mint_whitelist": crank.WHITELIST, "epoch_tracker": crank.EPOCH,
            "debouncer": crank.DEBOUNCER, "debouncer_ata": crank.B_ATA,
        }[entry["name"]], entry.get("signer", False), entry.get("writable", False))
                 for entry in crank.IX["accounts"]]
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000),
            Instruction(P, bytes(crank.IX["discriminator"]), metas)], PAYER.pubkey(), [PAYER, AUTH],
            __import__("solders.hash", fromlist=["Hash"]).Hash.default())
        crank_addresses = {"donation_fee_pda": create.DONATION, "quote_mint": create.QUOTE,
                           "donation_fee_pda_ata": crank.D_ATA, "epoch_tracker": crank.EPOCH,
                           "debouncer": crank.DEBOUNCER}
        rows.append(send(pool, "crank-token2022-quote-through-legacy-token-interface", tx,
                         [PAYER, AUTH], crank_addresses))
        loaded = pool.loaded_programs
    created = rows[0]["error"] is None and rows[0]["after"]["quote_mint"]["owner"] == str(TOKEN22)
    failed = rows[1]["error"] is not None
    confirmed = created and failed
    return {"status": "CONFIRMED" if confirmed else "INCONCLUSIVE", "loaded_programs": loaded,
            "observation": "Creation stored a Token-2022 quote mint, but the crank using the original legacy Token interface reverted before Relay settlement."
            if confirmed else "Token-2022 creation/crank incompatibility was not established.", "transactions": rows}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tests = {"L-07": test_l07, "L-08": test_l08, "L-15": test_l15,
             "M-07": test_m07, "M-12": test_m12}
    findings = {}
    for finding, test in tests.items():
        print(f"Running {finding}", flush=True)
        findings[finding] = test()
        print(f"{finding}: {findings[finding]['status']}", flush=True)
    report = {
        "scope": "Original deployed Fees ELF only, normally signed offline Surfpool transactions with original local dependencies; no off-chain data.",
        "surfpool_version": "1.6.1", "original_sha256": digest(FEES),
        "dependency_sha256": {name: digest(dependency(name)) for name in
                              ["donation_relay", "spl_token", "spl_token_2022", "associated_token"]},
        "findings": findings,
        "counts": {status: sum(v["status"] == status for v in findings.values())
                   for status in ["CONFIRMED", "BLOCKED", "INCONCLUSIVE"]},
    }
    (OUT / "fees.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["counts"]))


if __name__ == "__main__":
    main()
