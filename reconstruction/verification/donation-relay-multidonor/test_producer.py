#!/usr/bin/env python3
from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

import fixture
import producer


class DeclarationTests(unittest.TestCase):
    def test_case_inventory_and_transaction_count(self):
        self.assertEqual(len(producer.CASE_NAMES), 12)
        self.assertEqual(sum(len(producer.CASES[name]["steps"]) for name in producer.CASE_NAMES), 28)
        self.assertEqual(len(set(producer.CASE_NAMES)), len(producer.CASE_NAMES))

    def test_every_donation_step_names_real_donors_and_domains(self):
        value = fixture.Fixture.create("declarations")
        for case in producer.CASES.values():
            for step in case["steps"]:
                for row in step.get("donations", []):
                    self.assertIn(row["donor"], value.donors)
                    self.assertIn(row["domain"], value.domains)
                    if row.get("source_donor"):
                        self.assertIn(row["source_donor"], value.donors)

    def test_three_donor_transaction_requires_all_donor_signers(self):
        spec = producer.CASES["three_donors_one_transaction"]["steps"][0]
        value = fixture.Fixture.create("three-signers")
        instructions, signers, records = producer.build_step(value, spec)
        self.assertEqual(len(instructions), 3)
        self.assertEqual({str(key.pubkey()) for key in signers},
                         {str(value.donors[name].keypair.pubkey()) for name in "ABC"})
        self.assertEqual({row["donor"] for row in records}, set("ABC"))

    def test_expected_error_count_matches_steps(self):
        for name, case in producer.CASES.items():
            self.assertTrue(all("error" in step for step in case["steps"]), name)

    def test_source_manifest_is_nonempty_and_stable(self):
        rows, digest = producer.source_manifest(producer.ROOT)
        self.assertIn("programs/donation-relay/Cargo.toml", rows)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_build_receipt_claim_is_refused_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "not authenticated"):
                producer.execute(producer.ROOT, Path("unused"), Path(directory) / "out.json", Path("fake-build.json"))


if __name__ == "__main__":
    unittest.main()
