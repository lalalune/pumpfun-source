"""An inherited PYTHONOPTIMIZE must not strip the assertions of a packet verifier."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("revalidation_verifier_optimization", HERE / "audit.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class VerifierOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="audit-optimize-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.frozen = audit.load_frozen(HERE.parents[2])

    def status(self, source, **environment):
        packet = self.root / "packet"
        packet.mkdir(exist_ok=True)
        (packet / "verify.py").write_text(source, encoding="utf-8")
        with mock.patch.dict(os.environ, environment):
            return audit.run_verifier(self.frozen, self.root, packet, 10.0, 0.2)["status"]

    def test_inherited_optimization_cannot_erase_a_failing_assertion(self):
        for level in ("1", "2"):
            self.assertEqual(self.status("assert False\n", PYTHONOPTIMIZE=level), "fail")

    def test_verifier_sees_no_optimization_level(self):
        source = "import sys\nraise SystemExit(sys.flags.optimize)\n"
        self.assertEqual(self.status(source, PYTHONOPTIMIZE="2"), "pass")

    def test_other_environment_still_reaches_the_verifier(self):
        source = "import os\nraise SystemExit(0 if os.environ['AUDIT_KEEP'] == 'kept' else 1)\n"
        self.assertEqual(self.status(source, AUDIT_KEEP="kept", PYTHONOPTIMIZE="1"), "pass")


if __name__ == "__main__":
    unittest.main()
