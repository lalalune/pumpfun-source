"""Real retained verifier invocations and legacy working-directory controls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import revalidate_all as runner


class InvocationTests(unittest.TestCase):
    def test_retained_repository_aware_packets(self):
        for name in ('legacy-capture-metadata', 'roadmap-call-classification',
                     'token-program-constant-detector'):
            with self.subTest(packet=name):
                packet = ROOT / f'research/tooling-{name}-20261029'
                result = runner.run_verify(packet)
                self.assertEqual(result['status'], 'pass', result)
                self.assertEqual(result['returncode'], 0)

    @staticmethod
    def fixture(packet, returncode=0):
        packet.mkdir(parents=True)
        (packet / 'verify.py').write_text(
            'import json, os, sys\n'
            'print(json.dumps({"cwd": os.getcwd(), "args": sys.argv[1:]}))\n'
            f'raise SystemExit({returncode})\n', encoding='utf-8')

    def test_all_registered_commands_keep_cwd_and_failure_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for relative in runner.REPOSITORY_ARGUMENT_PACKETS:
                with self.subTest(packet=relative):
                    packet = root / relative
                    self.fixture(packet, returncode=7)
                    with patch.object(runner, 'REPO', root):
                        result = runner.run_verify(packet)
                    self.assertEqual(result['status'], 'fail')
                    self.assertEqual(result['returncode'], 7)
                    self.assertEqual(json.loads(result['output']), {
                        'cwd': str(packet), 'args': ['--repo', str(root)],
                    })

    def test_legacy_and_same_name_elsewhere_receive_no_extra_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            name = 'tooling-token-program-constant-detector-20261029'
            for packet in (root / 'research/legacy', root / 'other' / name,
                           root / 'outside/research' / name):
                with self.subTest(packet=packet):
                    self.fixture(packet)
                    repo = root if 'outside' not in packet.parts else root / 'separate'
                    with patch.object(runner, 'REPO', repo):
                        result = runner.run_verify(packet)
                    self.assertEqual(result['status'], 'pass', result)
                    self.assertEqual(json.loads(result['output']), {'cwd': str(packet), 'args': []})


if __name__ == '__main__':
    unittest.main(verbosity=2)
