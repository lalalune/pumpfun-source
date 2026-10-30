import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

H = Path(__file__).resolve().parent


class MinimizeOracleEncodingTests(unittest.TestCase):
    def test_oracle_config_loads_as_utf8_independent_of_host_locale(self):
        # Sibling of bisect_membership.load_oracle (merged #2610): a minimize
        # oracle whose command carries a non-ASCII label (here U+2192) cannot
        # be decoded by locale-default readers on hosts whose ANSI code page
        # is not UTF-8. The child runs under LC_ALL=C with locale coercion
        # off, where Path.read_text() defaults to ASCII and raises
        # UnicodeDecodeError on byte 0xe2; the pinned UTF-8 load must still
        # succeed. The child source stays ASCII-only (the arrow is a \u
        # escape) so argv decoding under the C locale cannot corrupt it.
        with tempfile.TemporaryDirectory() as temporary:
            oracle = Path(temporary) / "oracle.json"
            oracle.write_bytes(
                json.dumps(
                    {"command": ["rustc"], "note": "SOL \u2192 tokens"},
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            self.assertIn(b"\xe2\x86\x92", oracle.read_bytes())
            child = (
                "import sys, minimize_experiment\n"
                "from pathlib import Path\n"
                "config = minimize_experiment.load_oracle(Path(sys.argv[1]))\n"
                "assert config['note'] == 'SOL \\u2192 tokens', config\n"
            )
            env = dict(os.environ, LC_ALL="C", PYTHONCOERCECLOCALE="0",
                       PYTHONUTF8="0")
            result = subprocess.run(
                [sys.executable, "-B", "-c", child, str(oracle)],
                cwd=str(H), capture_output=True, env=env, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
