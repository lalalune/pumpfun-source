"""Captured Pump global-admin instructions against the recovered host.

The host is the claim. The captured ELF is the evidence. Agreement here is
behavioral on synthetic Global accounts, not a byte-identity or score.py result.

Attribution: SpaceXAI grok-4.7-high-fast, Cursor cloud agent.
"""
import base64
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
ELF = ROOT / "evidence/original/pump/deployed.so"
ELF_SHA256 = "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
IDL = json.loads((ROOT / "evidence/upstream/pump.json").read_text())
PROGRAM = Pubkey.from_string(IDL["address"])
DISC = {item["name"]: bytes(item["discriminator"]) for item in IDL["instructions"]}
GLOBAL_DISC = bytes([167, 232, 232, 177, 200, 108, 114, 127])
GLOBAL = Pubkey.find_program_address([b"global"], PROGRAM)[0]
EVENT = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]
AUTH = Keypair.from_seed(bytes([201]) * 32)
PAYER = Keypair.from_seed(bytes([203]) * 32)
WSOL = Pubkey.from_string("So11111111111111111111111111111111111111112")
USDC = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
TOKENZ = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
OTHER = Pubkey.from_bytes(bytes([77]) * 32)
ALT = Pubkey.from_bytes(bytes([90]) * 32)
TIMESTAMP = 1_700_000_000
FLAG_NAMES = (
    "present",
    "owner_ok",
    "is_pda",
    "global_writable",
    "authority_signer",
    "authority_matches",
    "authority_writable",
    "event_present",
    "event_is_pda",
    "program_present",
    "program_is_pump",
)


def flags(**overrides):
    value = 0
    for bit, name in enumerate(FLAG_NAMES):
        if overrides.get(name, True):
            value |= 1 << bit
    return value


def global_data(length=1088, **fields):
    data = bytearray(length)
    if length >= 8:
        data[:8] = GLOBAL_DISC if fields.get("disc", True) else bytes(8)
    if length >= 41:
        data[9:41] = bytes(fields.get("authority", AUTH.pubkey()))
    recipients = fields.get("recipients")
    if recipients and length >= 997:
        blob = b"".join(bytes(key) for key in recipients)
        data[741:741 + len(blob)] = blob
    if length >= 1005:
        data[997:1005] = int(fields.get("bps", 0)).to_bytes(8, "little")
    if length >= 1013:
        data[1005:1013] = int(fields.get("reserves", 0)).to_bytes(8, "little")
    whitelist = fields.get("whitelist")
    if whitelist is not None and length >= 1045:
        data[1013:1045] = bytes(whitelist)
    if length > 1045:
        data[1045] = fields.get("configurable", 0)
    if length >= 1054:
        data[1046:1054] = int(fields.get("max_fee", 0)).to_bytes(8, "little")
    if length >= 1086:
        holder = fields.get("holder")
        if holder is not None:
            data[1054:1086] = bytes(holder)
    if length > 1086:
        data[1086] = fields.get("holder_on", 0)
    if length > 1087:
        data[1087] = fields.get("depth", 0)
    tail = fields.get("tail", b"")
    if tail:
        data[1088:1088 + len(tail)] = tail
    return bytes(data)


def eight():
    return [Pubkey.from_bytes(bytes([10 + i]) * 32) for i in range(8)]


def case(name, ix, arg, data, remaining=(), admission=None, log_has=None, log_name=None):
    return {
        "name": name,
        "ix": ix,
        "arg": arg,
        "data": data,
        "remaining": list(remaining),
        "flags": flags(**(admission or {})),
        "admission": admission or {},
        "log_has": log_has,
        "log_name": log_name,
    }


def business_cases():
    minted = global_data(whitelist=USDC)
    wsol_slot = global_data(whitelist=WSOL)
    keys = eight()
    duplicated = list(keys)
    duplicated[7] = duplicated[0]
    zeroed = list(keys)
    zeroed[3] = Pubkey.default()
    both = list(keys)
    both[0] = Pubkey.default()
    both[1] = Pubkey.default()
    rows = [
        case("add-usdc", "add_quote_mint", bytes(USDC), global_data(), log_name="Instruction: AddQuoteMint"),
        case("add-token2022-native", "add_quote_mint", bytes(TOKENZ), global_data(), log_name="Instruction: AddQuoteMint"),
        case("add-other", "add_quote_mint", bytes(OTHER), global_data()),
        case("add-zero", "add_quote_mint", bytes(32), global_data(), log_has="programs/pump/src/lib.rs:1950"),
        case("add-wsol", "add_quote_mint", bytes(WSOL), global_data(), log_has="programs/pump/src/lib.rs:1955"),
        case("add-dup", "add_quote_mint", bytes(USDC), minted, log_has="programs/pump/src/lib.rs:1960"),
        case("add-full", "add_quote_mint", bytes(OTHER), minted, log_has="programs/pump/src/lib.rs:1971"),
        case("add-trailing", "add_quote_mint", bytes(USDC) + b"\x00", global_data()),
        case("add-short", "add_quote_mint", bytes(USDC)[:-1], global_data()),
        case("add-ignores-extra-account", "add_quote_mint", bytes(USDC), global_data(), [OTHER]),
        case("add-long-keeps-tail", "add_quote_mint", bytes(USDC), global_data(length=1089, tail=b"\xee")),
        case("add-uninit-bool", "add_quote_mint", bytes(OTHER), global_data()),
        case("remove-usdc", "remove_quote_mint", bytes(USDC), minted, log_name="Instruction: RemoveQuoteMint"),
        case("remove-wsol-present", "remove_quote_mint", bytes(WSOL), wsol_slot),
        case("remove-wsol-absent", "remove_quote_mint", bytes(WSOL), global_data(), log_has="programs/pump/src/lib.rs:1986"),
        case("remove-missing", "remove_quote_mint", bytes(OTHER), global_data(), log_has="programs/pump/src/lib.rs:1986"),
        case("remove-zero", "remove_quote_mint", bytes(32), global_data(), log_has="programs/pump/src/lib.rs:1975"),
        case("remove-short", "remove_quote_mint", b"\x01" * 31, global_data()),
        case("buyback-none", "update_buyback_config", b"\x00", global_data(bps=7), log_name="Instruction: UpdateBuybackConfig"),
        case("buyback-none-trailing", "update_buyback_config", b"\x00\xff", global_data(bps=7)),
        case("buyback-zero-bps", "update_buyback_config", b"\x01" + (0).to_bytes(8, "little"), global_data(bps=7)),
        case("buyback-max-bps", "update_buyback_config", b"\x01" + (10000).to_bytes(8, "little"), global_data(bps=7)),
        case("buyback-bps-range", "update_buyback_config", b"\x01" + (10001).to_bytes(8, "little"), global_data(bps=7), log_has="programs/pump/src/lib.rs:1870"),
        case("buyback-bps-maxint", "update_buyback_config", b"\x01" + (2**64 - 1).to_bytes(8, "little"), global_data(bps=7)),
        case("buyback-bad-tag", "update_buyback_config", b"\x02" + (1).to_bytes(8, "little"), global_data()),
        case("buyback-empty", "update_buyback_config", b"", global_data()),
        case("buyback-truncated", "update_buyback_config", b"\x01\x01\x00", global_data()),
        case("buyback-eight", "update_buyback_config", b"\x00", global_data(bps=7), keys),
        case("buyback-eight-and-bps", "update_buyback_config", b"\x01" + (42).to_bytes(8, "little"), global_data(bps=7), keys),
        case("buyback-zero-recipient", "update_buyback_config", b"\x00", global_data(bps=7), zeroed, log_has="programs/pump/src/lib.rs:1895"),
        case("buyback-duplicate-ends", "update_buyback_config", b"\x00", global_data(bps=7), duplicated, log_has="programs/pump/src/lib.rs:1905"),
        case("buyback-zero-before-dup", "update_buyback_config", b"\x00", global_data(), both, log_has="programs/pump/src/lib.rs:1895"),
        case("buyback-one", "update_buyback_config", b"\x00", global_data(), keys[:1], log_has="programs/pump/src/set_reserved_fee_recipients.rs:121"),
        case("buyback-seven", "update_buyback_config", b"\x00", global_data(), keys[:7]),
        case("buyback-nine", "update_buyback_config", b"\x00", global_data(), keys + [OTHER]),
        case("buyback-range-before-count", "update_buyback_config", b"\x01" + (10001).to_bytes(8, "little"), global_data(bps=7), keys[:1], log_has="programs/pump/src/lib.rs:1870"),
        case("buyback-range-before-write", "update_buyback_config", b"\x01" + (10001).to_bytes(8, "little"), global_data(bps=7), keys),
        case("depth-zero", "set_max_curve_depth", bytes([0]), global_data(depth=9), log_name="Instruction: SetMaxCurveDepth"),
        case("depth-255", "set_max_curve_depth", bytes([255]), global_data()),
        case("depth-extra", "set_max_curve_depth", bytes([3, 1]), global_data()),
        case("depth-empty", "set_max_curve_depth", b"", global_data()),
        case("reserves-zero", "set_virtual_quote_reserves", (0).to_bytes(8, "little"), global_data(reserves=5), log_name="Instruction: SetVirtualQuoteReserves"),
        case("reserves-max", "set_virtual_quote_reserves", (2**64 - 1).to_bytes(8, "little"), global_data()),
        case("reserves-short", "set_virtual_quote_reserves", b"\x01\x00", global_data()),
        case("creator-5000", "update_creator_fee_config", bytes([1]) + (5000).to_bytes(8, "little"), global_data(), log_name="Instruction: UpdateCreatorFeeConfig"),
        case("creator-above-10000", "update_creator_fee_config", bytes([1]) + (10001).to_bytes(8, "little"), global_data()),
        case("creator-clear", "update_creator_fee_config", bytes([0]) + (0).to_bytes(8, "little"), global_data(configurable=1, max_fee=9)),
        case("creator-trailing", "update_creator_fee_config", bytes([1]) + (5).to_bytes(8, "little") + b"\xff", global_data()),
        case("creator-bad-bool", "update_creator_fee_config", bytes([2]) + (1).to_bytes(8, "little"), global_data()),
        case("creator-short-fee", "update_creator_fee_config", bytes([1]) + b"\x01\x00", global_data()),
        case("holder-on", "update_holder_reward_config", bytes([1]) + bytes(OTHER), global_data(), log_name="Instruction: UpdateHolderRewardConfig"),
        case("holder-off", "update_holder_reward_config", bytes([0]) + bytes(32), global_data(holder=OTHER, holder_on=1)),
        case("holder-bad-bool", "update_holder_reward_config", bytes([2]) + bytes(OTHER), global_data()),
        case("holder-short", "update_holder_reward_config", bytes([1]) + bytes(OTHER)[:-1], global_data()),
    ]
    # The initialized bool is not an admission bit. Keep the byte clear and still succeed.
    cleared = bytearray(global_data())
    cleared[8] = 0
    rows[rows.index(next(row for row in rows if row["name"] == "add-uninit-bool"))]["data"] = bytes(cleared)
    return rows


def admission_cases():
    body = global_data()
    usdc = bytes(USDC)
    rows = [
        case("two-accounts", "add_quote_mint", usdc, body, admission={"event_present": False, "program_present": False}),
        case("three-accounts", "add_quote_mint", usdc, body, admission={"program_present": False}),
        case("bad-event", "add_quote_mint", usdc, body, admission={"event_is_pda": False}),
        case("unchecked-program-account", "add_quote_mint", usdc, body, admission={"program_is_pump": False}, log_name="Instruction: AddQuoteMint"),
        case("global-readonly", "add_quote_mint", usdc, body, admission={"global_writable": False}),
        case("authority-readonly", "add_quote_mint", usdc, body, admission={"authority_writable": False}),
        case("authority-unsigned", "add_quote_mint", usdc, body, admission={"authority_signer": False}),
        case("wrong-authority", "add_quote_mint", usdc, global_data(authority=PAYER.pubkey()), admission={"authority_matches": False}),
        case("wrong-pda", "add_quote_mint", usdc, body, admission={"is_pda": False}),
        case("wrong-owner", "add_quote_mint", usdc, body, admission={"owner_ok": False}),
        case("bad-disc", "add_quote_mint", usdc, global_data(disc=False)),
        case("len-0", "add_quote_mint", usdc, global_data(length=0)),
        case("len-7", "add_quote_mint", usdc, global_data(length=7)),
        case("len-8", "add_quote_mint", usdc, global_data(length=8)),
        case("len-8-bad-disc", "add_quote_mint", usdc, global_data(length=8, disc=False)),
        case("len-1087", "add_quote_mint", usdc, global_data(length=1087)),
        case("missing-global", "add_quote_mint", usdc, body, admission={"present": False}),
        case("depth-two-accounts", "set_max_curve_depth", bytes([1]), body, admission={"event_present": False, "program_present": False}),
        case("short-arg-beats-disc", "add_quote_mint", usdc[:-1], global_data(disc=False)),
        case("short-arg-beats-signer", "add_quote_mint", usdc[:-1], body, admission={"authority_signer": False}),
        case("short-arg-beats-keys", "add_quote_mint", b"", body, admission={"event_present": False, "program_present": False}),
        case("owner-beats-disc", "add_quote_mint", usdc, global_data(disc=False), admission={"owner_ok": False}),
        case("owner-beats-short", "add_quote_mint", usdc, global_data(length=4), admission={"owner_ok": False}),
        case("disc-beats-mut", "add_quote_mint", usdc, global_data(disc=False), admission={"global_writable": False}),
        case("signer-beats-has-one", "add_quote_mint", usdc, global_data(authority=PAYER.pubkey()), admission={"authority_signer": False, "authority_matches": False}),
        case("signer-beats-missing-event", "add_quote_mint", usdc, body, admission={"authority_signer": False, "event_present": False, "program_present": False}),
        case("key-count-beats-event-seeds", "add_quote_mint", usdc, body, admission={"event_is_pda": False, "program_present": False}),
        case("disc-beats-seeds", "add_quote_mint", usdc, global_data(disc=False), admission={"is_pda": False}),
        case("signer-beats-seeds", "add_quote_mint", usdc, body, admission={"authority_signer": False, "is_pda": False}),
        case("seeds-beat-mut", "add_quote_mint", usdc, body, admission={"is_pda": False, "global_writable": False}),
        case("global-mut-beats-event-seeds", "add_quote_mint", usdc, body, admission={"global_writable": False, "event_is_pda": False}),
        case("authority-mut-beats-event-seeds", "add_quote_mint", usdc, body, admission={"authority_writable": False, "event_is_pda": False}),
        case("has-one-beats-authority-mut", "add_quote_mint", usdc, global_data(authority=PAYER.pubkey()), admission={"authority_matches": False, "authority_writable": False}),
        case("seeds-beat-has-one", "add_quote_mint", usdc, global_data(authority=PAYER.pubkey()), admission={"is_pda": False, "authority_matches": False}),
        case("key-count-beats-seeds", "set_virtual_quote_reserves", (1).to_bytes(8, "little"), body, admission={"is_pda": False, "program_present": False}),
        case("creator-wrong-program", "update_creator_fee_config", bytes([1]) + (5000).to_bytes(8, "little"), global_data(), admission={"program_is_pump": False}),
    ]
    return rows


def field_hex(raw):
    return raw.hex() if raw else "-"


def host_line(row):
    remaining = b"".join(bytes(key) for key in row["remaining"])
    return "{} {} {} {} {} {}".format(
        row["ix"],
        row["flags"],
        TIMESTAMP,
        field_hex(row["arg"]),
        field_hex(row["data"]),
        field_hex(remaining),
    )


def run_captured(row):
    admission = row["admission"]
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PROGRAM, ELF)
    vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    vm.airdrop(PAYER.pubkey(), 10**10)
    vm.airdrop(AUTH.pubkey(), 10**10)
    global_key = GLOBAL if admission.get("is_pda", True) else ALT
    if admission.get("present", True):
        owner = PROGRAM if admission.get("owner_ok", True) else Pubkey.default()
        vm.set_account(global_key, Account(10**9, row["data"], owner))
    event_key = EVENT if admission.get("event_is_pda", True) else ALT
    program_key = PROGRAM if admission.get("program_is_pump", True) else OTHER
    metas = [
        AccountMeta(global_key, False, admission.get("global_writable", True)),
        AccountMeta(AUTH.pubkey(), admission.get("authority_signer", True), admission.get("authority_writable", True)),
    ]
    if admission.get("event_present", True):
        metas.append(AccountMeta(event_key, False, False))
    if admission.get("program_present", True):
        metas.append(AccountMeta(program_key, False, False))
    for key in row["remaining"]:
        metas.append(AccountMeta(key, False, False))
    signers = [PAYER]
    if admission.get("authority_signer", True):
        signers.append(AUTH)
    ix = Instruction(PROGRAM, DISC[row["ix"]] + row["arg"], metas)
    tx = Transaction.new_signed_with_payer([ix], PAYER.pubkey(), signers, vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    account = vm.get_account(global_key)
    observed = None if account is None else bytes(account.data)
    events = []
    for line in meta.logs():
        if line.startswith("Program data: "):
            events.append(base64.b64decode(line.split(": ", 1)[1]))
    return {
        "err": str(result.err()) if failed else None,
        "data": observed,
        "events": events,
        "logs": meta.logs(),
    }


class GlobalAdminCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        digest = hashlib.sha256(ELF.read_bytes()).hexdigest()
        if digest != ELF_SHA256:
            raise AssertionError(digest)
        with tempfile.TemporaryDirectory(prefix="pump-global-admin-") as temporary:
            host = Path(temporary) / "pump-global-admin-host"
            subprocess.run(
                ["rustc", "--edition=2021", "-O", str(ROOT / "programs/pump/recovered/global_admin_host.rs"), "-o", str(host)],
                check=True,
            )
            cls.rows = business_cases() + admission_cases()
            completed = subprocess.run(
                [str(host)],
                input="".join(host_line(row) + "\n" for row in cls.rows),
                text=True,
                capture_output=True,
                check=True,
            )
        cls.host = completed.stdout.splitlines()
        if len(cls.host) != len(cls.rows):
            raise AssertionError(completed.stderr)

    def test_host_matches_captured_program(self):
        for row, answer in zip(self.rows, self.host):
            with self.subTest(name=row["name"]):
                observed = run_captured(row)
                self.assert_outcome(row, answer, observed)

    def assert_outcome(self, row, answer, observed):
        logs = "\n".join(observed["logs"])
        if row["log_has"]:
            self.assertIn(row["log_has"], logs)
        if row["log_name"]:
            self.assertIn(row["log_name"], logs)
        if answer == "missing":
            self.assertIn("MissingAccount", observed["err"] or "")
            self.assertEqual(observed["data"], row["data"])
            self.assertTrue(any(line.startswith("Program data: ") for line in observed["logs"]))
            return
        if answer.startswith("err "):
            code = answer.split()[1]
            self.assertIn(f"InstructionErrorCustom({code})", observed["err"] or "", logs)
            if observed["data"] is not None:
                self.assertEqual(observed["data"], row["data"])
            else:
                self.assertFalse(row["admission"].get("present", True))
            return
        self.assertIsNone(observed["err"], logs)
        kind, data_hex, event_hex = answer.split()
        self.assertEqual(kind, "ok")
        self.assertEqual(observed["data"].hex(), data_hex)
        if event_hex == "-":
            self.assertEqual(observed["events"], [])
        else:
            self.assertEqual([event.hex() for event in observed["events"]], [event_hex])


if __name__ == "__main__":
    unittest.main()
