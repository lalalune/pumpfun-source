#!/usr/bin/env python3
"""The constant-product receipt binds the Rust file its native host is compiled from."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOST_STUB = "#!/bin/sh\nwhile IFS= read -r line; do echo 0; done\n"


@unittest.skipUnless(importlib.util.find_spec("solders"), "requires the documented solders runtime")
class ConstantProductSourceBindingTests(unittest.TestCase):
    def test_receipt_binds_the_host_source(self):
        with tempfile.TemporaryDirectory(prefix="constant-product-sources-") as temporary:
            host = Path(temporary) / "host.sh"
            host.write_text(HOST_STUB)
            host.chmod(0o755)
            output = Path(temporary) / "report.json"
            # The stub answers 0, so the run ends on recorded mismatches after
            # the report is published; only the source binding is under test.
            subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/pump_validate_constant_product.py"),
                 "--host", str(host), "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, timeout=300)
            report = json.loads(output.read_bytes())
        source = ROOT / "programs/pump/recovered/constant_product_host.rs"
        self.assertEqual(report.get("host_source_sha256"),
                         hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
