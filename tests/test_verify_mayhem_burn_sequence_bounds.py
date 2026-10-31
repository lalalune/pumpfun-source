"""Bounds, input-binding, and UTF-8 checks for verify_mayhem_burn_sequence.py."""

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from solders.compute_budget import set_compute_unit_limit
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction

REPO = Path(__file__).resolve().parents[1]
VERIFIER = REPO / "scripts/verify_mayhem_burn_sequence.py"
RUNNER = REPO / "scripts/mayhem_burn_sequence.py"
ORIGINAL_SO = REPO / "evidence/original/mayhem/deployed.so"

FIELDS = [
    "mayhem_state",
    "mint",
    "mayhem_token_vault",
    "sol_vault",
    "bonding_curve",
    "global",
    "pump_program",
    "pump_event_authority",
    "system_program",
    "token_program",
    "event_authority",
    "program",
]


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def account_snapshot(data: bytes, owner: str, lamports: int = 1_000_000) -> dict:
    return {
        "lamports": lamports,
        "owner": owner,
        "executable": False,
        "rent_epoch": 0,
        "data_bytes": len(data),
        "data_sha256": sha256_hex(data),
        "data_base64": base64.b64encode(data).decode("ascii"),
    }


def executable_snapshot(owner: str = "BPFLoader2111111111111111111111111111111111") -> dict:
    return {
        "lamports": 1,
        "owner": owner,
        "executable": True,
        "rent_epoch": 0,
        "data_bytes": 8,
        "data_sha256": "00" * 32,
        "data_base64": None,
    }


class VerifyMayhemBurnSequenceBoundsTests(unittest.TestCase):
    def build_valid_bundle(self, root: Path, extra_log: str = "Program log: burn ok"):
        fixtures = root / "fixtures"
        receipts = root / "receipts"
        fixtures.mkdir()
        receipts.mkdir()

        original_sha = sha256_hex(ORIGINAL_SO.read_bytes())
        candidate_path = root / "candidate.so"
        candidate_bytes = b"\x7fELF-synthetic-candidate-mayhem"
        candidate_path.write_bytes(candidate_bytes)
        candidate_sha = sha256_hex(candidate_bytes)

        shared_pubkeys = {
            "global": str(Keypair.from_seed(bytes([40]) * 32).pubkey()),
            "pump_program": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
            "pump_event_authority": str(Keypair.from_seed(bytes([41]) * 32).pubkey()),
            "system_program": "11111111111111111111111111111111",
            "token_program": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
            "event_authority": str(Keypair.from_seed(bytes([42]) * 32).pubkey()),
            "program": "MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e",
        }
        executable_keys = {
            shared_pubkeys["pump_program"],
            shared_pubkeys["system_program"],
            shared_pubkeys["token_program"],
            shared_pubkeys["program"],
        }

        captured_accounts = {
            shared_pubkeys["event_authority"]: {"exists": False},
        }
        for key in executable_keys:
            captured_accounts[key] = {"exists": False}

        for shared_field in ("global", "pump_event_authority"):
            key = shared_pubkeys[shared_field]
            rel_file = f"{shared_field}.bin"
            raw = bytes([7]) * 16
            (fixtures / rel_file).write_bytes(raw)
            captured_accounts[key] = {
                "exists": True,
                "executable": False,
                "owner": shared_pubkeys["program"],
                "lamports": 1_000_000,
                "rentEpoch": 0,
                "data_file": rel_file,
                "data_sha256": sha256_hex(raw),
            }

        families = []
        cases = []
        for idx in range(3):
            supply = 10_000 + idx * 1_000
            amount = 1_000 + idx * 100
            timestamp = 1_700_000_000 + idx
            fields = dict(shared_pubkeys)
            for offset, name in enumerate(
                ("mayhem_state", "mint", "mayhem_token_vault", "sol_vault", "bonding_curve")
            ):
                fields[name] = str(Keypair.from_seed(bytes([50 + idx * 10 + offset]) * 32).pubkey())

            state_before = bytearray(106)
            state_before[97] = 1
            struct.pack_into("<Q", state_before, 98, 0)
            state_after = bytearray(state_before)
            state_after[97] = 2
            struct.pack_into("<Q", state_after, 98, amount)

            mint_before = bytearray(82)
            struct.pack_into("<Q", mint_before, 36, supply)
            mint_after = bytearray(mint_before)
            struct.pack_into("<Q", mint_after, 36, supply - amount)

            vault_before = bytearray(165)
            struct.pack_into("<Q", vault_before, 64, amount)
            vault_after = bytearray(vault_before)
            struct.pack_into("<Q", vault_after, 64, 0)

            per_family_blobs = {
                "mayhem_state": (bytes(state_before), bytes(state_after)),
                "mint": (bytes(mint_before), bytes(mint_after)),
                "mayhem_token_vault": (bytes(vault_before), bytes(vault_after)),
                "sol_vault": (bytes([9]) * 16, bytes([9]) * 16),
                "bonding_curve": (bytes([11]) * 16, bytes([11]) * 16),
            }
            for field_name, (before_raw, _) in per_family_blobs.items():
                key = fields[field_name]
                rel_file = f"case-{idx}-{field_name}.bin"
                (fixtures / rel_file).write_bytes(before_raw)
                captured_accounts[key] = {
                    "exists": True,
                    "executable": False,
                    "owner": fields["program"],
                    "lamports": 1_000_000,
                    "rentEpoch": 0,
                    "data_file": rel_file,
                    "data_sha256": sha256_hex(before_raw),
                }

            families.append(
                {
                    "accounts": fields,
                    "mint": {"supply": supply},
                    "vault": {"amount": amount},
                    "clock": {"unix_timestamp": timestamp},
                }
            )

            payer = Keypair.from_seed(bytes([90 + idx]) * 32)
            payer_key = str(payer.pubkey())
            metas = [
                AccountMeta(Pubkey.from_string(fields[f]), False, pos < 5)
                for pos, f in enumerate(FIELDS)
            ]
            burn_ix = Instruction(
                Pubkey.from_string(fields["program"]),
                hashlib.sha256(b"global:burn_tokens").digest()[:8],
                metas,
            )
            bh1 = Hash.from_bytes(bytes([1 + idx]) * 32)
            bh2 = Hash.from_bytes(bytes([21 + idx]) * 32)
            tx1 = Transaction.new_signed_with_payer(
                [set_compute_unit_limit(1_000_000), burn_ix],
                payer.pubkey(),
                [payer],
                bh1,
            )
            tx2 = Transaction.new_signed_with_payer(
                [set_compute_unit_limit(1_000_000), burn_ix],
                payer.pubkey(),
                [payer],
                bh2,
            )
            raw1 = bytes(tx1)
            raw2 = bytes(tx2)
            msg_keys = list(map(str, tx1.message.account_keys))

            before_map = {
                payer_key: account_snapshot(b"", "11111111111111111111111111111111", 10_000_000_000),
                fields["event_authority"]: None,
            }
            after_map = {
                payer_key: account_snapshot(b"", "11111111111111111111111111111111", 10_000_000_000 - 5000),
                fields["event_authority"]: None,
            }
            for key in executable_keys:
                before_map[key] = executable_snapshot()
                after_map[key] = executable_snapshot()
            for shared_field in ("global", "pump_event_authority"):
                key = fields[shared_field]
                raw = (fixtures / captured_accounts[key]["data_file"]).read_bytes()
                before_map[key] = account_snapshot(raw, fields["program"])
                after_map[key] = account_snapshot(raw, fields["program"])
            for field_name, (before_raw, after_raw) in per_family_blobs.items():
                key = fields[field_name]
                before_map[key] = account_snapshot(before_raw, fields["program"])
                after_map[key] = account_snapshot(after_raw, fields["program"])

            second_after = dict(after_map)
            second_after[payer_key] = account_snapshot(
                b"", "11111111111111111111111111111111", 10_000_000_000 - 10_000
            )

            event = (
                hashlib.sha256(b"event:BurnEvent").digest()[:8]
                + struct.pack("<Q", amount)
                + bytes(Pubkey.from_string(fields["mint"]))
                + bytes(Pubkey.from_string(fields["mayhem_state"]))
                + struct.pack("<q", timestamp)
            )
            emit_data = bytes.fromhex("e445a52e51cb9a1d") + event
            burn_data = b"\x08" + struct.pack("<Q", amount)
            inner_instructions = [
                [],
                [
                    {
                        "stackHeight": 2,
                        "instruction": {
                            "programIdIndex": msg_keys.index(fields["token_program"]),
                            "accounts": [
                                [3],
                                msg_keys.index(fields["mayhem_token_vault"]),
                                msg_keys.index(fields["mint"]),
                                msg_keys.index(fields["sol_vault"]),
                            ],
                            "data": [[len(burn_data)], *burn_data],
                        },
                    },
                    {
                        "stackHeight": 2,
                        "instruction": {
                            "programIdIndex": msg_keys.index(fields["program"]),
                            "accounts": [[1], msg_keys.index(fields["event_authority"])],
                            "data": [[len(emit_data)], *emit_data],
                        },
                    },
                ],
            ]

            logs = [
                extra_log,
                "Program consumed 42000 of 1000000 compute units",
                "Program data: " + base64.b64encode(event).decode("ascii"),
            ]
            logs_norm = [
                extra_log,
                "Program consumed <units> of <budget> compute units",
                "Program data: " + base64.b64encode(event).decode("ascii"),
            ]
            second_logs = [
                "Program log: AnchorError thrown in programs/mayhem/src/lib.rs:88. Error Number: 6004.",
                "Program consumed 9000 of 1000000 compute units",
            ]
            second_logs_norm = [
                "Program log: AnchorError thrown in programs/mayhem/src/lib.rs:88. Error Number: 6004.",
                "Program consumed <units> of <budget> compute units",
            ]

            def side_payload(binary_sha: str) -> dict:
                return {
                    "binary_sha256": binary_sha,
                    "error": None,
                    "runtime_sigverify": True,
                    "runtime_blockhash_check": True,
                    "ordinary_payer": payer_key,
                    "transaction_base64": base64.b64encode(raw1).decode("ascii"),
                    "transaction_sha256": sha256_hex(raw1),
                    "before": copy.deepcopy(before_map),
                    "after": copy.deepcopy(after_map),
                    "parsed_after": {
                        "status": 2,
                        "burned_amount": amount,
                        "mint_supply": supply - amount,
                        "vault_amount": 0,
                    },
                    "events": ["Program data: " + base64.b64encode(event).decode("ascii")],
                    "inner_instructions": copy.deepcopy(inner_instructions),
                    "return_data": None,
                    "logs": list(logs),
                    "logs_without_compute_numbers": list(logs_norm),
                    "metadata": {"logs": list(logs)},
                    "compute_units_consumed": 42000,
                    "sequential_second": {
                        "transaction_base64": base64.b64encode(raw2).decode("ascii"),
                        "transaction_sha256": sha256_hex(raw2),
                        "new_blockhash": str(bh2),
                        "first_blockhash": str(bh1),
                        "before": copy.deepcopy(after_map),
                        "after": copy.deepcopy(second_after),
                        "error": "InstructionError(1, InstructionErrorCustom(6004))",
                        "metadata": {"inner_instructions": [[], []], "logs": list(second_logs)},
                        "logs_without_compute_numbers": list(second_logs_norm),
                    },
                }

            for side in ("original", "candidate"):
                (receipts / f"{idx}-{side}.transaction.bin").write_bytes(raw1)
                (receipts / f"{idx}-{side}.second.transaction.bin").write_bytes(raw2)

            case_obj = {
                "index": idx,
                "mint": fields["mint"],
                "original": side_payload(original_sha),
                "candidate": side_payload(candidate_sha),
                "same_signed_message": True,
                "different_fields": [],
            }
            cases.append(case_obj)
            (receipts / f"case-{idx}.json").write_text(
                json.dumps(case_obj, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )

        manifest = {
            "snapshots": {"eligible": {"accounts": captured_accounts}},
            "eligible_families": families,
        }
        manifest_path = fixtures / "fixture-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        input_sha256 = {
            "fixtures:fixture-manifest.json": sha256_hex(manifest_path.read_bytes()),
            "evidence/original/mayhem/deployed.so": original_sha,
        }
        for row in captured_accounts.values():
            if row["exists"]:
                input_sha256["fixtures:" + row["data_file"]] = sha256_hex(
                    (fixtures / row["data_file"]).read_bytes()
                )

        comparison = {
            "case_count": 3,
            "signed_transactions": 12,
            "inputs_unchanged": True,
            "mismatches": [],
            "input_sha256": input_sha256,
            "runner_sha256": sha256_hex(RUNNER.read_bytes()),
            "cases": cases,
        }
        (receipts / "comparison.json").write_text(
            json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return fixtures, receipts, manifest, comparison

    def invoke(self, fixtures: Path, receipts: Path, env=None):
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(VERIFIER),
                "--fixtures",
                str(fixtures),
                "--receipts",
                str(receipts),
            ],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def write_json(self, path: Path, obj: dict):
        path.write_text(
            json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def test_valid_three_family_bundle_verifies_under_c_locale(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures, receipts, _, _ = self.build_valid_bundle(
                Path(tmp), extra_log="Program log: burn sequence \u2192 verified"
            )
            env = dict(
                os.environ,
                LC_ALL="C",
                LANG="C",
                PYTHONUTF8="0",
                PYTHONCOERCECLOCALE="0",
            )
            result = self.invoke(fixtures, receipts, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            verification = json.loads((receipts / "verification.json").read_text(encoding="utf-8"))
            self.assertTrue(verification["success"])
            self.assertEqual(len(verification["cases"]), 3)
            self.assertEqual(verification["case_count"], 6)

    def test_explicit_external_candidate_input_stays_bound_to_its_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            fixtures, receipts, _, comparison = self.build_valid_bundle(root)
            candidate = root / "candidate.so"
            comparison["input_sha256"][candidate.as_posix()] = sha256_hex(candidate.read_bytes())
            self.write_json(receipts / "comparison.json", comparison)
            accepted = self.invoke(fixtures, receipts)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            (receipts / "verification.json").unlink()
            candidate.write_bytes(b"changed candidate")
            refused = self.invoke(fixtures, receipts)
            self.assertNotEqual(refused.returncode, 0)
            self.assertFalse((receipts / "verification.json").exists())

    def test_unrelated_external_input_is_not_admitted_as_the_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            fixtures, receipts, _, comparison = self.build_valid_bundle(root)
            unrelated = root / "unrelated.bin"
            unrelated.write_bytes(b"unrelated input")
            comparison["input_sha256"][unrelated.as_posix()] = sha256_hex(unrelated.read_bytes())
            self.write_json(receipts / "comparison.json", comparison)
            refused = self.invoke(fixtures, receipts)
            self.assertNotEqual(refused.returncode, 0)
            self.assertFalse((receipts / "verification.json").exists())

    def test_truncated_families_or_cases_are_rejected(self):
        for kind in ("empty_families", "single_family", "single_case"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                fixtures, receipts, manifest, comparison = self.build_valid_bundle(Path(tmp))
                if kind == "empty_families":
                    manifest["eligible_families"] = []
                elif kind == "single_family":
                    manifest["eligible_families"] = manifest["eligible_families"][:1]
                elif kind == "single_case":
                    comparison["cases"] = comparison["cases"][:1]
                manifest_path = fixtures / "fixture-manifest.json"
                self.write_json(manifest_path, manifest)
                comparison["input_sha256"]["fixtures:fixture-manifest.json"] = sha256_hex(
                    manifest_path.read_bytes()
                )
                self.write_json(receipts / "comparison.json", comparison)

                result = self.invoke(fixtures, receipts)
                self.assertNotEqual(result.returncode, 0, kind)
                self.assertFalse((receipts / "verification.json").exists())

    def test_missing_required_input_bindings_are_rejected(self):
        for kind in ("empty_inputs", "missing_manifest", "missing_original", "missing_account_blob"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                fixtures, receipts, _, comparison = self.build_valid_bundle(Path(tmp))
                if kind == "empty_inputs":
                    comparison["input_sha256"] = {}
                elif kind == "missing_manifest":
                    comparison["input_sha256"].pop("fixtures:fixture-manifest.json")
                elif kind == "missing_original":
                    comparison["input_sha256"].pop("evidence/original/mayhem/deployed.so")
                elif kind == "missing_account_blob":
                    blob_key = next(
                        k
                        for k in comparison["input_sha256"]
                        if k.startswith("fixtures:") and k != "fixtures:fixture-manifest.json"
                    )
                    comparison["input_sha256"].pop(blob_key)
                self.write_json(receipts / "comparison.json", comparison)

                result = self.invoke(fixtures, receipts)
                self.assertNotEqual(result.returncode, 0, kind)
                self.assertFalse((receipts / "verification.json").exists())

    def test_inconsistent_or_forged_binary_hashes_are_rejected(self):
        for kind in ("forged_original_sha", "mixed_original_sha", "mixed_candidate_sha"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                fixtures, receipts, _, comparison = self.build_valid_bundle(Path(tmp))
                if kind == "forged_original_sha":
                    for idx, case in enumerate(comparison["cases"]):
                        case["original"]["binary_sha256"] = "00" * 32
                        self.write_json(receipts / f"case-{idx}.json", case)
                elif kind == "mixed_original_sha":
                    comparison["cases"][1]["original"]["binary_sha256"] = "11" * 32
                    self.write_json(receipts / "case-1.json", comparison["cases"][1])
                elif kind == "mixed_candidate_sha":
                    comparison["cases"][2]["candidate"]["binary_sha256"] = "22" * 32
                    self.write_json(receipts / "case-2.json", comparison["cases"][2])
                self.write_json(receipts / "comparison.json", comparison)

                result = self.invoke(fixtures, receipts)
                self.assertNotEqual(result.returncode, 0, kind)
                self.assertFalse((receipts / "verification.json").exists())


if __name__ == "__main__":
    unittest.main()
