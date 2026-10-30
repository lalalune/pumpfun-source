#!/usr/bin/env python3
"""Run Mayhem dispatcher/decode/first-account differentials in fresh LiteSVMs."""

import argparse
import gzip
import hashlib
import io
import json
import pathlib
import re
import sys

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import inventory  # noqa: E402


PAYER = Keypair.from_seed(bytes([237]) * 32)
PAYER_LAMPORTS = 10**12
MAYHEM = Pubkey.from_string(inventory.PROGRAM_ID)
SYSTEM = Pubkey.default()
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
AMM = Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
WSOL = Pubkey.from_string("So11111111111111111111111111111111111111112")
BEHAVIOR = ("tx_sha256", "instruction_sha256", "error", "return_data", "events",
            "inner_instructions", "payer_lamports", "accounts")


def key(label):
    return Pubkey.from_bytes(hashlib.sha256(("mayhem-dispatch:" + label).encode()).digest())


def pda(seed, owner=MAYHEM):
    return Pubkey.find_program_address(seed, owner)[0]


def resolve_accounts(row):
    """Resolve source-order keys without claiming a fully initialized fixture."""
    mint = key(row["name"] + ":mint")
    quote = key(row["name"] + ":quote-mint")
    out = []
    for i, name in enumerate(row["accounts"]):
        fixed = {
            "system_program": SYSTEM,
            "associated_token_program": ATA,
            "pump_program": PUMP,
            "pump_swap_program": AMM,
            "program": MAYHEM,
            "wsol_mint": WSOL,
            "mint": mint,
            "quote_mint": quote,
            "global_params": pda([b"global-params"]),
            "sol_vault": pda([b"sol-vault"]),
            "event_authority": pda([b"__event_authority"]),
            "mayhem_state": pda([b"mayhem-state", bytes(mint)]),
            "pool_v2": pda([b"pool-v2", bytes(mint)]),
            "bonding_curve_v2": pda([b"bonding-curve-v2", bytes(mint)]),
            "bonding_curve": pda([b"bonding-curve", bytes(mint)], PUMP),
        }
        if name == "token_program":
            fixed[name] = TOKEN if row["name"] in ("sweep_fees", "sweep_fees_admin", "initialize_fee_recipient") else TOKEN22
        if name in ("quote_token_program",):
            fixed[name] = TOKEN
        if name in ("base_token_program",):
            fixed[name] = TOKEN22
        k = fixed.get(name, key(f"{row['name']}:{i}:{name}"))
        signer = i in row["signer"]
        # Only a controlled local key may sign. The captured PDA signer boundary is
        # exercised as an unsigned account, never by disabling signature checks.
        if signer and name in ("payer", "admin", "trader", "user"):
            k = PAYER.pubkey()
        else:
            signer = False
        out.append({"name": name, "key": str(k), "signer": signer, "writable": i in row["writable"]})
    return out


def account_shapes(row, data):
    base = resolve_accounts(row)
    shapes = []

    def add(label, accounts, setup=()):
        shapes.append({"label": label, "data": data.hex(), "accounts": accounts, "setup": list(setup)})

    add("one-account-short", base[:-1])
    add("source-order-unfunded", base)
    add("source-order-extra-account", base + [{"name": "extra", "key": str(key(row["name"] + ":extra")), "signer": False, "writable": False}])
    add("duplicate-payer-every-slot", [dict(a, key=str(PAYER.pubkey()), signer=True, writable=True) for a in base])

    if row["signer"]:
        i = row["signer"][0]
        changed = [dict(a) for a in base]
        changed[i] = dict(changed[i], key=str(key(row["name"] + ":unsigned")), signer=False)
        add("missing-first-required-signer", changed)
    mutable = next((i for i in row["writable"] if i not in row["signer"]), None)
    if mutable is not None:
        changed = [dict(a) for a in base]
        changed[mutable] = dict(changed[mutable], writable=False)
        add("first-required-writable-readonly", changed)

    typed_names = {"global_params", "mayhem_state", "bonding_curve", "pool", "global_config", "fee_recipient"}
    typed = next((i for i, a in enumerate(base) if a["name"] in typed_names), None)
    if typed is not None:
        setup = ({"key": base[typed]["key"], "lamports": 10**8, "owner": str(SYSTEM), "data": "00" * 256},)
        add("first-typed-account-wrong-owner", base, setup)
        setup = ({"key": base[typed]["key"], "lamports": 10**8, "owner": str(MAYHEM), "data": "00" * 256},)
        add("first-typed-account-wrong-discriminator", base, setup)

    derived_names = {"global_params", "mayhem_state", "sol_vault", "event_authority", "pool_v2", "bonding_curve", "bonding_curve_v2", "fee_recipient"}
    derived = next((i for i, a in enumerate(base) if a["name"] in derived_names), None)
    if derived is not None:
        changed = [dict(a) for a in base]
        changed[derived] = dict(changed[derived], key=str(key(row["name"] + ":wrong-pda")))
        add("first-derived-account-wrong-pda", changed)

    program_names = {"system_program", "token_program", "quote_token_program", "base_token_program",
                     "associated_token_program", "pump_program", "pump_swap_program", "program"}
    fixed = next((i for i, a in enumerate(base) if a["name"] in program_names), None)
    if fixed is not None:
        changed = [dict(a) for a in base]
        changed[fixed] = dict(changed[fixed], key=str(key(row["name"] + ":wrong-program")))
        add("first-fixed-program-wrong-id", changed)
    return shapes


def make_plan():
    rows = []

    def raw(label, data, accounts=()):
        return {"label": label, "data": data.hex(), "accounts": list(accounts), "setup": []}

    first = bytes.fromhex(inventory.INSTRUCTIONS[0]["discriminator"])
    ev = str(pda([b"__event_authority"]))
    dispatch = [
        raw("empty-data", b""), raw("one-byte-prefix", first[:1]), raw("four-byte-prefix", first[:4]),
        raw("seven-byte-prefix", first[:7]), raw("unknown-zero", bytes(8)), raw("unknown-ff", bytes([255]) * 8),
        raw("unknown-random", hashlib.sha256(b"unattributed-mayhem-selector").digest()[:8]),
        raw("event-cpi-no-accounts", inventory.EVENT_CPI_TAG),
        raw("event-cpi-seven-byte-prefix", inventory.EVENT_CPI_TAG[:7]),
        raw("event-cpi-unsigned-authority", inventory.EVENT_CPI_TAG,
            ({"name": "event_authority", "key": ev, "signer": False, "writable": False},)),
        raw("event-cpi-wrong-signer", inventory.EVENT_CPI_TAG,
            ({"name": "event_authority", "key": str(PAYER.pubkey()), "signer": True, "writable": True},)),
        raw("idl-no-accounts", inventory.IDL_TAG), raw("idl-seven-byte-prefix", inventory.IDL_TAG[:7]),
        raw("idl-create-payload", inventory.IDL_TAG + b"\x00" + (64).to_bytes(8, "little"),
            ({"name": "payer", "key": str(PAYER.pubkey()), "signer": True, "writable": True},)),
    ]
    rows.append({"name": "dispatcher", "steps": dispatch})

    for row in inventory.INSTRUCTIONS:
        disc = bytes.fromhex(row["discriminator"])
        variants = [raw("recognized-disc-only", disc)]
        variants.extend(raw(label, disc + args) for label, args in inventory.argument_variants(row["args"]))
        variants.extend(account_shapes(row, disc + inventory.default_args(row["args"])))
        rows.append({"name": row["name"], "discriminator": row["discriminator"],
                     "argument_contract": row["args"], "account_order": list(row["accounts"]), "steps": variants})
    return {
        "schema": 1,
        "program_id": inventory.PROGRAM_ID,
        "payer_seed_byte": 237,
        "payer_lamports": PAYER_LAMPORTS,
        "inventory_basis": "captured evidence/dispatch-map.json selectors plus maintained Rust argument/account contracts",
        "not_applicable_argument_families": ["bool", "enum", "vector"],
        "cases": rows,
    }


def make_vm(image):
    vm = LiteSVM().with_log_bytes_limit(None).with_transaction_history(0)
    vm.add_program_from_file(MAYHEM, str(image))
    vm.airdrop(PAYER.pubkey(), PAYER_LAMPORTS)
    return vm


def execute(image, step):
    vm = make_vm(image)
    for spec in step.get("setup", ()):
        vm.set_account(Pubkey.from_string(spec["key"]), Account(spec["lamports"], bytes.fromhex(spec["data"]), Pubkey.from_string(spec["owner"])))
    metas = [AccountMeta(Pubkey.from_string(a["key"]), a["signer"], a["writable"]) for a in step["accounts"]]
    data = bytes.fromhex(step["data"])
    ix = Instruction(MAYHEM, data, metas)
    bh = vm.latest_blockhash()
    tx = Transaction.new_signed_with_payer([ix], PAYER.pubkey(), [PAYER], bh)
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    ret = meta.return_data()
    logs = list(meta.logs())
    # The executable program account necessarily contains different ELF bytes.
    # It is an input identity, recorded by SHA-256 in provenance, not mutable
    # transaction state and therefore is not a watched account.
    watched = sorted(({a["key"] for a in step["accounts"]} - {str(MAYHEM)}) | {str(PAYER.pubkey())})
    state = []
    for address in watched:
        account = vm.get_account(Pubkey.from_string(address))
        state.append(None if account is None else {
            "address": address, "lamports": account.lamports, "owner": str(account.owner),
            "data_sha256": hashlib.sha256(bytes(account.data)).hexdigest(), "data_bytes": len(account.data),
        })
    return {
        "tx_sha256": hashlib.sha256(bytes(tx)).hexdigest(),
        "instruction_sha256": hashlib.sha256(bytes(ix)).hexdigest(),
        "error": str(result.err()) if failed else None,
        "return_data": None if ret is None or not bytes(ret.data) else bytes(ret.data).hex(),
        "events": [line for line in logs if line.startswith("Program data:")],
        "inner_instructions": json.loads(meta.to_json()).get("inner_instructions"),
        "payer_lamports": vm.get_account(PAYER.pubkey()).lamports,
        "accounts": state,
        "logs": logs,
        "compute_units": meta.compute_units_consumed(),
    }


def run(plan, images):
    receipts = []
    for case in plan["cases"]:
        for step in case["steps"]:
            receipt = {"case": case["name"], "label": step["label"], "data": step["data"]}
            for side in ("original", "candidate"):
                receipt[side] = execute(images[side], step)
            receipts.append(receipt)
    return receipts


PATH_SITE = re.compile(r"AnchorError thrown in ([^ ]+):(\d+)\.")


def normalize_site(line):
    return PATH_SITE.sub("AnchorError thrown in <source-path>:<line>.", line)


def error_code(error):
    if error is None:
        return "ok"
    match = re.search(r"Custom\((\d+)\)", error)
    if match:
        return match.group(1)
    match = re.search(r"InstructionError\(\s*\d+,\s*([A-Za-z]+)", error)
    return match.group(1) if match else error


def build_report(plan, receipts, provenance):
    behavior, log_diffs, cu_diffs, path_only = [], [], [], []
    outcomes, blamed = {}, {}
    for row in receipts:
        original, candidate = row["original"], row["candidate"]
        fields = [field for field in BEHAVIOR if original[field] != candidate[field]]
        if fields:
            behavior.append({"case": row["case"], "label": row["label"], "fields": fields})
        if original["logs"] != candidate["logs"]:
            entry = {"case": row["case"], "label": row["label"],
                     "original": original["logs"], "candidate": candidate["logs"]}
            log_diffs.append(entry)
            if list(map(normalize_site, original["logs"])) == list(map(normalize_site, candidate["logs"])):
                path_only.append({"case": row["case"], "label": row["label"]})
        delta = candidate["compute_units"] - original["compute_units"]
        if delta:
            cu_diffs.append({"case": row["case"], "label": row["label"], "delta": delta,
                             "original": original["compute_units"], "candidate": candidate["compute_units"]})
        outcomes.setdefault(row["case"], {})[row["label"]] = error_code(original["error"])
        for line in original["logs"]:
            match = re.search(r"caused by account: ([A-Za-z0-9_]+)\. Error Code: ([A-Za-z0-9_]+)", line)
            if match:
                blamed.setdefault(row["case"], {})[row["label"]] = ":".join(match.groups())
                break
    # Negative controls exercise the comparator itself without executing altered programs.
    sample = receipts[0]["original"]
    changed_error = dict(sample, error="negative-control-error")
    changed_state = dict(sample, accounts=[{"negative": True}])
    negative = {
        "changed_error_detected": [f for f in BEHAVIOR if sample[f] != changed_error[f]] == ["error"],
        "changed_state_detected": [f for f in BEHAVIOR if sample[f] != changed_state[f]] == ["accounts"],
    }
    return {
        "schema": 1,
        "program": "mayhem",
        "program_id": plan["program_id"],
        "confirmed_instruction_count": len(plan["cases"]) - 1,
        "cases": len(plan["cases"]),
        "paired_steps": len(receipts),
        "executions": len(receipts) * 2,
        "behavior_fields": list(BEHAVIOR),
        "behavior_mismatch_steps": behavior,
        "log_mismatch_steps": log_diffs,
        "source_path_only_log_mismatch_steps": path_only,
        "compute_unit_mismatch_steps": cu_diffs,
        "outcomes": outcomes,
        "first_blamed_accounts": blamed,
        "negative_controls": negative,
        "unsupported": {
            "argument_decoders": plan["not_applicable_argument_families"],
            "reason": "No confirmed maintained Mayhem instruction has a bool, enum, or vector argument.",
            "event_cpi_success": "Not attempted: the event-authority PDA cannot legitimately sign an outer transaction.",
            "initialized_handler_success": "Out of scope: this package stops at dispatcher, decoding, and first account admission.",
        },
        "provenance": provenance,
    }


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def gzip_bytes(data):
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", filename="", mtime=0) as stream:
        stream.write(data)
    return out.getvalue()


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def tree_hash(root):
    root = pathlib.Path(root)
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = str(path.relative_to(root)).encode()
        digest.update(len(rel).to_bytes(4, "little") + rel)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "little") + data)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=pathlib.Path)
    parser.add_argument("--images", required=True, help='JSON object with "original" and "candidate" paths')
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    images = {name: pathlib.Path(path) for name, path in json.loads(args.images).items()}
    plan = make_plan()
    provenance = {
        "original_path": str(images["original"]), "original_sha256": sha256(images["original"]),
        "candidate_path": str(images["candidate"]), "candidate_sha256": sha256(images["candidate"]),
        "mayhem_source_tree_sha256": tree_hash(args.root / "programs/mayhem"),
        "dispatch_map_sha256": sha256(args.root / "evidence/dispatch-map.json"),
        "producer_sha256": sha256(pathlib.Path(__file__)),
        "python": sys.version,
    }
    receipts = run(plan, images)
    report = build_report(plan, receipts, provenance)
    runtime = args.out / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "plan.json.gz").write_bytes(gzip_bytes(canonical(plan).encode()))
    (runtime / "receipts.jsonl.gz").write_bytes(gzip_bytes("".join(canonical(row) + "\n" for row in receipts).encode()))
    (runtime / "report.json.gz").write_bytes(gzip_bytes(json.dumps(report, sort_keys=True, indent=1).encode()))
    print(json.dumps({
        "instructions": report["confirmed_instruction_count"], "steps": report["paired_steps"],
        "behavior_mismatches": len(report["behavior_mismatch_steps"]),
        "log_mismatches": len(report["log_mismatch_steps"]),
        "cu_mismatches": len(report["compute_unit_mismatch_steps"]),
        "negative_controls": report["negative_controls"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
