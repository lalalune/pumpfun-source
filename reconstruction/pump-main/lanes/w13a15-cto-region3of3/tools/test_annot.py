import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("annot.py")


def load_module():
    spec = importlib.util.spec_from_file_location("admin_cto_annot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SymbolPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_candidate_defaults_to_itself(self):
        self.assertEqual(
            self.module.symbol_path("candidate.so", environ={}), "candidate.so"
        )

    def test_explicit_symbols_override_environment(self):
        self.assertEqual(
            self.module.symbol_path(
                "orig", "explicit.so", {"PUMP_ADMIN_CTO_SYMBOL_SO": "env.so"}
            ),
            "explicit.so",
        )

    def test_original_accepts_environment(self):
        self.assertEqual(
            self.module.symbol_path(
                "orig", environ={"PUMP_ADMIN_CTO_SYMBOL_SO": "env.so"}
            ),
            "env.so",
        )

    def test_original_requires_symbol_elf(self):
        with self.assertRaisesRegex(ValueError, "orig requires"):
            self.module.symbol_path("orig", environ={})


if __name__ == "__main__":
    unittest.main()
