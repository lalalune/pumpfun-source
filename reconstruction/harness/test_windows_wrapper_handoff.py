"""Real Windows child processes; no Rust compiler, linker or SDK runs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import link_order


@unittest.skipUnless(os.name == 'nt', 'Windows CRT exec handoff regression')
class WindowsWrapperHandoff(unittest.TestCase):
    def test_paths_arguments_and_child_failure_survive_both_handoffs(self):
        with tempfile.TemporaryDirectory(prefix='wrapper handoff ') as temporary:
            root = Path(temporary)
            following = root / 'next wrapper.py'
            receipt = root / 'argv.json'
            following.write_text('import json,os,sys\nfrom pathlib import Path\nPath(os.environ["TEST_ARGV"]).write_text(json.dumps(sys.argv[1:]))\nraise SystemExit(int(os.environ["TEST_CODE"]))\n', encoding='utf-8')
            arguments = ['source path/file.rs', 'argument "with quotes"', 'label-\u2192']
            for wrapper in ('link', 'physical'):
                for code in (0, 7):
                    with self.subTest(wrapper=wrapper, code=code):
                        receipt.unlink(missing_ok=True)
                        env = dict(os.environ, TEST_ARGV=str(receipt), TEST_CODE=str(code),
                                   PUMP_LINK_ROOT_CRATE='pump', PUMP_LINK_NEXT_WRAPPER=str(following),
                                   PUMP_LOGICAL_REGISTRY_SRC='')
                        if wrapper == 'link':
                            expected = ['not-a-compiler', *arguments]
                            command = [sys.executable, str(link_order.H / 'pump_link_rustc.py'), *expected]
                        else:
                            expected = arguments
                            command = [sys.executable, str(link_order.H / 'pump_physical_source_wrapper.py'), sys.executable, str(following), *arguments]
                        result = subprocess.run(command, env=env, capture_output=True, timeout=10)
                        self.assertEqual(result.returncode, code, result.stderr)
                        self.assertEqual(json.loads(receipt.read_text()), expected)


if __name__ == '__main__': unittest.main()
