#!/usr/bin/env python3
"""Pump Fees: Token-2022 token-account layout decoding boundaries (withdraw), on two images.

`withdraw` declares its token accounts as `Option<InterfaceAccount<token_interface::TokenAccount>>`
with `token::mint`, `token::authority` and `token::token_program` constraints. Anchor decodes them
with the spl-token-2022 `StateWithExtensions::<Account>::unpack` routine linked into pump_fees,
then pump_fees reads `vault_ata.amount` and CPIs `transfer_checked` into the token program (the
SPL Token / Token-2022 programs bundled with LiteSVM). This packet varies only the bytes (and in
the `o-*` family the owner) of `vault_ata` or `user_ata`:

  * length around 165 / 166 / 355 and the account-type byte at offset 165;
  * the state byte and the COption tags of delegate / is_native / close_authority;
  * the TLV extension area;
  * the decoded amount (0, u64::MAX) and the token::* constraints that read decoded fields.

Each case is one withdraw transaction on a fresh LiteSVM per image. Only the pump_fees image
differs between the two sides. Fixed keypair seeds, fixed clock, no wall time, no paths.

Usage: producer.py --root <repo> --images '{"original":..,"candidate":..}' --out <dir>
"""
import argparse
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
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA_PROGRAM = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSTEM = Pubkey.default()
EVENT = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]
USER = Keypair.from_seed(bytes([251]) * 32)
OTHER = Pubkey.from_bytes(bytes([252]) * 32)
VAULT = Pubkey.find_program_address([b"referral-vault", bytes(USER.pubkey())], PROGRAM)[0]
MINT22 = Pubkey.from_bytes(bytes([93]) * 32)  # Token-2022 mint, base layout, 6 decimals
MINTLEG = Pubkey.from_bytes(bytes([94]) * 32)  # SPL Token mint, 6 decimals
MINTX = Pubkey.from_bytes(bytes([95]) * 32)  # another Token-2022 mint
START = 1_700_000_000
AMOUNT = 1_000_000
RENT_LAMPORTS = 3_000_000


def disc(kind, name):
    return hashlib.sha256(f"{kind}:{name}".encode()).digest()[:8]


IX_WITHDRAW = disc("global", "withdraw")
EV_WITHDRAW = disc("event", "WithdrawEvent")


def ata(owner, mint, prog):
    return Pubkey.find_program_address([bytes(owner), bytes(prog), bytes(mint)], ATA_PROGRAM)[0]


def mint_bytes():
    m = bytearray(82)
    m[36:44] = (10**15).to_bytes(8, "little")
    m[44] = 6
    m[45] = 1
    return bytes(m)


def tlv(ext_type, length, value=None):
    value = bytes(length) if value is None else value
    return ext_type.to_bytes(2, "little") + length.to_bytes(2, "little") + value


def account_bytes(mint, owner, spec):
    """165-byte base Account, then (if requested) the account-type byte at 165 and a TLV area.
    spec keys: amount, state, delegate_tag, native_tag, close_tag, type, tlv, length, mint, owner."""
    d = bytearray(165)
    d[0:32] = bytes(spec.get("mint", mint))
    d[32:64] = bytes(spec.get("owner", owner))
    d[64:72] = spec.get("amount", AMOUNT).to_bytes(8, "little")
    d[72:76] = spec.get("delegate_tag", 0).to_bytes(4, "little")
    d[108] = spec.get("state", 1)
    d[109:113] = spec.get("native_tag", 0).to_bytes(4, "little")
    d[129:133] = spec.get("close_tag", 0).to_bytes(4, "little")
    if spec.get("type") is not None:
        d.append(spec["type"])
    d += spec.get("tlv", b"")
    length = spec.get("length", len(d))
    return bytes(d[:length] + bytes(max(0, length - len(d))))


class World:
    def __init__(self, image, case):
        vm = LiteSVM().with_transaction_history(0)
        vm.add_program_from_file(PROGRAM, image)
        vm.set_clock(Clock(1000, 0, 0, 0, START))
        vm.set_account(USER.pubkey(), Account(10**12, b"", SYSTEM))
        vm.set_account(VAULT, Account(10**6, b"", SYSTEM))
        legacy = case.get("legacy", False)
        self.mint = MINTLEG if legacy else MINT22
        self.tprog = TOKEN if legacy else TOKEN22
        vm.set_account(MINT22, Account(10**9, mint_bytes(), TOKEN22))
        vm.set_account(MINTLEG, Account(10**9, mint_bytes(), TOKEN))
        vm.set_account(MINTX, Account(10**9, mint_bytes(), TOKEN22))
        owners = {"token": TOKEN, "token22": TOKEN22, "system": SYSTEM}
        self.vault_ata = ata(VAULT, self.mint, self.tprog)
        self.user_ata = ata(USER.pubkey(), self.mint, self.tprog)
        vspec, uspec = case.get("vault", {}), case.get("user", {"amount": 0})
        self.vault_data = account_bytes(self.mint, VAULT, vspec)
        self.user_data = account_bytes(self.mint, USER.pubkey(), uspec)
        vm.set_account(self.vault_ata, Account(RENT_LAMPORTS, self.vault_data,
                                               owners[vspec.get("acct_owner", "token" if legacy else "token22")]))
        vm.set_account(self.user_ata, Account(RENT_LAMPORTS, self.user_data,
                                              owners[uspec.get("acct_owner", "token" if legacy else "token22")]))
        self.vm = vm

    def amounts(self):
        out = {}
        for label, key in (("vault_ata", self.vault_ata), ("user_ata", self.user_ata)):
            d = bytes(self.vm.get_account(key).data)
            out[label] = {"amount": int.from_bytes(d[64:72], "little") if len(d) >= 72 else None,
                          "sha256": hashlib.sha256(d).hexdigest(), "len": len(d)}
        return out

    def send(self):
        metas = [AccountMeta(USER.pubkey(), True, True), AccountMeta(VAULT, False, True),
                 AccountMeta(self.mint, False, False), AccountMeta(self.vault_ata, False, True),
                 AccountMeta(self.user_ata, False, True), AccountMeta(self.tprog, False, False),
                 AccountMeta(SYSTEM, False, False), AccountMeta(EVENT, False, False), AccountMeta(PROGRAM, False, False)]
        ix = Instruction(PROGRAM, IX_WITHDRAW, metas)
        vm = self.vm
        tx = Transaction.new_signed_with_payer([ix], USER.pubkey(), [USER], vm.latest_blockhash())
        before = self.amounts()
        result = vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        after = self.amounts()
        logs = list(meta.logs())
        return {"error": str(result.err()) if failed else None,
                "compute_units": meta.compute_units_consumed(),
                "logs": logs,
                "token_deltas": {k: (after[k]["amount"] or 0) - (before[k]["amount"] or 0) for k in after},
                "accounts_after": after}


def cases():
    out = []

    def add(name, note, **case):
        out.append({"name": name, "note": note, **case})

    def V(**spec):
        return {"vault": spec}

    # l-*: vault_ata length and account-type byte (Token-2022).
    add("l-165-base", "165-byte base account (control)")
    add("l-164", "vault_ata truncated to 164 bytes", **V(length=164))
    add("l-166-type-account", "type byte 2 at 165, nothing after", **V(type=2))
    add("l-167-type-account", "type byte 2 + one zero byte", **V(type=2, length=167))
    add("l-170-type-account", "type byte 2 + four zero bytes", **V(type=2, length=170))
    add("l-355-multisig-length", "type byte 2, zero tail, 355 bytes", **V(type=2, length=355))
    add("l-356-type-account", "type byte 2, zero tail, 356 bytes", **V(type=2, length=356))
    add("l-166-zero-type", "166 bytes, type byte 0", **V(type=0))
    for b in [0, 1, 3, 255]:
        add(f"t-type-{b}", f"type byte {b} at 165, four zero bytes after it", **V(type=b, length=170))
    # s-*: base-field state and COption tags.
    add("s-state-0", "state 0 (Uninitialized)", **V(state=0))
    add("s-state-2-frozen", "state 2 (Frozen)", **V(state=2))
    add("s-state-3", "state 3 (no variant)", **V(state=3))
    add("s-delegate-tag-2", "delegate COption tag 2", **V(delegate_tag=2))
    add("s-native-tag-1", "is_native COption tag 1 on a non-native mint", **V(native_tag=1))
    add("s-native-tag-2", "is_native COption tag 2", **V(native_tag=2))
    add("s-close-tag-2", "close_authority COption tag 2", **V(close_tag=2))
    add("s-delegate-tag-1", "delegate COption tag 1 (zero delegate key)", **V(delegate_tag=1))
    # e-*: TLV extension area after type 2.
    add("e-immutable-owner", "type 2 + ImmutableOwner (type 7, length 0)", **V(type=2, tlv=tlv(7, 0)))
    add("e-transfer-fee-amount", "type 2 + TransferFeeAmount (type 2, length 8)", **V(type=2, tlv=tlv(2, 8)))
    add("e-mint-extension-in-account", "type 2 + TransferFeeConfig (mint-side, type 1, length 108)",
        **V(type=2, tlv=tlv(1, 108)))
    add("e-unknown-type-65535", "type 2 + extension type 65535, length 0", **V(type=2, tlv=tlv(65535, 0)))
    add("e-length-past-end", "type 2 + ImmutableOwner declaring length 8 with 2 bytes present",
        **V(type=2, tlv=tlv(7, 8)[:6]))
    add("e-partial-header-2", "type 2 + two TLV header bytes", **V(type=2, tlv=b"\x07\x00"))
    add("e-duplicate", "type 2 + ImmutableOwner twice", **V(type=2, tlv=tlv(7, 0) + tlv(7, 0)))
    add("e-entry-then-garbage", "type 2 + ImmutableOwner + 3 bytes 0xEE", **V(type=2, tlv=tlv(7, 0) + b"\xee" * 3))
    # a-*: decoded amount and token::* constraints on decoded fields.
    add("a-amount-0", "vault amount 0", **V(amount=0))
    add("a-amount-u64-max", "vault amount u64::MAX (more than the mint supply)", **V(amount=2**64 - 1))
    add("a-amount-1-extended", "vault amount 1, type 2 + ImmutableOwner", **V(amount=1, type=2, tlv=tlv(7, 0)))
    add("a-mint-field-other", "vault mint field = another Token-2022 mint", **V(mint=MINTX))
    add("a-owner-field-user", "vault owner field = USER instead of the referral vault", **V(owner=USER.pubkey()))
    add("a-owner-field-other-extended", "vault owner field = OTHER, type 2 layout", **V(owner=OTHER, type=2, length=170))
    # u-*: the destination user_ata goes through the same decoder.
    add("u-user-170-type-account", "user_ata type 2 + four zero bytes", user={"amount": 0, "type": 2, "length": 170})
    add("u-user-166-type-account", "user_ata type 2 only (166 bytes)", user={"amount": 0, "type": 2})
    add("u-user-unknown-ext", "user_ata type 2 + extension type 65535",
        user={"amount": 0, "type": 2, "tlv": tlv(65535, 0)})
    add("u-user-state-2-frozen", "user_ata state 2 (Frozen)", user={"amount": 0, "state": 2})
    add("u-user-type-1", "user_ata type byte 1 (Mint) at 170 bytes", user={"amount": 0, "type": 1, "length": 170})
    # o-*: legacy SPL Token owner with the same layouts (mint and token_program are SPL Token).
    add("o-token-165-base", "SPL Token: 165-byte base account (control)", legacy=True)
    add("o-token-170-type-account", "SPL Token: vault with type 2 + four zero bytes", legacy=True,
        **V(type=2, length=170))
    add("o-token-166-type-account", "SPL Token: vault with type 2 only", legacy=True, **V(type=2))
    add("o-token-immutable-owner", "SPL Token: vault type 2 + ImmutableOwner", legacy=True,
        **V(type=2, tlv=tlv(7, 0)))
    add("o-token-user-170", "SPL Token: user_ata with type 2 + four zero bytes", legacy=True,
        user={"amount": 0, "type": 2, "length": 170})
    add("o-system-owned-vault", "vault_ata owned by System", **V(acct_owner="system"))
    add("o-token-owned-vault-t22-program", "vault_ata owned by SPL Token, token_program Token-2022",
        **V(acct_owner="token"))
    return out


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def comparable(row):
    out = dict(row)
    out.pop("compute_units")
    out["logs"] = [l for l in row["logs"] if " consumed " not in l]
    return out


def outcome(row):
    """Short form for the README table: who failed and with what."""
    if row["error"] is None:
        return "success"
    for line in row["logs"]:
        if "Error Code:" in line:
            name = line.split("Error Code: ")[1].split(".")[0]
            if "AnchorError" in line:
                return line.split("Error Number: ")[1].split(".")[0] + " " + name
            return "ProgramError " + name
    token_fail = [l for l in row["logs"] if l.startswith("Program Token") and " failed: " in l]
    if token_fail:
        prog = "Token-2022" if token_fail[0].startswith("Program TokenzQ") else "SPL Token"
        return f"{prog} CPI: " + token_fail[0].split(" failed: ")[1]
    return row["error"]


def build(images):
    receipts, summary = [], []
    for case in cases():
        o = World(images["original"], case).send()
        c = World(images["candidate"], case).send()
        w = World(images["original"], case)
        summary.append({"case": case["name"], "note": case["note"], "owner": "token" if case.get("legacy") else "token22",
                        "vault_len": len(w.vault_data), "user_len": len(w.user_data),
                        "behavior_match": comparable(o) == comparable(c),
                        "logs_identical": o["logs"] == c["logs"], "cu_equal": o["compute_units"] == c["compute_units"],
                        "outcome_original": outcome(o), "outcome_candidate": outcome(c),
                        "user_received": o["token_deltas"]["user_ata"],
                        "cu_original": o["compute_units"], "cu_candidate": c["compute_units"]})
        receipts.append({"case": case["name"], "vault_sha256": hashlib.sha256(w.vault_data).hexdigest(),
                         "user_sha256": hashlib.sha256(w.user_data).hexdigest(), "original": o, "candidate": c})
    blob = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in receipts).encode()
    report = {"scope": "pump_fees withdraw InterfaceAccount<TokenAccount> decoding, one transaction per case on a "
                       "fresh LiteSVM per image (LiteSVM-bundled SPL Token / Token-2022 programs).",
              "original_sha256": sha256_file(images["original"]), "candidate_sha256": sha256_file(images["candidate"]),
              "receipts_sha256": hashlib.sha256(blob).hexdigest(), "case_count": len(summary),
              "behavior_mismatches": [s["case"] for s in summary if not s["behavior_match"]],
              "log_or_cu_differences": [s["case"] for s in summary if not (s["logs_identical"] and s["cu_equal"])],
              "cases": summary}
    return blob, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--images", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    blob, report = build(json.loads(args.images))
    out = pathlib.Path(args.out) / "runtime"
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipts.jsonl.gz").write_bytes(gzip.compress(blob, compresslevel=9, mtime=0))
    (out / "report.json.gz").write_bytes(
        gzip.compress(json.dumps(report, sort_keys=True, indent=1).encode() + b"\n", compresslevel=9, mtime=0))
    print(json.dumps({k: report[k] for k in ["case_count", "behavior_mismatches", "log_or_cu_differences"]}))


if __name__ == "__main__":
    main()
