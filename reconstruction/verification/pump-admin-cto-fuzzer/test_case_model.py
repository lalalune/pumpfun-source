import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import case_model as model


class CaseModelTests(unittest.TestCase):
    def test_seed_replay_is_exact_and_duplicate_free(self):
        first = model.generate_corpus(20261101, 64)
        second = model.generate_corpus(20261101, 64)
        self.assertEqual(first, second)
        self.assertEqual(len({row["case_id"] for row in first}), 64)
        for index, row in enumerate(first):
            self.assertEqual(row, model.generate_case(20261101, index))

    def test_generation_is_python_hash_seed_independent(self):
        script = ("import json,sys;sys.path.insert(0,sys.argv[1]);"
                  "import case_model;print(json.dumps(case_model.generate_corpus(9,12),sort_keys=True))")
        outputs = []
        for seed in ("1", "987654"):
            env = dict(__import__("os").environ, PYTHONHASHSEED=seed)
            outputs.append(subprocess.check_output(
                [sys.executable, "-c", script, str(Path(__file__).resolve().parent)], env=env))
        self.assertEqual(outputs[0], outputs[1])

    def test_tampered_case_identity_is_rejected(self):
        case = model.generate_case(1, 2)
        changed = copy.deepcopy(case)
        changed["steps"][0]["fee"] = 123
        with self.assertRaisesRegex(ValueError, "identity"):
            model.validate_case(changed)

    def test_case_manifest_is_compact_and_complete(self):
        case = model.generate_case(7, 11)
        encoded = model.canonical(case)
        self.assertLess(len(encoded), 4096)
        decoded = json.loads(encoded)
        self.assertEqual(model.validate_case(decoded), case)
        self.assertEqual(decoded["case_seed"], model.derive_case_seed(7, 11))

    def test_invalid_seed_and_count_domains_fail_closed(self):
        for value in (-1, 2**128, True):
            with self.assertRaises(ValueError):
                model.generate_case(value, 0)
        for index in (-1, 2**64, True):
            with self.assertRaises(ValueError):
                model.generate_case(1, index)
        for value in (0, 10001, True):
            with self.assertRaises(ValueError):
                model.generate_corpus(0, value)

    def simple_case(self, mode="native"):
        case = model.generate_case(13, 0)
        case.update(config={"mints": [mode]}, initial_mutations=[],
                    steps=[{"name": "change-creator", "op": "admin_cto", "new": 1}])
        case["case_id"] = model.case_identity(case)
        return model.validate_case(case)

    def reject_resealed(self, change, mode="native"):
        case = self.simple_case(mode)
        change(case)
        with self.assertRaises(ValueError):
            # Invalid nested fields remain invalid after a fresh identity hash.
            case["case_id"] = model.case_identity(case)
            model.validate_case(case)

    def test_resealed_unknown_fields_and_coerced_booleans_are_not_cases(self):
        changes = [
            lambda c: c.update(ignored=True),
            lambda c: c["config"].update(ignored=True),
            lambda c: c["steps"][0].update(ignored=True),
            lambda c: c["config"].update(shared=1),
            lambda c: c["config"].update(complete="false"),
            lambda c: c["config"].update(holder_initial=0),
            lambda c: c["steps"][0].update(holder=1),
            lambda c: c["steps"][0].update(new_none=[]),
            lambda c: c["steps"][0].update(fee=True),
            lambda c: c["steps"][0].update(new=False),
            lambda c: c["config"].update(native_vault_lamports=True),
            lambda c: c["config"].update(spl_vault_tokens=1),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                self.reject_resealed(change)
        self.reject_resealed(lambda c: c["config"].update(frozen_wallet=1), "spl")
        self.reject_resealed(lambda c: c["config"].update(spl_vault_tokens=2**64), "token22")

    def test_resealed_names_indices_and_argument_domains_are_unambiguous(self):
        changes = [
            lambda c: c["steps"].append(copy.deepcopy(c["steps"][0])),
            lambda c: c["steps"][0].update(name=""),
            lambda c: c["steps"][0].update(name="   "),
            lambda c: c["steps"][0].update(name="bad\nname"),
            lambda c: c["steps"][0].update(name="x" * 129),
            lambda c: c["steps"][0].update(op="collect"),
            lambda c: c["steps"][0].update(new=4),
            lambda c: c["steps"][0].update(new_none=True),
            lambda c: c["steps"][0].update(fee=-1),
            lambda c: c["steps"][0].update(fee=2**64),
            lambda c: c["steps"][0].update(wrong="not-a-role"),
            lambda c: c["steps"][0].update(readonly=[True]),
            lambda c: c["steps"][0].update(readonly=[0, 0]),
            lambda c: c["steps"][0].update(readonly=[28]),
            lambda c: c["steps"][0].update(readonly="0"),
            lambda c: c["steps"][0].update(drop_accounts=28),
            lambda c: c["steps"][0].update(replace_accounts=[{"index": 0, "creator": 4}]),
            lambda c: c["steps"][0].update(replace_accounts=[{"index": 0, "creator": 1,
                                                           "ignored": 1}]),
            lambda c: c["steps"][0].update(replace_accounts=[{"index": 0, "creator": 1},
                                                           {"index": 0, "creator": 2}]),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                self.reject_resealed(change)

    def test_resealed_mutations_require_typed_bounded_action_fields(self):
        invalid = [
            {"target": "missing", "action": "owner", "value": "system"},
            {"target": "curve", "action": "missing", "value": 0},
            {"target": "curve", "action": "set_byte", "value": 0},
            {"target": "curve", "action": "set_byte", "offset": True, "value": 0},
            {"target": "curve", "action": "set_byte", "offset": 0, "value": 256},
            {"target": "curve", "action": "set_byte", "offset": 16_384, "value": 0},
            {"target": "curve", "action": "truncate", "value": 16_385},
            {"target": "curve", "action": "owner", "value": "system", "offset": 0},
            {"target": "curve", "action": "owner", "value": 0},
            {"target": "curve", "action": "lamports", "value": True},
            {"target": "curve", "action": "token_amount", "value": 0},
            {"target": "creator_vault_token", "action": "token_state", "value": 1},
            {"target": "curve", "action": "lamports", "value": 0, "ignored": 1},
        ]
        for mutation in invalid:
            with self.subTest(mutation=mutation):
                self.reject_resealed(lambda c: c.update(initial_mutations=[mutation]))
        self.reject_resealed(lambda c: c.update(initial_mutations=[
            {"target": "amm_vault_token", "action": "token_state", "value": 256}]), "spl")
        for mutation in [
            {"action": "append", "value": "0"}, {"action": "append", "value": "FF"},
            {"action": "append", "value": "00 00"}, {"action": "append", "value": "00" * 1025},
            {"action": "truncate", "value": True}, {"action": "holder_tag", "value": 256},
            {"action": "append", "value": "00", "ignored": True},
        ]:
            with self.subTest(instruction_mutation=mutation):
                self.reject_resealed(lambda c: c["steps"][0].update(instruction_mutation=mutation))

    def test_reduction_defaults_and_valid_extreme_values_remain_representable(self):
        for mode in model.MODES:
            case = self.simple_case(mode)
            step = case["steps"][0]
            step.update(new=3, holder=False, fee=2**64 - 1, readonly=[0, 27],
                        replace_accounts=[{"index": 0, "creator": 0},
                                          {"index": 27, "creator": 3}],
                        drop_accounts=27, instruction_mutation={"action": "append", "value": "00ff"})
            case["initial_mutations"] = [
                {"target": "curve", "action": "set_byte", "offset": 0, "value": 255},
                {"target": "global", "action": "lamports", "value": 2**64 - 1},
            ]
            case["case_id"] = model.case_identity(case)
            self.assertEqual(model.validate_case(case), case)
            # Reductions may remove optional config and step fields entirely.
            step.clear()
            step.update(name="reduced", op="admin_cto")
            case["initial_mutations"] = []
            case["case_id"] = model.case_identity(case)
            self.assertEqual(model.validate_case(case), case)

    def test_index_overflow_and_nonfinite_data_are_rejected_before_generation(self):
        for index, count in [(True, 1), (-1, 1), (2**64, 1), (2**64 - 1, 2)]:
            with self.subTest(index=index, count=count), self.assertRaises(ValueError):
                model.generate_corpus(0, count, index)
        self.assertEqual(len(model.generate_corpus(0, 1, 2**64 - 1)), 1)
        with self.assertRaises(ValueError):
            model.canonical({"value": float("nan")})


if __name__ == "__main__":
    unittest.main()
