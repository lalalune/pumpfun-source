"""`scripts/fees_admin_cto_differential.py` must execute one candidate image per run.

Sibling of #2757 (pump creator-distribution differential), merged #2753
(pump cashback differential), #2746 (pump legacy buy differential), #2744
(pump legacy sell differential), #2740 (pump sell_v2 differential) and
#2738 (pump buy_v2 differential), which pinned their candidate images:
this script's `main()` calls `run(c, a.candidate)` once per case, and
`run()` hands the candidate path straight to `add_program_from_file`
for the pump_fees program, which reads the file on every call — so
replacing the candidate file mid-run makes later cases execute a
different image, while the report's `candidate_sha256` is read from
the candidate path only at the end. One receipt would then cover two
images. Unlike the pump admin_cto / set-creator / creator-collect /
fee-sweep suites, this script computes no pre-loop provenance and
asserts nothing about its inputs after the loop, so nothing catches
the swap.

The script module itself is not imported here (it needs solders and
the LiteSVM fixture); only the pinning wiring is checked by AST, so
the test fails on base (no `pin_program` use) and passes with the
fix. The runtime swap test of #2722 is not runnable here (solders
is absent).
"""

import ast
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT = ROOT / "scripts" / "fees_admin_cto_differential.py"


def load_tree():
    return ast.parse(SCRIPT.read_text(encoding="utf-8"))


def calls_to_attribute(tree, attr):
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == attr:
                found.append(node)
    return found


def is_pin_program_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "pin_program"
    )


class FeesAdminCtoPinnedImageTests(unittest.TestCase):
    def test_candidate_image_is_pinned(self):
        tree = load_tree()
        imported = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "pump_amm_reusable_harness"
            and any(alias.name == "pin_program" for alias in node.names)
            for node in ast.walk(tree)
        )
        self.assertTrue(imported, "pin_program is not imported")

        # run() must hand the pinned snapshot, not the live path, to the VM.
        pinned_load = False
        for call in calls_to_attribute(tree, "add_program_from_file"):
            if len(call.args) < 2:
                continue
            arg = call.args[1]
            if isinstance(arg, ast.IfExp):
                arg = arg.body
            if is_pin_program_call(arg):
                pinned_load = True
        self.assertTrue(pinned_load, "candidate binary is not pinned before loading")

        # The report hash must come from the same pinned snapshot.
        pinned_hash = False
        for call in calls_to_attribute(tree, "read_bytes"):
            value = call.func.value
            if is_pin_program_call(value):
                pinned_hash = True
        self.assertTrue(pinned_hash, "report hash is not read from the pinned snapshot")


if __name__ == "__main__":
    unittest.main()
