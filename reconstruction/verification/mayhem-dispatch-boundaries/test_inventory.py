#!/usr/bin/env python3
import importlib.util
import json
import pathlib
import unittest


HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("mayhem_inventory", HERE / "inventory.py")
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def test_all_25_selectors_are_anchor_hashes(self):
        self.assertEqual(len(inventory.INSTRUCTIONS), 25)
        for row in inventory.INSTRUCTIONS:
            self.assertEqual(inventory.selector(row["name"]).hex(), row["discriminator"])

    def test_inventory_equals_captured_dispatch_map(self):
        root = HERE.parents[2]
        captured = json.loads((root / "evidence/dispatch-map.json").read_text())["mayhem"]
        expected = {row["name"]: row["discriminator"] for row in inventory.INSTRUCTIONS}
        actual = {name: row["discriminator"] for name, row in captured["instructions"].items()}
        self.assertEqual(actual, expected)
        self.assertEqual(captured["binary_sha256"],
                         "a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb")

    def test_argument_widths(self):
        expected = {"none": 0, inventory.TRADE: 20, "u64": 8, "u8": 1,
                    "pubkey": 32, inventory.OPTIONS: 16}
        for row in inventory.INSTRUCTIONS:
            self.assertEqual(len(inventory.default_args(row["args"])), expected[row["args"]])

    def test_option_cases_are_bounded(self):
        variants = inventory.argument_variants(inventory.OPTIONS)
        self.assertEqual(sum("invalid-tag" in label for label, _ in variants), 16)
        self.assertEqual(sum("truncated-body" in label for label, _ in variants), 16)
        self.assertLess(max(map(len, (data for _, data in variants))), 256)

    def test_account_indices_are_in_range(self):
        for row in inventory.INSTRUCTIONS:
            n = len(row["accounts"])
            self.assertTrue(all(i < n for i in row["signer"] + row["writable"]))


if __name__ == "__main__":
    unittest.main()
