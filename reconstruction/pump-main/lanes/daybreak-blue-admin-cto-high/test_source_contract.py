import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "programs/pump/src/creator/admin_cto.rs"


class AdminCtoCompositionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_retains_qualified_state_field_order(self):
        self.assertIn(
            "struct CtoState{creator:Pubkey,max_fee:u64,mayhem:bool,"
            "holder_reward:bool,holder_enabled:bool,fee_configurable:bool,"
            "cashback:bool,quote_locked:bool}",
            self.source,
        )

    def test_retains_passthrough_compatible_stitch_pair(self):
        fee_guard = (
            "unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as "
            "*const u8)}/*shim: holder_key byte read placeholder before the "
            "fee_configurable test*/;if !st.fee_configurable"
        )
        self.assertEqual(self.source.count(fee_guard), 1)
        self.assertEqual(self.source.count("if !collection_native||coin_present{"), 1)
        self.assertNotIn("if collection_native==false||coin_present{", self.source)


if __name__ == "__main__":
    unittest.main()
