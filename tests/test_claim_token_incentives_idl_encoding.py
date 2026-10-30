"""The claim token-incentives verifier must read the upstream Pump IDL as UTF-8.

Sibling of open #2699 (admin token-incentives verifier) and merged #2654
(the IDL-reader sweep). scripts/pump_claim_token_incentives_verify.py re-read
the same checked-in pump.json that its own differential pins to
encoding='utf-8' (pump_claim_token_incentives_differential.py), but the
verifier's own read used the platform default encoding. The checked-in IDL
carries non-ASCII documentation bytes (U+2192 in the buy instruction docs),
so on an ASCII-locale host the verifier died with UnicodeDecodeError before
checking any discriminator -- the same position 56968 failure #2654 documents
for the differential scripts.

The repo-wide scan in tests/test_pump_idl_reader_encoding.py does not catch
this one: it only flags a bare read in a file that itself binds the IDL path
in that same file, while the verifier reads through the imported differential
module as diff.IDL.read_text(). This test executes
the verifier's own IDL-read statement under a hostile locale, so it fails
while the statement carries no explicit encoding and passes once pinned.

The verifier module itself is not imported here (it needs solders and the
on-chain binaries); only its IDL-read statement is executed, against the
checked-in IDL, with a minimal diff namespace.
"""

import ast
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VERIFIER = ROOT / "scripts" / "pump_claim_token_incentives_verify.py"
IDL = ROOT / "evidence" / "upstream" / "pump.json"

DRIVER = r"""
import ast, json, sys
from pathlib import Path
from types import SimpleNamespace

verifier_path, idl_path = sys.argv[1], sys.argv[2]
source = Path(verifier_path).read_text(encoding="utf-8")
tree = ast.parse(source)
statement = None
for node in ast.walk(tree):
    if not isinstance(node, ast.Assign):
        continue
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "read_text"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "IDL"
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "diff"
        ):
            statement = ast.get_source_segment(source, node)
            break
    if statement:
        break
if statement is None:
    raise SystemExit("no diff.IDL.read_text() statement found in verifier")
namespace = {"json": json, "diff": SimpleNamespace(IDL=Path(idl_path))}
exec(statement, namespace)
idl = namespace["idl"]
names = [item["name"] for item in idl["events"]]
assert "ClaimTokenIncentivesEvent" in names, names
print("idl-ok", len(idl["instructions"]))
"""


class ClaimIncentivesIdlEncodingTests(unittest.TestCase):
    def test_verifier_idl_read_survives_ascii_locale(self):
        self.assertTrue(VERIFIER.is_file(), f"missing verifier: {VERIFIER}")
        self.assertTrue(IDL.is_file(), f"missing checked-in IDL: {IDL}")
        env = dict(os.environ, LC_ALL="C", PYTHONCOERCECLOCALE="0")
        env.pop("PYTHONUTF8", None)
        proc = subprocess.run(
            [sys.executable, "-B", "-X", "utf8=0", "-c", DRIVER,
             str(VERIFIER), str(IDL)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=60,
        )
        output = proc.stdout.decode("utf-8", "replace")
        self.assertEqual(proc.returncode, 0, output)
        self.assertIn("idl-ok 56", output)


if __name__ == "__main__":
    unittest.main()
