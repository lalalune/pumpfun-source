#!/usr/bin/env python3
from __future__ import annotations

import unittest

import fixture


class FixtureTests(unittest.TestCase):
    def test_owned_signers_are_distinct_and_exclude_production_relayer(self):
        value = fixture.Fixture.create("keys")
        keys = [value.fee.pubkey(), value.outsider.pubkey(),
                *(donor.keypair.pubkey() for donor in value.donors.values())]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertNotIn(fixture.RELAYER, keys)

    def test_every_donor_has_an_independent_canonical_source(self):
        value = fixture.Fixture.create("sources")
        addresses = set()
        for donor in value.donors.values():
            for mint_name, source in donor.sources.items():
                self.assertEqual(source, fixture.associated_token_address(
                    donor.keypair.pubkey(), value.mints[mint_name]))
                addresses.add(source)
        self.assertEqual(len(addresses), len(fixture.DONOR_NAMES) * len(fixture.MINT_NAMES))

    def test_domains_use_canonical_config_and_mint_pdas(self):
        value = fixture.Fixture.create("domains")
        for domain in value.domains.values():
            self.assertEqual(domain.epoch, fixture.pda(
                b"epoch_tracker_v1", domain.config, bytes(domain.mint))[0])
            self.assertEqual(domain.debouncer, fixture.pda(
                b"debouncer_v1", domain.config, bytes(domain.mint))[0])
            self.assertEqual(domain.destination,
                             fixture.associated_token_address(domain.debouncer, domain.mint))

    def test_balance_overrides_are_per_owner_and_mint(self):
        value = fixture.Fixture.create("balances", {"A:mint_x": 5, "B:mint_y": 9})
        for donor_name, mint_name, expected in (("A", "mint_x", 5), ("B", "mint_y", 9),
                                                ("C", "mint_x", 10_000_000)):
            source = value.donors[donor_name].sources[mint_name]
            row = {"data_base64": __import__("base64").b64encode(value.accounts[source].data).decode()}
            self.assertEqual(fixture.token_amount(row), expected)

    def test_donation_requires_the_selected_donor_signature(self):
        value = fixture.Fixture.create("instruction")
        instruction = value.donation("B", 7)
        signers = [meta.pubkey for meta in instruction.accounts if meta.is_signer]
        self.assertEqual(signers, [value.donors["B"].keypair.pubkey()])
        self.assertNotIn(value.donors["A"].keypair.pubkey(), signers)


if __name__ == "__main__":
    unittest.main()
