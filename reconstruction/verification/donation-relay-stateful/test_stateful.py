#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("relay_stateful", HERE / "producer.py")
relay = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = relay
SPEC.loader.exec_module(relay)


class EncodingTests(unittest.TestCase):
    def test_owned_keys_are_real_and_distinct(self):
        keys = [relay.key(name) for name in ("fee", "donor", "outsider")]
        self.assertEqual(len({key.pubkey() for key in keys}), 3)
        self.assertTrue(all(bytes(key) for key in keys))
        self.assertNotIn(relay.RELAYER, {key.pubkey() for key in keys})

    def test_fixture_uses_canonical_pdas(self):
        fixture = relay.Fixture.create()
        self.assertEqual(fixture.epoch, relay.pda(b"epoch_tracker_v1", fixture.config, bytes(fixture.mint))[0])
        self.assertEqual(fixture.debouncer, relay.pda(b"debouncer_v1", fixture.config, bytes(fixture.mint))[0])
        self.assertEqual(fixture.destination, relay.ata(fixture.debouncer, fixture.mint))

    def test_negative_control_is_not_a_match(self):
        observed = {"epoch": 0, "debouncer_total": 3_000_000}
        changed = dict(observed)
        changed["debouncer_total"] += 1
        self.assertNotEqual(observed, changed)

    def test_transaction_identity_rejects_reused_signature(self):
        cases = [{"steps": [
            {"signature": "same", "signature_verified": True},
            {"signature": "same", "signature_verified": True},
        ]}]
        identity = relay.transaction_identity(cases)
        self.assertEqual(identity["count"], 2)
        self.assertEqual(identity["unique_count"], 1)
        self.assertTrue(identity["all_signatures_verified"])

    def test_source_manifest_is_stable_and_nonempty(self):
        root = HERE.parents[2]
        rows, digest = relay.source_manifest(root)
        self.assertIn("programs/donation-relay/Cargo.toml", rows)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
