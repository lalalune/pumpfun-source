#!/usr/bin/env python3
"""Pump Fees: Token-2022 mint layout decoding boundaries, on two images.

Every pump_fees handler that takes a mint declares it as
`InterfaceAccount<token_interface::Mint>`. Anchor decodes such an account with
the spl-token-2022 `StateWithExtensions::<Mint>::unpack` routine that is linked
into the pump_fees binary, whichever token program owns the account. This
packet measures that decoder (and the owner check in front of it) on byte
layouts that a real token program never produces but that the decoder must
still accept or reject: lengths around 82 / 165 / 166 / 355, the account-type
byte, padding, the base-field COption/bool tags, and the TLV extension area.

The host is `admin_cto_sharing_config`. It makes no CPI, so only the pump_fees
image is loaded. Its pool_authority account is a pump PDA and cannot sign, so
each transaction runs with LiteSVM signature verification off; the wallets
that can sign still sign (Transaction.new_unsigned + partial_sign). Every case
runs one transaction on a fresh LiteSVM per image: the mint account is the
only input that changes. Fixed keypair seeds, fixed clock, no wall time and
no paths in the results.

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
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
SYSTEM = Pubkey.default()
EVENT = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]
PUMP_GLOBAL = Pubkey.find_program_address([b"global"], PUMP)[0]

AUTH = Keypair.from_seed(bytes([241]) * 32)
OTHER = Keypair.from_seed(bytes([242]) * 32)
PAYER = Keypair.from_seed(bytes([243]) * 32)
THIRD = Keypair.from_seed(bytes([244]) * 32)
WALLETS = [AUTH, OTHER, PAYER, THIRD]
MINT = Pubkey.from_bytes(bytes([91]) * 32)
MINT_AUTH = Pubkey.from_bytes(bytes([92]) * 32)
SHARING, SHARING_BUMP = Pubkey.find_program_address([b"sharing-config", bytes(MINT)], PROGRAM)
POOL_AUTH = Pubkey.find_program_address([b"pool-authority", bytes(MINT)], PUMP)[0]
START = 1_700_000_000
GLOBAL_LEN = 1088  # pump Global; admin_set_creator_authority at [418, 450)


def disc(kind, name):
    return hashlib.sha256(f"{kind}:{name}".encode()).digest()[:8]


IX_CTO = disc("global", "admin_cto_sharing_config")


def pump_global_bytes():
    data = bytearray(GLOBAL_LEN)
    data[0:8] = disc("account", "Global")
    data[8] = 1
    data[418:450] = bytes(AUTH.pubkey())
    return bytes(data)


def sharing_bytes():
    """SharingConfig v1, Active, admin OTHER, one shareholder OTHER at 10,000 bps, 1,024 bytes."""
    data = disc("account", "SharingConfig") + bytes([SHARING_BUMP, 1, 1]) + bytes(MINT)
    data += bytes(OTHER.pubkey()) + bytes([0]) + (1).to_bytes(4, "little") + bytes(OTHER.pubkey())
    data += (10000).to_bytes(2, "little")
    return data + bytes(1024 - len(data))


def tlv(ext_type, length, value=None):
    """One TLV entry: u16 type, u16 length, value (zeros of `length` unless given)."""
    value = bytes(length) if value is None else value
    return ext_type.to_bytes(2, "little") + length.to_bytes(2, "little") + value


# TransferFeeConfig (type 1, 108 bytes): two authorities, withheld u64, two TransferFee
# {epoch u64, maximum_fee u64, basis_points u16}.
TRANSFER_FEE_CONFIG = (bytes([5]) * 32 + bytes([6]) * 32 + (0).to_bytes(8, "little")
                       + ((0).to_bytes(8, "little") + (5000).to_bytes(8, "little") + (100).to_bytes(2, "little")) * 2)
# MintCloseAuthority (type 3, 32 bytes).
CLOSE_AUTH = bytes([7]) * 32


def mint_bytes(spec):
    """82-byte base Mint, then (if length > 82) zero padding to 165, the account-type byte at 165
    and a TLV area. spec keys: length, init, auth_tag, freeze_tag, decimals, supply, type, tlv, pad."""
    base = bytearray(82)
    base[0:4] = spec.get("auth_tag", 1).to_bytes(4, "little")
    base[4:36] = bytes(MINT_AUTH)
    base[36:44] = spec.get("supply", 1_000_000).to_bytes(8, "little")
    base[44] = spec.get("decimals", 6)
    base[45] = spec.get("init", 1)
    base[46:50] = spec.get("freeze_tag", 0).to_bytes(4, "little")
    data = bytearray(base)
    if "type" in spec or "tlv" in spec:
        data += bytes(165 - 82)
        if spec.get("type") is not None:
            data.append(spec["type"])
        data += spec.get("tlv", b"")
    length = spec.get("length", len(data))
    data = data[:length] + bytes(max(0, length - len(data)))
    for offset, value in spec.get("pad", {}).items():
        data[int(offset)] = value
    return bytes(data)


class World:
    def __init__(self, image, mint_spec):
        vm = LiteSVM().with_transaction_history(0).with_sigverify(False)
        vm.add_program_from_file(PROGRAM, image)
        vm.set_clock(Clock(1000, 0, 0, 0, START))
        for kp in WALLETS:
            vm.set_account(kp.pubkey(), Account(10**12, b"", SYSTEM))
        vm.set_account(PUMP_GLOBAL, Account(10**9, pump_global_bytes(), PUMP))
        vm.set_account(SHARING, Account(10**8, sharing_bytes(), PROGRAM))
        owner = {"token": TOKEN, "token22": TOKEN22, "system": SYSTEM}[mint_spec.get("owner", "token22")]
        self.mint_data = mint_bytes(mint_spec)
        vm.set_account(MINT, Account(10**9, self.mint_data, owner))
        self.vm = vm

    def send(self):
        metas = [AccountMeta(POOL_AUTH, True, False), AccountMeta(AUTH.pubkey(), True, False),
                 AccountMeta(PUMP_GLOBAL, False, False), AccountMeta(MINT, False, False),
                 AccountMeta(SHARING, False, True), AccountMeta(EVENT, False, False),
                 AccountMeta(PROGRAM, False, False)]
        ix = Instruction(PROGRAM, IX_CTO + b"\x01" + bytes(THIRD.pubkey()), metas)
        vm = self.vm
        blockhash = vm.latest_blockhash()
        msg = Message.new_with_blockhash([ix], PAYER.pubkey(), blockhash)
        tx = Transaction.new_unsigned(msg)
        signer_keys = list(msg.account_keys)[:msg.header.num_required_signatures]
        tx.partial_sign([kp for kp in WALLETS if kp.pubkey() in signer_keys], blockhash)
        result = vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        sharing = bytes(vm.get_account(SHARING).data)
        mint = vm.get_account(MINT)
        return {"error": str(result.err()) if failed else None,
                "compute_units": meta.compute_units_consumed(),
                "logs": list(meta.logs()),
                "sharing_sha256": hashlib.sha256(sharing).hexdigest(),
                "sharing_version": sharing[9], "sharing_admin_is_third": sharing[43:75] == bytes(THIRD.pubkey()),
                "mint_unchanged": bytes(mint.data) == self.mint_data}


def cases():
    out = []

    def add(name, note, **spec):
        out.append({"name": name, "note": note, "mint": spec})

    T = 1  # AccountType::Mint
    # l-*: account length around the base / extended boundaries (Token-2022 owner).
    add("l-82-base", "82-byte base mint (control)")
    for n in [83, 100, 164, 165]:
        add(f"l-{n}-zero-tail", f"82-byte base mint + zero tail to {n} bytes (no account-type byte)", length=n)
    add("l-166-type-mint", "zero padding to 165, account type 1 (Mint), no TLV", type=T)
    for n in [167, 168, 169]:
        add(f"l-{n}-type-mint-zero-tail", f"type 1, {n - 166} zero byte(s) after it", type=T, length=n)
    add("l-170-type-mint-zero-tlv", "type 1, four zero bytes after it (TLV type 0, length 0)", type=T, length=170)
    add("l-355-multisig-length", "type 1, zero TLV area, total 355 bytes (= Multisig::LEN)", type=T, length=355)
    add("l-354-type-mint", "type 1, zero TLV area, total 354 bytes", type=T, length=354)
    add("l-356-type-mint", "type 1, zero TLV area, total 356 bytes", type=T, length=356)
    add("l-10240-type-mint", "type 1, zero TLV area, total 10,240 bytes", type=T, length=10240)
    # t-*: the account-type byte at offset 165.
    for b, label in [(0, "uninitialized"), (2, "account"), (3, "invalid-3"), (255, "invalid-255")]:
        add(f"t-type-{b}-{label}", f"account-type byte {b} at offset 165, four zero bytes after it", type=b,
            length=170)
    add("t-type-2-with-tlv", "account-type byte 2 (Account) followed by a TransferFeeConfig entry",
        type=2, tlv=tlv(1, 108, TRANSFER_FEE_CONFIG))
    # p-*: padding bytes [82, 165) that a real mint keeps zero (170-byte accounts, type 1).
    add("p-pad-82-nonzero", "type 1, 170 bytes, padding byte 82 = 0xFF", type=T, length=170, pad={"82": 255})
    add("p-pad-164-nonzero", "type 1, 170 bytes, padding byte 164 = 0xFF", type=T, length=170, pad={"164": 255})
    add("p-pad-164-nonzero-no-type", "165-byte account (no type byte), padding byte 164 = 0xFF", length=165,
        pad={"164": 255})
    # e-*: TLV extension area.
    add("e-transfer-fee-config", "type 1 + TransferFeeConfig (type 1, length 108)", type=T,
        tlv=tlv(1, 108, TRANSFER_FEE_CONFIG))
    add("e-close-authority", "type 1 + MintCloseAuthority (type 3, length 32)", type=T, tlv=tlv(3, 32, CLOSE_AUTH))
    add("e-two-extensions", "type 1 + TransferFeeConfig + MintCloseAuthority", type=T,
        tlv=tlv(1, 108, TRANSFER_FEE_CONFIG) + tlv(3, 32, CLOSE_AUTH))
    add("e-duplicate-extension", "type 1 + MintCloseAuthority twice", type=T,
        tlv=tlv(3, 32, CLOSE_AUTH) + tlv(3, 32, CLOSE_AUTH))
    add("e-account-extension-in-mint", "type 1 + TransferFeeAmount (type 2, account-side, length 8)", type=T,
        tlv=tlv(2, 8))
    add("e-unknown-type-65535", "type 1 + extension type 65535 with length 0", type=T, tlv=tlv(65535, 0))
    add("e-unknown-type-1000-len-4", "type 1 + extension type 1000 with length 4", type=T, tlv=tlv(1000, 4))
    add("e-wrong-length-for-type", "type 1 + MintCloseAuthority declared length 31", type=T, tlv=tlv(3, 31))
    add("e-length-past-end", "type 1 + MintCloseAuthority declaring 32 bytes, 16 present", type=T,
        tlv=tlv(3, 32, CLOSE_AUTH)[:4 + 16])
    for k in [1, 2, 3]:
        add(f"e-partial-header-{k}", f"type 1 + {k} non-zero TLV header byte(s) only", type=T, tlv=b"\x03\x00\x20"[:k])
    add("e-header-only", "type 1 + TLV header (type 3, length 32) with no value bytes", type=T, tlv=tlv(3, 32)[:4])
    add("e-zero-type-then-entry", "type 1 + TLV (type 0, length 0) followed by MintCloseAuthority", type=T,
        tlv=tlv(0, 0) + tlv(3, 32, CLOSE_AUTH))
    add("e-entry-then-garbage", "type 1 + MintCloseAuthority + 3 bytes 0xEE", type=T,
        tlv=tlv(3, 32, CLOSE_AUTH) + b"\xee\xee\xee")
    # b-*: base-field tags (82-byte layout).
    add("b-init-2", "is_initialized byte 2", init=2)
    add("b-init-0", "is_initialized byte 0 (82 bytes)", init=0)
    add("b-init-0-extended", "is_initialized byte 0 with type 1 at 170 bytes", init=0, type=T, length=170)
    add("b-init-2-extended", "is_initialized byte 2 with type 1 at 170 bytes", init=2, type=T, length=170)
    add("b-auth-tag-0", "mint_authority COption tag 0 (None)", auth_tag=0)
    add("b-auth-tag-2", "mint_authority COption tag 2", auth_tag=2)
    add("b-auth-tag-256", "mint_authority COption tag 256 (low byte 0)", auth_tag=256)
    add("b-freeze-tag-1", "freeze_authority COption tag 1", freeze_tag=1)
    add("b-freeze-tag-2", "freeze_authority COption tag 2", freeze_tag=2)
    add("b-decimals-255-supply-max", "decimals 255, supply u64::MAX", decimals=255, supply=2**64 - 1)
    # o-*: the same layouts under the legacy SPL Token owner.
    add("o-token-82-base", "SPL Token owner, 82-byte base mint (control)", owner="token")
    add("o-token-166-type-mint", "SPL Token owner, extended layout with type 1, 166 bytes", owner="token", type=T)
    add("o-token-170-type-mint", "SPL Token owner, extended layout with type 1, 170 bytes", owner="token", type=T,
        length=170)
    add("o-token-transfer-fee-config", "SPL Token owner, type 1 + TransferFeeConfig", owner="token", type=T,
        tlv=tlv(1, 108, TRANSFER_FEE_CONFIG))
    add("o-token-83-zero-tail", "SPL Token owner, 83 bytes", owner="token", length=83)
    add("o-token-355-multisig-length", "SPL Token owner, type 1, 355 bytes", owner="token", type=T, length=355)
    add("o-token-type-2", "SPL Token owner, account-type byte 2, 170 bytes", owner="token", type=2, length=170)
    add("o-system-166-type-mint", "System owner, extended layout with type 1", owner="system", type=T)
    return out


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def comparable(row):
    """Fields compared between images. Compute units and the runtime 'consumed' log lines are compared separately."""
    out = dict(row)
    out.pop("compute_units")
    out["logs"] = [l for l in row["logs"] if " consumed " not in l]
    return out


def outcome(row):
    """Short form of the result for the README table."""
    if row["error"] is None:
        return "success"
    for line in row["logs"]:
        if "Error Code:" in line:
            name = line.split("Error Code: ")[1].split(".")[0]
            if "AnchorError" in line:
                return line.split("Error Number: ")[1].split(".")[0] + " " + name
            return "ProgramError " + name
    return row["error"]


def produce(images):
    receipts, summary = [], []
    for case in cases():
        o = World(images["original"], case["mint"]).send()
        c = World(images["candidate"], case["mint"]).send()
        mint_len = len(mint_bytes(case["mint"]))
        summary.append({"case": case["name"], "note": case["note"], "mint_owner": case["mint"].get("owner", "token22"),
                        "mint_len": mint_len, "behavior_match": comparable(o) == comparable(c),
                        "logs_identical": o["logs"] == c["logs"], "cu_equal": o["compute_units"] == c["compute_units"],
                        "outcome_original": outcome(o), "outcome_candidate": outcome(c),
                        "cu_original": o["compute_units"], "cu_candidate": c["compute_units"]})
        receipts.append({"case": case["name"], "mint_spec": {k: (v.hex() if isinstance(v, bytes) else v)
                                                            for k, v in case["mint"].items()},
                         "mint_sha256": hashlib.sha256(mint_bytes(case["mint"])).hexdigest(),
                         "original": o, "candidate": c})
    return receipts, summary


def build(images):
    receipts, summary = produce(images)
    blob = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in receipts).encode()
    report = {"scope": "pump_fees InterfaceAccount<Mint> decoding (admin_cto_sharing_config host), "
                       "one transaction per case on a fresh LiteSVM per image, pump_fees image only.",
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
    images = json.loads(args.images)
    blob, report = build(images)
    out = pathlib.Path(args.out) / "runtime"
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipts.jsonl.gz").write_bytes(gzip.compress(blob, compresslevel=9, mtime=0))
    (out / "report.json.gz").write_bytes(
        gzip.compress(json.dumps(report, sort_keys=True, indent=1).encode() + b"\n", compresslevel=9, mtime=0))
    print(json.dumps({k: report[k] for k in ["case_count", "behavior_mismatches", "log_or_cu_differences"]}))


if __name__ == "__main__":
    main()
