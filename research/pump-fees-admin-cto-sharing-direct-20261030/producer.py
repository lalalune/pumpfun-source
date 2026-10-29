#!/usr/bin/env python3
"""Pump Fees admin_cto_sharing_config called directly, on two images.

pump normally reaches this handler only through its own admin_cto CPI, which
always passes the canonical accounts. Here the handler is invoked as a
top-level instruction so that every account constraint, the Option<Pubkey>
argument decoder, SharingConfig size/version boundaries and multi-step
sequences (including create_donation_fee_pda's sharing route, which reads the
fields this handler writes) can be measured with only the pump_fees image.

The pool_authority account is a pump PDA and cannot sign, so every
transaction runs with LiteSVM signature verification off; the wallets that
can sign still sign (Transaction.new_unsigned + partial_sign). Every case
starts from a fresh LiteSVM per image. Fixed keypair seeds, fixed clock, no
wall time, no paths in the results.

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
from solders.message import Message
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
FEE_GLOBAL, FEE_GLOBAL_BUMP = Pubkey.find_program_address([b"fee-program-global"], PROGRAM)
EVENT = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]
PUMP_GLOBAL = Pubkey.find_program_address([b"global"], PUMP)[0]

AUTH = Keypair.from_seed(bytes([223]) * 32)
OTHER = Keypair.from_seed(bytes([224]) * 32)
PAYER = Keypair.from_seed(bytes([225]) * 32)
THIRD = Keypair.from_seed(bytes([226]) * 32)
WALLETS = {"AUTH": AUTH, "OTHER": OTHER, "PAYER": PAYER, "THIRD": THIRD}

MINTS = {"A": Pubkey.from_bytes(bytes([71]) * 32), "B": Pubkey.from_bytes(bytes([74]) * 32)}
CONFIGS = {"c1": Pubkey.from_bytes(bytes([72]) * 32), "c2": Pubkey.from_bytes(bytes([75]) * 32)}
SH = {"S%d" % i: Pubkey.from_bytes(bytes([100 + i]) * 32) for i in range(12)}
START = 1_700_000_000
GLOBAL_LEN = 740  # pump Global per programs/pump-fees/idls/pump.json, fixed fields only


def disc(kind, name):
    return hashlib.sha256(f"{kind}:{name}".encode()).digest()[:8]


IX_CTO = disc("global", "admin_cto_sharing_config")
IX_CREATE = disc("global", "create_donation_fee_pda")
EV_RESET = disc("event", "ResetFeeSharingConfigEvent")
FEE_GLOBAL_DATA = (disc("account", "FeeProgramGlobal") + bytes([FEE_GLOBAL_BUMP]) + bytes(AUTH.pubkey())
                   + bytes([0]) + bytes([44]) * 32 + (123).to_bytes(8, "little") + bytes(256))


def key_of(name):
    """Resolve a symbolic key used in case definitions."""
    if name in WALLETS:
        return WALLETS[name].pubkey()
    if name in SH:
        return SH[name]
    if name == "ZERO":
        return Pubkey.default()
    if name == "PROGRAM":
        return PROGRAM
    if name.startswith("SHARING:"):
        return sharing_key(MINTS[name.split(":")[1]])[0]
    if name.startswith("PA:"):
        return pool_authority(MINTS[name.split(":")[1]])
    if name.startswith("MINT:"):
        return MINTS[name.split(":")[1]]
    raise KeyError(name)


def sharing_key(mint):
    return Pubkey.find_program_address([b"sharing-config", bytes(mint)], PROGRAM)


def curve_key(mint):
    return Pubkey.find_program_address([b"bonding-curve", bytes(mint)], PUMP)[0]


def donation_key(mint, config):
    return Pubkey.find_program_address([b"donation-fee-pda", bytes(mint), bytes(config)], PROGRAM)[0]


def pool_authority(mint):
    return Pubkey.find_program_address([b"pool-authority", bytes(mint)], PUMP)[0]


def pool_key(mint, quote=WSOL, index=0):
    return Pubkey.find_program_address(
        [b"pool", index.to_bytes(2, "little"), bytes(pool_authority(mint)), bytes(mint), bytes(quote)], AMM)


def pump_global_bytes(spec):
    """pump Global: disc(8) initialized(1) authority fee_recipient 5xu64 withdraw_authority
    enable_migrate u64 u64 fee_recipients[7] set_creator_authority admin_set_creator_authority(418..450)
    create_v2_enabled whitelist_pda reserved_fee_recipient mayhem_mode_enabled reserved_fee_recipients[7]."""
    data = bytearray(GLOBAL_LEN)
    data[0:8] = disc("account", "Global")
    data[8] = 1
    data[418:450] = bytes(key_of(spec.get("admin_set_creator", "AUTH")))
    if spec.get("bad_disc"):
        data[0] ^= 1
    length = spec.get("length", 1088)
    return bytes((bytes(data) + bytes(max(0, length - GLOBAL_LEN)))[:length])


def sharing_bytes(mint, spec):
    """SharingConfig: disc bump version status mint admin admin_revoked Vec<Shareholder{pubkey,u16}>."""
    _, bump = sharing_key(mint)
    smint = MINTS[spec["mint"]] if "mint" in spec else mint
    holders = spec.get("holders", [[spec.get("admin", "OTHER"), 10000]])
    data = bytearray(disc("account", "SharingConfig"))
    data += bytes([spec.get("bump", bump), spec.get("version", 1), spec.get("status", 1)])
    data += bytes(smint) + bytes(key_of(spec.get("admin", "OTHER"))) + bytes([spec.get("revoked", 0)])
    data += spec.get("vec_len", len(holders)).to_bytes(4, "little")
    for name, bps in holders:
        data += bytes(key_of(name)) + bps.to_bytes(2, "little")
    if spec.get("bad_disc"):
        data[0] ^= 1
    length = spec.get("length", 1024)
    if length < len(data):
        return bytes(data[:length])
    # Stale bytes past the serialized content make shrink/grow visible.
    return bytes(data) + bytes([spec.get("fill", 0)]) * (length - len(data))


def decode_sharing(d):
    if len(d) < 80:
        return None
    out = {"bump": d[8], "version": d[9], "status": d[10], "mint": str(Pubkey.from_bytes(d[11:43])),
           "admin": str(Pubkey.from_bytes(d[43:75])), "admin_revoked": d[75],
           "vec_len": int.from_bytes(d[76:80], "little")}
    holders = []
    for i in range(min(out["vec_len"], 30)):
        o = 80 + 34 * i
        if o + 34 > len(d):
            break
        holders.append([str(Pubkey.from_bytes(d[o:o + 32])), int.from_bytes(d[o + 32:o + 34], "little")])
    out["holders"] = holders
    end = 80 + 34 * out["vec_len"]
    out["tail_nonzero"] = sum(1 for b in d[end:] if b) if end <= len(d) else None
    return out


def decode_reset(line):
    """Decode a ResetFeeSharingConfigEvent `Program data:` line, else None."""
    if not line.startswith("Program data: "):
        return None
    raw = base64.b64decode(line[len("Program data: "):])
    if raw[:8] != EV_RESET:
        return None
    o = 8
    ts = int.from_bytes(raw[o:o + 8], "little", signed=True)
    o += 8
    keys = []
    for _ in range(3):
        keys.append(str(Pubkey.from_bytes(raw[o:o + 32])))
        o += 32

    def vec(o):
        n = int.from_bytes(raw[o:o + 4], "little")
        o += 4
        items = []
        for _ in range(n):
            items.append([str(Pubkey.from_bytes(raw[o:o + 32])), int.from_bytes(raw[o + 32:o + 34], "little")])
            o += 34
        return items, o
    old_holders, o = vec(o)
    new_admin = str(Pubkey.from_bytes(raw[o:o + 32]))
    o += 32
    new_holders, o = vec(o)
    return {"timestamp": ts, "mint": keys[0], "sharing_config": keys[1], "old_admin": keys[2],
            "old_shareholders": old_holders, "new_admin": new_admin, "new_shareholders": new_holders,
            "old_version": raw[o], "new_version": raw[o + 1], "trailing": len(raw) - o - 2}


def mint_bytes(spec):
    data = bytearray(82)
    data[44] = 6
    data[45] = spec.get("initialized", 1)
    return bytes(data[:spec.get("length", 82)])


def curve_bytes(spec):
    """Bonding curve: 8 disc, 5 x u64, complete, creator, 2 flags, quote(32), zero tail to 200."""
    data = bytearray(disc("account", "BondingCurve"))
    for value in spec.get("reserves", [0, 0, 0, 0, 1_000]):
        data += value.to_bytes(8, "little")
    data += bytes([spec.get("complete", 1)]) + bytes(key_of(spec.get("creator", "AUTH"))) + bytes(2) + bytes(32)
    return bytes(data + bytes(200 - len(data)))


def pool_bytes(mint, spec):
    _, bump = pool_key(mint)
    return (disc("account", "Pool") + bytes([bump]) + (0).to_bytes(2, "little") + bytes(pool_authority(mint))
            + bytes(mint) + bytes(WSOL) + bytes(96) + bytes(8) + bytes(key_of(spec.get("coin_creator", "AUTH")))
            + bytes(2) + bytes(16))


class World:
    def __init__(self, image):
        self.vm = LiteSVM().with_transaction_history(0).with_sigverify(False)
        self.vm.add_program_from_file(PROGRAM, image)
        self.vm.set_clock(Clock(1000, 0, 0, 0, START))
        for kp in WALLETS.values():
            self.vm.set_account(kp.pubkey(), Account(10**12, b"", SYSTEM))
        self.vm.set_account(FEE_GLOBAL, Account(10**9, FEE_GLOBAL_DATA, PROGRAM))
        self.write_pump_global({})
        for name in MINTS:
            self.write_mint(name, {})
            self.write_sharing(name, {})
            # Graduated curve + pool whose coin_creator is the sharing PDA: the
            # donation create route that reads SharingConfig.
            self.vm.set_account(curve_key(MINTS[name]), Account(10**9, curve_bytes({}), PUMP))
            self.vm.set_account(pool_key(MINTS[name])[0],
                                Account(10**9, pool_bytes(MINTS[name], {"coin_creator": "SHARING:" + name}), AMM))

    def write_pump_global(self, spec):
        owner = Pubkey.from_string(spec.get("owner", str(PUMP)))
        self.vm.set_account(PUMP_GLOBAL, Account(10**9, pump_global_bytes(spec), owner))

    def write_mint(self, name, spec):
        owner = Pubkey.from_string(spec.get("owner", str(TOKEN)))
        self.vm.set_account(MINTS[name], Account(10**9, mint_bytes(spec), owner))

    def write_sharing(self, name, spec):
        if spec.get("absent"):
            self.vm.set_account(sharing_key(MINTS[name])[0], Account(0, b"", SYSTEM))
            return
        owner = Pubkey.from_string(spec.get("owner", str(PROGRAM)))
        self.vm.set_account(sharing_key(MINTS[name])[0],
                            Account(10**8, sharing_bytes(MINTS[name], spec), owner))

    def cto_ix(self, op):
        """("cto", authority, mint, new_admin|None, overrides)"""
        _, auth, mint_name, new_admin, ov = op
        mint = MINTS[mint_name]
        keys = {"pool_authority": pool_authority(mint), "authority": key_of(auth), "global": PUMP_GLOBAL,
                "mint": mint, "sharing_config": sharing_key(mint)[0], "event_authority": EVENT,
                "program": PROGRAM}
        for name, value in ov.get("keys", {}).items():
            keys[name] = key_of(value)
        signer = {"pool_authority": ov.get("pa_signer", True), "authority": ov.get("auth_signer", True)}
        order = ["pool_authority", "authority", "global", "mint", "sharing_config", "event_authority", "program"]
        metas = [AccountMeta(keys[n], signer.get(n, False), n == "sharing_config") for n in order]
        metas = metas[:ov.get("accounts", len(metas))]
        if "arg" in ov:
            arg = bytes.fromhex(ov["arg"])
        elif new_admin is None:
            arg = b"\x00"
        else:
            arg = b"\x01" + bytes(key_of(new_admin))
        return Instruction(PROGRAM, IX_CTO + arg, metas)

    def create_ix(self, op):
        """("create", payer, mint, config)"""
        _, payer, mint_name, config_name = op
        mint = MINTS[mint_name]
        metas = [AccountMeta(EVENT, False, False), AccountMeta(PROGRAM, False, False),
                 AccountMeta(WALLETS[payer].pubkey(), True, True), AccountMeta(SYSTEM, False, False),
                 AccountMeta(FEE_GLOBAL, False, False),
                 AccountMeta(donation_key(mint, CONFIGS[config_name]), False, True),
                 AccountMeta(CONFIGS[config_name], False, False), AccountMeta(mint, False, False),
                 AccountMeta(curve_key(mint), False, False), AccountMeta(pool_key(mint)[0], False, False),
                 AccountMeta(sharing_key(mint)[0], False, False)]
        return Instruction(PROGRAM, IX_CREATE, metas)

    def watched(self):
        out = {}
        for name in MINTS:
            acct = self.vm.get_account(sharing_key(MINTS[name])[0])
            if acct is None or (acct.lamports == 0 and not acct.data):
                out["sharing:" + name] = None
            else:
                out["sharing:" + name] = {"lamports": acct.lamports, "owner": str(acct.owner), "len": len(acct.data),
                                          "sha256": hashlib.sha256(acct.data).hexdigest(),
                                          "decoded": decode_sharing(acct.data)}
            for c in CONFIGS:
                acct = self.vm.get_account(donation_key(MINTS[name], CONFIGS[c]))
                exists = acct is not None and (acct.lamports > 0 or len(acct.data) > 0)
                out[f"donation:{name}:{c}"] = None if not exists else {
                    "lamports": acct.lamports, "len": len(acct.data), "sha256": hashlib.sha256(acct.data).hexdigest()}
        return out

    def balances(self):
        return {name: self.vm.get_account(kp.pubkey()).lamports for name, kp in WALLETS.items()}

    def send(self, ops):
        instructions = [self.cto_ix(op) if op[0] == "cto" else self.create_ix(op) for op in ops]
        self.vm.expire_blockhash()
        blockhash = self.vm.latest_blockhash()
        msg = Message.new_with_blockhash(instructions, PAYER.pubkey(), blockhash)
        tx = Transaction.new_unsigned(msg)
        signer_keys = list(msg.account_keys)[:msg.header.num_required_signatures]
        tx.partial_sign([kp for kp in WALLETS.values() if kp.pubkey() in signer_keys], blockhash)
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
                "reset_events": [decode_reset(l) for l in logs if decode_reset(l)],
                "inner_instruction_count": sum(len(x) for x in md["inner_instructions"] or []),
                "return_data": md.get("return_data"),
                "balance_deltas": {k: after[k] - before[k] for k in after},
                "state": self.watched()}


def run_case(image, case):
    world = World(image)
    steps = []
    for index, step in enumerate(case["steps"]):
        kind = step[0]
        if kind == "tx":
            row = world.send(step[1])
            row.update({"i": index, "op": step})
            steps.append(row)
            continue
        if kind == "sharing":
            world.write_sharing(step[1], step[2])
        elif kind == "pump_global":
            world.write_pump_global(step[1])
        elif kind == "mint":
            world.write_mint(step[1], step[2])
        elif kind == "clock":
            world.vm.set_clock(Clock(1000, 0, 0, 0, step[1]))
        else:
            raise ValueError(kind)
        steps.append({"i": index, "op": step, "state_write": True})
    return steps


def cto(auth="AUTH", mint="A", new="THIRD", **ov):
    return ["cto", auth, mint, new, ov]


def tx(*ops):
    return ["tx", [list(op) for op in ops]]


def cases():
    out = []

    def add(name, steps, note):
        out.append({"name": name, "note": note, "steps": [list(s) for s in steps]})

    # a-*: account constraints and argument decoding, one transaction each.
    add("a-base-some", [tx(cto())], "canonical accounts, new_admin Some(THIRD)")
    add("a-base-none", [tx(cto(new=None))], "canonical accounts, new_admin None")
    add("a-new-admin-zero", [tx(cto(new="ZERO"))], "Some(default pubkey)")
    add("a-new-admin-sharing-pda", [tx(cto(new="SHARING:A"))], "Some(the sharing PDA itself)")
    add("a-pa-not-signer", [tx(cto(pa_signer=False))], "pool_authority passed without signer flag")
    add("a-pa-other-mint", [tx(cto(keys={"pool_authority": "PA:B"}))], "pool_authority of mint B for mint A")
    add("a-auth-not-signer", [tx(cto(auth_signer=False))], "authority AUTH without signer flag")
    add("a-auth-mismatch", [tx(cto(auth="OTHER"))], "authority OTHER signs, Global admin_set_creator_authority = AUTH")
    add("a-global-wrong-key", [tx(cto(keys={"global": "SHARING:B"}))], "sharing PDA of B in the global slot")
    add("a-global-bad-disc", [["pump_global", {"bad_disc": True}], tx(cto())], "pump Global discriminator byte 0 flipped")
    for length in [450, 739, 740]:
        add(f"a-global-length-{length}", [["pump_global", {"length": length}], tx(cto())],
            f"pump Global truncated to {length} bytes")
    add("a-mint-b-for-sharing-a", [tx(cto(keys={"mint": "MINT:B"}))], "mint B with sharing PDA of A")
    add("a-mint-token2022-owner", [["mint", "A", {"owner": str(TOKEN22)}], tx(cto())], "mint A owned by Token-2022")
    add("a-mint-system-owner", [["mint", "A", {"owner": str(SYSTEM)}], tx(cto())], "mint A owned by System")
    add("a-mint-uninitialized", [["mint", "A", {"initialized": 0}], tx(cto())], "mint A is_initialized = 0")
    add("a-mint-length-81", [["mint", "A", {"length": 81}], tx(cto())], "mint A 81 bytes")
    add("a-sharing-mint-field-b", [["sharing", "A", {"mint": "B"}], tx(cto())], "sharing A whose mint field is B")
    add("a-sharing-bump-wrong", [["sharing", "A", {"bump": 0}], tx(cto())], "sharing A stored bump 0")
    add("a-sharing-owner-pump", [["sharing", "A", {"owner": str(PUMP)}], tx(cto())], "sharing A owned by pump")
    add("a-sharing-bad-disc", [["sharing", "A", {"bad_disc": True}], tx(cto())], "sharing A discriminator flipped")
    add("a-sharing-absent", [["sharing", "A", {"absent": True}], tx(cto())], "sharing A does not exist")
    add("a-event-wrong", [tx(cto(keys={"event_authority": "THIRD"}))], "THIRD in event_authority slot")
    add("a-program-wrong", [tx(cto(keys={"program": "SHARING:A"}))], "sharing PDA in program slot")
    add("a-accounts-6", [tx(cto(accounts=6))], "program account omitted")
    add("a-arg-empty", [tx(cto(arg=""))], "no argument bytes")
    add("a-arg-tag-2", [tx(cto(arg="02" + bytes(THIRD.pubkey()).hex()))], "Option tag 2")
    add("a-arg-truncated", [tx(cto(arg="01" + bytes(THIRD.pubkey()).hex()[:62]))], "tag 1 + 31 key bytes")
    add("a-arg-some-trailing", [tx(cto(arg="01" + bytes(THIRD.pubkey()).hex() + "00"))], "Some + one trailing byte")
    add("a-order-pa-and-auth", [tx(cto(auth="OTHER", keys={"pool_authority": "PA:B"}))],
        "wrong pool_authority and wrong authority together")
    add("a-order-auth-and-sharing", [["sharing", "A", {"mint": "B"}], tx(cto(auth="OTHER"))],
        "wrong authority and sharing mint field B together")
    add("a-order-zero-admin-and-sharing", [["sharing", "A", {"mint": "B"}], tx(cto(new="ZERO"))],
        "Some(default) and sharing mint field B together")

    # b-*: SharingConfig content and size boundaries.
    for version in [0, 2, 255]:
        add(f"b-version-{version}", [["sharing", "A", {"version": version}], tx(cto())], f"stored version {version}")
    add("b-status-paused", [["sharing", "A", {"status": 0}], tx(cto())], "stored status Paused")
    add("b-status-2", [["sharing", "A", {"status": 2}], tx(cto())], "stored status byte 2 (no variant)")
    add("b-revoked-2", [["sharing", "A", {"revoked": 2}], tx(cto())], "stored admin_revoked byte 2")
    add("b-len-80-empty-none", [["sharing", "A", {"holders": [], "length": 80}], tx(cto(new=None))],
        "80-byte account, 0 holders, None")
    add("b-len-80-empty-some", [["sharing", "A", {"holders": [], "length": 80}], tx(cto())],
        "80-byte account, 0 holders, Some")
    add("b-len-113-empty-some", [["sharing", "A", {"holders": [], "length": 113}], tx(cto())],
        "113-byte account, 0 holders, Some (needs 114)")
    add("b-len-114-empty-some", [["sharing", "A", {"holders": [], "length": 114}], tx(cto())],
        "114-byte account, 0 holders, Some")
    ten = [["S%d" % i, 1000] for i in range(10)]
    add("b-ten-holders-some", [["sharing", "A", {"holders": ten, "fill": 0xAA}], tx(cto())],
        "10 holders, tail filled 0xAA, Some: vec shrinks to 1")
    add("b-ten-holders-none", [["sharing", "A", {"holders": ten, "fill": 0xAA}], tx(cto(new=None))],
        "10 holders, tail filled 0xAA, None: vec shrinks to 0")
    add("b-twelve-holders-some", [["sharing", "A", {"holders": [["S%d" % i, 1] for i in range(12)]}], tx(cto())],
        "12 stored holders (above the 10 update limit), Some")
    add("b-vec-len-huge", [["sharing", "A", {"vec_len": 2**32 - 1}], tx(cto())], "vec length u32::MAX")
    add("b-vec-len-past-end", [["sharing", "A", {"holders": [], "vec_len": 1, "length": 100}], tx(cto())],
        "vec length 1 but only 20 bytes after the length field")

    # c-*: sequences on persistent state.
    add("c-some-some-none-some", [tx(cto(new="THIRD")), tx(cto(new="PAYER")), tx(cto(new=None)), tx(cto(new="OTHER"))],
        "four resets: THIRD, PAYER, None, OTHER")
    add("c-none-none", [tx(cto(new=None)), tx(cto(new=None))], "None twice")
    add("c-authority-rotated", [tx(cto(new="THIRD")), ["pump_global", {"admin_set_creator": "OTHER"}],
                                tx(cto(new="PAYER")), tx(cto(auth="OTHER", new="PAYER"))],
        "pump admin_set_creator_authority AUTH->OTHER between resets")
    add("c-same-tx-two", [tx(cto(new="THIRD"), cto(new="PAYER"))], "two resets in one tx")
    add("c-same-tx-then-fail", [tx(cto(new="THIRD"), cto(new="ZERO"))], "reset, then Some(default) in one tx: rollback")
    add("c-two-mints", [tx(cto(mint="A", new="THIRD"), cto(mint="B", new=None))], "A and B in one tx")
    add("c-clock-timestamps", [["clock", -7], tx(cto(new="THIRD")), ["clock", 2**63 - 1], tx(cto(new=None))],
        "event timestamp at unix -7 and i64 max")

    # d-*: create_donation_fee_pda sharing route after a reset.
    add("d-none-then-create", [tx(cto(new=None)), tx(["create", "OTHER", "A", "c1"]), tx(["create", "AUTH", "A", "c1"])],
        "after None: old admin OTHER and global admin AUTH create")
    add("d-some-then-create", [tx(cto(new="THIRD")), tx(["create", "OTHER", "A", "c1"]), tx(["create", "THIRD", "A", "c1"])],
        "after Some(THIRD): old admin OTHER, then THIRD create")
    add("d-revoked-paused-reactivated", [["sharing", "A", {"revoked": 1, "status": 0}], tx(["create", "OTHER", "A", "c1"]),
                                         tx(cto(new="OTHER")), tx(["create", "OTHER", "A", "c1"])],
        "revoked+paused sharing rejects OTHER; reset Some(OTHER); OTHER creates")
    add("d-same-tx-reset-then-create", [tx(cto(new="THIRD"), ["create", "THIRD", "A", "c1"])],
        "reset Some(THIRD) and THIRD create in one tx")
    add("d-same-tx-create-then-none", [tx(["create", "OTHER", "A", "c1"], cto(new=None)),
                                       tx(["create", "OTHER", "A", "c2"])],
        "OTHER create then None in one tx; OTHER creates c2")
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
        summary.append({"case": case["name"], "transactions": len(txs), "behavior_match": behavior,
                        "logs_identical": all(a["logs"] == b["logs"] for a, b in txs),
                        "cu_equal": all(x == y for x, y in cu),
                        "cu_original": [x for x, _ in cu], "cu_candidate": [y for _, y in cu],
                        "errors_original": [a["error"] for a, _ in txs],
                        "errors_candidate": [b["error"] for _, b in txs]})
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
