#!/usr/bin/env python3
"""Pump Fees update_fee_shares compute units vs old shareholder count K and new count L (1..10 each), original vs rebuild.

One update_fee_shares transaction per point on a fresh LiteSVM per image; pump and pump_amm deployed images are CPI dependencies only.
Usage: producer.py --root <repo> --images <json> --out <dir>
"""
import argparse
import base64
import gzip
import hashlib
import json
import pathlib

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
AMM = Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA_PROG = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
WSOL = Pubkey.from_string("So11111111111111111111111111111111111111112")
SYSTEM = Pubkey.default()

AUTH = Keypair.from_seed(bytes([231]) * 32)
PAYER = Keypair.from_seed(bytes([232]) * 32)
MINT = Pubkey.from_bytes(bytes([73]) * 32)
SHARING, SHARING_BUMP = Pubkey.find_program_address([b"sharing-config", bytes(MINT)], PROGRAM)
CURVE = Pubkey.find_program_address([b"bonding-curve", bytes(MINT)], PUMP)[0]
PUMP_GLOBAL = Pubkey.find_program_address([b"global"], PUMP)[0]
PUMP_VAULT = Pubkey.find_program_address([b"creator-vault", bytes(SHARING)], PUMP)[0]
EVENT = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]
PUMP_EVENT = Pubkey.find_program_address([b"__event_authority"], PUMP)[0]
AMM_EVENT = Pubkey.find_program_address([b"__event_authority"], AMM)[0]
AMM_VAULT_AUTH = Pubkey.find_program_address([b"creator_vault", bytes(SHARING)], AMM)[0]
AMM_VAULT_ATA = Pubkey.find_program_address([bytes(AMM_VAULT_AUTH), bytes(TOKEN), bytes(WSOL)], ATA_PROG)[0]

# Non-executable shareholders: fixed byte-pattern keys that never sign.
HOLDERS = {n: Pubkey.from_bytes(bytes([110 + i]) * 32) for i, n in enumerate("ABCDEFGHIJ")}
# Executable shareholders: program accounts present in every world.
EXEC = {"X": TOKEN, "Y": ATA_PROG, "Z": SYSTEM, "P": PUMP, "M": AMM, "R": PROGRAM, "T": TOKEN22}
START = 1_700_000_000
GLOBAL_LEN = 740
STEP_FUND = 10_000_000


def disc(kind, name):
    return hashlib.sha256(f"{kind}:{name}".encode()).digest()[:8]


IX_UPDATE = disc("global", "update_fee_shares")
IX_DISTRIBUTE = disc("global", "distribute_creator_fees")
EV_UPDATE = disc("event", "UpdateFeeSharesEvent")
EV_DISTRIBUTE = disc("event", "DistributeCreatorFeesEvent")


def key_of(name):
    if name in HOLDERS:
        return HOLDERS[name]
    if name in EXEC:
        return EXEC[name]
    if name == "AUTH":
        return AUTH.pubkey()
    if name == "W":  # a fresh non-executable key that is not a shareholder
        return Pubkey.from_bytes(bytes([99]) * 32)
    raise KeyError(name)


def holders_bytes(holders):
    out = len(holders).to_bytes(4, "little")
    for name, bps in holders:
        out += bytes(key_of(name)) + bps.to_bytes(2, "little")
    return out


def sharing_bytes(holders, version=2):
    data = disc("account", "SharingConfig") + bytes([SHARING_BUMP, version, 1]) + bytes(MINT)
    data += bytes(AUTH.pubkey()) + bytes([0]) + holders_bytes(holders)
    return data + bytes(1024 - len(data))


def curve_bytes():
    """pump BondingCurve: non-zero reserves (no AMM CPI), not complete, creator = sharing config."""
    data = disc("account", "BondingCurve")
    for value in [1_000_000_000, 30_000_000_000, 800_000_000, 1_000_000, 1_000_000_000_000]:
        data += value.to_bytes(8, "little")
    data += bytes([0]) + bytes(SHARING) + bytes(2) + bytes(32)
    return data + bytes(200 - len(data))


def decode_holders(raw, o):
    n = int.from_bytes(raw[o:o + 4], "little")
    o += 4
    items = []
    for _ in range(n):
        items.append([name_of(Pubkey.from_bytes(raw[o:o + 32])), int.from_bytes(raw[o + 32:o + 34], "little")])
        o += 34
    return items, o


def name_of(key):
    for table in (HOLDERS, EXEC):
        for n, k in table.items():
            if k == key:
                return n
    if key == AUTH.pubkey():
        return "AUTH"
    if key == key_of("W"):
        return "W"
    return str(key)


def decode_sharing(d):
    if len(d) < 80:
        return None
    holders, end = decode_holders(d, 76)
    return {"version": d[9], "status": d[10], "admin_revoked": d[75], "holders": holders,
            "tail_nonzero": sum(1 for b in d[end:] if b)}


def decode_event(line):
    if not line.startswith("Program data: "):
        return None
    raw = base64.b64decode(line[len("Program data: "):])
    if raw[:8] == EV_UPDATE:
        holders, o = decode_holders(raw, 8 + 8 + 32 * 3)
        return {"event": "UpdateFeeSharesEvent", "new_shareholders": holders, "version": raw[o]}
    if raw[:8] == EV_DISTRIBUTE:
        holders, o = decode_holders(raw, 8 + 8 + 32 * 4)
        return {"event": "DistributeCreatorFeesEvent", "shareholders": holders,
                "distributed": int.from_bytes(raw[o:o + 8], "little")}
    return {"event": "unknown", "head": raw[:8].hex()}


class World:
    def __init__(self, fees_image, pump_image, amm_image, case):
        vm = LiteSVM()
        vm.set_clock(Clock(1000, START, 0, 0, START))
        vm.add_program_from_file(PROGRAM, fees_image)
        vm.add_program_from_file(PUMP, pump_image)
        vm.add_program_from_file(AMM, amm_image)
        self.vm = vm
        for kp in (AUTH, PAYER):
            vm.set_account(kp.pubkey(), Account(100_000_000_000, b"", SYSTEM))
        g = bytearray(GLOBAL_LEN)
        g[0:8] = disc("account", "Global")
        g[8] = 1
        vm.set_account(PUMP_GLOBAL, Account(10**9, bytes(g), PUMP))
        mint = bytearray(82)
        mint[44] = 6
        mint[45] = 1
        vm.set_account(MINT, Account(10**9, bytes(mint), TOKEN))
        wsol = bytearray(82)
        wsol[44] = 9
        wsol[45] = 1
        vm.set_account(WSOL, Account(10**9, bytes(wsol), TOKEN))
        vm.set_account(CURVE, Account(10**9, curve_bytes(), PUMP))
        vm.set_account(SHARING, Account(10**9, sharing_bytes(case["old"], case.get("version", 2)), PROGRAM))
        self.rent0 = vm.minimum_balance_for_rent_exemption(0)
        vm.set_account(PUMP_VAULT, Account(self.rent0 + case.get("vault", 0), b"", SYSTEM))
        for name, lamports in case.get("funded", {}).items():
            vm.set_account(key_of(name), Account(lamports, b"", SYSTEM))

    def remaining(self, names):
        return [AccountMeta(key_of(n), False, n not in EXEC) for n in names]

    def update_ix(self, new, remaining):
        a = [(EVENT, False, False), (PROGRAM, False, False), (AUTH.pubkey(), True, False),
             (PUMP_GLOBAL, False, False), (MINT, False, False), (SHARING, False, True), (CURVE, False, False),
             (PUMP_VAULT, False, True), (SYSTEM, False, False), (PUMP, False, False), (PUMP_EVENT, False, False),
             (AMM, False, False), (AMM_EVENT, False, False), (WSOL, False, False), (TOKEN, False, False),
             (ATA_PROG, False, False), (AMM_VAULT_AUTH, False, True), (AMM_VAULT_ATA, False, True)]
        metas = [AccountMeta(k, s, w) for k, s, w in a] + self.remaining(remaining)
        return Instruction(PROGRAM, IX_UPDATE + holders_bytes(new), metas)

    def distribute_ix(self, remaining):
        a = [(MINT, False, False), (CURVE, False, False), (SHARING, False, False), (PUMP_VAULT, False, True),
             (SYSTEM, False, False), (PUMP_EVENT, False, False), (PUMP, False, False)]
        return Instruction(PUMP, IX_DISTRIBUTE, [AccountMeta(k, s, w) for k, s, w in a] + self.remaining(remaining))

    def watched(self, names):
        keys = {"sharing_config": SHARING, "pump_creator_vault": PUMP_VAULT, "payer": PAYER.pubkey()}
        for n in names:
            if n not in EXEC:
                keys["holder:" + n] = key_of(n)
        return keys

    def snap(self, keys):
        out = {}
        for label, key in keys.items():
            a = self.vm.get_account(key)
            if a is None or (a.lamports == 0 and not a.data):
                out[label] = None
                continue
            out[label] = {"lamports": a.lamports, "owner": str(a.owner), "len": len(a.data),
                          "sha256": hashlib.sha256(bytes(a.data)).hexdigest()}
        return out

    def send(self, instructions, watch_names):
        vm = self.vm
        vm.expire_blockhash()
        signers = [PAYER]
        if any(m.pubkey == AUTH.pubkey() and m.is_signer for ix in instructions for m in ix.accounts):
            signers.append(AUTH)
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000)] + instructions,
                                               PAYER.pubkey(), signers, vm.latest_blockhash())
        keys = self.watched(watch_names)
        before = self.snap(keys)
        r = vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        after = self.snap(keys)
        logs = list(meta.logs())
        sc = vm.get_account(SHARING)
        deltas = {k: ((after[k] or {}).get("lamports", 0) - (before[k] or {}).get("lamports", 0)) for k in keys}
        return {
            "transaction_sha256": hashlib.sha256(bytes(tx)).hexdigest(),
            "error": str(r.err()) if failed else None,
            "logs": logs,
            "events": [decode_event(l) for l in logs if l.startswith("Program data:")],
            "lamport_deltas": deltas,
            "accounts_after": after,
            "sharing_after": decode_sharing(bytes(sc.data)) if sc else None,
            "compute_units": meta.compute_units_consumed(),
        }


def holder_names(holders):
    return [n for n, _ in holders]



BEHAVIOR = ["transaction_sha256", "error", "logs", "events", "lamport_deltas", "accounts_after", "sharing_after"]


def equal(names):
    n = len(names)
    return [(x, 10000 // n + (10000 % n if i == 0 else 0)) for i, x in enumerate(names)]


def cases():
    out = []
    for k in range(1, 11):
        for l in range(1, 11):
            out.append({"name": f"k{k:02d}-l{l:02d}", "k": k, "l": l,
                        "old": equal("ABCDEFGHIJ"[:k]), "new": equal("JIHGFEDCBA"[:l]), "vault": 1_000_000_000})
    return out


def run_point(paths, image, case):
    w = World(image, paths["pump"], paths["pump_amm"], case)
    old = holder_names(case["old"])
    names = sorted(set(old + holder_names(case["new"])))
    return w.send([w.update_ix(case["new"], old)], names)


def produce(paths, case_list):
    rows = []
    for c in case_list:
        o = run_point(paths, paths["original"], c)
        k = run_point(paths, paths["candidate"], c)
        rows.append({"case": c, "behavior_match": all(o[f] == k[f] for f in BEHAVIOR),
                     "logs_match": o["logs"] == k["logs"], "cu_match": o["compute_units"] == k["compute_units"],
                     "original": o, "candidate": k})
    shas = {n: sha(paths[n]) for n in ("original", "candidate", "pump", "pump_amm")}
    grid = {r["case"]["name"]: [r["original"]["compute_units"], r["candidate"]["compute_units"]] for r in rows}
    report = {"program_id": str(PROGRAM), "image_sha256": shas, "point_count": len(rows),
              "outcomes": sorted(set("ok" if r["original"]["error"] is None else r["original"]["error"] for r in rows)),
              "behavior_mismatched": [r["case"]["name"] for r in rows if not r["behavior_match"]],
              "cu_mismatched": [r["case"]["name"] for r in rows if not r["cu_match"]],
              "logs_mismatched": [r["case"]["name"] for r in rows if not r["logs_match"]],
              "cu_original_candidate": grid}
    return rows, report


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def gz(b):
    return gzip.compress(b, compresslevel=9, mtime=0)


def encode(rows, report):
    rec = gz(b"".join(json.dumps(r, sort_keys=True, separators=(",", ":")).encode() + b"\n" for r in rows))
    rep = gz(json.dumps(report, sort_keys=True, indent=1).encode() + b"\n")
    return rec, rep


def load_paths(images_arg, root=None):
    a = images_arg.strip()
    images = json.loads(a if a.startswith("{") else pathlib.Path(a).read_text())
    base = pathlib.Path(root) / "evidence/original" if root else pathlib.Path(images["original"]).resolve().parent.parent
    return {"original": images["original"], "candidate": images["candidate"],
            "pump": str(base / "pump/deployed.so"), "pump_amm": str(base / "pump_amm/deployed.so")}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--images", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    paths = load_paths(a.images, a.root)
    rec, rep = encode(*produce(paths, cases()))
    rt = pathlib.Path(a.out) / "runtime"
    rt.mkdir(parents=True, exist_ok=True)
    (rt / "receipts.jsonl.gz").write_bytes(rec)
    (rt / "report.json.gz").write_bytes(rep)
    r = json.loads(gzip.decompress(rep))
    print(json.dumps({k: r[k] for k in ("point_count", "outcomes", "behavior_mismatched", "cu_mismatched", "logs_mismatched")}))


if __name__ == "__main__":
    main()
