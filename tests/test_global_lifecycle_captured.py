"""Captured Pump initialize, toggles, and authority rotation versus the host.

The host is the claim. The captured ELF is the evidence. Agreement is behavior
on synthetic accounts under default rent, not a byte-identity or score result.

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
from solders.system_program import ID as SYSTEM
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
USER = Keypair.from_seed(bytes([201]) * 32)
PAYER = Keypair.from_seed(bytes([203]) * 32)
OTHER = Pubkey.from_bytes(bytes([91]) * 32)
NEW = Pubkey.from_bytes(bytes([77]) * 32)
TIMESTAMP = 1_700_000_000
RENT = 8_463_360
INIT_NAMES = (
    "user_signer", "user_writable", "global_writable", "system_ok", "is_pda",
    "global_present", "owner_is_system", "system_present", "user_present",
)
TOGGLE_NAMES = (
    "event_present", "program_present", "event_is_pda", "authority_matches",
    "authority_signer", "global_writable", "authority_writable",
)
AUTH_NAMES = (
    "event_present", "program_present", "event_is_pda", "authority_signer",
    "global_writable", "program_is_pump", "authority_matches",
)


def bitfield(names, **overrides):
    value = 0
    for bit, name in enumerate(names):
        default = name not in ("global_present", "owner_is_system")
        if overrides.get(name, default):
            value |= 1 << bit
    return value


def global_bytes(**fields):
    data = bytearray(1088)
    data[:8] = GLOBAL_DISC
    data[8] = 1
    data[9:41] = bytes(fields.get("authority", USER.pubkey()))
    data[450] = fields.get("create_v2", 0)
    data[515] = fields.get("mayhem", 0)
    data[740] = fields.get("cashback", 0)
    return bytes(data)


def hx(raw):
    return raw.hex() if raw else "-"


class GlobalLifecycleCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        digest = hashlib.sha256(ELF.read_bytes()).hexdigest()
        if digest != ELF_SHA256:
            raise AssertionError(digest)
        with tempfile.TemporaryDirectory(prefix="pump-global-lifecycle-") as temporary:
            host = Path(temporary) / "pump-global-lifecycle-host"
            subprocess.run(
                ["rustc", "--edition=2021", "-O", str(ROOT / "programs/pump/recovered/global_lifecycle_host.rs"), "-o", str(host)],
                check=True,
            )
            cls.rows = init_cases() + toggle_cases() + authority_cases()
            completed = subprocess.run(
                [str(host)],
                input="".join(row["line"] + "\n" for row in cls.rows),
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
                self.assert_row(row, answer)

    def assert_row(self, row, answer):
        observed = row["run"]()
        logs = "\n".join(observed["logs"])
        if row.get("log_has"):
            self.assertIn(row["log_has"], logs)
        if answer == "privilege":
            self.assertIn("PrivilegeEscalation", observed["err"] or "")
            self.assertEqual(observed["global"], row["global_before"])
            self.assertEqual(observed["user"], row["user_before"])
            return
        if answer == "missing":
            self.assertIn("MissingAccount", observed["err"] or "")
            self.assertEqual(observed["global_data"], row["data_before"])
            self.assertTrue(any(line.startswith("Program data: ") for line in observed["logs"]))
            return
        if answer.startswith("err "):
            code = answer.split()[1]
            self.assertIn(f"InstructionErrorCustom({code})", observed["err"] or "", logs)
            self.assertEqual(observed["global_data"], row["data_before"])
            if row["kind"] == "initialize":
                expected_user = None if row["user_before"] == 0 else row["user_before"]
                self.assertEqual(observed["user"], expected_user)
            return
        self.assertIsNone(observed["err"], logs)
        if row["kind"] == "initialize":
            _, lamports, data_hex, user = answer.split()
            self.assertEqual(observed["global_lamports"], int(lamports))
            self.assertEqual(observed["global_data"].hex(), data_hex)
            self.assertEqual(observed["owner"], PROGRAM)
            self.assertEqual(None if observed["user"] is None else observed["user"], None if user == "-" else int(user))
            self.assertIn("Instruction: Initialize", logs)
        elif row["kind"] == "toggle":
            self.assertEqual(observed["global_data"].hex(), answer.split()[1])
        else:
            _, data_hex, event_hex = answer.split()
            self.assertEqual(observed["global_data"].hex(), data_hex)
            self.assertEqual([item.hex() for item in observed["events"]], [event_hex])


def init_cases():
    user = bytes(USER.pubkey())
    rows = []

    def add(name, user_lamports, global_spec, log_has=None, **flags):
        if global_spec is not None:
            flags["global_present"] = True
            flags["owner_is_system"] = global_spec["owner"] == SYSTEM
        packed = bitfield(INIT_NAMES, **flags)
        data = b"" if global_spec is None else global_spec["data"]
        glamports = 0 if global_spec is None else global_spec["lamports"]
        line = f"initialize {packed} {user_lamports} {glamports} {user.hex()} {hx(data)}"
        rows.append({
            "name": name,
            "kind": "initialize",
            "line": line,
            "log_has": log_has,
            "user_before": user_lamports,
            "global_before": None if global_spec is None else (glamports, data, global_spec["owner"]),
            "data_before": None if global_spec is None else data,
            "run": lambda user_lamports=user_lamports, global_spec=global_spec, flags=flags: run_init(user_lamports, global_spec, flags),
        })

    add("fresh", 10**12, None, log_has="Instruction: Initialize")
    add("exact-rent", RENT, None)
    add("one-above-rent", RENT + 1, None)
    add("one-below-rent", RENT - 1, None)
    add("user-zero", 0, None)
    add("trailing", 10**12, None, trailing=True)
    add("pre-one", 10**12, {"lamports": 1, "data": b"", "owner": SYSTEM})
    add("pre-rent", 10**12, {"lamports": RENT, "data": b"", "owner": SYSTEM})
    add("pre-excess", 10**12, {"lamports": RENT + 100, "data": b"", "owner": SYSTEM})
    add("pre-data", 10**12, {"lamports": RENT, "data": b"\x00", "owner": SYSTEM})
    owned = global_bytes()
    add("already-program", 10**12, {"lamports": 10**9, "data": owned, "owner": PROGRAM})
    add("two-accounts", 10**12, None, system_present=False)
    add("one-account", 10**12, None, user_present=False, system_present=False)
    add("unsigned", 10**12, None, user_signer=False)
    add("unsigned-beats-system", 10**12, None, user_signer=False, system_ok=False)
    add("wrong-system", 10**12, None, system_ok=False)
    add("system-beats-seeds", 10**12, None, system_ok=False, is_pda=False)
    add("wrong-pda", 10**12, None, is_pda=False)
    add("seeds-beat-readonly", 10**12, None, is_pda=False, global_writable=False)
    add("readonly-global", 10**12, None, global_writable=False)
    add("readonly-user", 10**12, None, user_writable=False)
    return rows


def toggle_cases():
    rows = []

    def add(name, ix, arg, data, log_has=None, **flags):
        packed = bitfield(TOGGLE_NAMES, **flags)
        line = f"toggle {ix} {packed} {hx(arg)} {data.hex()}"
        rows.append({
            "name": name,
            "kind": "toggle",
            "line": line,
            "log_has": log_has,
            "data_before": data,
            "run": lambda ix=ix, arg=arg, data=data, flags=flags: run_toggle(ix, arg, data, flags),
        })

    for ix, field, line in (
        ("toggle_create_v2", "create_v2", "programs/pump/src/lib.rs:114"),
        ("toggle_mayhem_mode", "mayhem", "programs/pump/src/lib.rs:149"),
        ("toggle_cashback_enabled", "cashback", "programs/pump/src/lib.rs:121"),
    ):
        add(f"{ix}-on", ix, bytes([1]), global_bytes())
        add(f"{ix}-off", ix, bytes([0]), global_bytes(**{field: 1}))
        add(f"{ix}-same", ix, bytes([1]), global_bytes(**{field: 1}), log_has=line)
        add(f"{ix}-bad-bool", ix, bytes([2]), global_bytes())
        add(f"{ix}-empty", ix, b"", global_bytes())
        add(f"{ix}-trailing", ix, bytes([1, 9]), global_bytes())
    add("toggle-missing-event", "toggle_create_v2", bytes([1]), global_bytes(), event_present=False, program_present=False)
    add("toggle-bad-event", "toggle_create_v2", bytes([1]), global_bytes(), event_is_pda=False)
    add("toggle-unchecked-program", "toggle_create_v2", bytes([1]), global_bytes(), program_is_pump=False)
    add("toggle-wrong-authority", "toggle_create_v2", bytes([1]), global_bytes(), authority_matches=False)
    add("toggle-readonly-authority", "toggle_create_v2", bytes([1]), global_bytes(), authority_writable=False)
    add("toggle-short-beats-keys", "toggle_create_v2", b"", global_bytes(), event_present=False, program_present=False)
    return rows


def authority_cases():
    rows = []
    def add(name, new, log_has=None, **flags):
        stored = global_bytes() if flags.get("authority_matches", True) else global_bytes(authority=PAYER.pubkey())
        packed = bitfield(AUTH_NAMES, **flags)
        line = f"authority {packed} {TIMESTAMP} {bytes(GLOBAL).hex()} {bytes(new).hex()} {stored.hex()}"
        rows.append({
            "name": name,
            "kind": "authority",
            "line": line,
            "log_has": log_has,
            "data_before": stored,
            "run": lambda new=new, flags=flags, stored=stored: run_authority(new, flags, stored),
        })

    add("to-new", NEW)
    add("to-self", USER.pubkey())
    add("to-zero", Pubkey.default())
    add("missing-program", NEW, program_present=False)
    add("wrong-program", NEW, program_is_pump=False)
    add("bad-event", NEW, event_is_pda=False)
    add("unsigned", NEW, authority_signer=False)
    add("readonly-global", NEW, global_writable=False)
    add("wrong-authority", NEW, authority_matches=False)
    return rows


def boot():
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PROGRAM, ELF)
    vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    vm.airdrop(PAYER.pubkey(), 10**12)
    return vm


def finish(vm, result, global_key):
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    account = vm.get_account(global_key)
    user = vm.get_account(USER.pubkey())
    events = []
    for line in meta.logs():
        if line.startswith("Program data: "):
            events.append(base64.b64decode(line.split(": ", 1)[1]))
    return {
        "err": str(result.err()) if failed else None,
        "logs": meta.logs(),
        "events": events,
        "global": None if account is None else (account.lamports, bytes(account.data), account.owner),
        "global_data": None if account is None else bytes(account.data),
        "global_lamports": None if account is None else account.lamports,
        "owner": None if account is None else account.owner,
        "user": None if user is None else user.lamports,
    }


def run_init(user_lamports, global_spec, flags):
    vm = boot()
    vm.set_account(USER.pubkey(), Account(user_lamports, b"", Pubkey.default()))
    global_key = GLOBAL if flags.get("is_pda", True) else OTHER
    if global_spec is not None:
        vm.set_account(global_key, Account(global_spec["lamports"], global_spec["data"], global_spec["owner"]))
    user_key = USER.pubkey()
    metas = []
    if flags.get("user_present", True) or True:
        metas.append(AccountMeta(global_key, False, flags.get("global_writable", True)))
    if flags.get("user_present", True):
        metas.append(AccountMeta(user_key, flags.get("user_signer", True), flags.get("user_writable", True)))
    if flags.get("system_present", True):
        system = SYSTEM if flags.get("system_ok", True) else PROGRAM
        metas.append(AccountMeta(system, False, False))
    if not flags.get("user_present", True) and not flags.get("system_present", True) and flags.get("drop_global"):
        metas = []
    signers = [PAYER]
    if flags.get("user_present", True) and flags.get("user_signer", True):
        signers.append(USER)
    arg = b"\xde\xad" if flags.get("trailing") else b""
    tx = Transaction.new_signed_with_payer(
        [Instruction(PROGRAM, DISC["initialize"] + arg, metas)],
        PAYER.pubkey(), signers, vm.latest_blockhash(),
    )
    return finish(vm, vm.send_transaction(tx), global_key)


def run_toggle(ix, arg, data, flags):
    vm = boot()
    vm.airdrop(USER.pubkey(), 10**12)
    vm.set_account(GLOBAL, Account(10**9, data, PROGRAM))
    authority = USER.pubkey() if flags.get("authority_matches", True) else PAYER.pubkey()
    metas = [AccountMeta(GLOBAL, False, flags.get("global_writable", True))]
    metas.append(AccountMeta(authority, flags.get("authority_signer", True), flags.get("authority_writable", True)))
    if flags.get("event_present", True):
        metas.append(AccountMeta(EVENT if flags.get("event_is_pda", True) else OTHER, False, False))
    if flags.get("program_present", True):
        metas.append(AccountMeta(PROGRAM if flags.get("program_is_pump", True) else OTHER, False, False))
    signers = [PAYER]
    if flags.get("authority_signer", True) and authority == USER.pubkey():
        signers.append(USER)
    tx = Transaction.new_signed_with_payer(
        [Instruction(PROGRAM, DISC[ix] + arg, metas)],
        PAYER.pubkey(), signers, vm.latest_blockhash(),
    )
    return finish(vm, vm.send_transaction(tx), GLOBAL)


def run_authority(new, flags, data):
    vm = boot()
    vm.airdrop(USER.pubkey(), 10**12)
    vm.set_account(GLOBAL, Account(10**9, data, PROGRAM))
    metas = [
        AccountMeta(GLOBAL, False, flags.get("global_writable", True)),
        AccountMeta(USER.pubkey(), flags.get("authority_signer", True), False),
        AccountMeta(new, False, False),
    ]
    if flags.get("event_present", True):
        metas.append(AccountMeta(EVENT if flags.get("event_is_pda", True) else OTHER, False, False))
    if flags.get("program_present", True):
        metas.append(AccountMeta(PROGRAM if flags.get("program_is_pump", True) else OTHER, False, False))
    signers = [PAYER] + ([USER] if flags.get("authority_signer", True) else [])
    tx = Transaction.new_signed_with_payer(
        [Instruction(PROGRAM, DISC["update_global_authority"], metas)],
        PAYER.pubkey(), signers, vm.latest_blockhash(),
    )
    return finish(vm, vm.send_transaction(tx), GLOBAL)


if __name__ == "__main__":
    unittest.main()
