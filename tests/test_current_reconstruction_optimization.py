"""Regression checks for current-reconstruction verification under optimized Python.

verify() in scripts/verify_current_reconstruction.py is the top-level gate
over the current selections: it authenticates the relay selection and the
sealed P27 catalogue, checks the mayhem manifest and stats binding, and
requires every program checkpoint report to PASS with the candidate hash from
repro/status.json. Before this fix every one of those checks was a bare
assert, so under -O/-OO a relay selection that failed verification, mayhem
stats bound to a different candidate, or a checkpoint report for the wrong
candidate was still reported as PASS_CURRENT_RECONSTRUCTION. The relay,
bridge, mayhem and checkpoint scripts are stubbed here (the real ones need
the sealed packages and on-chain artifacts), so the driver exercises the
verifier's own admission logic, not the replay engines.
"""

from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
MAYHEM = "repro/mayhem/initializer-current-20261027"
MAYHEM_SEAL = "b6b01b400fb7c5ab10db803ba27fe6a76e0e59e9ea7fad25250dc95760cf485c"
REPEAT_SEAL = "ad2353dec21a94f5d9a202e956d95b112f3130420301988399c845b8122aaea3"

DRIVER = (
    "import sys, hashlib, json\n"
    "from pathlib import Path\n"
    "import verify_current_reconstruction as v\n"
    "root = Path(sys.argv[1])\n"
    "real_sha = v.sha\n"
    "def patched_sha(path):\n"
    "    p = Path(path)\n"
    "    if p.name == 'manifest.json' and 'relay-current-repeat-20261028' in str(p):\n"
    "        return '" + REPEAT_SEAL + "'\n"
    "    if p.name == 'manifest.json' and 'initializer-current-20261027' in str(p):\n"
    "        return '" + MAYHEM_SEAL + "'\n"
    "    return real_sha(path)\n"
    "v.sha = patched_sha\n"
    "v.verify(root)\n"
    "print('OK')\n"
)

CHECKPOINT_STUB = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "args = sys.argv[1:]\n"
    "root = Path(args[args.index('--repo') + 1]) if '--repo' in args else Path('.')\n"
    "status = json.loads((root / 'repro/status.json').read_text())\n"
    "prog = 'pump_fees' if 'pump_fees' in args else ('pump_amm' if 'amm' in Path(__file__).name else 'pump')\n"
    "print(json.dumps({'status': 'PASS', 'candidate_sha256': status[prog]['candidate_sha256']}))\n"
)

MAYHEM_STUB = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "args = sys.argv[1:]\n"
    "root = Path(args[args.index('--current-source') + 1])\n"
    "status = json.loads((root / 'repro/status.json').read_text())\n"
    "print(json.dumps({'status': 'PASS', 'candidate_sha256': status['mayhem']['candidate_sha256']}))\n"
)

COMMON_STUB = (
    "import json\n"
    "class Context:\n"
    "    def __init__(self, root):\n"
    "        status = json.loads((root / 'repro/status.json').read_text())\n"
    "        self.F = {'compiled': {'pump_fees': {'source': ['a.rs', 'b.rs']}},\n"
    "                'status': {'pump_fees': status['pump_fees']}}\n"
    "        self.R = {'source_layout': {'pump_fees': {'crate': 'programs/pump-fees',\n"
    "                'workspace': '.', 'extra_inputs': []}}}\n"
    "    def catalogue(self):\n"
    "        return list(range(53))\n"
    "    def unchanged(self, path):\n"
    "        pass\n"
    "def metadata_context(root, p27, seal):\n"
    "    return Context(root)\n"
    "def source_names(crate, workspace, root, extra):\n"
    "    return {'a.rs', 'b.rs'}\n"
)

MODES = ([], ["-O"], ["-OO"])


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CurrentReconstructionOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "repro").mkdir()
        self.status = {
            "pump": {"candidate_artifact": "repro/pump/other/candidate.so",
                     "candidate_sha256": "p" * 64},
            "pump_amm": {"candidate_artifact": "repro/pump_amm/other/candidate.so",
                         "candidate_sha256": "a" * 64},
            "pump_fees": {"candidate_artifact": "repro/pump_fees/other/candidate.so",
                          "candidate_sha256": "f" * 64},
            "mayhem": {"candidate_artifact": MAYHEM + "/candidate.so",
                       "candidate_sha256": "m" * 64,
                       "candidate_symbols_artifact": MAYHEM + "/unstripped.so",
                       "comparison_report": MAYHEM + "/comparison.json",
                       "full_byte_equality": False},
        }
        (self.root / "repro" / "status.json").write_text(json.dumps(self.status))
        relay_dir = self.root / "repro" / "donation-relay" / "canonical-exact-selection"
        relay_dir.mkdir(parents=True)
        (relay_dir / "verify_selection.py").write_text("def authenticate():\n    pass\n")
        (relay_dir / "common.py").write_text(COMMON_STUB)
        bridge_dir = self.root / "research" / "all-contract-completion-20261028" / "relay"
        bridge_dir.mkdir(parents=True)
        self.bridge_path = bridge_dir / "verify_current_bridge.py"
        self.write_bridge(True)
        repeat_dir = self.root / "research" / "relay-current-repeat-20261028"
        repeat_dir.mkdir(parents=True)
        (repeat_dir / "manifest.json").write_text("{}")
        (repeat_dir / "verify.py").write_text(
            "import json\n"
            "print(json.dumps({'meaningful_elf_equal': True,\n"
            "                  'genuine_loader_payload_equal': True}))\n")
        replay_dir = self.root / "repro" / "donation-relay" / "linked-elf-reproduction"
        replay_dir.mkdir(parents=True)
        (replay_dir / "verify.py").write_text("print('ok')\n")
        mayhem_dir = self.root / MAYHEM
        mayhem_dir.mkdir(parents=True)
        (mayhem_dir / "unstripped.so").write_bytes(b"symbols-bytes")
        (mayhem_dir / "verify.py").write_text(MAYHEM_STUB)
        self.stats_path = mayhem_dir / "stats.json"
        self.write_stats("m" * 64)
        (mayhem_dir / "manifest.json").write_text(json.dumps({"files": {
            "stats.json": file_sha(self.stats_path),
            "verify.py": file_sha(mayhem_dir / "verify.py"),
            "unstripped.so": file_sha(mayhem_dir / "unstripped.so"),
        }}))
        scripts_dir = self.root / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "verify_pump_main_checkpoint.py").write_text(CHECKPOINT_STUB)
        (scripts_dir / "verify_pump_amm_checkpoint.py").write_text(CHECKPOINT_STUB)
        (scripts_dir / "verify_current_checkpoint.py").write_text(CHECKPOINT_STUB)
        self.pump_stub_path = scripts_dir / "verify_pump_main_checkpoint.py"

    def write_bridge(self, verified):
        self.bridge_path.write_text(
            "def verify(root):\n"
            "    return {'current_selection': {\n"
            f"        'verified': {verified}, 'canonical_source60_verified': True,\n"
            "        'all492_raw': True, 'meaningful_elf_literal_equal': True,\n"
            "        'selected_payload_literal_checked': True}}\n")

    def write_stats(self, candidate_sha):
        mayhem_dir = self.root / MAYHEM
        self.stats_path.write_text(json.dumps({
            "candidate_sha256": candidate_sha,
            "unstripped_sha256": file_sha(mayhem_dir / "unstripped.so"),
        }))

    def write_pump_stub(self, candidate_sha):
        if candidate_sha is None:
            self.pump_stub_path.write_text(CHECKPOINT_STUB)
        else:
            self.pump_stub_path.write_text(
                "import json\n"
                f"print(json.dumps({{'status': 'PASS', 'candidate_sha256': '{candidate_sha}'}}))\n")

    def run_driver(self, optimization):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, str(self.root)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_admission_tampers_rejected_in_all_modes(self):
        variants = {
            "relay unverified": lambda: self.write_bridge(False),
            "mayhem stats candidate": lambda: self.write_stats("0" * 64),
            "checkpoint candidate": lambda: self.write_pump_stub("0" * 64),
        }
        for name, tamper in variants.items():
            with self.subTest(variant=name):
                tamper()
                for optimization in MODES:
                    with self.subTest(optimization=optimization or "normal"):
                        completed = self.run_driver(optimization)
                        self.assertNotEqual(completed.returncode, 0, completed.stdout)
                        self.assertNotIn("OK", completed.stdout)
                self.write_bridge(True)
                self.write_stats("m" * 64)
                self.write_pump_stub(None)

    def test_valid_reconstruction_accepted_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
