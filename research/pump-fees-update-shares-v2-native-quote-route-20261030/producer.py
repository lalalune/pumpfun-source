#!/usr/bin/env python3
"""Pump Fees update_fee_shares_v2 on a native-quote curve (stored quote_mint = zero key).

update_fee_shares_v2 on such a curve runs, in this order:

  1. version != 1, then the sharing-config admin check;
  2. the quote_mint account must be WSOL (InvalidQuoteMint otherwise); the
     pump creator-vault ATA account is seed-checked against the passed quote
     mint before the handler runs;
  3. preprocess_remaining with the WSOL pool PDA on a complete curve;
  4. if all four reserves are 0 and the AMM coin-creator vault WSOL ATA is
     not System-owned, a CPI to pump_amm transfer_creator_fees_to_pump_v2;
  5. because the stored quote is zero, the single-stride (holders only)
     executable rescale, pump distribute_creator_fees_v2 (skipped when no
     holder survives), then the new-share validation.

Each case runs on one fresh LiteSVM per image:

  u1  pump_fees update_fee_shares_v2(new shareholders)  <- the measured step
  u2  (only if u1 succeeded) fund the creator vault + a second update_fee_shares_v2

The pump_fees image is the one under test. pump and pump_amm are the
original deployed images (evidence/original/<prog>/deployed.so) on both sides;
they are CPI dependencies only. All state is synthetic: fixed keypair seeds,
fixed clock, a fresh LiteSVM per case and image, no wall time and no paths
in the results.

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
OTHER_AUTH = Keypair.from_seed(bytes([234]) * 32)  # not the sharing-config admin
MINT = Pubkey.from_bytes(bytes([73]) * 32)
SHARING, SHARING_BUMP = Pubkey.find_program_address([b"sharing-config", bytes(MINT)], PROGRAM)
CURVE = Pubkey.find_program_address([b"bonding-curve", bytes(MINT)], PUMP)[0]
PUMP_GLOBAL = Pubkey.find_program_address([b"global"], PUMP)[0]
PUMP_VAULT = Pubkey.find_program_address([b"creator-vault", bytes(SHARING)], PUMP)[0]
PUMP_VAULT_ATA = Pubkey.find_program_address([bytes(PUMP_VAULT), bytes(TOKEN), bytes(WSOL)], ATA_PROG)[0]
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


IX_UPDATE = disc("global", "update_fee_shares_v2")
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


def curve_bytes(complete=False, zero_reserves=False, quote=None, length=200):
    """pump BondingCurve: creator = sharing config, quote_mint at [83,115) (default = zero key)."""
    data = disc("account", "BondingCurve")
    for value in [1_000_000_000, 30_000_000_000, 800_000_000, 1_000_000, 1_000_000_000_000]:
        data += (0 if zero_reserves and value != 1_000_000_000_000 else value).to_bytes(8, "little")
    data += bytes([1 if complete else 0]) + bytes(SHARING) + bytes(2) + bytes(quote or SYSTEM)
    data = data + bytes(max(0, 200 - len(data)))
    return data[:length]


POOL_AUTH = Pubkey.find_program_address([b"pool-authority", bytes(MINT)], PUMP)[0]
POOL = Pubkey.find_program_address([b"pool", (0).to_bytes(2, "little"), bytes(POOL_AUTH), bytes(MINT),
                                    bytes(WSOL)], AMM)[0]
OTHER_QUOTE = Pubkey.from_bytes(bytes([81]) * 32)
U64_MAX = 2**64 - 1


def pool_bytes(length, creator_fees):
    """pump_amm Pool: pump_fees reads only the u64 at [279,287) when len >= 287."""
    d = bytearray(length)
    d[0:8] = disc("account", "Pool")[:min(8, length)]
    if length >= 287:
        d[279:287] = creator_fees.to_bytes(8, "little")
    return bytes(d)


def wsol_account_bytes(owner, amount, rent, mint=None):
    """SPL Token account for the native mint: is_native = Some(rent)."""
    t = bytearray(165)
    t[0:32] = bytes(mint or WSOL)
    t[32:64] = bytes(owner)
    t[64:72] = amount.to_bytes(8, "little")
    t[108] = 1
    if mint is None:
        t[109:113] = (1).to_bytes(4, "little")
        t[113:121] = rent.to_bytes(8, "little")
    return bytes(t)


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
        vm = LiteSVM().with_log_bytes_limit(None)
        vm.set_clock(Clock(1000, START, 0, 0, START))
        vm.add_program_from_file(PROGRAM, fees_image)
        vm.add_program_from_file(PUMP, pump_image)
        vm.add_program_from_file(AMM, amm_image)
        self.vm = vm
        for kp in (AUTH, PAYER, OTHER_AUTH):
            vm.set_account(kp.pubkey(), Account(100_000_000_000, b"", SYSTEM))
        g = bytearray(GLOBAL_LEN)
        g[0:8] = disc("account", "Global")
        g[8] = 1
        vm.set_account(PUMP_GLOBAL, Account(10**9, bytes(g), PUMP))
        mint = bytearray(82)
        mint[44] = 6
        mint[45] = 1
        vm.set_account(MINT, Account(10**9, bytes(mint), TOKEN))
        vm.set_account(OTHER_QUOTE, Account(10**9, bytes(mint), TOKEN))
        wsol = bytearray(82)
        wsol[44] = 9
        wsol[45] = 1
        vm.set_account(WSOL, Account(10**9, bytes(wsol), TOKEN))
        quote = OTHER_QUOTE if case.get("curve_quote") == "other" else None
        vm.set_account(CURVE, Account(10**9, curve_bytes(case.get("complete", False), case.get("zero_reserves", False),
                                                          quote, case.get("curve_len", 200)), PUMP))
        vm.set_account(SHARING, Account(10**9, sharing_bytes(case["old"], case.get("version", 2)), PROGRAM))
        self.rent0 = vm.minimum_balance_for_rent_exemption(0)
        vm.set_account(PUMP_VAULT, Account(self.rent0 + case.get("vault", 0), b"", SYSTEM))
        self.pool_slot = None
        pool = case.get("pool")
        if pool is not None:
            self.pool_slot = key_of("W") if pool == "wrong_key" else POOL
            states = {"swept": (AMM, 301, 0), "unswept": (AMM, 301, 1), "unswept_max": (AMM, 301, U64_MAX),
                      "exact_287_unswept": (AMM, 287, 1), "short_286": (AMM, 286, 1),
                      "foreign_owner_unswept": (PUMP, 301, 1)}
            if pool in states:
                owner, length, fees = states[pool]
                vm.set_account(POOL, Account(10**9, pool_bytes(length, fees), owner))
            # "missing" / "wrong_key": no account at the pool PDA
        rent_ta = vm.minimum_balance_for_rent_exemption(165)
        amm = case.get("amm_ata")  # AMM coin-creator vault WSOL ATA: None = absent, int = token amount
        if amm == "wrong_mint":
            vm.set_account(AMM_VAULT_ATA, Account(rent_ta, wsol_account_bytes(AMM_VAULT_AUTH, 7, rent_ta, OTHER_QUOTE), TOKEN))
        elif amm is not None:
            vm.set_account(AMM_VAULT_ATA, Account(rent_ta + amm, wsol_account_bytes(AMM_VAULT_AUTH, amm, rent_ta), TOKEN))
        pva = case.get("pump_vault_ata")  # pump creator-vault WSOL ATA: None = absent, int = token amount
        if pva is not None:
            vm.set_account(PUMP_VAULT_ATA, Account(rent_ta + pva, wsol_account_bytes(PUMP_VAULT, pva, rent_ta), TOKEN))
        self.quote = OTHER_QUOTE if case.get("pass_quote") == "other" else WSOL
        # ATA slots are derived from the passed quote mint unless "ata_quote" pins them to WSOL.
        aq = WSOL if case.get("ata_quote") == "wsol" else self.quote
        self.pva = Pubkey.find_program_address([bytes(PUMP_VAULT), bytes(TOKEN), bytes(aq)], ATA_PROG)[0]
        self.amm_ata = Pubkey.find_program_address([bytes(AMM_VAULT_AUTH), bytes(TOKEN), bytes(aq)], ATA_PROG)[0]

    def remaining(self, names):
        return [AccountMeta(key_of(n), False, n not in EXEC) for n in names]

    def update_ix(self, new, remaining, pool_first=False, signer=None):
        signer = signer or AUTH
        a = [(EVENT, False, False), (PROGRAM, False, False), (signer.pubkey(), True, True),
             (PUMP_GLOBAL, False, False), (MINT, False, False), (SHARING, False, True), (CURVE, False, False),
             (PUMP_VAULT, False, True), (self.pva, False, True), (SYSTEM, False, False),
             (PUMP, False, False), (PUMP_EVENT, False, False), (AMM, False, False), (AMM_EVENT, False, False),
             (self.quote, False, False), (TOKEN, False, False), (ATA_PROG, False, False),
             (AMM_VAULT_AUTH, False, True), (self.amm_ata, False, True)]
        rest = self.remaining(remaining)
        if self.pool_slot is not None:  # graduated curve: the pool is the last remaining account
            slot = AccountMeta(self.pool_slot, False, False)
            rest = [slot] + rest if pool_first else rest + [slot]
        metas = [AccountMeta(k, s, w) for k, s, w in a] + rest
        return Instruction(PROGRAM, IX_UPDATE + holders_bytes(new), metas)

    def watched(self, names):
        keys = {"sharing_config": SHARING, "pump_creator_vault": PUMP_VAULT, "amm_vault_ata": AMM_VAULT_ATA,
                "pump_vault_ata": PUMP_VAULT_ATA, "authority": AUTH.pubkey(), "pool": POOL, "payer": PAYER.pubkey()}
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
            d = bytes(a.data)
            row = {"lamports": a.lamports, "owner": str(a.owner), "len": len(d),
                   "sha256": hashlib.sha256(d).hexdigest()}
            if a.owner == TOKEN and len(d) == 165:
                row["token_amount"] = int.from_bytes(d[64:72], "little")
            out[label] = row
        return out

    def send(self, instructions, watch_names):
        vm = self.vm
        vm.expire_blockhash()
        needed = {m.pubkey for ix in instructions for m in ix.accounts if m.is_signer}
        signers = [PAYER] + [kp for kp in (AUTH, OTHER_AUTH) if kp.pubkey() in needed]
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


def run_case(paths, image, case):
    """u1 = the measured update_fee_shares; if it succeeds, u2 = fund the pump creator vault and run a
    second update_fee_shares with the same remaining-account shape against the new list."""
    w = World(image, paths["pump"], paths["pump_amm"], case)
    old_names = case.get("remaining", holder_names(case["old"]))
    new = case["new"]
    names = sorted(set(old_names + holder_names(new) + holder_names(case["old"])) - set(EXEC))
    signer = OTHER_AUTH if case.get("wrong_auth") else AUTH
    steps = [["u1", w.send([w.update_ix(new, old_names, case.get("pool_first", False), signer)], names)]]
    if steps[-1][1]["error"] is None:
        fund = transfer(TransferParams(from_pubkey=PAYER.pubkey(), to_pubkey=PUMP_VAULT, lamports=STEP_FUND))
        steps.append(["u2", w.send([fund, w.update_ix([("J", 10000)], holder_names(new))], names)])
    return [{"step": s, **r} for s, r in steps]


BEHAVIOR = ["transaction_sha256", "error", "logs", "events", "lamport_deltas", "accounts_after", "sharing_after"]


def cases():
    out = []

    def add(name, old, new=None, **kw):
        out.append({"name": name, "old": old, "new": [("J", 10000)] if new is None else new, **kw})

    V = 1_000_000_000  # lamports above rent in the pump creator vault
    EX3 = [("A", 2500), ("X", 5000), ("B", 2500)]
    NOX = [("A", 5000), ("B", 5000)]
    # r-*: active native curve; remaining accounts are holders only (single stride, no ATA partners).
    add("r-native-exec-middle", EX3, vault=V)
    add("r-native-no-exec", NOX, vault=V)
    add("r-native-all-executable", [("X", 10000)], vault=V)
    add("r-native-with-ata-partners", EX3, vault=V, remaining=["A", "X", "B", "A", "X", "B"])
    add("r-native-missing-last-holder", EX3, vault=V, remaining=["A", "X"])
    add("r-native-zero-vault", EX3, vault=0)
    # q-*: the quote_mint account must equal WSOL when the stored curve quote is the zero key.
    add("q-other-quote-passed", EX3, vault=V, pass_quote="other")
    add("q-other-quote-wsol-atas", EX3, vault=V, pass_quote="other", ata_quote="wsol")
    add("q-other-quote-graduated-no-slot", EX3, pass_quote="other", vault=V, complete=True, zero_reserves=True)
    add("q-other-quote-version-1", EX3, vault=V, pass_quote="other", version=1)
    add("q-other-quote-wrong-authority", EX3, vault=V, pass_quote="other", wrong_auth=True)
    add("q-curve-len-114", EX3, vault=V, curve_len=114)
    add("q-curve-len-82", EX3, vault=V, curve_len=82)
    add("q-curve-len-81", EX3, vault=V, curve_len=81)
    # o-*: check order.
    add("o-version-1-wrong-authority", EX3, vault=V, version=1, wrong_auth=True)
    add("o-wrong-authority-graduated-no-slot", EX3, wrong_auth=True, vault=V, complete=True, zero_reserves=True)
    # g-*: graduated curve with the WSOL pool PDA as the last remaining account.
    G = dict(vault=V, complete=True, zero_reserves=True)
    add("g-no-pool-slot", EX3, **G)
    add("g-pool-wrong-key", EX3, pool="wrong_key", **G)
    add("g-pool-missing-account", EX3, pool="missing", **G)
    add("g-pool-swept", EX3, pool="swept", **G)
    add("g-pool-unswept-1", EX3, pool="unswept", **G)
    add("g-pool-len-287-unswept", EX3, pool="exact_287_unswept", **G)
    add("g-pool-len-286-unswept", EX3, pool="short_286", **G)
    add("g-pool-foreign-owner-unswept", EX3, pool="foreign_owner_unswept", **G)
    add("g-pool-first-not-last", EX3, pool="swept", pool_first=True, **G)
    add("g-pool-other-quote-passed", EX3, pool="swept", pass_quote="other", **G)
    add("g-pool-other-quote-wsol-atas", EX3, pool="swept", pass_quote="other", ata_quote="wsol", **G)
    # a-*: zero reserves + existing AMM coin-creator vault WSOL ATA -> transfer_creator_fees_to_pump_v2.
    A = dict(vault=V, zero_reserves=True)
    add("a-amm-ata-funded", EX3, amm_ata=500_000_000, **A)
    add("a-amm-ata-funded-no-exec", NOX, amm_ata=500_000_000, **A)
    add("a-amm-ata-empty", EX3, amm_ata=0, **A)
    add("a-amm-ata-funded-pump-vault-ata-exists", EX3, amm_ata=500_000_000, pump_vault_ata=0, **A)
    add("a-amm-ata-funded-pump-vault-ata-holds", EX3, amm_ata=500_000_000, pump_vault_ata=7, **A)
    add("a-amm-ata-funded-pump-vault-empty", EX3, amm_ata=500_000_000, vault=0, zero_reserves=True)
    add("a-amm-ata-funded-nonzero-reserves", EX3, amm_ata=500_000_000, vault=V)
    add("a-amm-ata-wrong-mint", EX3, amm_ata="wrong_mint", **A)
    add("a-amm-ata-funded-all-executable", [("X", 10000)], amm_ata=500_000_000, **A)
    add("a-amm-ata-funded-graduated-swept", EX3, amm_ata=500_000_000, pool="swept", complete=True, **A)
    add("a-amm-ata-funded-graduated-unswept", EX3, amm_ata=500_000_000, pool="unswept", complete=True, **A)
    add("a-amm-ata-funded-invalid-new", EX3, amm_ata=500_000_000, new=[("J", 9999)], **A)
    return out


def run_all(paths, case_list):
    rows = []
    for case in case_list:
        o = run_case(paths, paths["original"], case)
        c = run_case(paths, paths["candidate"], case)
        diffs = []
        for so, sc in zip(o, c):
            for k in BEHAVIOR:
                if so[k] != sc[k]:
                    diffs.append(f"{so['step']}:{k}")
        if len(o) != len(c):
            diffs.append("step_count")
        rows.append({"case": case, "original": o, "candidate": c, "behavior_match": not diffs, "diff": diffs,
                     "cu_match": [s["compute_units"] for s in o] == [s["compute_units"] for s in c]})
    return rows


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def gz_bytes(text):
    return gzip.compress(text.encode(), compresslevel=9, mtime=0)


def msgs(logs):
    keep = ("Unable to distribute", "Insufficient", "Error Code", "Error Message", "panicked", "failed:",
            "Left:", "Right:")
    return [l for l in logs if any(k in l for k in keep)]


def summary(rows):
    out = []
    for r in rows:
        o = r["original"]
        out.append({
            "case": r["case"]["name"], "behavior_match": r["behavior_match"], "cu_match": r["cu_match"],
            "diff": r["diff"],
            "steps": [{"step": s["step"], "error": s["error"],
                       "holder_deltas": {k[7:]: v for k, v in s["lamport_deltas"].items() if k.startswith("holder:") and v},
                       "vault_delta": s["lamport_deltas"]["pump_creator_vault"],
                       "amm_ata_delta": s["lamport_deltas"]["amm_vault_ata"],
                       "pump_vault_ata_delta": s["lamport_deltas"]["pump_vault_ata"],
                       "authority_delta": s["lamport_deltas"]["authority"],
                       "stored_after": (s["sharing_after"] or {}).get("holders"),
                       "revoked_after": (s["sharing_after"] or {}).get("admin_revoked"),
                       "events": s["events"], "msgs": msgs(s["logs"]),
                       "amm_cpi": any(l.startswith(f"Program {AMM} invoke") for l in s["logs"]),
                       "pump_cpi": any(l.startswith(f"Program {PUMP} invoke") for l in s["logs"]),
                       "cu": [s["compute_units"], cs["compute_units"]]}
                      for s, cs in zip(o, r["candidate"])],
        })
    return out


def produce(paths):
    rows = run_all(paths, cases())
    receipts = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows)
    report = {
        "scope": "pump_fees update_fee_shares_v2 on a native (zero-key) quote curve: quote-mint match, graduated WSOL "
                 "pool slot, pump_amm transfer_creator_fees_to_pump_v2 (WSOL) and the single-stride payout, on synthetic state; pump/pump_amm original images as CPI dependencies on both sides.",
        "images_sha256": {"original": sha(paths["original"]), "candidate": sha(paths["candidate"]),
                          "pump_dependency": sha(paths["pump"]), "pump_amm_dependency": sha(paths["pump_amm"])},
        "case_count": len(rows),
        "step_count": sum(len(r["original"]) for r in rows),
        "behavior_mismatch_cases": [r["case"]["name"] for r in rows if not r["behavior_match"]],
        "cu_mismatch_cases": [r["case"]["name"] for r in rows if not r["cu_match"]],
        "receipts_sha256": hashlib.sha256(receipts.encode()).hexdigest(),
        "summary": summary(rows),
    }
    return receipts, report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--images", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    images = json.loads(a.images)
    root = pathlib.Path(a.root)
    paths = {"original": images["original"], "candidate": images["candidate"],
             "pump": str(root / "evidence/original/pump/deployed.so"),
             "pump_amm": str(root / "evidence/original/pump_amm/deployed.so")}
    receipts, report = produce(paths)
    out = pathlib.Path(a.out) / "runtime"
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipts.jsonl.gz").write_bytes(gz_bytes(receipts))
    (out / "report.json.gz").write_bytes(gz_bytes(json.dumps(report, sort_keys=True, indent=1) + "\n"))
    print(json.dumps({k: report[k] for k in ["case_count", "step_count", "behavior_mismatch_cases", "cu_mismatch_cases"]}))


if __name__ == "__main__":
    main()
