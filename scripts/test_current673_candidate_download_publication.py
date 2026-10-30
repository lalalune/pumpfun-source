"""Candidate qualification must not publish unauthenticated archives."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import pump_current673_macos_candidate as candidate


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Current673CandidateDownloadTests(unittest.TestCase):
    def test_candidate_hash_failure_does_not_publish_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow = (
                root / '.github/workflows/qualify-pump-macos-v144.yml')
            workflow.parent.mkdir(parents=True)
            workflow.write_text('name: qualification\n')
            original = root / 'evidence/original/pump/deployed.so'
            original.parent.mkdir(parents=True)
            original.write_bytes(b'captured original')
            cold = root / 'cold'
            (cold / 'tools').mkdir(parents=True)
            (cold / 'build.py').write_text('# builder\n')
            (cold / 'build-inputs.json').write_text('{}\n')
            candidates = (
                root / 'research/pump-current673-macos-qualification/candidates')
            candidates.mkdir(parents=True)
            (candidates / 'descriptors.json').write_text('{}\n')
            proof = root / 'work/pump-current673-control-proof'
            proof.mkdir(parents=True)
            source_bytes = b'untrusted candidate dependency archive'
            source = root / 'source.tar.bz2'
            source.write_bytes(source_bytes)
            frozen = root / 'proposed-source.rs'
            frozen.write_text('fn proposed() {}\n')
            builder = proof / 'executed-builder.py'
            builder.write_bytes(b'authenticated builder')
            for name in ('candidate.so', 'unstripped.so'):
                (proof / name).write_bytes(name.encode())
            result = {
                'status': 'reproduced',
                'base_commit': 'base',
                'cold_empty_target': True,
                'candidate_sha256': sha(proof / 'candidate.so'),
                'unstripped_sha256': sha(proof / 'unstripped.so'),
            }
            (proof / 'MANIFEST.json').write_text('{}\n')
            (proof / 'RESULT.json').write_text(json.dumps(result))
            (proof / 'host.json').write_text(
                json.dumps({'revision': 'control-head'}))

            spec = {
                'base_commit': 'base',
                'builder_sha256': sha(builder),
                'original_sha256': sha(original),
                'expected': {
                    'candidate_sha256': result['candidate_sha256'],
                    'unstripped_sha256': result['unstripped_sha256'],
                },
                'archives': {
                    'dependency': {
                        'url': source.as_uri(),
                        'sha256': '0' * 64,
                    },
                },
            }
            expected = {
                'candidate_sha256': result['candidate_sha256'],
                'unstripped_sha256': result['unstripped_sha256'],
                'source_inputs': {},
            }
            descriptor = (
                spec,
                cold,
                root / 'source',
                {'control_head': 'control-head', 'control_run': 1},
                {},
                frozen,
                expected,
                '# candidate builder\n',
                '',
            )
            with mock.patch.object(candidate, 'ROOT', root), \
                    mock.patch.object(candidate, 'DIRECTORY', candidates), \
                    mock.patch.object(candidate, 'descriptor',
                                      return_value=descriptor), \
                    mock.patch.object(candidate.platform, 'system',
                                      return_value='Darwin'), \
                    mock.patch.object(candidate.platform, 'machine',
                                      return_value='arm64'), \
                    mock.patch.object(candidate.subprocess, 'check_output',
                                      return_value='base\n'), \
                    mock.patch.object(sys, 'argv', [
                        str(Path(candidate.__file__)),
                        '--candidate', 'cto',
                        '--source-directory', str(root / 'source'),
                    ]), \
                    mock.patch.object(candidate.control, 'WORK', root), \
                    mock.patch.object(candidate.control, 'EVIDENCE', root), \
                    mock.patch.object(candidate.control, 'retain'):
                with self.assertRaises((AssertionError, ValueError)):
                    candidate.main()

            work = root / 'work/pump-current673-macos-cto'
            archive = work / 'dependency.tar.bz2'
            self.assertFalse(archive.exists())
            self.assertEqual(list(work.glob('.dependency.tar.bz2.*')), [])


if __name__ == '__main__':
    unittest.main()
