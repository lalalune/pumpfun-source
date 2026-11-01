#!/usr/bin/env python3
"""Execute generated Admin CTO cases in independent authenticated LiteSVMs."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import struct
import sys
import types
import uuid
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.hash import Hash
from solders.message import Message
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# Bootstrap the source-only loader from the captured raw bytes, never a pyc.
_corpus_path = HERE / "corpus.py"
_corpus_raw = _corpus_path.read_bytes()
_corpus_name = "_pump_fuzz_corpus_" + uuid.uuid4().hex
P = types.ModuleType(_corpus_name)
P.__file__ = str(_corpus_path)
P.__source_path__ = str(_corpus_path)
P.__source_sha256__ = hashlib.sha256(_corpus_raw).hexdigest()
sys.modules[_corpus_name] = P
try:
    exec(compile(_corpus_raw, str(_corpus_path), "exec"), P.__dict__)
finally:
    sys.modules.pop(_corpus_name, None)
C = P.source_module("case_model", HERE / "case_model.py")
canonical, sha, validate_case = C.canonical, C.sha, C.validate_case
_output = P.source_module("pump_differential_output", ROOT / "scripts/pump_differential_output.py")
L = P.source_module("pump_admin_cto_stateful_lifecycle",
                    ROOT / "reconstruction/verification/pump-admin-cto-stateful/lifecycle.py",
                    imports={"pump_differential_output": _output})
RUNTIME_SOURCE_HASHES = {
    module.__source_path__: module.__source_sha256__ for module in (P, C, _output, L)
}
RUNTIME_SOURCE_HASHES.update({str(L.IDL_PATH): sha(L.IDL_BYTES),
                              str(L.CONFIG_PATH): sha(L.CONFIG_BYTES)})
RUNTIME_SOURCE_HASHES[str(Path(__file__).resolve())] = globals().get(
    "__source_sha256__", sha(Path(__file__).read_bytes()))


SCHEMA = "pump-admin-cto-fuzz-execution-v1"
CANONICAL_ORIGINAL_SHA256 = "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
STRICT_FIELDS = (
    "transaction_base64", "signature", "message_sha256", "error", "outcome",
    "failure_class", "events", "semantic_logs", "inner_instructions", "return_data",
    "before", "after", "rollback_nonfee_equal", "instruction_data_base64",
    "instruction_accounts",
)


class UnsupportedFixture(ValueError):
    """The generated mutation cannot be represented by this fixture version."""


def _account_copy(account, *, lamports=None, data=None, owner=None):
    return Account(
        account.lamports if lamports is None else lamports,
        bytes(account.data) if data is None else data,
        account.owner if owner is None else owner,
        account.executable,
        account.rent_epoch,
    )


class FuzzHarness(L.Harness):
    """Stateful harness with explicit, bounded input mutation hooks."""

    OWNER_ROLES = {
        "system": L.SYSTEM,
        "pump": L.PUMP,
        "fees": L.FEES,
        "token": L.TOKEN,
        "token22": L.TOKEN22,
    }

    def __init__(self, pump_image: Path, case: dict, images=None):
        validate_case(case)
        self.fuzz_case = copy.deepcopy(case)
        super().__init__(pump_image, case["config"], images, case["case_index"])
        self.initial_creators = {
            fixture.mint: (fixture.sharing if case["config"].get("shared")
                           else L.CREATORS[0].pubkey())
            for fixture in self.mints
        }
        for mutation in case["initial_mutations"]:
            self.apply_mutation(mutation)
        self.prepare_watchset()

    def prepare_watchset(self):
        """Keep absent as well as present possible instruction inputs observable."""
        executable = {L.PUMP, L.AMM, L.FEES, L.TOKEN, L.TOKEN22, L.ATA, L.SYSTEM}
        fixture = self.mints[0]
        creators = {self.curve_creator(fixture), fixture.sharing, fixture.holder,
                    *(pair.pubkey() for pair in L.CREATORS)}
        for creator in creators:
            vault = L.pda(b"creator-vault", bytes(creator))
            amm_vault = L.pda(b"creator_vault", bytes(creator), program=L.AMM)
            self.tracked.update((creator, vault, amm_vault,
                                 L.ata(creator, fixture.quote, fixture.token_program),
                                 L.ata(vault, fixture.quote, fixture.token_program),
                                 L.ata(amm_vault, fixture.quote, fixture.token_program)))
        for step in self.fuzz_case["steps"]:
            self.tracked.update(meta.pubkey for meta in self.admin_instruction(step).accounts)
        self.tracked.difference_update(executable)

    def curve_creator(self, fixture):
        """Resolve the live creator, retaining an account-list value for malformed data."""
        account = self.vm.get_account(fixture.curve)
        if account is not None and len(account.data) >= 81:
            return L.Pubkey.from_bytes(bytes(account.data[49:81]))
        return self.initial_creators[fixture.mint]

    def mutation_target(self, name: str):
        fixture = self.mints[0]
        targets = {
            "global": L.GLOBAL,
            "curve": fixture.curve,
            "sharing": fixture.sharing,
            "pool": fixture.pool,
            "quote_mint": fixture.quote,
        }
        if name in ("current_wallet_token", "creator_vault_token", "amm_vault_token"):
            current = self.curve_creator(fixture)
            vault = L.pda(b"creator-vault", bytes(current))
            amm_vault = L.pda(b"creator_vault", bytes(current), program=L.AMM)
            targets.update({
                "current_wallet_token": L.ata(current, fixture.quote, fixture.token_program),
                "creator_vault_token": L.ata(vault, fixture.quote, fixture.token_program),
                "amm_vault_token": L.ata(amm_vault, fixture.quote, fixture.token_program),
            })
        if name not in targets:
            raise UnsupportedFixture(f"unknown account mutation target: {name}")
        return targets[name]

    def apply_mutation(self, mutation: dict) -> None:
        if not isinstance(mutation, dict):
            raise UnsupportedFixture("account mutation must be an object")
        key = self.mutation_target(mutation.get("target"))
        account = self.vm.get_account(key)
        if account is None:
            raise UnsupportedFixture(f"mutation target is absent: {mutation.get('target')}")
        action = mutation.get("action")
        value = mutation.get("value")
        if action == "truncate":
            if type(value) is not int or not 0 <= value <= len(account.data):
                raise UnsupportedFixture("truncate length is outside retained account data")
            changed = _account_copy(account, data=bytes(account.data[:value]))
        elif action == "set_byte":
            offset = mutation.get("offset")
            if type(offset) is not int or not 0 <= offset < len(account.data):
                raise UnsupportedFixture("byte mutation offset is outside retained account data")
            if type(value) is not int or not 0 <= value <= 255:
                raise UnsupportedFixture("byte mutation value is invalid")
            data = bytearray(account.data)
            data[offset] = value
            changed = _account_copy(account, data=bytes(data))
        elif action == "owner":
            if value not in self.OWNER_ROLES:
                raise UnsupportedFixture("unknown owner role")
            changed = _account_copy(account, owner=self.OWNER_ROLES[value])
        elif action == "lamports":
            if type(value) is not int or not 0 <= value < 2**64:
                raise UnsupportedFixture("invalid lamport value")
            changed = _account_copy(account, lamports=value)
        elif action == "token_amount":
            if type(value) is not int or not 0 <= value < 2**64 or len(account.data) < 72:
                raise UnsupportedFixture("token amount mutation needs a token account")
            data = bytearray(account.data)
            data[64:72] = value.to_bytes(8, "little")
            changed = _account_copy(account, data=bytes(data))
        elif action == "token_state":
            if type(value) is not int or not 0 <= value <= 255 or len(account.data) < 109:
                raise UnsupportedFixture("token state mutation needs a token account")
            data = bytearray(account.data)
            data[108] = value
            changed = _account_copy(account, data=bytes(data))
        else:
            raise UnsupportedFixture(f"unknown account mutation action: {action}")
        self.put(key, changed)

    def admin_instruction(self, step: dict) -> Instruction:
        base = super().admin_instruction(step)
        metas = list(base.accounts)
        for row in step.get("replace_accounts", []):
            index, creator = row.get("index"), row.get("creator")
            if type(index) is not int or not 0 <= index < len(metas):
                raise UnsupportedFixture("replacement account index is outside instruction")
            if type(creator) is not int or not 0 <= creator < len(L.CREATORS):
                raise UnsupportedFixture("replacement creator is invalid")
            old = metas[index]
            metas[index] = AccountMeta(L.CREATORS[creator].pubkey(), old.is_signer, old.is_writable)
        for index in step.get("readonly", []):
            if type(index) is not int or not 0 <= index < len(metas):
                raise UnsupportedFixture("readonly account index is outside instruction")
            old = metas[index]
            metas[index] = AccountMeta(old.pubkey, old.is_signer, False)
        remove = step.get("drop_accounts", 0)
        if type(remove) is not int or not 0 <= remove < len(metas):
            raise UnsupportedFixture("invalid account removal count")
        if remove:
            metas = metas[:-remove]
        data = bytearray(base.data)
        mutation = step.get("instruction_mutation")
        if mutation:
            action, value = mutation.get("action"), mutation.get("value")
            if action == "truncate":
                if type(value) is not int or not 0 <= value <= len(data):
                    raise UnsupportedFixture("instruction truncation is outside data")
                data = data[:value]
            elif action == "append":
                try:
                    data.extend(bytes.fromhex(value))
                except (TypeError, ValueError) as error:
                    raise UnsupportedFixture("instruction append is not hex") from error
            elif action == "holder_tag":
                if len(data) < 9 or type(value) is not int or not 0 <= value <= 255:
                    raise UnsupportedFixture("holder option tag cannot be mutated")
                data[8] = value
            else:
                raise UnsupportedFixture("unknown instruction mutation")
        return Instruction(base.program_id, bytes(data), metas)

    @staticmethod
    def _signers(instruction: Instruction):
        known = {pair.pubkey(): pair for pair in (L.ADMIN, *L.CREATORS)}
        pairs = [L.PAYER]
        for meta in instruction.accounts:
            if meta.is_signer and meta.pubkey != L.PAYER.pubkey():
                if meta.pubkey not in known:
                    raise UnsupportedFixture(f"no retained keypair for signer {meta.pubkey}")
                if all(pair.pubkey() != meta.pubkey for pair in pairs):
                    pairs.append(known[meta.pubkey])
        return pairs

    def execute(self, step: dict, index: int) -> dict:
        self.vm.expire_blockhash()
        self.vm.set_clock(Clock(1_000 + index, 0, 0, 0, 1_700_000_000 + index))
        before = self.snapshot()
        instruction = self.admin_instruction(step)
        blockhash = self.vm.latest_blockhash()
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), instruction], L.PAYER.pubkey(),
            self._signers(instruction), blockhash,
        )
        checks = list(tx.verify_with_results())
        if not checks or not all(checks):
            raise UnsupportedFixture("locally constructed transaction failed signature verification")
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        raw = json.loads(meta.to_json())
        logs = list(meta.logs())
        after = self.snapshot()
        nonfee = lambda state: {key: value for key, value in state.items() if key != str(L.PAYER.pubkey())}
        error = str(result.err()) if failed else None
        return {
            "step": step["name"], "operation": "admin_cto", "recent_blockhash": str(blockhash),
            "mint_index": 0,
            "instruction_data_base64": base64.b64encode(bytes(instruction.data)).decode(),
            "instruction_accounts": [{"pubkey": str(row.pubkey), "signer": row.is_signer,
                                      "writable": row.is_writable} for row in instruction.accounts],
            "transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "signature": str(tx.signatures[0]), "signature_verification": checks,
            "message_sha256": L.sha(bytes(tx.message)), "error": error,
            "outcome": L.outcome(logs, error), "failure_class": failure_class(error),
            "compute_units": meta.compute_units_consumed(), "logs": logs,
            "semantic_logs": L.semantic_logs(logs),
            "events": [line[14:] for line in logs if line.startswith("Program data: ")],
            "inner_instructions": raw.get("inner_instructions"), "return_data": raw.get("return_data"),
            "before_hash": L.canonical_hash(before), "after_hash": L.canonical_hash(after),
            "before": before, "after": after,
            "rollback_nonfee_equal": None if not failed else nonfee(before) == nonfee(after),
        }


def run_image(image: Path, case: dict, images=None) -> dict:
    harness = FuzzHarness(image, case, images)
    initial = harness.snapshot()
    receipts = [harness.execute(step, index) for index, step in enumerate(case["steps"], 1)]
    signatures = [row["signature"] for row in receipts]
    if len(signatures) != len(set(signatures)):
        raise ValueError("case reused a transaction signature")
    fixture = harness.mints[0]
    return {
        "initial_state_hash": L.canonical_hash(initial),
        "receipts": receipts,
        "mint_accounts": [{"mint": str(fixture.mint), "curve": str(fixture.curve),
                           "pool": str(fixture.pool), "sharing": str(fixture.sharing)}],
    }


def compare_runs(original: dict, candidate: dict) -> tuple[list[str], list[dict]]:
    mismatches = []
    if original["initial_state_hash"] != candidate["initial_state_hash"]:
        mismatches.append("initial_state_hash")
    if len(original["receipts"]) != len(candidate["receipts"]):
        return mismatches + ["receipt_count"], []
    comparisons = []
    for left, right in zip(original["receipts"], candidate["receipts"]):
        strict = [field for field in STRICT_FIELDS
                  if L.canonical_hash(left.get(field)) != L.canonical_hash(right.get(field))]
        diagnostic = [field for field in ("logs", "compute_units")
                      if L.canonical_hash(left.get(field)) != L.canonical_hash(right.get(field))]
        comparisons.append({"step": left["step"], "mismatch_fields": strict,
                            "diagnostic_difference_fields": diagnostic})
        mismatches.extend(f"{left['step']}:{field}" for field in strict)
    return mismatches, comparisons


def same_json(left, right):
    """JSON equality which never equates bool with integer."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return (left.keys() == right.keys()
                and all(same_json(left[key], right[key]) for key in left))
    if isinstance(left, list):
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def failure_class(error):
    # Guest traps and compute exhaustion are observed program behavior. Host
    # transport/authentication failures cannot qualify a behavioral comparison.
    if error is None:
        return None
    return "infrastructure" if any(name in error for name in
           ("BlockhashNotFound", "AlreadyProcessed", "SignatureFailure")) else "program"


class FixtureAccounts:
    """Account storage only: no VM, program loading or transaction execution."""
    def __init__(self):
        self.accounts = {}

    def set_account(self, key, value):
        # LiteSVM follows Solana zero-lamport account reclamation.
        if value.lamports == 0:
            self.accounts.pop(key, None)
        else:
            self.accounts[key] = value

    def get_account(self, key):
        return self.accounts.get(key)


def fixture_plan(case):
    """Reconstruct synthetic fixture inputs independently of all saved receipts."""
    validate_case(case)
    harness = FuzzHarness.__new__(FuzzHarness)
    harness.fuzz_case = copy.deepcopy(case)
    harness.config = copy.deepcopy(case["config"])
    harness.vm, harness.tracked = FixtureAccounts(), set()
    harness.mints = [harness._mint_fixture(i, mode)
                     for i, mode in enumerate(harness.config["mints"])]
    harness._seed()
    harness.initial_creators = {
        f.mint: f.sharing if harness.config.get("shared") else L.CREATORS[0].pubkey()
        for f in harness.mints
    }
    for mutation in case["initial_mutations"]:
        harness.apply_mutation(mutation)
    harness.prepare_watchset()
    for step in case["steps"]:
        harness._signers(harness.admin_instruction(step))
    return harness


def _account_rows(state, keys):
    if type(state) is not dict or set(state) != keys:
        raise ValueError("snapshot key set")
    rows = {}
    for key, account in state.items():
        pubkey = L.P(key)
        if str(pubkey) != key:
            raise ValueError("noncanonical account key")
        if account is None:
            rows[pubkey] = None
            continue
        fields = {"lamports", "owner", "data_len", "data_sha256", "executable",
                  "rent_epoch", "data_base64"}
        if type(account) is not dict or set(account) != fields:
            raise ValueError("account metadata fields")
        for name in ("lamports", "rent_epoch"):
            if type(account[name]) is not int or not 0 <= account[name] < 2**64:
                raise ValueError("account integer")
        if type(account["executable"]) is not bool or account["executable"]:
            raise ValueError("watched account executable flag")
        data = base64.b64decode(account["data_base64"], validate=True)
        if (type(account["data_len"]) is not int or account["data_len"] != len(data)
                or type(account["data_sha256"]) is not str or account["data_sha256"] != sha(data)
                or base64.b64encode(data).decode() != account["data_base64"]):
            raise ValueError("account data identity")
        owner = L.P(account["owner"])
        if str(owner) != account["owner"]:
            raise ValueError("account owner")
        rows[pubkey] = Account(account["lamports"], data, owner, False, account["rent_epoch"])
    return rows


def validate_run(run: dict, case: dict, *, images=None) -> list[str]:
    """Admit the exact case, fixture, complete signed message and typed state."""
    del images  # Fixture validation deliberately does not execute any image.
    failures, signatures = [], []
    try:
        fixture = fixture_plan(case)
        initial = fixture.snapshot()
        if type(run) is not dict or set(run) != {"initial_state_hash", "receipts", "mint_accounts"}:
            raise ValueError("run fields")
        f = fixture.mints[0]
        expected_mints = [{"mint": str(f.mint), "curve": str(f.curve),
                           "pool": str(f.pool), "sharing": str(f.sharing)}]
        if not same_json(run["mint_accounts"], expected_mints):
            failures.append("mint-accounts")
        receipts = run["receipts"]
        if type(receipts) is not list or len(receipts) != len(case["steps"]) or not receipts:
            raise ValueError("receipt count")
        if run["initial_state_hash"] != L.canonical_hash(initial):
            failures.append("initial-state-hash")
        keys, previous = set(initial), initial
        fields = {"step", "operation", "recent_blockhash", "mint_index", "instruction_data_base64",
                  "instruction_accounts", "transaction_base64", "signature", "signature_verification",
                  "message_sha256", "error", "outcome", "failure_class", "compute_units", "logs",
                  "semantic_logs", "events", "inner_instructions", "return_data", "before_hash",
                  "after_hash", "before", "after", "rollback_nonfee_equal"}
        for step, row in zip(case["steps"], receipts):
            tag = step["name"]
            if type(row) is not dict or set(row) != fields:
                raise ValueError("receipt fields")
            if (row["step"] != tag or row["operation"] != "admin_cto"
                    or type(row["mint_index"]) is not int or row["mint_index"] != 0):
                failures.append(tag + ":case-step")
            before_rows = _account_rows(row["before"], keys)
            _account_rows(row["after"], keys)
            if not same_json(previous, row["before"]):
                failures.append(tag + ":state-continuity")
            fixture.vm.accounts = before_rows
            instruction = fixture.admin_instruction(step)
            expected_accounts = [{"pubkey": str(m.pubkey), "signer": m.is_signer,
                                  "writable": m.is_writable} for m in instruction.accounts]
            if not same_json(row["instruction_accounts"], expected_accounts):
                failures.append(tag + ":instruction-accounts")
            encoded_data = base64.b64encode(bytes(instruction.data)).decode()
            if row["instruction_data_base64"] != encoded_data:
                failures.append(tag + ":instruction-data")
            blockhash = Hash.from_string(row["recent_blockhash"])
            expected_message = Message.new_with_blockhash(
                [set_compute_unit_limit(1_400_000), instruction], L.PAYER.pubkey(), blockhash)
            raw = base64.b64decode(row["transaction_base64"], validate=True)
            tx = Transaction.from_bytes(raw)
            checked = list(tx.verify_with_results())
            declared_checks = row["signature_verification"]
            required = expected_message.header.num_required_signatures
            expected_signers = {pair.pubkey() for pair in fixture._signers(instruction)}
            if (bytes(tx) != raw or base64.b64encode(raw).decode() != row["transaction_base64"]
                    or bytes(tx.message) != bytes(expected_message)
                    or len(tx.signatures) != required or checked != [True] * required
                    or not checked or type(declared_checks) is not list
                    or any(type(value) is not bool for value in declared_checks)
                    or checked != declared_checks
                    or set(tx.message.account_keys[:required]) != expected_signers
                    or row["signature"] != str(tx.signatures[0])
                    or row["message_sha256"] != sha(bytes(tx.message))):
                failures.append(tag + ":transaction-integrity")
            signatures.append(str(tx.signatures[0]))
            for stage in ("before", "after"):
                if row[stage + "_hash"] != L.canonical_hash(row[stage]):
                    failures.append(tag + ":" + stage + "-hash")
            if (row["error"] is not None and type(row["error"]) is not str
                    or type(row["compute_units"]) is not int or row["compute_units"] < 0
                    or type(row["logs"]) is not list
                    or any(type(line) is not str for line in row["logs"])):
                raise ValueError("receipt result types")
            nonfee = lambda state: {key: value for key, value in state.items()
                                    if key != str(L.PAYER.pubkey())}
            rollback = (None if row["error"] is None
                        else same_json(nonfee(row["before"]), nonfee(row["after"])))
            if not same_json(rollback, row["rollback_nonfee_equal"]) or rollback is False:
                failures.append(tag + ":non-atomic-failure")
            if (not same_json(row["outcome"], L.outcome(row["logs"], row["error"]))
                    or not same_json(row["failure_class"], failure_class(row["error"]))
                    or not same_json(row["semantic_logs"], L.semantic_logs(row["logs"]))
                    or not same_json(row["events"], [line[14:] for line in row["logs"]
                                                    if line.startswith("Program data: ")])):
                failures.append(tag + ":derived-fields")
            previous = row["after"]
        if len(signatures) != len(set(signatures)):
            failures.append("duplicate-signature")
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        failures.append("malformed-receipt:" + type(error).__name__)
    return failures


def validate_result(result, case, *, images=None):
    """Independent case-bound admission, including excluded fixture records."""
    failures = []
    try:
        validate_case(case)
        if (type(result) is not dict or result.get("schema") != SCHEMA
                or result.get("case_id") != case["case_id"]
                or not same_json(result.get("case"), case)):
            return ["result-case"]
        if "original" not in result:
            if set(result) != {"schema", "case_id", "case", "classification", "reason"}:
                return ["excluded-result-fields"]
            if result.get("classification") != "unsupported_fixture":
                return ["unverified-infrastructure-failure"]
            try:
                fixture_plan(case)
            except UnsupportedFixture as error:
                return [] if result.get("reason") == str(error) else ["unsupported-reason"]
            return ["unsupported-fixture-not-reproduced"]
        fields = {"schema", "case_id", "case", "classification", "reason", "original", "candidate",
                  "comparison", "mismatch_fields", "invariant_failures", "infrastructure_failures"}
        if set(result) != fields or result["reason"] is not None:
            failures.append("executed-result-fields")
        invariants = {side: validate_run(result[side], case, images=images)
                      for side in ("original", "candidate")}
        mismatches, comparisons = compare_runs(result["original"], result["candidate"])
        infrastructure = [f"{side}:{row['step']}" for side in ("original", "candidate")
                          for row in result[side]["receipts"]
                          if row["failure_class"] == "infrastructure"]
        for name, expected in (("invariant_failures", invariants), ("mismatch_fields", mismatches),
                               ("comparison", comparisons), ("infrastructure_failures", infrastructure)):
            if not same_json(result.get(name), expected):
                failures.append(name)
        classification = ("infrastructure_failure" if any(invariants.values()) or infrastructure
                          else "different_behavior" if mismatches else "equal_observed_behavior")
        if result.get("classification") != classification:
            failures.append("classification")
        failures.extend(f"{side}:{error}" for side, errors in invariants.items() for error in errors)
        if infrastructure:
            failures.append("execution-infrastructure")
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        failures.append("malformed-result:" + type(error).__name__)
    return failures


def execute_case(case: dict, original: Path, candidate: Path, images=None) -> dict:
    """Execute one case twice and return a four-way classified record."""
    validate_case(case)
    result = {"schema": SCHEMA, "case_id": case["case_id"], "case": copy.deepcopy(case)}
    try:
        fixture_plan(case)
        if sha(P.regular_bytes(original)) != CANONICAL_ORIGINAL_SHA256:
            raise ValueError("original image is not the captured Pump Main")
        left = run_image(original, case, images)
        right = run_image(candidate, case, images)
    except UnsupportedFixture as error:
        result.update(classification="unsupported_fixture", reason=str(error))
        return result
    except BaseException as error:  # PyO3 panic exceptions intentionally inherit BaseException.
        if isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit)):
            raise
        result.update(classification="infrastructure_failure",
                      reason=f"{type(error).__name__}: {error}")
        return result
    mismatches, comparison = compare_runs(left, right)
    invariants = {"original": validate_run(left, case), "candidate": validate_run(right, case)}
    infrastructure = [f"{side}:{row['step']}" for side, run in (("original", left), ("candidate", right))
                      for row in run["receipts"] if row["failure_class"] == "infrastructure"]
    if any(invariants.values()) or infrastructure:
        classification = "infrastructure_failure"
    elif mismatches:
        classification = "different_behavior"
    else:
        classification = "equal_observed_behavior"
    result.update(classification=classification, reason=None, original=left, candidate=right,
                  comparison=comparison, mismatch_fields=mismatches,
                  invariant_failures=invariants, infrastructure_failures=infrastructure)
    return result


def execution_identity(result: dict) -> str:
    return hashlib.sha256(canonical(result)).hexdigest()
