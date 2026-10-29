#!/usr/bin/env python3
"""Pump Fees create_donation_fee_pda: persistent-state sequences on two images.

Every case starts from a fresh LiteSVM per image. Steps are signed transactions
(create_donation_fee_pda, set_disable_flags, set_authority, System transfers)
or explicit writes of accounts owned by other programs (pump bonding curve,
pump_amm pool) and of the sharing-config PDA, which stand in for changes made
by those programs between transactions. Every receipt line is deterministic:
fixed keypair seeds, fixed clock, no wall time, no paths.

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
WSOL = Pubkey.from_string("So11111111111111111111111111111111111111112")
SYSTEM = Pubkey.default()
GLOBAL, GLOBAL_BUMP = Pubkey.find_program_address([b"fee-program-global"], PROGRAM)
EVENT = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]

AUTH = Keypair.from_seed(bytes([213]) * 32)
OTHER = Keypair.from_seed(bytes([214]) * 32)
PAYER = Keypair.from_seed(bytes([215]) * 32)
THIRD = Keypair.from_seed(bytes([216]) * 32)
WALLETS = {"AUTH": AUTH, "OTHER": OTHER, "PAYER": PAYER, "THIRD": THIRD}

MINTS = {"A": Pubkey.from_bytes(bytes([61]) * 32), "B": Pubkey.from_bytes(bytes([64]) * 32)}
CONFIGS = {"c1": Pubkey.from_bytes(bytes([62]) * 32), "c2": Pubkey.from_bytes(bytes([65]) * 32)}
QUOTE_Q = Pubkey.from_bytes(bytes([70]) * 32)
START = 1_700_000_000


def disc(kind, name):
    return hashlib.sha256(f"{kind}:{name}".encode()).digest()[:8]


IX_CREATE = disc("global", "create_donation_fee_pda")
IX_FLAGS = disc("global", "set_disable_flags")
IX_SETAUTH = disc("global", "set_authority")
GLOBAL_DATA = (disc("account", "FeeProgramGlobal") + bytes([GLOBAL_BUMP]) + bytes(AUTH.pubkey())
               + bytes([0]) + bytes([44]) * 32 + (123).to_bytes(8, "little") + bytes(256))


def curve_key(mint):
    return Pubkey.find_program_address([b"bonding-curve", bytes(mint)], PUMP)[0]


def sharing_key(mint):
    return Pubkey.find_program_address([b"sharing-config", bytes(mint)], PROGRAM)


def donation_key(mint, config):
    return Pubkey.find_program_address([b"donation-fee-pda", bytes(mint), bytes(config)], PROGRAM)[0]


def pool_authority(mint):
    return Pubkey.find_program_address([b"pool-authority", bytes(mint)], PUMP)[0]


def pool_key(mint, quote, index=0):
    return Pubkey.find_program_address(
        [b"pool", index.to_bytes(2, "little"), bytes(pool_authority(mint)), bytes(mint), bytes(quote)], AMM)


def key_of(name):
    """Resolve a symbolic key used in case definitions."""
    if name in WALLETS:
        return WALLETS[name].pubkey()
    if name == "ZERO":
        return Pubkey.default()
    if name.startswith("SHARING:"):
        return sharing_key(MINTS[name.split(":")[1]])[0]
    raise KeyError(name)


def curve_bytes(spec):
    """Bonding curve image: 8 disc, 5 x u64 reserves/supply, complete, creator,
    mayhem, cashback, quote_mint (offset 83..115), zero tail to 200 bytes."""
    reserves = spec.get("reserves", [0, 0, 0, 0, 0])
    data = bytearray(disc("account", "BondingCurve"))
    for value in reserves:
        data += value.to_bytes(8, "little")
    data += bytes([spec.get("complete", 0)]) + bytes(key_of(spec.get("creator", "AUTH")))
    data += bytes([0, 0])
    quote = spec.get("quote")
    data += bytes(32) if quote is None else bytes(QUOTE_Q if quote == "Q" else Pubkey.from_string(quote))
    data += bytes(200 - len(data))
    length = spec.get("length", 200)
    return bytes((data + bytes(max(0, length - len(data))))[:length])


def pool_bytes(mint, spec):
    quote = QUOTE_Q if spec.get("quote") == "Q" else WSOL
    index = spec.get("index", 0)
    _, bump = pool_key(mint, quote, index)
    data = (disc("account", "Pool") + bytes([bump]) + index.to_bytes(2, "little") + bytes(pool_authority(mint))
            + bytes(mint) + bytes(quote) + bytes(96) + bytes(8) + bytes(key_of(spec.get("coin_creator", "AUTH")))
            + bytes(2) + bytes(16))
    return data, quote, index


def sharing_bytes(mint, spec):
    _, bump = sharing_key(mint)
    smint = MINTS[spec.get("mint", "A")] if spec.get("mint", "A") in MINTS else Pubkey.from_bytes(bytes([99]) * 32)
    data = (disc("account", "SharingConfig") + bytes([bump, spec.get("version", 1), spec.get("status", 1)])
            + bytes(smint) + bytes(key_of(spec.get("admin", "OTHER"))) + bytes([spec.get("revoked", 0)]) + bytes(4))
    if spec.get("empty"):
        data = b""
    return data


def mint_bytes():
    data = bytearray(82)
    data[44] = 6
    data[45] = 1
    return bytes(data)


EV_CREATED = disc("event", "DonationFeePdaCreated")


def decode_created(line):
    """Decode a DonationFeePdaCreated `Program data:` line, else None."""
    if not line.startswith("Program data: "):
        return None
    raw = base64.b64decode(line[len("Program data: "):])
    if raw[:8] != EV_CREATED or len(raw) != 8 + 8 + 6 * 32:
        return None
    keys = [str(Pubkey.from_bytes(raw[16 + 32 * i:48 + 32 * i])) for i in range(6)]
    return {"timestamp": int.from_bytes(raw[8:16], "little", signed=True), "created_by": keys[0],
            "donation_fee_pda": keys[1], "config_id": keys[2], "base_mint": keys[3],
            "quote_mint": keys[4], "creator": keys[5]}


class World:
    def __init__(self, image):
        self.vm = LiteSVM().with_transaction_history(0)
        self.vm.add_program_from_file(PROGRAM, image)
        self.vm.set_clock(Clock(1000, 0, 0, 0, START))
        for kp in WALLETS.values():
            self.vm.set_account(kp.pubkey(), Account(10**12, b"", SYSTEM))
        self.vm.set_account(GLOBAL, Account(10**9, GLOBAL_DATA, PROGRAM))
        for mint in MINTS.values():
            self.vm.set_account(mint, Account(10**9, mint_bytes(), TOKEN))
        self.pools = {}
        # Default: active curve for every mint, creator AUTH, no quote bytes.
        for name in MINTS:
            self.write_curve(name, {"reserves": [1_000, 1_000, 1_000, 1_000, 1_000]})

    def write_curve(self, mint_name, spec):
        data = curve_bytes(spec)
        self.vm.set_account(curve_key(MINTS[mint_name]), Account(10**9, data, PUMP))

    def write_pool(self, mint_name, spec):
        data, quote, index = pool_bytes(MINTS[mint_name], spec)
        key = pool_key(MINTS[mint_name], quote, index)[0]
        self.vm.set_account(key, Account(10**9, data, Pubkey.from_string(spec.get("owner", str(AMM)))))
        self.pools[mint_name] = key

    def write_sharing(self, mint_name, spec):
        data = sharing_bytes(MINTS[mint_name], spec)
        owner = Pubkey.from_string(spec.get("owner", str(PROGRAM)))
        self.vm.set_account(sharing_key(MINTS[mint_name])[0], Account(10**9 if data else 0, data, owner if data else SYSTEM))

    def create_ix(self, payer, mint_name, config_name):
        mint = MINTS[mint_name]
        pool = self.pools.get(mint_name, pool_key(mint, WSOL)[0])
        metas = [AccountMeta(EVENT, False, False), AccountMeta(PROGRAM, False, False),
                 AccountMeta(WALLETS[payer].pubkey(), True, True), AccountMeta(SYSTEM, False, False),
                 AccountMeta(GLOBAL, False, False), AccountMeta(donation_key(mint, CONFIGS[config_name]), False, True),
                 AccountMeta(CONFIGS[config_name], False, False), AccountMeta(mint, False, False),
                 AccountMeta(curve_key(mint), False, False), AccountMeta(pool, False, False),
                 AccountMeta(sharing_key(mint)[0], False, False)]
        return Instruction(PROGRAM, IX_CREATE, metas), [payer]

    def admin_ix(self, data, signer):
        metas = [AccountMeta(WALLETS[signer].pubkey(), True, True), AccountMeta(GLOBAL, False, True),
                 AccountMeta(EVENT, False, False), AccountMeta(PROGRAM, False, False)]
        return Instruction(PROGRAM, data, metas), [signer]

    def build(self, op):
        kind = op[0]
        if kind == "create":
            return self.create_ix(op[1], op[2], op[3])
        if kind == "flags":
            return self.admin_ix(IX_FLAGS + bytes([op[2]]), op[1])
        if kind == "setauth":
            return self.admin_ix(IX_SETAUTH + bytes(key_of(op[2])), op[1])
        if kind == "fund":
            target = donation_key(MINTS[op[2]], CONFIGS[op[3]])
            return transfer(TransferParams(from_pubkey=WALLETS[op[1]].pubkey(), to_pubkey=target, lamports=op[4])), [op[1]]
        raise ValueError(kind)

    def watched(self):
        keys = [("global", GLOBAL)]
        for m in MINTS:
            for c in CONFIGS:
                keys.append((f"donation:{m}:{c}", donation_key(MINTS[m], CONFIGS[c])))
        out = {}
        for label, key in keys:
            acct = self.vm.get_account(key)
            if acct is None or (acct.lamports == 0 and not acct.data):
                out[label] = None
                continue
            row = {"lamports": acct.lamports, "owner": str(acct.owner), "len": len(acct.data),
                   "sha256": hashlib.sha256(acct.data).hexdigest()}
            if label.startswith("donation") and len(acct.data) == 218:
                d = acct.data
                row["decoded"] = {"bump": d[8], "version": d[9], "config_id": str(Pubkey.from_bytes(d[10:42])),
                                  "base_mint": str(Pubkey.from_bytes(d[42:74])),
                                  "quote_mint": str(Pubkey.from_bytes(d[74:106])),
                                  "creator": str(Pubkey.from_bytes(d[106:138])),
                                  "total_donated": int.from_bytes(d[138:146], "little"),
                                  "last_crank_ts": int.from_bytes(d[146:154], "little", signed=True)}
            if label == "global":
                row["authority"] = str(Pubkey.from_bytes(acct.data[9:41]))
                row["disable_flags"] = acct.data[41]
            out[label] = row
        return out

    def balances(self):
        return {name: self.vm.get_account(kp.pubkey()).lamports for name, kp in WALLETS.items()}

    def send(self, ops):
        instructions, signers = [], ["PAYER"]
        for op in ops:
            ix, sig = self.build(op)
            instructions.append(ix)
            signers += [s for s in sig if s not in signers]
        self.vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer(instructions, PAYER.pubkey(), [WALLETS[s] for s in signers],
                                               self.vm.latest_blockhash())
        before = self.balances()
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        after = self.balances()
        md = json.loads(meta.to_json())
        logs = list(meta.logs())
        return {"error": str(result.err()) if failed else None,
                "compute_units": meta.compute_units_consumed(),
                "logs": logs,
                "events": [l for l in logs if l.startswith("Program data:")],
                "created_events": [decode_created(l) for l in logs if decode_created(l)],
                "inner_instruction_count": sum(len(x) for x in md["inner_instructions"] or []),
                "return_data": md.get("return_data"),
                "balance_deltas": {k: after[k] - before[k] for k in after},
                "state": self.watched()}


def run_case(image, case):
    world = World(image)
    steps = []
    for index, step in enumerate(case["steps"]):
        kind = step[0]
        if kind == "curve":
            world.write_curve(step[1], step[2])
            steps.append({"i": index, "op": step, "state_write": True})
        elif kind == "pool":
            world.write_pool(step[1], step[2])
            steps.append({"i": index, "op": step, "state_write": True})
        elif kind == "sharing":
            world.write_sharing(step[1], step[2])
            steps.append({"i": index, "op": step, "state_write": True})
        elif kind == "clock":
            world.vm.set_clock(Clock(1000, 0, 0, 0, step[1]))
            steps.append({"i": index, "op": step, "state_write": True})
        elif kind == "tx":
            row = world.send(step[1])
            row.update({"i": index, "op": step})
            steps.append(row)
        else:
            raise ValueError(kind)
    return steps


ACTIVE = [1_000, 1_000, 1_000, 1_000, 1_000]
GRAD = [0, 0, 0, 0, 1_000]


def tx(*ops):
    return ("tx", [list(op) for op in ops])


def cases():
    out = []

    def add(name, steps, note):
        out.append({"name": name, "note": note, "steps": [list(s) if s[0] != "tx" else s for s in steps]})

    # a-*: active-curve route (some reserve non-zero) and the curve quote bytes.
    add("a-active-quote-zero", [tx(("create", "AUTH", "A", "c1"))], "active curve, quote bytes zero")
    add("a-active-quote-custom", [("curve", "A", {"reserves": ACTIVE, "quote": "Q"}), tx(("create", "AUTH", "A", "c1"))],
        "active curve, quote bytes 0x46*32")
    add("a-active-quote-wsol", [("curve", "A", {"reserves": ACTIVE, "quote": str(WSOL)}), tx(("create", "AUTH", "A", "c1"))],
        "active curve, quote bytes = WSOL")
    for length in [81, 82, 83, 114, 115, 116, 151]:
        add(f"a-curve-length-{length}", [("curve", "A", {"reserves": ACTIVE, "quote": "Q", "length": length}),
                                         tx(("create", "AUTH", "A", "c1"))],
            f"active curve truncated to {length} bytes, quote Q written where it fits")
    for field in range(5):
        reserves = [0] * 5
        reserves[field] = 1
        add(f"a-single-field-{field}", [("curve", "A", {"reserves": reserves, "quote": "Q"}), ("pool", "A", {"coin_creator": "OTHER"}),
                                        tx(("create", "AUTH", "A", "c1")), tx(("create", "OTHER", "A", "c2"))],
            f"only u64 field {field} of the curve is 1; pool coin_creator OTHER; AUTH then OTHER create")
    add("a-complete-flag-active", [("curve", "A", {"reserves": ACTIVE, "complete": 1, "quote": "Q"}),
                                   tx(("create", "AUTH", "A", "c1"))], "complete=1 with non-zero reserves")
    add("a-non-creator-then-creator", [tx(("create", "OTHER", "A", "c1")), tx(("create", "AUTH", "A", "c1"))],
        "OTHER (not creator) then AUTH")
    add("a-curve-creator-sharing", [("curve", "A", {"reserves": ACTIVE, "creator": "SHARING:A"}), ("sharing", "A", {"admin": "OTHER"}),
                                    tx(("create", "AUTH", "A", "c1")), tx(("create", "OTHER", "A", "c1"))],
        "active curve creator = sharing PDA, admin OTHER: AUTH then OTHER")
    add("a-curve-creator-zero", [("curve", "A", {"reserves": ACTIVE, "creator": "ZERO"}), tx(("create", "AUTH", "A", "c1"))],
        "active curve creator = zero key")

    # b-*: graduation and pool route.
    add("b-graduate-after-create", [("curve", "A", {"reserves": ACTIVE, "quote": "Q"}), tx(("create", "AUTH", "A", "c1")),
                                    ("curve", "A", {"reserves": GRAD}), ("pool", "A", {"coin_creator": "OTHER"}),
                                    tx(("create", "OTHER", "A", "c1")), tx(("create", "OTHER", "A", "c2")),
                                    tx(("create", "AUTH", "A", "c2"))],
        "create on curve, then curve zeroed + pool coin_creator OTHER")
    add("b-graduated-pool-index-1", [("curve", "A", {"reserves": GRAD}), ("pool", "A", {"coin_creator": "AUTH", "index": 1}),
                                     tx(("create", "AUTH", "A", "c1"))], "pool index 1")
    add("b-graduated-pool-quote-custom", [("curve", "A", {"reserves": GRAD, "quote": str(WSOL)}), ("pool", "A", {"coin_creator": "AUTH", "quote": "Q"}),
                                          tx(("create", "AUTH", "A", "c1"))], "pool quote Q, curve quote bytes WSOL")
    add("b-graduated-no-pool", [("curve", "A", {"reserves": GRAD}), tx(("create", "AUTH", "A", "c1")),
                                ("pool", "A", {"coin_creator": "AUTH"}), tx(("create", "AUTH", "A", "c1"))],
        "graduated with no pool account, then pool appears")
    add("b-pool-wrong-owner-then-fixed", [("curve", "A", {"reserves": GRAD}), ("pool", "A", {"coin_creator": "AUTH", "owner": str(PUMP)}),
                                          tx(("create", "AUTH", "A", "c1")), ("pool", "A", {"coin_creator": "AUTH"}),
                                          tx(("create", "AUTH", "A", "c1"))], "pool owned by pump, then by pump_amm")
    add("b-reactivate-after-graduate", [("curve", "A", {"reserves": GRAD}), ("pool", "A", {"coin_creator": "OTHER"}),
                                        tx(("create", "AUTH", "A", "c1")), ("curve", "A", {"reserves": ACTIVE}),
                                        tx(("create", "AUTH", "A", "c1"))],
        "graduated route rejects AUTH, curve becomes active again")

    # c-*: disable flags and authority, persisted through real setters.
    add("c-disable-then-enable", [tx(("flags", "AUTH", 4)), tx(("create", "AUTH", "A", "c1")), tx(("flags", "AUTH", 0)),
                                  tx(("create", "AUTH", "A", "c1"))], "flag 4 set, create, cleared, create")
    add("c-disable-after-create", [tx(("create", "AUTH", "A", "c1")), tx(("flags", "AUTH", 4)), tx(("create", "AUTH", "A", "c1")),
                                   tx(("flags", "AUTH", 0)), tx(("create", "AUTH", "A", "c1"))],
        "existing PDA under flag 4")
    add("c-all-other-bits", [tx(("flags", "AUTH", 0xFB)), tx(("create", "AUTH", "A", "c1")), tx(("flags", "AUTH", 0xFF)),
                             tx(("create", "AUTH", "A", "c2"))], "flags 0xFB then 0xFF")
    add("c-authority-moved", [tx(("setauth", "AUTH", "OTHER")), tx(("flags", "AUTH", 4)), tx(("flags", "OTHER", 4)),
                              tx(("create", "AUTH", "A", "c1")), tx(("flags", "OTHER", 0)), tx(("create", "AUTH", "A", "c1"))],
        "global authority AUTH->OTHER, then flag setters")
    add("c-same-tx-disable-then-create", [tx(("flags", "AUTH", 4), ("create", "AUTH", "A", "c1")),
                                          tx(("create", "AUTH", "A", "c1"))], "one tx: flags(4) then create")
    add("c-same-tx-create-then-disable", [tx(("create", "AUTH", "A", "c1"), ("flags", "AUTH", 4)),
                                          tx(("create", "AUTH", "A", "c1")), tx(("create", "AUTH", "A", "c2"))],
        "one tx: create then flags(4)")

    # d-*: idempotency, multiplicity, prefunding, clock.
    add("d-twice-same-tx", [tx(("create", "AUTH", "A", "c1"), ("create", "AUTH", "A", "c1"))], "two creates in one tx")
    add("d-existing-non-creator", [tx(("create", "AUTH", "A", "c1")), tx(("create", "OTHER", "A", "c1")),
                                   tx(("create", "THIRD", "A", "c1"))], "existing PDA re-created by non-creators")
    add("d-two-configs-two-mints", [tx(("create", "AUTH", "A", "c1")), tx(("create", "AUTH", "A", "c2")),
                                    tx(("create", "AUTH", "B", "c1")), tx(("create", "AUTH", "B", "c2"))],
        "4 PDAs from 2 mints x 2 config ids")
    add("d-prefund-then-create", [tx(("fund", "OTHER", "A", "c1", 5_000_000)), tx(("create", "AUTH", "A", "c1"))],
        "System transfer to PDA address before create")
    add("d-prefund-above-rent", [tx(("fund", "OTHER", "A", "c1", 3_000_000)), tx(("fund", "OTHER", "A", "c1", 3_000_000)),
                                 tx(("create", "AUTH", "A", "c1"))], "two prefunds (6,000,000) before create")
    add("d-prefund-below-rent", [tx(("fund", "OTHER", "A", "c1", 1_000_000)), tx(("create", "AUTH", "A", "c1"))],
        "prefund 1,000,000 (below the 218-byte rent minimum) before create")
    add("d-donate-after-create", [tx(("create", "AUTH", "A", "c1")), tx(("fund", "OTHER", "A", "c1", 1_000_000)),
                                  tx(("create", "AUTH", "A", "c1"))], "lamports donated after create, re-create")
    add("d-creator-rotated", [tx(("create", "AUTH", "A", "c1")), ("curve", "A", {"reserves": ACTIVE, "creator": "OTHER"}),
                              tx(("create", "OTHER", "A", "c1")), tx(("create", "OTHER", "A", "c2")), tx(("create", "AUTH", "A", "c2"))],
        "curve creator AUTH->OTHER after first create")
    add("d-clock-timestamps", [("clock", START + 1), tx(("create", "AUTH", "A", "c1")), ("clock", -5),
                               tx(("create", "AUTH", "A", "c2")), ("clock", 2**63 - 1), tx(("create", "AUTH", "B", "c1"))],
        "event timestamp at unix START+1, -5, i64 max")

    # e-*: sharing-config route on a graduated pool.
    sharing_pool = [("curve", "A", {"reserves": GRAD}), ("pool", "A", {"coin_creator": "SHARING:A"})]
    add("e-sharing-active", sharing_pool + [("sharing", "A", {"admin": "OTHER"}), tx(("create", "AUTH", "A", "c1")),
                                             tx(("create", "OTHER", "A", "c1"))], "admin OTHER: AUTH then OTHER")
    add("e-sharing-paused-then-active", sharing_pool + [("sharing", "A", {"admin": "OTHER", "status": 0}), tx(("create", "OTHER", "A", "c1")),
                                                         ("sharing", "A", {"admin": "OTHER", "status": 1}), tx(("create", "OTHER", "A", "c1"))],
        "status Paused, then Active")
    add("e-sharing-revoked-order", sharing_pool + [("sharing", "A", {"admin": "OTHER", "revoked": 1, "status": 0}),
                                                    tx(("create", "AUTH", "A", "c1")), tx(("create", "OTHER", "A", "c1")),
                                                    ("sharing", "A", {"admin": "OTHER", "revoked": 0, "status": 0}),
                                                    tx(("create", "OTHER", "A", "c1"))],
        "revoked + paused: wrong payer, admin payer, then un-revoked")
    add("e-sharing-status-2", sharing_pool + [("sharing", "A", {"admin": "OTHER", "status": 2}), tx(("create", "OTHER", "A", "c1"))],
        "status byte 2 (no enum variant)")
    add("e-sharing-revoked-2", sharing_pool + [("sharing", "A", {"admin": "OTHER", "revoked": 2}), tx(("create", "OTHER", "A", "c1"))],
        "admin_revoked byte 2 (invalid bool)")
    add("e-sharing-admin-rotated", sharing_pool + [("sharing", "A", {"admin": "OTHER"}), tx(("create", "OTHER", "A", "c1")),
                                                    ("sharing", "A", {"admin": "THIRD"}), tx(("create", "OTHER", "A", "c2")),
                                                    tx(("create", "THIRD", "A", "c2")), tx(("create", "THIRD", "A", "c1"))],
        "admin OTHER->THIRD after one create")
    add("e-sharing-missing-then-written", sharing_pool + [tx(("create", "OTHER", "A", "c1")), ("sharing", "A", {"admin": "OTHER", "owner": str(AMM)}),
                                                           tx(("create", "OTHER", "A", "c1")), ("sharing", "A", {"admin": "OTHER", "mint": "X"}),
                                                           tx(("create", "OTHER", "A", "c1")), ("sharing", "A", {"admin": "OTHER"}),
                                                           tx(("create", "OTHER", "A", "c1"))],
        "sharing PDA empty, wrong owner, wrong mint, then valid")
    return out


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def comparable(step):
    """Fields compared between images. Compute units and the runtime's
    'consumed' log lines are compared separately."""
    if step.get("state_write"):
        return step
    row = dict(step)
    row.pop("compute_units")
    row["logs"] = [l for l in step["logs"] if " consumed " not in l]
    return row


def produce(images):
    receipts, summary = [], []
    for case in cases():
        o = run_case(images["original"], case)
        c = run_case(images["candidate"], case)
        txs = [(a, b) for a, b in zip(o, c) if not a.get("state_write")]
        behavior = all(comparable(a) == comparable(b) for a, b in zip(o, c))
        cu = [(a["compute_units"], b["compute_units"]) for a, b in txs]
        logs_equal = all(a["logs"] == b["logs"] for a, b in txs)
        summary.append({"case": case["name"], "transactions": len(txs), "behavior_match": behavior,
                        "logs_identical": logs_equal, "cu_equal": all(x == y for x, y in cu),
                        "errors_original": [a["error"] for a, _ in txs]})
        receipts.append({"case": case["name"], "note": case["note"], "original": o, "candidate": c})
    return receipts, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--images", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = args.images
    images = json.loads(pathlib.Path(raw).read_text() if pathlib.Path(raw).is_file() else raw)
    receipts, summary = produce(images)
    out = pathlib.Path(args.out) / "runtime"
    out.mkdir(parents=True, exist_ok=True)
    blob = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in receipts).encode()
    (out / "receipts.jsonl.gz").write_bytes(gzip.compress(blob, mtime=0))
    report = {"original_sha256": sha256_file(images["original"]), "candidate_sha256": sha256_file(images["candidate"]),
              "receipts_sha256": hashlib.sha256(blob).hexdigest(), "case_count": len(summary),
              "transaction_count": sum(s["transactions"] for s in summary),
              "behavior_mismatches": [s["case"] for s in summary if not s["behavior_match"]],
              "log_or_cu_differences": [s["case"] for s in summary if not (s["logs_identical"] and s["cu_equal"])],
              "cases": summary}
    (out / "report.json.gz").write_bytes(gzip.compress(json.dumps(report, sort_keys=True, indent=1).encode() + b"\n", mtime=0))
    print(json.dumps({k: report[k] for k in ["case_count", "transaction_count", "behavior_mismatches", "log_or_cu_differences"]}))


if __name__ == "__main__":
    main()
