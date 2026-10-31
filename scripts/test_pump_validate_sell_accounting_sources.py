#!/usr/bin/env python3
"""The sell-accounting receipt binds the Rust file its native host is compiled from."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CURVE_STUB = "\n".join((
    "#!" + sys.executable + " -I",
    "import sys",
    "for line in sys.stdin:",
    "    amount, reserve_in, reserve_out = map(int, line.split(','))",
    "    print(amount * reserve_out // (reserve_in + amount))",
    ""))
SELL_STUB = "#!/bin/sh\nwhile IFS= read -r line; do echo 0,0,0,0,0; done\n"


def stub(path, text):
    path.write_text(text)
    path.chmod(0o755)
    return path


@unittest.skipUnless(importlib.util.find_spec("solders"), "requires the documented solders runtime")
class SellAccountingSourceBindingTests(unittest.TestCase):
    def test_receipt_binds_the_host_source(self):
        with tempfile.TemporaryDirectory(prefix="sell-accounting-sources-") as temporary:
            folder = Path(temporary)
            curve = folder / "curve.json"
            subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/pump_validate_constant_product.py"),
                 "--host", str(stub(folder / "curve-host", CURVE_STUB)), "--output", str(curve)],
                cwd=ROOT, capture_output=True, text=True, timeout=300, check=True)
            output = folder / "report.json"
            # The stub answers zeros, so the run ends on recorded mismatches after
            # the report is published; only the source binding is under test.
            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/pump_validate_sell_accounting.py"),
                 "--host", str(stub(folder / "sell-host", SELL_STUB)),
                 "--curve-report", str(curve), "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, timeout=300)
            self.assertTrue(output.exists(), completed.stderr[-2000:])
            report = json.loads(output.read_bytes())
        source = ROOT / "programs/pump/recovered/sell_accounting_host.rs"
        self.assertEqual(report.get("host_source_sha256"),
                         hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
