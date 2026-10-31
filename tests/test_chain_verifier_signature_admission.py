"""A chain verifier must reject a receipt whose signature vector was stripped.

``all(tx.verify_with_results())`` is true for a transaction that carries no
signatures: solders returns no verification results to inspect, and ``all`` of
an empty list is true. The gate therefore accepts a receipt whose signatures
were removed, so the packet's own tamper check has to be exercised with one.
"""
import base64
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from solders.transaction import Transaction

ROOT = Path(__file__).resolve().parents[1]
PACKET = 'amm-multi-hop-split-boost-tf-multi-user-pool-chains-20261029'
SUPPORT = (
    'evidence/original/pump_amm/deployed.so',
    'research/amm-multi-hop-images/control.so.gz',
    'research/amm-multi-hop-images/candidate.so.gz',
)


def strip_signatures(packet):
    """Rewrite every receipt without signatures and re-pin what pins them."""
    report_path = packet / 'runtime/report.json.gz'
    report = json.loads(gzip.decompress(report_path.read_bytes()))
    stripped = 0
    for part in report['parts']:
        path = packet / part['file']
        records = []
        for line in gzip.decompress(path.read_bytes()).splitlines():
            record = json.loads(line)
            tx = Transaction.from_bytes(base64.b64decode(record['transaction_base64']))
            wire = bytes([0]) + bytes(tx.message)
            record['transaction_base64'] = base64.b64encode(wire).decode()
            stripped += 1
            records.append(json.dumps(record, separators=(',', ':')).encode() + b'\n')
        data = gzip.compress(b''.join(records), mtime=0)
        path.write_bytes(data)
        part['sha256'], part['bytes'] = hashlib.sha256(data).hexdigest(), len(data)
    new_report = gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0)
    report_path.write_bytes(new_report)
    digests = {part['file']: part['sha256'] for part in report['parts']}
    digests['runtime/report.json.gz'] = hashlib.sha256(new_report).hexdigest()
    manifest_path = packet / 'MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    for entry in manifest['files']:
        if entry['path'] in digests:
            entry['sha256'] = digests[entry['path']]
    manifest_path.write_text(json.dumps(manifest, indent=1) + '\n')
    return stripped


def add_excess_signature(packet):
    """Rebind an actual retained signed receipt carrying an extra signature."""
    report_path = packet / 'runtime/report.json.gz'
    report = json.loads(gzip.decompress(report_path.read_bytes()))
    part = report['parts'][0]
    path = packet / part['file']
    records = [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
    tx = Transaction.from_bytes(base64.b64decode(records[0]['transaction_base64']))
    tx = Transaction.populate(tx.message, [*tx.signatures, tx.signatures[0]])
    records[0]['transaction_base64'] = base64.b64encode(bytes(tx)).decode()
    data = gzip.compress(b''.join(json.dumps(record, separators=(',', ':')).encode() + b'\n' for record in records), mtime=0)
    path.write_bytes(data)
    part['sha256'], part['bytes'] = hashlib.sha256(data).hexdigest(), len(data)
    report_data = gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0)
    report_path.write_bytes(report_data)
    manifest_path = packet / 'MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    for entry in manifest['files']:
        if entry['path'] == part['file']:
            entry['sha256'] = part['sha256']
        if entry['path'] == 'runtime/report.json.gz':
            entry['sha256'] = hashlib.sha256(report_data).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=1) + '\n')


class SignatureAdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='chain-signatures-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(ROOT / 'research' / PACKET, self.root / 'research' / PACKET)
        for relative in SUPPORT:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.packet = self.root / 'research' / PACKET

    def verify(self):
        return subprocess.run([sys.executable, '-I', '-B', str(self.packet / 'verify.py')],
                              cwd=self.root, text=True, capture_output=True, timeout=300)

    def test_the_copied_packet_passes_before_tampering(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS:', result.stdout)

    def test_excess_signature_is_rejected(self):
        add_excess_signature(self.packet)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('signature verification failed', result.stdout + result.stderr)

    def test_a_receipt_without_signatures_is_rejected(self):
        self.assertEqual(strip_signatures(self.packet), 396)
        result = self.verify()
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, combined)
        self.assertIn('signature verification failed', combined)
        self.assertNotIn('PASS:', result.stdout)


if __name__ == '__main__':
    unittest.main()
