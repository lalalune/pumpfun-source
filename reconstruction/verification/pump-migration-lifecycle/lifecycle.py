#!/usr/bin/env python3
"""Persistent, signed Pump migration lifecycle differential.

The archived migration probes intentionally remain unchanged.  This module
builds the same synthetic completed curve in a persistent LiteSVM and sends a
freshly signed transaction for every step of a lifecycle.
"""

from __future__ import annotations

import argparse
import base64
import copy
import gzip
import hashlib
import json
import struct
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
IDL_PATH = ROOT / "evidence/upstream/pump.json"
FIXTURE_PATH = ROOT / "research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json"
IDL = json.loads(IDL_PATH.read_text())

PUMP = Pubkey.from_string(IDL["address"])
PUMP_AMM = Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
WSOL = Pubkey.from_string("So11111111111111111111111111111111111111112")
SYSTEM = Pubkey.default()
RENT = Pubkey.from_string("SysvarRent111111111111111111111111111111111")

USER = Keypair.from_seed(bytes([212]) * 32)
PAYER = Keypair.from_seed(bytes([213]) * 32)
BASE_MINT = Pubkey.from_bytes(bytes([214]) * 32)
STRANGER = Pubkey.from_bytes(bytes([216]) * 32)
STABLE_MINT = Pubkey.from_bytes(bytes([217]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([218]) * 32)

CAPTURED_PROGRAMS = {
    "pump_original": ROOT / "evidence/original/pump/deployed.so",
    "pump_amm": ROOT / "evidence/original/pump_amm/deployed.so",
    "spl_token": ROOT / "evidence/dependencies/spl_token/deployed.so",
    "spl_token_2022": ROOT / "evidence/dependencies/spl_token_2022/deployed.so",
    "associated_token": ROOT / "evidence/dependencies/associated_token/deployed.so",
}
PROGRAM_IDS = {
    "pump": str(PUMP),
    "pump_amm": str(PUMP_AMM),
    "spl_token": str(TOKEN),
    "spl_token_2022": str(TOKEN22),
    "associated_token": str(ATA),
}
STRICT_FIELDS = (
    "transaction_base64",
    "signature",
    "message_sha256",
    "error",
    "outcome",
    "failure_class",
    "events",
    "semantic_logs",
    "inner_instructions",
    "return_data",
    "before",
    "after",
    "rollback_nonfee_equal",
)
EXPECTED_OUTCOMES = {
    "legacy/native-success-repeat": ["ok", "ok"],
    "legacy/disabled-flag-observed": ["ok", "ok"],
    "legacy/mayhem-success-repeat": ["ok", "ok"],
    "legacy/incomplete-rollback": ["error:BondingCurveNotComplete"],
    "legacy/missing-boost-rollback": ["error:NotEnoughRemainingAccounts"],
    "legacy/insufficient-base-rollback": ["error:ZeroBaseAmount"],
    "v2/native-token22-success-repeat": ["ok", "ok"],
    "v2/native-spl-success-repeat": ["ok", "ok"],
    "v2/stable-spl-success-repeat": ["ok", "ok"],
    "v2/stable-token22-success-repeat": ["ok", "ok"],
    "v2/stable-token22-transfer-fee-success-repeat": ["ok", "ok"],
    "v2/nonwhitelisted-stable-observed": ["ok", "ok"],
    "v2/disabled-flag-observed": ["ok", "ok"],
    "v2/mint-authority-set-observed": ["ok", "ok"],
    "v2/freeze-authority-set-observed": ["ok", "ok"],
    "v2/incomplete-rollback": ["error:BondingCurveNotComplete"],
    "v2/missing-boost-rollback": ["error:NotEnoughRemainingAccounts"],
    "v2/readonly-boost-vault-rollback": [
        "error:TransactionErrorInstructionError((1, Fieldless(PrivilegeEscalation)))"
    ],
    "v2/readonly-pool-base-rollback": ["error:ConstraintMut"],
    "v2/readonly-pool-quote-rollback": ["error:ConstraintMut"],
    "v2/insufficient-base-rollback": ["error:ZeroBaseAmount"],
    "v2/insufficient-quote-rollback": [
        "error:TransactionErrorInstructionError((1, Tagged(InstructionErrorCustom(1))))"
    ],
    "v2/invalid-base-mint-owner": ["error:AccountOwnedByWrongProgram"],
    "v2/invalid-base-account-owner": ["error:AccountOwnedByWrongProgram"],
    "v2/invalid-quote-account-owner": [
        "error:TransactionErrorInstructionError((1, Fieldless(ExternalAccountDataModified)))"
    ],
    "v2/wrong-pump-amm-event-authority": ["error:ConstraintSeeds"],
    "v2/committed-then-invalid-then-repeat": ["ok", "error:ConstraintSeeds", "ok"],
}


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_hash(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(seeds, program)[0]


def ata(wallet, mint, token_program=TOKEN):
    return pda([bytes(wallet), bytes(token_program), bytes(mint)], ATA)


def spl_mint_data(base: bytes, authority=False, freeze_authority=False):
    data = bytearray(base[:82])
    if authority:
        data[0:4] = struct.pack("<I", 1)
        data[4:36] = bytes(USER.pubkey())
    if freeze_authority:
        data[46:50] = struct.pack("<I", 1)
        data[50:82] = bytes(USER.pubkey())
    return bytes(data)


def transfer_fee_mint_data(base: bytes, bps=100, maximum=2**64 - 1):
    """Add a Token-2022 TransferFeeConfig TLV entry to an 82-byte mint."""
    authority = bytes([94]) * 32
    withdraw = bytes([95]) * 32
    fee = struct.pack("<QQH", 0, maximum, bps)
    body = authority + withdraw + struct.pack("<Q", 0) + fee + fee
    assert len(body) == 108
    return bytes(base[:82]) + bytes(83) + b"\x01" + struct.pack("<HH", 1, len(body)) + body


def token_account_data(mint, owner, amount, transfer_fee=False):
    data = struct.pack(
        "<32s32sQI32sBI8sQI32s",
        bytes(mint),
        bytes(owner),
        amount,
        0,
        bytes(32),
        1,
        0,
        bytes(8),
        0,
        0,
        bytes(32),
    )
    if transfer_fee:
        data += b"\x02" + struct.pack("<HHQ", 2, 8, 0)
    return data


def semantic_logs(logs):
    out = []
    for line in logs:
        if " consumed " in line:
            continue
        if line.startswith("Program ") and (
            line.endswith(" success") or " invoke [" in line
        ):
            continue
        out.append(line.replace("programs/pump/src/", "src/"))
    return out


def outcome(logs, error):
    if error is None:
        return "ok"
    for line in logs:
        if "Error Code: " in line:
            return "error:" + line.split("Error Code: ", 1)[1].split(".", 1)[0]
    return "error:" + error


def failure_class(error):
    if error is None:
        return None
    infrastructure = (
        "ComputationalBudgetExceeded",
        "ProgramFailedToComplete",
        "BlockhashNotFound",
        "AlreadyProcessed",
        "SignatureFailure",
    )
    return "infrastructure" if any(x in error for x in infrastructure) else "program"


def fixture_before():
    packet = json.loads(FIXTURE_PATH.read_text())
    return packet["missing_boost"]["before"]


class MigrationHarness:
    def __init__(self, image: Path, config: dict):
        self.image = Path(image).resolve()
        self.config = copy.deepcopy(config)
        self.family = config["family"]
        self.base_program = TOKEN22 if config.get("base_token22") else TOKEN
        self.quote = (
            WSOL
            if self.family == "legacy" or config.get("quote_mode") == "native"
            else STABLE_MINT
        )
        self.quote_program = TOKEN22 if config.get("quote_mode") == "token22" else TOKEN
        self.saved = fixture_before()
        self.vm = (
            LiteSVM()
            .with_sigverify(True)
            .with_transaction_history(64)
            .with_log_bytes_limit(250_000)
        )
        self.vm.set_clock(Clock(100, 1_234_567_890, 0, 0, 1_234_567_890))
        self.tracked = set()
        self._load_programs()
        self._seed()

    def _load_programs(self):
        for program, path in (
            (PUMP, self.image),
            (PUMP_AMM, CAPTURED_PROGRAMS["pump_amm"]),
            (TOKEN, CAPTURED_PROGRAMS["spl_token"]),
            (TOKEN22, CAPTURED_PROGRAMS["spl_token_2022"]),
            (ATA, CAPTURED_PROGRAMS["associated_token"]),
        ):
            self.vm.add_program_from_file(program, path)

    def put(self, key, account):
        self.tracked.add(key)
        self.vm.set_account(key, account)

    def _seed(self):
        c = self.config
        curve = pda([b"bonding-curve", bytes(BASE_MINT)])
        pool_authority = pda([b"pool-authority", bytes(BASE_MINT)])
        pool = pda(
            [b"pool", bytes(2), bytes(pool_authority), bytes(BASE_MINT), bytes(self.quote)],
            PUMP_AMM,
        )
        lp_mint = pda([b"pool_lp_mint", bytes(pool)], PUMP_AMM)
        global_data = bytearray(base64.b64decode(self.saved["global"]["data_base64"]))
        withdraw = Pubkey.from_bytes(bytes(global_data[113:145]))
        global_data[145] = int(c.get("enable_migrate", 1))
        if self.family == "v2" and c.get("quote_mode") != "native" and c.get("quote_whitelisted", True):
            global_data[1013:1045] = bytes(self.quote)

        names = {
            "global": pda([b"global"]),
            "withdraw_authority": withdraw,
            "base_mint": BASE_MINT,
            "mint": BASE_MINT,
            "quote_mint": self.quote,
            "bonding_curve": curve,
            "associated_base_bonding_curve": ata(curve, BASE_MINT, self.base_program),
            "associated_bonding_curve": ata(curve, BASE_MINT, self.base_program),
            "associated_quote_bonding_curve": ata(curve, self.quote, self.quote_program),
            "user": USER.pubkey(),
            "system_program": SYSTEM,
            "token_program": TOKEN,
            "base_token_program": self.base_program,
            "quote_token_program": self.quote_program,
            "pump_amm": PUMP_AMM,
            "pool": pool,
            "pool_authority": pool_authority,
            "pool_authority_mint_account": ata(pool_authority, BASE_MINT, self.base_program),
            "pool_authority_wsol_account": ata(pool_authority, WSOL, TOKEN),
            "pool_authority_quote_account": ata(pool_authority, self.quote, self.quote_program),
            "amm_global_config": pda([b"global_config"], PUMP_AMM),
            "wsol_mint": WSOL,
            "lp_mint": lp_mint,
            "user_pool_token_account": ata(pool_authority, lp_mint, TOKEN22),
            "pool_base_token_account": ata(pool, BASE_MINT, self.base_program),
            "pool_quote_token_account": ata(pool, self.quote, self.quote_program),
            "token_2022_program": TOKEN22,
            "associated_token_program": ATA,
            "pump_amm_event_authority": pda([b"__event_authority"], PUMP_AMM),
            "event_authority": pda([b"__event_authority"]),
            "program": PUMP,
            "rent": RENT,
        }
        boost = pda([b"boost_vault", bytes(pool)], PUMP_AMM)
        names["boost_authority"] = boost
        names["boost_vault"] = ata(boost, self.quote, self.quote_program)
        self.names = names

        payer_lamports = c.get("payer_lamports", 10**12)
        user_lamports = c.get("user_lamports", 10**12)
        self.put(PAYER.pubkey(), Account(payer_lamports, b"", SYSTEM))
        self.put(USER.pubkey(), Account(user_lamports, b"", SYSTEM))
        self.put(STRANGER, Account(10**9, b"", SYSTEM))
        self.put(
            names["global"],
            Account(self.saved["global"]["lamports"], bytes(global_data), PUMP),
        )

        curve_data = bytearray(base64.b64decode(self.saved["curve"]["data_base64"]))
        curve_data[48] = int(c.get("complete", 1))
        curve_data[49:81] = bytes(USER.pubkey())
        curve_data[81] = int(c.get("mayhem", 0))
        if self.family == "v2" and c.get("quote_mode") != "native":
            curve_data[83:115] = bytes(self.quote)
        curve_lamports = (
            self.saved["curve"]["lamports"]
            if self.family == "legacy" or c.get("quote_mode") == "native"
            else 660_837_992
        )
        self.put(curve, Account(curve_lamports, bytes(curve_data), PUMP))

        base_mint_data = spl_mint_data(
            base64.b64decode(self.saved["mint"]["data_base64"]),
            c.get("mint_authority", False),
            c.get("freeze_authority", False),
        )
        base_mint_owner = SYSTEM if c.get("invalid_base_mint_owner") else self.base_program
        self.put(BASE_MINT, Account(1_461_600, base_mint_data, base_mint_owner))

        base_amount = c.get("base_amount")
        if base_amount is None:
            base_data = bytearray(base64.b64decode(self.saved["curve_base"]["data_base64"])[:165])
            base_data[:32] = bytes(BASE_MINT)
            base_data[32:64] = bytes(curve)
        else:
            base_data = bytearray(token_account_data(BASE_MINT, curve, base_amount))
        base_owner = SYSTEM if c.get("invalid_base_account_owner") else self.base_program
        self.put(names["associated_base_bonding_curve"], Account(2_039_280, bytes(base_data), base_owner))

        quote_mint_data = bytearray(82)
        quote_mint_data[44] = 6 if c.get("quote_mode") != "native" else 9
        quote_mint_data[45] = 1
        if c.get("quote_transfer_fee_bps") is not None:
            quote_mint_data = bytearray(
                transfer_fee_mint_data(quote_mint_data, c["quote_transfer_fee_bps"])
            )
        self.put(self.quote, Account(1_461_600, bytes(quote_mint_data), self.quote_program))

        if self.family == "v2" and c.get("quote_mode") != "native":
            qamount = c.get("quote_amount", 85_005_359_063)
            qdata = token_account_data(
                self.quote,
                curve,
                qamount,
                c.get("quote_transfer_fee_bps") is not None,
            )
            qowner = SYSTEM if c.get("invalid_quote_account_owner") else self.quote_program
            self.put(names["associated_quote_bonding_curve"], Account(2_039_280, qdata, qowner))

        amm = self.saved["amm_global_config"]
        self.put(
            names["amm_global_config"],
            Account(amm["lamports"], base64.b64decode(amm["data_base64"]), PUMP_AMM),
        )

    def snapshot(self):
        out = {}
        keys = self.tracked | set(self.names.values()) | {PAYER.pubkey(), STRANGER}
        for key in sorted(keys, key=str):
            account = self.vm.get_account(key)
            if account is not None and account.executable:
                continue
            out[str(key)] = None if account is None else {
                "lamports": account.lamports,
                "owner": str(account.owner),
                "data_hex": bytes(account.data).hex(),
            }
        return out

    def _metas(self, step):
        instruction_name = "migrate" if self.family == "legacy" else "migrate_v2"
        spec = next(i for i in IDL["instructions"] if i["name"] == instruction_name)
        metas = []
        wrong = step.get("wrong")
        readonly = set(step.get("readonly", []))
        writable = set(step.get("writable", []))
        for account in spec["accounts"]:
            name = account["name"]
            key = STRANGER if name == wrong else self.names[name]
            metas.append(
                AccountMeta(
                    key,
                    bool(account.get("signer")),
                    (bool(account.get("writable")) or name in writable) and name not in readonly,
                )
            )
        remaining = step.get("remaining_count", 2)
        if remaining:
            metas.extend(
                [
                    AccountMeta(self.names["boost_authority"], False, False),
                    AccountMeta(
                        self.names["boost_vault"],
                        False,
                        "boost_vault" not in readonly,
                    ),
                ][:remaining]
            )
        return instruction_name, spec, metas

    def execute(self, step, index):
        self.vm.expire_blockhash()
        self.vm.set_clock(Clock(100 + index, 1_234_567_890, 0, 0, 1_234_567_890 + index))
        instruction_name, spec, metas = self._metas(step)
        before = self.snapshot()
        blockhash = self.vm.latest_blockhash()
        tx = Transaction.new_signed_with_payer(
            [
                set_compute_unit_limit(1_400_000),
                Instruction(PUMP, bytes(spec["discriminator"]), metas),
            ],
            PAYER.pubkey(),
            [PAYER, USER],
            blockhash,
        )
        signature_checks = list(tx.verify_with_results())
        if not signature_checks or not all(signature_checks):
            raise ValueError("locally constructed transaction failed signature verification")
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        metadata = json.loads(meta.to_json())
        logs = list(meta.logs())
        after = self.snapshot()
        nonfee_before = {k: v for k, v in before.items() if k != str(PAYER.pubkey())}
        nonfee_after = {k: v for k, v in after.items() if k != str(PAYER.pubkey())}
        error = str(result.err()) if failed else None
        return {
            "step": step["name"],
            "instruction": instruction_name,
            "recent_blockhash": str(blockhash),
            "transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "signature": str(tx.signatures[0]),
            "signatures_distinct_input": True,
            "signature_verification": signature_checks,
            "message_sha256": sha256_bytes(bytes(tx.message)),
            "error": error,
            "outcome": outcome(logs, error),
            "failure_class": failure_class(error),
            "compute_units": meta.compute_units_consumed(),
            "logs": logs,
            "semantic_logs": semantic_logs(logs),
            "events": [line[14:] for line in logs if line.startswith("Program data: ")],
            "inner_instructions": metadata.get("inner_instructions"),
            "return_data": metadata.get("return_data"),
            "before_hash": canonical_hash(before),
            "after_hash": canonical_hash(after),
            "before": before,
            "after": after,
            "rollback_nonfee_equal": None if not failed else nonfee_before == nonfee_after,
            "nonfee_state_equal": nonfee_before == nonfee_after,
        }


def scenarios():
    success = [
        {"name": "migrate", "remaining_count": 2},
        {"name": "repeat-with-fresh-signature", "remaining_count": 2},
    ]
    return [
        {"name": "legacy/native-success-repeat", "family": "legacy", "steps": success},
        {"name": "legacy/disabled-flag-observed", "family": "legacy", "enable_migrate": 0, "steps": success},
        {"name": "legacy/mayhem-success-repeat", "family": "legacy", "mayhem": 1, "steps": success},
        {"name": "legacy/incomplete-rollback", "family": "legacy", "complete": 0,
         "steps": [{"name": "migrate", "remaining_count": 2}]},
        {"name": "legacy/missing-boost-rollback", "family": "legacy",
         "steps": [{"name": "migrate", "remaining_count": 0}]},
        {"name": "legacy/insufficient-base-rollback", "family": "legacy", "base_amount": 0,
         "steps": [{"name": "migrate", "remaining_count": 2}]},
        {"name": "v2/native-token22-success-repeat", "family": "v2", "base_token22": True,
         "quote_mode": "native", "steps": success},
        {"name": "v2/native-spl-success-repeat", "family": "v2", "quote_mode": "native", "steps": success},
        {"name": "v2/stable-spl-success-repeat", "family": "v2", "quote_mode": "spl", "steps": success},
        {"name": "v2/stable-token22-success-repeat", "family": "v2", "quote_mode": "token22", "steps": success},
        {"name": "v2/stable-token22-transfer-fee-success-repeat", "family": "v2", "quote_mode": "token22",
         "quote_transfer_fee_bps": 100, "steps": [
             {"name": "migrate", "remaining_count": 2, "writable": ["quote_mint"]},
             {"name": "repeat-with-fresh-signature", "remaining_count": 2,
              "writable": ["quote_mint"]},
         ]},
        {"name": "v2/nonwhitelisted-stable-observed", "family": "v2", "quote_mode": "spl",
         "quote_whitelisted": False, "steps": success},
        {"name": "v2/disabled-flag-observed", "family": "v2", "base_token22": True,
         "quote_mode": "native", "enable_migrate": 0, "steps": success},
        {"name": "v2/mint-authority-set-observed", "family": "v2", "quote_mode": "native",
         "mint_authority": True, "steps": success},
        {"name": "v2/freeze-authority-set-observed", "family": "v2", "quote_mode": "native",
         "freeze_authority": True, "steps": success},
        {"name": "v2/incomplete-rollback", "family": "v2", "quote_mode": "native", "complete": 0,
         "steps": [{"name": "migrate", "remaining_count": 2}]},
        {"name": "v2/missing-boost-rollback", "family": "v2", "quote_mode": "native",
         "steps": [{"name": "migrate", "remaining_count": 0}]},
        {"name": "v2/readonly-boost-vault-rollback", "family": "v2", "quote_mode": "native",
         "steps": [{"name": "migrate", "remaining_count": 2, "readonly": ["boost_vault"]}]},
        {"name": "v2/readonly-pool-base-rollback", "family": "v2", "quote_mode": "native",
         "steps": [{"name": "migrate", "remaining_count": 2, "readonly": ["pool_base_token_account"]}]},
        {"name": "v2/readonly-pool-quote-rollback", "family": "v2", "quote_mode": "native",
         "steps": [{"name": "migrate", "remaining_count": 2, "readonly": ["pool_quote_token_account"]}]},
        {"name": "v2/insufficient-base-rollback", "family": "v2", "quote_mode": "native", "base_amount": 0,
         "steps": [{"name": "migrate", "remaining_count": 2}]},
        {"name": "v2/insufficient-quote-rollback", "family": "v2", "quote_mode": "spl", "quote_amount": 0,
         "steps": [{"name": "migrate", "remaining_count": 2}]},
        {"name": "v2/invalid-base-mint-owner", "family": "v2", "quote_mode": "native",
         "invalid_base_mint_owner": True, "steps": [{"name": "migrate", "remaining_count": 2}]},
        {"name": "v2/invalid-base-account-owner", "family": "v2", "quote_mode": "native",
         "invalid_base_account_owner": True, "steps": [{"name": "migrate", "remaining_count": 2}]},
        {"name": "v2/invalid-quote-account-owner", "family": "v2", "quote_mode": "spl",
         "invalid_quote_account_owner": True, "steps": [{"name": "migrate", "remaining_count": 2}]},
        {"name": "v2/wrong-pump-amm-event-authority", "family": "v2", "quote_mode": "native",
         "steps": [{"name": "migrate", "remaining_count": 2, "wrong": "pump_amm_event_authority"}]},
        {"name": "v2/committed-then-invalid-then-repeat", "family": "v2", "base_token22": True,
         "quote_mode": "native", "steps": [
             {"name": "migrate", "remaining_count": 2},
             {"name": "invalid-event-authority-after-commit", "remaining_count": 2,
              "wrong": "pump_amm_event_authority"},
             {"name": "valid-repeat-after-failed-attempt", "remaining_count": 2},
         ]},
    ]


def run_image(image, scenario):
    harness = MigrationHarness(image, scenario)
    initial = harness.snapshot()
    receipts = [harness.execute(step, i) for i, step in enumerate(scenario["steps"], 1)]
    signatures = [r["signature"] for r in receipts]
    if len(signatures) != len(set(signatures)):
        raise ValueError(f"replayed signature in {scenario['name']}")
    for receipt in receipts:
        receipt["signatures_distinct_input"] = len(signatures) == len(set(signatures))
    return {
        "initial_state_hash": canonical_hash(initial),
        "account_names": {name: str(key) for name, key in harness.names.items()},
        "receipts": receipts,
    }


def compare_runs(original, candidate):
    mismatches = []
    if original["initial_state_hash"] != candidate["initial_state_hash"]:
        mismatches.append("initial_state_hash")
    if len(original["receipts"]) != len(candidate["receipts"]):
        mismatches.append("receipt_count")
        return mismatches, []
    steps = []
    for left, right in zip(original["receipts"], candidate["receipts"]):
        different = [field for field in STRICT_FIELDS if left.get(field) != right.get(field)]
        diagnostic = [field for field in ("logs", "compute_units") if left.get(field) != right.get(field)]
        steps.append({"step": left["step"], "mismatch_fields": different,
                      "diagnostic_difference_fields": diagnostic})
        mismatches.extend(f"{left['step']}:{field}" for field in different)
    return mismatches, steps


def program_hashes(candidate):
    values = {name: sha256_file(path) for name, path in CAPTURED_PROGRAMS.items()}
    values["pump_candidate"] = sha256_file(candidate)
    return values


def account_amount(snapshot, key):
    account = snapshot.get(key)
    if not account:
        return None
    data = bytes.fromhex(account["data_hex"])
    return int.from_bytes(data[64:72], "little") if len(data) >= 72 else None


def validate_lifecycle(run):
    failures = []
    receipts = run["receipts"]
    signatures = [receipt["signature"] for receipt in receipts]
    if len(signatures) != len(set(signatures)):
        failures.append("duplicate-transaction-signature")
    for receipt in receipts:
        if not all(receipt["signature_verification"]):
            failures.append(receipt["step"] + ":signature-verification")
        if receipt["error"] and receipt["rollback_nonfee_equal"] is not True:
            failures.append(receipt["step"] + ":failure-not-atomic")
        if "repeat" in receipt["step"] and receipt["outcome"] == "ok":
            if not receipt["nonfee_state_equal"]:
                failures.append(receipt["step"] + ":repeat-changed-state")
            if receipt["events"]:
                failures.append(receipt["step"] + ":repeat-emitted-event")

    first = receipts[0]
    if first["outcome"] == "ok":
        names = run["account_names"]
        after = first["after"]
        curve = after[names["bonding_curve"]]
        curve_data = bytes.fromhex(curve["data_hex"])
        reserves = [int.from_bytes(curve_data[offset:offset + 8], "little")
                    for offset in (8, 16, 24, 32)]
        if reserves != [0, 0, 0, 0]:
            failures.append("migrate:curve-reserves-not-zero")
        pool = after[names["pool"]]
        if not pool or pool["owner"] != str(PUMP_AMM) or not pool["data_hex"]:
            failures.append("migrate:pool-not-created")
        if account_amount(after, names["associated_base_bonding_curve"]) != 0:
            failures.append("migrate:source-base-not-drained")
        if not (account_amount(after, names["pool_base_token_account"]) or 0) > 0:
            failures.append("migrate:pool-base-not-funded")
        if not (account_amount(after, names["pool_quote_token_account"]) or 0) > 0:
            failures.append("migrate:pool-quote-not-funded")
        lp = after[names["lp_mint"]]
        lp_data = bytes.fromhex(lp["data_hex"]) if lp else b""
        if (not lp or lp["owner"] != str(TOKEN22) or len(lp_data) < 44
                or int.from_bytes(lp_data[36:44], "little") != 0):
            failures.append("migrate:lp-mint-not-burned-to-zero")
        for temporary in (
            "user_pool_token_account",
            "pool_authority_mint_account",
            "pool_authority_quote_account",
        ):
            if after[names[temporary]] is not None:
                failures.append("migrate:" + temporary + "-not-closed")
        if first["nonfee_state_equal"]:
            failures.append("migrate:success-did-not-change-state")
    return failures


def run_suite(candidate):
    candidate = Path(candidate).resolve()
    hashes = program_hashes(candidate)
    fixture_hash = sha256_file(FIXTURE_PATH)
    rows = []
    for scenario in scenarios():
        original = run_image(CAPTURED_PROGRAMS["pump_original"], scenario)
        rebuilt = run_image(candidate, scenario)
        mismatches, step_comparison = compare_runs(original, rebuilt)
        observed_outcomes = [receipt["outcome"] for receipt in original["receipts"]]
        expected_outcomes = EXPECTED_OUTCOMES.get(scenario["name"])
        oracle_mismatches = [] if observed_outcomes == expected_outcomes else [
            {"expected": expected_outcomes, "observed": observed_outcomes}
        ]
        invariant_failures = {
            "original": validate_lifecycle(original),
            "candidate": validate_lifecycle(rebuilt),
        }
        rollback_failures = []
        infrastructure_failures = []
        for role, run in (("original", original), ("candidate", rebuilt)):
            for receipt in run["receipts"]:
                if receipt["error"] and receipt["rollback_nonfee_equal"] is not True:
                    rollback_failures.append(f"{role}:{receipt['step']}")
                if receipt["failure_class"] == "infrastructure":
                    infrastructure_failures.append(f"{role}:{receipt['step']}")
        rows.append({
            "case": scenario["name"],
            "instruction": "migrate" if scenario["family"] == "legacy" else "migrate_v2",
            "fixture_sha256": fixture_hash,
            "program_sha256": hashes,
            "config": {k: v for k, v in scenario.items() if k not in ("steps",)},
            "steps": scenario["steps"],
            "original": original,
            "candidate": rebuilt,
            "comparison": step_comparison,
            "mismatch_fields": mismatches,
            "expected_original_outcomes": expected_outcomes,
            "observed_original_outcomes": observed_outcomes,
            "oracle_mismatches": oracle_mismatches,
            "invariant_failures": invariant_failures,
            "rollback_failures": rollback_failures,
            "infrastructure_failures": infrastructure_failures,
        })
    return {
        "schema": "pump-migration-lifecycle-v1",
        "scope": "Authenticated persistent legacy migrate and migrate_v2 lifecycle differential; synthetic state, captured programs, local LiteSVM, no network.",
        "upstream_sha": "7e26cbf36c5c0c824e3eb36417ce8a35866f530a",
        "program_ids": PROGRAM_IDS,
        "program_sha256": hashes,
        "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
        "fixture_sha256": fixture_hash,
        "idl_sha256": sha256_file(IDL_PATH),
        "case_count": len(rows),
        "transaction_count_per_image": sum(len(row["original"]["receipts"]) for row in rows),
        "mismatch_cases": [row["case"] for row in rows if row["mismatch_fields"]],
        "oracle_mismatch_cases": [row["case"] for row in rows if row["oracle_mismatches"]],
        "invariant_failure_cases": [row["case"] for row in rows
                                    if any(row["invariant_failures"].values())],
        "rollback_failure_cases": [row["case"] for row in rows if row["rollback_failures"]],
        "infrastructure_failure_cases": [row["case"] for row in rows if row["infrastructure_failures"]],
        "cases": rows,
    }


def negative_control(report):
    """Prove strict comparison notices both an altered error and altered state."""
    base = report["cases"][0]
    checks = {}
    for field, mutate in (
        ("error", lambda r: r.update(error="negative-control-error")),
        ("after", lambda r: r["after"].update({"negative-control": None})),
    ):
        changed = copy.deepcopy(base["candidate"])
        mutate(changed["receipts"][0])
        different, _ = compare_runs(base["original"], changed)
        checks[field] = any(item.endswith(":" + field) for item in different)
    return checks


def write_report(path, report):
    raw = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-mismatches", action="store_true")
    args = parser.parse_args()
    report = run_suite(args.candidate)
    report["negative_controls"] = negative_control(report)
    write_report(args.output, report)
    summary = {k: report[k] for k in (
        "case_count", "transaction_count_per_image", "mismatch_cases",
        "oracle_mismatch_cases", "invariant_failure_cases", "rollback_failure_cases",
        "infrastructure_failure_cases", "negative_controls",
    )}
    print(json.dumps(summary, indent=2))
    failed = (
        report["mismatch_cases"]
        or report["oracle_mismatch_cases"]
        or report["invariant_failure_cases"]
        or report["rollback_failure_cases"]
        or report["infrastructure_failure_cases"]
        or not all(report["negative_controls"].values())
    )
    return 0 if args.allow_mismatches or not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
