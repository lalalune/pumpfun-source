"""The ``lfx`` gene must edit the accounts literal it names, or refuse.

``lfx_<site>_<label>`` rewrites one ``label:a.<acct>.to_account_info()`` field
of a named CPI accounts literal into an Rc-locals-first clone. The guard that
kept the rewrite inside the literal compared a match position with a closing
brace but ended in ``or True``, so it could not fail: a label only after the
literal's closing brace was rewritten in place, in another CPI entirely.

Each of the four copies of the gene library must refuse that.
"""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANES = ROOT / "reconstruction/pump-main/lanes"
COPIES = (
    LANES / "w14a64-cto-shiftpair/genes_s11.py",
    LANES / "w15a01-cto-devolfill/tools/genes_s11.py",
    LANES / "w15a01-cto-devolfill/tools/genes_s11b.py",
    LANES / "w14a53-cto-stitch11/genes.py",
)
LITERAL = "crate::pump_amm::cpi::accounts::CollectCoinCreatorFee"
INSIDE = (f"{LITERAL}{{payer:a.admin.to_account_info(),"
          "program:a.pump_fees.to_account_info()}")
OUTSIDE = (f"{LITERAL}{{}} tail ,payer:a.bar.to_account_info()")
MESSAGE = "ccf:payer is not inside the accounts literal"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LaneGeneLiteralGuardTests(unittest.TestCase):
    def copies(self):
        return [(str(path.relative_to(ROOT)), load(path, f"lane_genes_{index}"))
                for index, path in enumerate(COPIES)]

    def test_the_only_matching_label_is_rewritten_inside_the_literal(self):
        for copy, module in self.copies():
            with self.subTest(copy=copy):
                out = module.apply(INSIDE, ["lfx_ccf_payer"])
                self.assertIn("payer:{let x:&AccountInfo=a.admin.as_ref();", out)
                self.assertIn("program:a.pump_fees.to_account_info()", out)

    def test_a_match_outside_the_literal_is_refused(self):
        for copy, module in self.copies():
            with self.subTest(copy=copy):
                with self.assertRaises(AssertionError) as raised:
                    module.apply(OUTSIDE, ["lfx_ccf_payer"])
                self.assertIn(MESSAGE, str(raised.exception))

    def test_a_label_the_literal_lacks_is_refused(self):
        for copy, module in self.copies():
            with self.subTest(copy=copy):
                with self.assertRaises(AssertionError) as raised:
                    module.apply(OUTSIDE, ["lfx_ccf_program"])
                self.assertTrue(str(raised.exception))

    def test_two_fields_can_be_rewritten_in_source_order(self):
        source = f"{LITERAL}{{quote_mint:a.mint.to_account_info(),payer:a.admin.to_account_info()}}"
        for copy, module in self.copies():
            with self.subTest(copy=copy):
                out = module.apply(source, ["lfx_ccf_quote_mint", "lfx_ccf_payer"])
                self.assertIn("quote_mint:{let x:&AccountInfo=a.mint.as_ref();", out)
                self.assertIn("payer:{let x:&AccountInfo=a.admin.as_ref();", out)

    def test_nested_fields_cannot_satisfy_the_requested_label(self):
        source = f"{LITERAL}{{other:Nested{{payer:a.admin.to_account_info()}}}}"
        for copy, module in self.copies():
            with self.subTest(copy=copy):
                with self.assertRaisesRegex(AssertionError, "ccf:payer"):
                    module.apply(source, ["lfx_ccf_payer"])

    def test_ambiguous_or_unterminated_literals_are_refused(self):
        for source in (f'{LITERAL}{{note:"}}",payer:a.admin.to_account_info()}}',
                       f'{LITERAL}{{/* unterminated payer:a.admin.to_account_info()}}',
                       f'{LITERAL}{{payer:a.admin.to_account_info()'):
            for copy, module in self.copies():
                with self.subTest(copy=copy, source=source):
                    with self.assertRaisesRegex(AssertionError, "ccf:payer"):
                        module.apply(source, ["lfx_ccf_payer"])

    def test_comments_cannot_close_the_literal_or_supply_a_field(self):
        for comment in ('/* } /* nested */ } */', '// }\n'):
            for copy, module in self.copies():
                with self.subTest(copy=copy, comment=comment):
                    source = (f"{LITERAL}{{other:a.other.to_account_info(){comment},"
                              "payer:a.admin.to_account_info()}")
                    out = module.apply(source, ["lfx_ccf_payer"])
                    self.assertIn("payer:{let x:&AccountInfo=a.admin.as_ref();", out)
                    absent = f"{LITERAL}{{/* ,payer:a.admin.to_account_info() */}}"
                    with self.assertRaisesRegex(AssertionError, "ccf:payer"):
                        module.apply(absent, ["lfx_ccf_payer"])

    def test_duplicate_fields_and_sites_are_refused(self):
        for source in (f"{LITERAL}{{payer:a.admin.to_account_info(),payer:a.other.to_account_info()}}",
                       INSIDE + INSIDE):
            for copy, module in self.copies():
                with self.subTest(copy=copy, source=source):
                    with self.assertRaisesRegex(AssertionError, "ccf:payer"):
                        module.apply(source, ["lfx_ccf_payer"])


if __name__ == "__main__":
    unittest.main()
