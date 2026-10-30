#!/usr/bin/env python3
"""Pump Fees create_fee_sharing_config: authorization, idempotency and curve/pool branches.

create_fee_sharing_config is the only way a coin enters fee sharing. It
init_if_needed's the 1024-byte SharingConfig PDA, returns Ok without doing
anything when the stored version is non-zero, picks the "graduated" branch
when all four bonding-curve reserves are zero, authorizes the payer against
either pump Global.admin_set_creator_authority or the coin creator, writes a
single 10,000-bps shareholder, and then CPIs into pump extend_account +
migrate_bonding_curve_creator (and, when graduated, pump_amm extend_account +
migrate_pool_coin_creator). This producer runs each case as

  c1  create_fee_sharing_config            <- the measured step
  c2  the same instruction again (only when c1 succeeded)

on both pump_fees images. pump and pump_amm are the original deployed images
(evidence/original/<prog>/deployed.so) on both sides; they are CPI
dependencies only. All state is synthetic: fixed keypair seeds, fixed clock,
a fresh LiteSVM per case and image, no wall time and no paths in the results.

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
WSOL = Pubkey.from_string("So11111111111111111111111111111111111111112")
SYSTEM = Pubkey.default()

KEYS = {"CREATOR": Keypair.from_seed(bytes([201]) * 32), "ADMIN": Keypair.from_seed(bytes([202]) * 32),
        "OTHER": Keypair.from_seed(bytes([203]) * 32), "POOL_CREATOR": Keypair.from_seed(bytes([204]) * 32)}
MINT = Pubkey.from_bytes(bytes([73]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([74]) * 32)
SHARING, SHARING_BUMP = Pubkey.find_program_address([b"sharing-config", bytes(MINT)], PROGRAM)
CURVE = Pubkey.find_program_address([b"bonding-curve", bytes(MINT)], PUMP)[0]
PUMP_GLOBAL = Pubkey.find_program_address([b"global"], PUMP)[0]
EVENT = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]
PUMP_EVENT = Pubkey.find_program_address([b"__event_authority"], PUMP)[0]
AMM_EVENT = Pubkey.find_program_address([b"__event_authority"], AMM)[0]
POOL_AUTHORITY = Pubkey.find_program_address([b"pool-authority", bytes(MINT)], PUMP)[0]
START = 1_700_000_000
GLOBAL_LEN = 740  # pump Global fixed fields; admin_set_creator_authority at 418..450
RESERVES = [1_000_000_000, 30_000_000_000, 800_000_000, 1_000_000, 1_000_000_000_000]


def disc(kind, name):
    return hashlib.sha256(f"{kind}:{name}".encode()).digest()[:8]


IX_CREATE = disc("global", "create_fee_sharing_config")
EV_CREATE = disc("event", "CreateFeeSharingConfigEvent")


def key_of(name):
    if name in KEYS:
        return KEYS[name].pubkey()
    return {"ZERO": SYSTEM, "SHARING": SHARING, "POOL_AUTHORITY": POOL_AUTHORITY, "MINT": MINT,
            "OTHER_MINT": OTHER_MINT}[name]


def name_of(key):
    for n in list(KEYS) + ["ZERO", "SHARING", "POOL_AUTHORITY", "MINT", "OTHER_MINT"]:
        if key_of(n) == key:
            return n
    return str(key)


def pool_key(spec):
    creator = key_of(spec.get("creator", "POOL_AUTHORITY"))
    base = key_of(spec.get("base_mint", "MINT"))
    seeds = [b"pool", (0).to_bytes(2, "little"), bytes(creator), bytes(base), bytes(WSOL)]
    key, bump = Pubkey.find_program_address(seeds, AMM)
    if spec.get("bump_delta"):
        bump = (bump + spec["bump_delta"]) % 256
    return key, bump, creator, base


def pool_bytes(spec):
    _, bump, creator, base = pool_key(spec)
    data = disc("account", "Pool") + bytes([bump]) + (0).to_bytes(2, "little") + bytes(creator) + bytes(base)
    data += bytes(WSOL) + bytes([81]) * 32 + bytes([82]) * 32 + bytes([83]) * 32 + (0).to_bytes(8, "little")
    data += bytes(key_of(spec.get("coin_creator", "POOL_CREATOR"))) + bytes(2)
    return data + bytes(spec.get("len", 261) - len(data))


def curve_bytes(spec):
    data = disc("account", "BondingCurve")
    for value in spec.get("reserves", RESERVES):
        data += value.to_bytes(8, "little")
    data += bytes([spec.get("complete", 0)]) + bytes(key_of(spec.get("creator", "CREATOR")))
    data += bytes(max(0, 200 - len(data)))
    return data[:spec.get("len", 151)]


def global_bytes(spec):
    g = bytearray(GLOBAL_LEN)
    g[0:8] = disc("account", "Global")
    g[8] = 1
    g[418:450] = bytes(key_of(spec.get("admin", "ADMIN")))
    if spec.get("bad_disc"):
        g[0] ^= 1
    return bytes(g)[:spec.get("len", GLOBAL_LEN)]


def sharing_pre_bytes(spec):
    data = disc("account", "SharingConfig") + bytes([SHARING_BUMP, spec.get("version", 2), 1]) + bytes(MINT)
    data += bytes(key_of(spec.get("admin", "OTHER"))) + bytes([0]) + (1).to_bytes(4, "little")
    data += bytes(key_of(spec.get("holder", "OTHER"))) + (10000).to_bytes(2, "little")
    if spec.get("bad_disc"):
        data = bytes([data[0] ^ 1]) + data[1:]
    return (data + bytes(max(0, spec.get("len", 1024) - len(data))))[:spec.get("len", 1024)]


def decode_holders(raw, o):
    n = int.from_bytes(raw[o:o + 4], "little")
    o += 4
    items = []
    for _ in range(min(n, 32)):
        if o + 34 > len(raw):
            items.append("truncated")
            break
        items.append([name_of(Pubkey.from_bytes(raw[o:o + 32])), int.from_bytes(raw[o + 32:o + 34], "little")])
        o += 34
    return items, o


def decode_sharing(d):
    if len(d) < 80 or d[:8] != disc("account", "SharingConfig"):
        return None
    holders, end = decode_holders(d, 76)
    return {"bump_ok": d[8] == SHARING_BUMP, "version": d[9], "status": d[10],
            "mint": name_of(Pubkey.from_bytes(d[11:43])), "admin": name_of(Pubkey.from_bytes(d[43:75])),
            "admin_revoked": d[75], "holders": holders, "tail_nonzero": sum(1 for b in d[end:] if b)}


def decode_curve(d):
    if len(d) < 81:
        return {"len": len(d)}
    return {"len": len(d), "creator": name_of(Pubkey.from_bytes(d[49:81])), "complete": d[48],
            "tail_nonzero": sum(1 for b in d[81:] if b)}


def decode_pool(d):
    if len(d) < 243:
        return {"len": len(d)}
    return {"len": len(d), "coin_creator": name_of(Pubkey.from_bytes(d[211:243])),
            "tail_nonzero": sum(1 for b in d[245:] if b)}


def decode_event(line):
    if not line.startswith("Program data: "):
        return None
    raw = base64.b64decode(line[len("Program data: "):])
    if raw[:8] == EV_CREATE:
        o = 8 + 8 + 32 + 32
        has_pool = raw[o]
        o += 1
        pool = None
        if has_pool:
            pool = "POOL" if Pubkey.from_bytes(raw[o:o + 32]) == SPEC_POOL[0] else str(Pubkey.from_bytes(raw[o:o + 32]))
            o += 32
        sharing = name_of(Pubkey.from_bytes(raw[o:o + 32]))
        admin = name_of(Pubkey.from_bytes(raw[o + 32:o + 64]))
        holders, o = decode_holders(raw, o + 64)
        return {"event": "CreateFeeSharingConfigEvent", "timestamp": int.from_bytes(raw[8:16], "little", signed=True),
                "mint": name_of(Pubkey.from_bytes(raw[16:48])), "bonding_curve_ok": Pubkey.from_bytes(raw[48:80]) == CURVE,
                "pool": pool, "sharing_config": sharing, "admin": admin, "initial_shareholders": holders,
                "status": raw[o]}
    return {"event": "unknown", "head": raw[:8].hex()}


SPEC_POOL = [None]


class World:
    def __init__(self, fees_image, pump_image, amm_image, case):
        vm = LiteSVM()
        vm.set_clock(Clock(1000, START, 0, 0, START))
        vm.add_program_from_file(PROGRAM, fees_image)
        vm.add_program_from_file(PUMP, pump_image)
        vm.add_program_from_file(AMM, amm_image)
        self.vm = vm
        self.case = case
        for name, kp in KEYS.items():
            vm.set_account(kp.pubkey(), Account(case.get("payer_lamports", 100_000_000_000) if name == case.get("payer", "CREATOR")
                                                else 100_000_000_000, b"", SYSTEM))
        g = case.get("global", {})
        vm.set_account(PUMP_GLOBAL, Account(10**9, global_bytes(g), PROGRAM if g.get("wrong_owner") else PUMP))
        m = case.get("mint", {})
        mint = bytearray(82)
        mint[44] = 6
        mint[45] = 1
        mint_owner = {"token": TOKEN, "token22": TOKEN22, "system": SYSTEM}[m.get("owner", "token")]
        vm.set_account(MINT, Account(10**9, bytes(mint)[:m.get("len", 82)], mint_owner))
        c = case.get("curve", {})
        cdata = curve_bytes(c)
        vm.set_account(CURVE, Account(vm.minimum_balance_for_rent_exemption(len(cdata)) + c.get("extra_lamports", 0),
                                      cdata, PROGRAM if c.get("wrong_owner") else PUMP))
        pre = case.get("sharing_pre")
        if pre is not None:
            if pre.get("system_lamports"):
                vm.set_account(SHARING, Account(pre["system_lamports"], b"", SYSTEM))
            else:
                vm.set_account(SHARING, Account(10**9, sharing_pre_bytes(pre), PROGRAM))
        self.pool = None
        p = case.get("pool")
        if p is not None:
            self.pool = pool_key(p)[0] if not p.get("key_mismatch") else Pubkey.from_bytes(bytes([90]) * 32)
            pdata = pool_bytes(p)
            vm.set_account(self.pool, Account(vm.minimum_balance_for_rent_exemption(len(pdata)), pdata,
                                              PROGRAM if p.get("wrong_owner") else AMM))
        SPEC_POOL[0] = self.pool

    def create_ix(self):
        case = self.case
        payer = key_of(case.get("payer", "CREATOR"))
        amm = case.get("amm_accounts", self.pool is not None)
        a = [(EVENT, False, False), (PROGRAM, False, False), (payer, True, True), (PUMP_GLOBAL, False, False),
             (MINT, False, False), (SHARING, False, True), (SYSTEM, False, False), (CURVE, False, True),
             (PUMP, False, False), (PUMP_EVENT, False, False),
             (self.pool, False, True) if self.pool is not None else (PROGRAM, False, False),
             (AMM, False, False) if amm else (PROGRAM, False, False),
             (AMM_EVENT, False, False) if amm else (PROGRAM, False, False)]
        return Instruction(PROGRAM, IX_CREATE, [AccountMeta(k, s, w) for k, s, w in a])

    def watched(self):
        keys = {"payer": key_of(self.case.get("payer", "CREATOR")), "sharing_config": SHARING, "bonding_curve": CURVE}
        if self.pool is not None:
            keys["pool"] = self.pool
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

    def send(self):
        vm = self.vm
        vm.expire_blockhash()
        payer = KEYS[self.case.get("payer", "CREATOR")]
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), self.create_ix()],
                                               payer.pubkey(), [payer], vm.latest_blockhash())
        keys = self.watched()
        before = self.snap(keys)
        r = vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        after = self.snap(keys)
        logs = list(meta.logs())
        sc = vm.get_account(SHARING)
        cv = vm.get_account(CURVE)
        pl = vm.get_account(self.pool) if self.pool is not None else None
        return {
            "transaction_sha256": hashlib.sha256(bytes(tx)).hexdigest(),
            "error": str(r.err()) if failed else None,
            "logs": logs,
            "events": [decode_event(l) for l in logs if l.startswith("Program data:")],
            "lamport_deltas": {k: ((after[k] or {}).get("lamports", 0) - (before[k] or {}).get("lamports", 0)) for k in keys},
            "accounts_after": after,
            "sharing_after": decode_sharing(bytes(sc.data)) if sc else None,
            "curve_after": decode_curve(bytes(cv.data)) if cv else None,
            "pool_after": decode_pool(bytes(pl.data)) if pl else None,
            "compute_units": meta.compute_units_consumed(),
        }


def run_case(paths, image, case):
    w = World(image, paths["pump"], paths["pump_amm"], case)
    steps = [["c1", w.send()]]
    if steps[0][1]["error"] is None:
        steps.append(["c2", w.send()])
    return [{"step": s, **r} for s, r in steps]


BEHAVIOR = ["transaction_sha256", "error", "logs", "events", "lamport_deltas", "accounts_after",
            "sharing_after", "curve_after", "pool_after"]
GRAD = [0, 0, 0, 0, 1_000_000_000_000]
POOL_OK = {}


def cases():
    out = []

    def add(name, **kw):
        out.append({"name": name, **kw})

    # a-*: who may create (bonding-curve path).
    add("a-creator-pays")
    add("a-global-admin-pays", payer="ADMIN")
    add("a-other-rejected", payer="OTHER")
    add("a-other-rejected-admin-zero", payer="OTHER", **{"global": {"admin": "ZERO"}})
    add("a-creator-is-also-admin", **{"global": {"admin": "CREATOR"}})
    add("a-admin-pays-admin-equals-other", payer="OTHER", **{"global": {"admin": "OTHER"}})
    add("a-creator-pays-but-curve-creator-other", curve={"creator": "OTHER"})
    # e-*: pre-existing sharing-config account.
    add("e-existing-v2-noop", sharing_pre={"version": 2})
    add("e-existing-v1-noop", sharing_pre={"version": 1})
    add("e-existing-v255-noop", sharing_pre={"version": 255})
    add("e-existing-v2-noop-other-payer", payer="OTHER", sharing_pre={"version": 2})
    add("e-existing-v0-reinitialized", sharing_pre={"version": 0})
    add("e-existing-v0-other-payer", payer="OTHER", sharing_pre={"version": 0})
    add("e-existing-bad-discriminator", sharing_pre={"version": 2, "bad_disc": True})
    add("e-existing-len-109", sharing_pre={"version": 2, "len": 109})
    add("e-prefunded-system-account", sharing_pre={"system_lamports": 5_000_000})
    add("e-prefunded-system-account-above-rent", sharing_pre={"system_lamports": 50_000_000})
    # r-*: graduation is "all four reserves zero".
    add("r-graduated-no-pool", curve={"reserves": GRAD})
    add("r-only-vtr-zero", curve={"reserves": [0] + RESERVES[1:]})
    add("r-three-zero-rsr-one", curve={"reserves": [0, 0, 0, 1, 10**12]})
    add("r-three-zero-vtr-one", curve={"reserves": [1, 0, 0, 0, 10**12]})
    add("r-complete-flag-not-graduation", curve={"complete": 1})
    add("r-total-supply-zero-only", curve={"reserves": RESERVES[:4] + [0]})
    # p-*: graduated pool validation.
    PC = "POOL_CREATOR"
    add("p-pool-coin-creator-pays", payer=PC, curve={"reserves": GRAD}, pool={})
    add("p-pool-global-admin-pays", payer="ADMIN", curve={"reserves": GRAD}, pool={})
    add("p-pool-curve-creator-rejected", curve={"reserves": GRAD}, pool={})
    add("p-pool-coin-creator-equals-curve-creator", curve={"reserves": GRAD}, pool={"coin_creator": "CREATOR"})
    add("p-pool-other-rejected", payer="OTHER", curve={"reserves": GRAD}, pool={})
    add("p-pool-wrong-base-mint", payer=PC, curve={"reserves": GRAD}, pool={"base_mint": "OTHER_MINT"})
    add("p-pool-wrong-creator", payer=PC, curve={"reserves": GRAD}, pool={"creator": "CREATOR"})
    add("p-pool-key-not-pda", payer=PC, curve={"reserves": GRAD}, pool={"key_mismatch": True})
    add("p-pool-bad-bump", payer=PC, curve={"reserves": GRAD}, pool={"bump_delta": 1})
    add("p-pool-wrong-base-mint-other-payer", payer="OTHER", curve={"reserves": GRAD}, pool={"base_mint": "OTHER_MINT"})
    add("p-pool-without-amm-program", payer=PC, curve={"reserves": GRAD}, pool={}, amm_accounts=False)
    add("p-pool-wrong-owner", payer=PC, curve={"reserves": GRAD}, pool={"wrong_owner": True})
    add("p-pool-on-active-curve-ignored", pool={"base_mint": "OTHER_MINT"})
    for n in (245, 260, 300):
        add(f"p-pool-len-{n}", payer=PC, curve={"reserves": GRAD}, pool={"len": n})
    # s-*: curve size before pump extend_account.
    for n in (81, 82, 150, 151, 152, 166, 200):
        add(f"s-curve-len-{n}", curve={"len": n})
    add("s-curve-creator-is-sharing-pda", curve={"creator": "SHARING"})
    # x-*: account shapes.
    add("x-mint-token-2022", mint={"owner": "token22"})
    add("x-mint-system-owned", mint={"owner": "system"})
    add("x-curve-wrong-owner", curve={"wrong_owner": True})
    add("x-global-bad-discriminator", **{"global": {"bad_disc": True}})
    add("x-global-len-450", **{"global": {"len": 450}})
    add("x-global-len-739", **{"global": {"len": 739}})
    add("x-global-wrong-owner", **{"global": {"wrong_owner": True}})
    add("x-payer-cannot-fund-rent", payer_lamports=5_000_000)
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


def short_msgs(logs):
    return [l for l in logs if ("Error Code" in l or "panicked" in l or "failed:" in l or "Error Number" in l
                                or "insufficient" in l.lower() or "AnchorError" in l)]


def summary(rows):
    out = []
    for r in rows:
        out.append({
            "case": r["case"]["name"], "behavior_match": r["behavior_match"], "cu_match": r["cu_match"], "diff": r["diff"],
            "steps": [{"step": s["step"], "error": s["error"], "msgs": short_msgs(s["logs"]),
                       "pump_cpis": sum(1 for l in s["logs"] if l.startswith(f"Program {PUMP} invoke [2]")),
                       "amm_cpis": sum(1 for l in s["logs"] if l.startswith(f"Program {AMM} invoke [2]")),
                       "lamport_deltas": s["lamport_deltas"], "sharing_after": s["sharing_after"],
                       "curve_after": s["curve_after"], "pool_after": s["pool_after"], "events": s["events"],
                       "cu": [s["compute_units"], cs["compute_units"]]}
                      for s, cs in zip(r["original"], r["candidate"])],
        })
    return out


def build(paths):
    rows = run_all(paths, cases())
    receipts = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows)
    report = {
        "scope": "pump_fees create_fee_sharing_config authorization, idempotency, graduation and pool branches, "
                 "curve size and account shapes on synthetic state; pump/pump_amm original images as CPI "
                 "dependencies on both sides.",
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
    receipts, report = build(paths)
    out = pathlib.Path(a.out) / "runtime"
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipts.jsonl.gz").write_bytes(gz_bytes(receipts))
    (out / "report.json.gz").write_bytes(gz_bytes(json.dumps(report, sort_keys=True, indent=1) + "\n"))
    print(json.dumps({k: report[k] for k in ["case_count", "step_count", "behavior_mismatch_cases", "cu_mismatch_cases"]}))


if __name__ == "__main__":
    main()
