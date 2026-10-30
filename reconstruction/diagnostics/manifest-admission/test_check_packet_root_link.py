"""A packet directory that is itself a link must not pass admission.

Sibling of merged #2980, which closed the same gap in
scripts/revalidate_all.py: the manifest-admission checker's payload walk
lstats every entry under the packet root but never the root itself, so a
packet rooted in an external tree passed with the external tree's own
manifest and payloads. The retained batch revalidator (run.py) substitutes
this checker for the frozen one, so the gap reached it too.
"""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class ManifestAdmissionPacketRootLinkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        # An internally consistent packet living outside the packet tree.
        self.external = self.root / 'external-packet'
        self.external.mkdir()
        (self.external / 'data.txt').write_bytes(b'outside bytes\n')
        (self.external / 'manifest.json').write_text(json.dumps(
            {'data.txt': sha256(b'outside bytes\n')}))

    def test_real_packet_directory_passes(self):
        result = check.check_manifest(self.external)
        self.assertEqual(result['status'], 'pass', result)

    def test_symlinked_packet_directory_is_rejected(self):
        link = self.root / 'packet-link'
        link.symlink_to(self.external, target_is_directory=True)
        result = check.check_manifest(link)
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(
            any(error.startswith('linked_path') for error in result['errors']),
            result)

    def test_actual_batch_records_linked_root_failure_without_mutating_it(self):
        repository = self.root / 'repo'; (repository / 'scripts').mkdir(parents=True)
        source_root = Path(__file__).resolve().parents[3]
        shutil.copyfile(source_root / 'scripts/revalidate_all.py', repository / 'scripts/revalidate_all.py')
        research = repository / 'research'; research.mkdir()
        linked = research / 'linked'; linked.symlink_to(self.external, target_is_directory=True)
        shutil.copytree(self.external, research / 'regular')
        before = {p.name: p.read_bytes() for p in self.external.iterdir()}
        output = repository / 'audit'
        run = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('run.py')),
            '--repo', str(repository), '--output', str(output)], capture_output=True, text=True, timeout=20)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        results = {row['packet']: row for row in json.loads((output / 'results.json').read_bytes())}
        self.assertEqual(results['linked']['manifest_check']['status'], 'fail')
        self.assertEqual(results['linked']['overall'], 'fail')
        self.assertEqual(results['regular']['overall'], 'pass')
        self.assertTrue(linked.is_symlink())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.external.iterdir()})

    def test_symlinked_payload_still_rejected(self):
        packet = self.root / 'packet'
        packet.mkdir()
        (packet / 'alias').symlink_to(self.external, target_is_directory=True)
        (packet / 'manifest.json').write_text(json.dumps(
            {'alias/data.txt': sha256(b'outside bytes\n')}))
        result = check.check_manifest(packet)
        self.assertEqual(result['status'], 'fail', result)


if __name__ == '__main__':
    unittest.main()
