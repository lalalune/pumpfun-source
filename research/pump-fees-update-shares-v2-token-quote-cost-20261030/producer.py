#!/usr/bin/env python3
"""Pump Fees update_fee_shares_v2 (token-quote route) compute units vs old shareholder count K and
new count L (1..10 each), SPL Token and Token-2022 quote mints, original vs rebuild.

One update_fee_shares_v2 transaction per point on a fresh LiteSVM per image. The curve's stored
quote mint is a non-native mint, so pump_fees CPIs pump distribute_creator_fees_v2(initialize_ata=true),
which pays the K old holders from the creator-vault quote ATA (creating holder ATAs when missing).
pump and pump_amm are the original deployed images on both sides; they are CPI dependencies only.
All state is synthetic: fixed keypair seeds, fixed clock, no wall time and no paths in the results.

Usage: producer.py --root <repo> --images '{"original":..,"candidate":..}' --out <dir>
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
MINT_AUTH = Keypair.from_seed(bytes([233]) * 32)
MINT = Pubkey.from_bytes(bytes([73]) * 32)
QUOTE = Pubkey.from_bytes(bytes([81]) * 32)  # SPL Token quote mint
QUOTE22 = Pubkey.from_bytes(bytes([82]) * 32)  # Token-2022 quote mint (no extensions)
OTHER = Pubkey.from_bytes(bytes([83]) * 32)  # an unrelated SPL Token mint
SHARING, SHARING_BUMP = Pubkey.find_program_address([b"sharing-config", bytes(MINT)], PROGRAM)
CURVE = Pubkey.find_program_address([b"bonding-curve", bytes(MINT)], PUMP)[0]
PUMP_GLOBAL = Pubkey.find_program_address([b"global"], PUMP)[0]
PUMP_VAULT = Pubkey.find_program_address([b"creator-vault", bytes(SHARING)], PUMP)[0]
EVENT = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]
PUMP_EVENT = Pubkey.find_program_address([b"__event_authority"], PUMP)[0]
AMM_EVENT = Pubkey.find_program_address([b"__event_authority"], AMM)[0]
AMM_VAULT_AUTH = Pubkey.find_program_address([b"creator_vault", bytes(SHARING)], AMM)[0]

# Non-executable shareholders: fixed byte-pattern keys that never sign.
HOLDERS = {n: Pubkey.from_bytes(bytes([110 + i]) * 32) for i, n in enumerate("ABCDEFGHIJ")}
# Executable shareholders: program accounts present in every world.
EXEC = {"X": TOKEN, "Y": ATA_PROG, "Z": SYSTEM, "P": PUMP, "M": AMM, "R": PROGRAM, "T": TOKEN22}
W = Pubkey.from_bytes(bytes([99]) * 32)  # a fresh non-executable key that is not a shareholder
START = 1_700_000_000
GLOBAL_LEN = 740
STEP_FUND = 10_000_000
U64_MAX = 2**64 - 1


def disc(kind, name):
    return hashlib.sha256(f"{kind}:{name}".encode()).digest()[:8]


IX_UPDATE = disc("global", "update_fee_shares_v2")
IX_DISTRIBUTE = disc("global", "distribute_creator_fees_v2")
EV_UPDATE = disc("event", "UpdateFeeSharesEvent")
EV_DISTRIBUTE = disc("event", "DistributeCreatorFeesEvent")


def ata(owner, mint, prog):
    return Pubkey.find_program_address([bytes(owner), bytes(prog), bytes(mint)], ATA_PROG)[0]


def key_of(name):
    if name in HOLDERS:
        return HOLDERS[name]
    if name in EXEC:
        return EXEC[name]
    if name == "W":
        return W
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


def curve_bytes(quote, complete=False, zero_reserves=False):
    """pump BondingCurve: creator = sharing config, quote_mint at [83,115). By default non-zero
    reserves and not complete. zero_reserves only reaches the AMM CPI when the AMM coin-creator vault
    ATA exists; it never does here, so the AMM transfer is always skipped."""
    data = disc("account", "BondingCurve")
    for value in [1_000_000_000, 30_000_000_000, 800_000_000, 1_000_000, 1_000_000_000_000]:
        data += (0 if zero_reserves and value != 1_000_000_000_000 else value).to_bytes(8, "little")
    data += bytes([1 if complete else 0]) + bytes(SHARING) + bytes(2) + bytes(quote)
    return data + bytes(200 - len(data))


POOL_AUTH = Pubkey.find_program_address([b"pool-authority", bytes(MINT)], PUMP)[0]


def pool_key(quote):
    return Pubkey.find_program_address([b"pool", (0).to_bytes(2, "little"), bytes(POOL_AUTH), bytes(MINT),
                                        bytes(quote)], AMM)[0]


def pool_bytes(length, creator_fees):
    """pump_amm Pool: pump_fees reads only creator_fees at [279,287) when len >= 287."""
    d = bytearray(length)
    d[0:8] = disc("account", "Pool")[:min(8, length)]
    if length >= 287:
        d[279:287] = creator_fees.to_bytes(8, "little")
    return bytes(d)


def mint_bytes(decimals, supply):
    m = bytearray(82)
    m[0:4] = (1).to_bytes(4, "little")
    m[4:36] = bytes(MINT_AUTH.pubkey())
    m[36:44] = supply.to_bytes(8, "little")
    m[44] = decimals
    m[45] = 1
    return bytes(m)


def token_account_bytes(mint, owner, amount):
    t = bytearray(165)
    t[0:32] = bytes(mint)
    t[32:64] = bytes(owner)
    t[64:72] = amount.to_bytes(8, "little")
    t[108] = 1
    return bytes(t)


NAMES = {}


def name_of(key):
    if not NAMES:
        for table in (HOLDERS, EXEC):
            NAMES.update({v: k for k, v in table.items()})
        NAMES[W] = "W"
        NAMES[AUTH.pubkey()] = "AUTH"
        for m, ml in ((QUOTE, "Q"), (QUOTE22, "Q22"), (WSOL, "WSOL"), (OTHER, "O")):
            NAMES[m] = ml
    return NAMES.get(key, str(key))


def decode_holders(raw, o):
    n = int.from_bytes(raw[o:o + 4], "little")
    o += 4
    items = []
    for _ in range(n):
        items.append([name_of(Pubkey.from_bytes(raw[o:o + 32])), int.from_bytes(raw[o + 32:o + 34], "little")])
        o += 34
    return items, o


def decode_sharing(d):
    if len(d) < 80:
        return None
    holders, end = decode_holders(d, 76)
    return {"version": d[9], "status": d[10], "admin_revoked": d[75], "holders": holders,
            "tail_nonzero": sum(1 for b in d[end:] if b)}


def decode_event(line):
    raw = base64.b64decode(line[len("Program data: "):])
    if raw[:8] == EV_UPDATE:
        holders, o = decode_holders(raw, 8 + 8 + 32 * 3)
        return {"event": "UpdateFeeSharesEvent", "new_shareholders": holders, "version": raw[o]}
    if raw[:8] == EV_DISTRIBUTE:
        holders, o = decode_holders(raw, 8 + 8 + 32 * 4)
        return {"event": "DistributeCreatorFeesEvent", "shareholders": holders,
                "distributed": int.from_bytes(raw[o:o + 8], "little"),
                "quote_mint": name_of(Pubkey.from_bytes(raw[o + 8:o + 40]))}
    return {"event": "unknown", "head": raw[:8].hex()}


class World:
    def __init__(self, fees_image, pump_image, amm_image, case):
        vm = LiteSVM().with_log_bytes_limit(None)  # ten-holder payouts exceed the default log limit
        vm.set_clock(Clock(1000, START, 0, 0, START))
        vm.add_program_from_file(PROGRAM, fees_image)
        vm.add_program_from_file(PUMP, pump_image)
        vm.add_program_from_file(AMM, amm_image)
        self.vm = vm
        self.case = case
        for kp in (AUTH, PAYER, MINT_AUTH):
            vm.set_account(kp.pubkey(), Account(100_000_000_000, b"", SYSTEM))
        g = bytearray(GLOBAL_LEN)
        g[0:8] = disc("account", "Global")
        g[8] = 1
        vm.set_account(PUMP_GLOBAL, Account(10**9, bytes(g), PUMP))
        vm.set_account(MINT, Account(10**9, mint_bytes(6, 0), TOKEN))
        vm.set_account(WSOL, Account(10**9, bytes(44) + bytes([9, 1]) + bytes(36), TOKEN))
        vault_amount = case.get("vault", 0)
        vm.set_account(QUOTE, Account(10**9, mint_bytes(6, vault_amount), TOKEN))
        vm.set_account(QUOTE22, Account(10**9, mint_bytes(6, vault_amount), TOKEN22))
        vm.set_account(OTHER, Account(10**9, mint_bytes(6, vault_amount), TOKEN))
        stored = {"Q": QUOTE, "Q22": QUOTE22, "DEFAULT": SYSTEM}[case.get("stored_quote", "Q")]
        vm.set_account(CURVE, Account(10**9, curve_bytes(stored, case.get("complete", False),
                                                          case.get("zero_reserves", False)), PUMP))
        self.pool_slot = None
        pool = case.get("pool")
        if pool is not None:
            pk = pool_key(stored if stored != SYSTEM else WSOL)
            self.pool_slot = W if pool == "wrong_key" else pk
            states = {"swept": (AMM, 300, 0), "unswept": (AMM, 300, 1), "unswept_max": (AMM, 300, U64_MAX),
                      "exact_287_unswept": (AMM, 287, 1), "short_286": (AMM, 286, 1),
                      "foreign_owner_unswept": (PUMP, 300, 1)}
            if pool in states:
                owner, length, fees = states[pool]
                vm.set_account(pk, Account(10**9, pool_bytes(length, fees), owner))
            # "missing" / "wrong_key": no account at the pool PDA
        vm.set_account(SHARING, Account(10**9, sharing_bytes(case["old"], case.get("version", 2)), PROGRAM))
        self.quote = {"Q": QUOTE, "Q22": QUOTE22, "WSOL": WSOL, "O": OTHER}[case.get("pass_quote", case.get("stored_quote", "Q"))]
        self.tprog = TOKEN22 if self.quote == QUOTE22 else TOKEN
        self.vault_ata = ata(PUMP_VAULT, self.quote, self.tprog)
        vm.set_account(PUMP_VAULT, Account(vm.minimum_balance_for_rent_exemption(0), b"", SYSTEM))
        rent_ta = vm.minimum_balance_for_rent_exemption(165)
        vstate = case.get("vault_ata", "ok")
        if vstate == "ok":
            vm.set_account(self.vault_ata, Account(rent_ta, token_account_bytes(self.quote, PUMP_VAULT, vault_amount), self.tprog))
        elif vstate == "wrong_mint":
            vm.set_account(self.vault_ata, Account(rent_ta, token_account_bytes(OTHER, PUMP_VAULT, vault_amount), self.tprog))
        # vstate == "missing": the vault ATA does not exist
        self.amm_ata = ata(AMM_VAULT_AUTH, self.quote, self.tprog)
        amm = case.get("amm_ata")  # AMM coin-creator vault ATA: None = absent (System), int = amount
        if amm == "wrong_mint":
            vm.set_account(self.amm_ata, Account(rent_ta, token_account_bytes(OTHER, AMM_VAULT_AUTH, 7), self.tprog))
        elif amm is not None:
            vm.set_account(self.amm_ata, Account(rent_ta, token_account_bytes(self.quote, AMM_VAULT_AUTH, amm), self.tprog))
        for name in case.get("ata_exists", []):
            vm.set_account(self.holder_ata(name), Account(rent_ta, token_account_bytes(self.quote, key_of(name), 0), self.tprog))

    def holder_ata(self, name):
        return ata(key_of(name), self.quote, self.tprog)

    def slot_key(self, spec):
        """'A' -> A's canonical ATA; 'A@T22' -> A's ATA under the other token program; 'raw:W' -> W itself."""
        if spec.startswith("raw:"):
            return key_of(spec[4:])
        if spec.endswith("@other"):
            other = TOKEN if self.tprog == TOKEN22 else TOKEN22
            return ata(key_of(spec[:-6]), self.quote, other)
        return self.holder_ata(spec)

    def remaining(self, holders, atas):
        metas = [AccountMeta(key_of(n), False, n not in EXEC) for n in holders]
        return metas + [AccountMeta(self.slot_key(s), False, True) for s in atas]

    def update_ix(self, new, holders, atas):
        a = [(EVENT, False, False), (PROGRAM, False, False), (AUTH.pubkey(), True, True),
             (PUMP_GLOBAL, False, False), (MINT, False, False), (SHARING, False, True), (CURVE, False, False),
             (PUMP_VAULT, False, True), (self.vault_ata, False, True), (SYSTEM, False, False),
             (PUMP, False, False), (PUMP_EVENT, False, False), (AMM, False, False), (AMM_EVENT, False, False),
             (self.quote, False, False), (self.tprog, False, False), (ATA_PROG, False, False),
             (AMM_VAULT_AUTH, False, True), (ata(AMM_VAULT_AUTH, self.quote, self.tprog), False, True)]
        metas = [AccountMeta(k, s, w) for k, s, w in a] + self.remaining(holders, atas)
        if self.pool_slot is not None:  # graduated curve: the pool is the last remaining account
            metas.append(AccountMeta(self.pool_slot, False, False))
        return Instruction(PROGRAM, IX_UPDATE + holders_bytes(new), metas)

    def distribute_ix(self, holders, atas):
        a = [(PAYER.pubkey(), True, True), (MINT, False, False), (CURVE, False, False), (SHARING, False, False),
             (PUMP_VAULT, False, True), (SYSTEM, False, False), (PUMP_EVENT, False, False), (PUMP, False, False),
             (self.vault_ata, False, True), (self.quote, False, False), (self.tprog, False, False),
             (ATA_PROG, False, False)]
        return Instruction(PUMP, IX_DISTRIBUTE + bytes([1]),
                           [AccountMeta(k, s, w) for k, s, w in a] + self.remaining(holders, atas))

    def mint_to_ix(self, amount):
        return Instruction(self.tprog, bytes([7]) + amount.to_bytes(8, "little"),
                           [AccountMeta(self.quote, False, True), AccountMeta(self.vault_ata, False, True),
                            AccountMeta(MINT_AUTH.pubkey(), True, False)])

    def watched(self, names):
        keys = {"sharing_config": SHARING, "vault_ata": self.vault_ata, "amm_vault_ata": self.amm_ata,
                "authority": AUTH.pubkey(),
                "payer": PAYER.pubkey()}
        for n in names:
            if n not in EXEC:
                keys["ata:" + n] = self.holder_ata(n)
        return keys

    def snap(self, keys):
        out = {}
        for label, key in keys.items():
            a = self.vm.get_account(key)
            if a is None or (a.lamports == 0 and not a.data):
                out[label] = None
                continue
            d = bytes(a.data)
            row = {"lamports": a.lamports, "owner": name_of(a.owner) if a.owner in (TOKEN, TOKEN22) else str(a.owner),
                   "len": len(d), "sha256": hashlib.sha256(d).hexdigest()}
            if a.owner in (TOKEN, TOKEN22) and len(d) >= 72:
                row["token_amount"] = int.from_bytes(d[64:72], "little")
            out[label] = row
        return out

    def send(self, instructions, watch_names):
        vm = self.vm
        vm.expire_blockhash()
        needed = {m.pubkey for ix in instructions for m in ix.accounts if m.is_signer}
        signers = [PAYER] + [kp for kp in (AUTH, MINT_AUTH) if kp.pubkey() in needed]
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

        def tok(v):
            return (v or {}).get("token_amount", 0)

        return {
            "transaction_sha256": hashlib.sha256(bytes(tx)).hexdigest(),
            "error": str(r.err()) if failed else None,
            "logs": logs,
            "events": [decode_event(l) for l in logs if l.startswith("Program data: ")],
            "lamport_deltas": {k: (after[k] or {}).get("lamports", 0) - (before[k] or {}).get("lamports", 0) for k in keys},
            "token_deltas": {k: tok(after[k]) - tok(before[k]) for k in keys if k in ("vault_ata", "amm_vault_ata") or k.startswith("ata:")},
            "accounts_after": after,
            "sharing_after": decode_sharing(bytes(sc.data)) if sc else None,
            "compute_units": meta.compute_units_consumed(),
        }


def holder_names(holders):
    return [n for n, _ in holders]


BEHAVIOR = ["transaction_sha256", "error", "logs", "events", "lamport_deltas", "token_deltas",
            "accounts_after", "sharing_after"]
V = 1_000_000_000  # quote base units in the creator-vault ATA


def equal(names):
    n = len(names)
    return [(x, 10000 // n + (10000 % n if i == 0 else 0)) for i, x in enumerate(names)]


def cases():
    out = []
    # q-*: SPL Token quote, holder ATAs created by the CPI; t-*: Token-2022 quote, same grid.
    for prefix, quote in (("q", "Q"), ("t", "Q22")):
        for k in range(1, 11):
            for l in range(1, 11):
                out.append({"name": f"{prefix}-k{k:02d}-l{l:02d}", "k": k, "l": l, "stored_quote": quote,
                            "old": equal("ABCDEFGHIJ"[:k]), "new": equal("JIHGFEDCBA"[:l]), "vault": V})
    # e-*: SPL Token quote, every old holder's ATA already exists (no ATA creation), L = 1.
    # z-*: SPL Token quote, empty vault (no transfers, ATAs still created), L = 1.
    for k in range(1, 11):
        old = equal("ABCDEFGHIJ"[:k])
        out.append({"name": f"e-k{k:02d}-l01", "k": k, "l": 1, "stored_quote": "Q", "old": old,
                    "new": equal("J"), "vault": V, "ata_exists": [n for n, _ in old]})
    for k in range(1, 11):
        out.append({"name": f"z-k{k:02d}-l01", "k": k, "l": 1, "stored_quote": "Q",
                    "old": equal("ABCDEFGHIJ"[:k]), "new": equal("J"), "vault": 0})
    # c-*: K = 10, L = 1 with the first P old-holder ATAs already created (instruction-trace controls).
    for quote, tag in (("Q", "q"), ("Q22", "t")):
        for pre in (1, 2, 5):
            old = equal("ABCDEFGHIJ")
            out.append({"name": f"c{tag}-k10-l01-pre{pre:02d}", "k": 10, "l": 1, "stored_quote": quote, "old": old,
                        "new": equal("J"), "vault": V, "ata_exists": [n for n, _ in old[:pre]]})
    # a-*: SPL quote, zero curve reserves + funded AMM coin-creator vault ATA, so pump_fees first CPIs
    # pump_amm transfer_creator_fees_to_pump_v2 (two more trace entries) before the payout.
    for k, pre in ((1, 0), (9, 0), (10, 0), (10, 1)):
        old = equal("ABCDEFGHIJ"[:k])
        out.append({"name": f"a-k{k:02d}-l01-pre{pre:02d}", "k": k, "l": 1, "stored_quote": "Q", "old": old,
                    "new": equal("J"), "vault": V, "zero_reserves": True, "amm_ata": 500_000_000,
                    "ata_exists": [n for n, _ in old[:pre]]})
    return out


def trace_entries(logs):
    """Instruction-trace entries reached, counted from the 'invoke [n]' log lines (top level included)."""
    return sum(1 for l in logs if l.startswith("Program ") and " invoke [" in l)


def run_point(paths, image, case):
    w = World(image, paths["pump"], paths["pump_amm"], case)
    old = holder_names(case["old"])
    names = sorted(set(old + holder_names(case["new"])))
    return w.send([w.update_ix(case["new"], old, old)], names)


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
              "cu_original_candidate": grid,
              "trace_entries_original_candidate": {r["case"]["name"]: [trace_entries(r["original"]["logs"]),
                                                                        trace_entries(r["candidate"]["logs"])] for r in rows},
              "holder_ata_bump_distance": {
                  label: {n: 255 - Pubkey.find_program_address([bytes(HOLDERS[n]), bytes(tp), bytes(q)], ATA_PROG)[1]
                          for n in "ABCDEFGHIJ"}
                  for label, q, tp in (("Q", QUOTE, TOKEN), ("Q22", QUOTE22, TOKEN22))},
              "error_by_point":{r["case"]["name"]: r["original"]["error"] for r in rows if r["original"]["error"]}}
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
