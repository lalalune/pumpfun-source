"""Offline signer-boundary replay for Pump SetMayhemVirtualParams.

Optional --capture performs one read-only getMultipleAccounts request. The normal
mode uses the saved public account snapshot and sends only to an in-process
LiteSVM with a captured Pump ELF. No PDA signature is fabricated.
"""

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction


ROOT = Path(__file__).resolve().parents[1]


def check(condition, message):
    """Fail closed under optimized Python, where assert statements vanish."""
    if not condition:
        raise AssertionError(message)
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
MAYHEM = Pubkey.from_string("MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e")
TOKEN_2022 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
MINT = Pubkey.from_string("DKsuJCZ3d3mLcNR3vPCb83qhDzS1YxR6XMvd8GWmpump")
SELECTOR = bytes.fromhex("3da9bcbf99952a61")
TARGET_SHA256 = "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
SOL_VAULT, BUMP = Pubkey.find_program_address([b"sol-vault"], MAYHEM)
ACCOUNTS = [
    SOL_VAULT,
    Pubkey.find_program_address([bytes(SOL_VAULT), bytes(TOKEN_2022), bytes(MINT)], ATA)[0],
    MINT,
    Pubkey.find_program_address([b"global"], PUMP)[0],
    Pubkey.find_program_address([b"bonding-curve", bytes(MINT)], PUMP)[0],
    TOKEN_2022,
    Pubkey.find_program_address([b"__event_authority"], PUMP)[0],
    PUMP,
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def capture(path, rpc):
    request = {
        "jsonrpc": "2.0", "id": 1, "method": "getMultipleAccounts",
        "params": [[str(key) for key in ACCOUNTS],
                   {"encoding": "base64", "commitment": "finalized"}],
    }
    response = json.load(urlopen(Request(
        rpc, data=json.dumps(request).encode(),
        headers={"Content-Type": "application/json"}), timeout=20))
    if "error" in response:
        raise RuntimeError(response["error"])
    value = response["result"]
    if any(account is None for account in value["value"]):
        raise AssertionError("The selected public account set is incomplete")
    fixture = {
        "rpc": rpc, "method": "getMultipleAccounts", "commitment": "finalized",
        "context_slot": value["context"]["slot"], "mint": str(MINT),
        "accounts": [dict(address=str(key), **account)
                     for key, account in zip(ACCOUNTS, value["value"])],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as out:
        with gzip.GzipFile(fileobj=out, mode="wb", filename="", mtime=0) as zipped:
            zipped.write((json.dumps(fixture, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return fixture


def account_state(account):
    return (account.lamports, bytes(account.data), account.owner,
            account.executable, account.rent_epoch)


def verify_traces(path):
    records = json.loads(gzip.decompress(path.read_bytes()))
    check(len(records) == 2, "signer-boundary verification failed: len(records) == 2")
    summary = []
    for record in records:
        transaction = record["transaction"]
        signed = base64.b64decode(record["signed_transaction_base64"], validate=True)
        check(digest(signed) == record["signed_transaction_sha256"], "signer-boundary verification failed: digest(signed) == record['signed_transaction_sha256']")
        decoded = VersionedTransaction.from_bytes(signed)
        check(all(decoded.verify_with_results()), "signer-boundary verification failed: all(decoded.verify_with_results())")
        check(str(decoded.signatures[0]) == record["signature"], "signer-boundary verification failed: str(decoded.signatures[0]) == record['signature']")
        check(transaction["transaction"]["signatures"][0] == record["signature"], "signer-boundary verification failed: transaction['transaction']['signatures'][0] == record['signature']")
        check(transaction["meta"]["err"] is None, "signer-boundary verification failed: transaction['meta']['err'] is None")
        logs = transaction["meta"]["logMessages"]
        check(any("Instruction: CreateV2" in line for line in logs), "signer-boundary verification failed: any('Instruction: CreateV2' in line for line in logs)")
        positions = [i for i, line in enumerate(logs)
                     if line == "Program log: Instruction: InitializeMayhemState"]
        check(len(positions) == 1, "signer-boundary verification failed: len(positions) == 1")
        check(logs[positions[0] - 1] == f"Program {MAYHEM} invoke [2]", "signer-boundary verification failed: logs[positions[0] - 1] == f'Program {MAYHEM} invoke [2]'")
        check(not any("Instruction: SetMayhemVirtualParams" in line for line in logs), "signer-boundary verification failed: not any('Instruction: SetMayhemVirtualParams' in line for line in logs")
        summary.append({"signature": record["signature"], "slot": transaction["slot"],
                        "signed_transaction_sha256": digest(signed),
                        "all_transaction_signatures_valid": True,
                        "successful_mayhem_initializer_cpi": True,
                        "set_mayhem_virtual_params_cpi_in_trace": False})
    return summary


def replay(fixture_path, trace_path, target, output):
    check(digest(target.read_bytes()) == TARGET_SHA256, "signer-boundary verification failed: digest(target.read_bytes()) == TARGET_SHA256")
    fixture = json.loads(gzip.decompress(fixture_path.read_bytes()))
    check(fixture["mint"] == str(MINT), "signer-boundary verification failed: fixture['mint'] == str(MINT)")
    check([item["address"] for item in fixture["accounts"]] == [str(key) for key in ACCOUNTS], "signer-boundary verification failed: [item['address'] for item in fixture['accounts']] == [str(key) for key")
    check(not SOL_VAULT.is_on_curve() and BUMP == 253, "signer-boundary verification failed: not SOL_VAULT.is_on_curve() and BUMP == 253")
    mainnet_traces = verify_traces(trace_path)
    vm = LiteSVM().with_sigverify(True).with_blockhash_check(True)
    vm.add_program_from_file(PUMP, str(target))
    payer = Keypair.from_seed(bytes([212]) * 32)
    vm.airdrop(payer.pubkey(), 10**9)
    account_hashes = []
    for index, (key, item) in enumerate(zip(ACCOUNTS, fixture["accounts"])):
        raw = base64.b64decode(item["data"][0], validate=True)
        check(len(raw) == item["space"], "signer-boundary verification failed: len(raw) == item['space']")
        account_hashes.append({"address": str(key), "data_sha256": digest(raw),
                               "owner": item["owner"], "lamports": item["lamports"]})
        if index != 7:  # add_program_from_file installed the captured Pump ELF.
            vm.set_account(key, Account(item["lamports"], raw,
                                        Pubkey.from_string(item["owner"]),
                                        item["executable"], item["rentEpoch"]))
    before = [account_state(vm.get_account(key)) for key in ACCOUNTS[:7]]
    metas = [AccountMeta(key, False, index in (0, 1, 4))
             for index, key in enumerate(ACCOUNTS)]
    instruction = Instruction(PUMP, SELECTOR, metas)
    message = Message.new_with_blockhash([instruction], payer.pubkey(), vm.latest_blockhash())
    transaction = VersionedTransaction(message, [payer])
    check(all(transaction.verify_with_results()), "signer-boundary verification failed: all(transaction.verify_with_results())")
    result = vm.send_transaction(transaction)
    check(hasattr(result, "err"), "signer-boundary verification failed: hasattr(result, 'err')")
    error = str(result.err())
    logs = result.meta().logs()
    check("InstructionErrorCustom(2002)" in error, "signer-boundary verification failed: 'InstructionErrorCustom(2002)' in error")
    check(any("account: sol_vault_authority" in line and
               "Error Code: ConstraintSigner" in line for line in logs), "signer-boundary verification failed: any('account: sol_vault_authority' in line and")
    check(before == [account_state(vm.get_account(key)) for key in ACCOUNTS[:7]], "signer-boundary verification failed: before == [account_state(vm.get_account(key)) for key in ACCOUNTS[:7]]")
    report = {
        "scope": "Normally signed, offline target-only signer-boundary replay",
        "target_sha256": TARGET_SHA256,
        "snapshot_sha256": digest(fixture_path.read_bytes()),
        "mainnet_trace_archive_sha256": digest(trace_path.read_bytes()),
        "mainnet_creation_traces": mainnet_traces,
        "snapshot_context_slot": fixture["context_slot"],
        "mint": str(MINT), "sol_vault_pda": str(SOL_VAULT),
        "sol_vault_bump": BUMP, "sol_vault_on_curve": False,
        "selector_hex": SELECTOR.hex(),
        "outer_sol_vault_signer": False,
        "normal_transaction_signatures_valid": True,
        "error": error,
        "relevant_logs": [line for line in logs if "Instruction:" in line or
                          "AnchorError" in line or "failed" in line],
        "watched_accounts_unchanged": True,
        "account_snapshot_hashes": account_hashes,
        "qualification": "The public typed accounts reach the target signer check. "
        "This rejects a direct outer transaction, not a genuine Mayhem "
        "invoke_signed CPI. No positive route, reserve mutation, broadcast, "
        "or fund movement is established.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"error": error, "slot": fixture["context_slot"],
                      "watched_accounts_unchanged": True}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path,
                        default=ROOT / "evidence/original/pump/deployed.so")
    parser.add_argument("--fixture", type=Path,
                        default=ROOT / "repro/pump/mayhem-signer-boundary/account-snapshot.json.gz")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "repro/pump/mayhem-signer-boundary/signer-boundary.json")
    parser.add_argument("--traces", type=Path,
                        default=ROOT / "repro/pump/mayhem-signer-boundary/mainnet-createv2-traces.json.gz")
    parser.add_argument("--capture", action="store_true",
                        help="Refresh public account data via read-only mainnet RPC")
    parser.add_argument("--rpc", default="https://api.mainnet-beta.solana.com")
    args = parser.parse_args()
    if args.capture:
        capture(args.fixture, args.rpc)
    replay(args.fixture, args.traces, args.target, args.output)


if __name__ == "__main__":
    main()
