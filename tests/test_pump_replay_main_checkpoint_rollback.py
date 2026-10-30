#!/usr/bin/env python3
"""Reject failed Pump checkpoint replays without leaving materialized source."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    'pump_replay_main_checkpoint_rollback',
    SCRIPTS / 'pump_replay_main_checkpoint.py',
)
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)


class ReplayFailureRollbackTests(unittest.TestCase):
    def test_failed_validation_rolls_back_materialized_source(self):
        with tempfile.TemporaryDirectory(prefix='pump-replay-rollback-') as temporary:
            root = Path(temporary)
            package = root / 'research/pump-create-used-boundaries-20261028'
            fixture = package / 'builds/primary'
            fixture.mkdir(parents=True)
            (root / 'repro').mkdir()
            candidate = (
                'research/pump-create-used-boundaries-20261028/'
                'artifacts/candidate.so'
            )
            (root / 'repro/status.json').write_text(
                json.dumps({'pump': {'candidate_artifact': candidate}})
            )

            destination = root / 'compiled/source/nested/created.txt'
            data = b'verified source material\n'
            comparison = {
                'source_sha256': {
                    destination.relative_to(root).as_posix():
                    hashlib.sha256(data).hexdigest()
                }
            }
            (fixture / 'build-comparison.json').write_text(
                json.dumps(comparison)
            )
            with tarfile.open(
                fixture / 'compiled-source.tar.gz', 'w:gz'
            ) as archive:
                member = tarfile.TarInfo('nested/created.txt')
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))

            failure = subprocess.CalledProcessError(7, ['replay-suite'])
            with mock.patch.object(REPLAY, 'ROOT', root), \
                    mock.patch.object(REPLAY, 'verify', return_value=None), \
                    mock.patch.object(
                        REPLAY.subprocess, 'run', side_effect=failure
                    ), \
                    mock.patch.object(sys, 'argv', [
                        'pump_replay_main_checkpoint.py',
                        '--output', str(root / 'reports/result.json.gz'),
                    ]):
                with self.assertRaises(subprocess.CalledProcessError):
                    REPLAY.main()

            self.assertFalse(
                destination.exists(),
                'failed replay left materialized source',
            )
            self.assertFalse(
                (root / 'compiled').exists(),
                'failed replay left created source directories',
            )


if __name__ == '__main__':
    unittest.main()
