#!/usr/bin/env python3
"""Exercise capture failure/retry over HTTP with unchanged retained account bytes."""
import base64
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from capture_retry import capture, module

ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def rpc_server(responses):
    pending = list(responses)
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(request)
            response = {'jsonrpc': '2.0', 'id': request['id'], **pending.pop(0)}
            body = json.dumps(response).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01))
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', requests, pending
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def capture_responses(name):
    folder = ROOT / 'evidence/dependencies' / name
    manifest = json.loads((folder / 'capture.json').read_text())
    slot = max(manifest['context_slots'])

    def account(filename, executable):
        return {'result': {'context': {'slot': slot}, 'value': {
            'owner': manifest['owner'], 'executable': executable, 'lamports': 1,
            'data': [base64.b64encode((folder / filename).read_bytes()).decode(), 'base64'],
        }}}

    program = account('program-account.bin', True)
    responses = [program]
    if manifest.get('loader') == 'legacy-v2':
        responses.append(program)
    else:
        responses.extend([account('programdata-account.bin', False), program])
        metadata = account('programdata-account.bin', False)
        raw = (folder / 'programdata-account.bin').read_bytes()[:45]
        metadata['result']['value']['data'][0] = base64.b64encode(raw).decode()
        responses.append(metadata)
    responses.append({'result': manifest['genesis_hash']})
    return folder, manifest, responses


class CaptureRetryTests(unittest.TestCase):
    def test_changed_archive_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'scripts').mkdir()
            (root / 'scripts/capture.py').write_text("raise RuntimeError('untrusted source executed')\n")
            adapter = root / 'reconstruction/capture-rpc-retry/capture_retry.py'
            adapter.parent.mkdir(parents=True)
            adapter.write_bytes(Path(__file__).with_name('capture_retry.py').read_bytes())
            result = subprocess.run([sys.executable, '-B', str(adapter)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('archived capture source changed', result.stderr)
            self.assertNotIn('untrusted source executed', result.stderr)

    def check_retry(self, name, failure):
        folder, manifest, responses = capture_responses(name)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'capture'
            if failure == 'account':
                failed = [{'result': {'context': {'slot': 1}, 'value': None}}]
                error = ValueError
            else:
                failed = responses[:-1] + [{'error': {'code': -32000, 'message': 'unavailable'}}] * 6
                error = RuntimeError
            with rpc_server(failed + responses) as (url, requests, pending):
                # Keep the six real HTTP error responses, skipping only retry delays.
                with patch.object(module.time, 'sleep'), self.assertRaises(error):
                    capture(url, name, manifest['program'], output)
                self.assertFalse(output.exists(), 'failed RPC capture reserved its destination')
                capture(url, name, manifest['program'], output)
                self.assertFalse(pending)
                self.assertEqual(len(requests), len(failed) + len(responses))
            expected_files = {'capture.json', 'program-account.bin', 'deployed.so'}
            if manifest.get('loader') != 'legacy-v2':
                expected_files.add('programdata-account.bin')
            self.assertEqual({p.name for p in output.iterdir()}, expected_files)
            for filename in expected_files - {'capture.json'}:
                self.assertEqual((output / filename).read_bytes(), (folder / filename).read_bytes())
            saved = json.loads((output / 'capture.json').read_text())
            for key in ('program', 'owner', 'genesis_hash', 'payload_sha256', 'payload_bytes',
                        'program_sha256', 'last_deploy_slot', 'upgrade_authority'):
                self.assertEqual(saved[key], manifest[key])

    def test_missing_account_can_retry_at_same_destination(self):
        for name in ('associated_token', 'spl_token'):
            with self.subTest(loader=name):
                self.check_retry(name, 'account')

    def test_genesis_failure_can_retry_at_same_destination(self):
        for name in ('associated_token', 'spl_token'):
            with self.subTest(loader=name):
                self.check_retry(name, 'genesis')

    def test_existing_evidence_is_preserved_without_rpc(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'capture'
            output.mkdir()
            sentinel = output / 'capture.json'
            sentinel.write_bytes(b'prior evidence')
            with rpc_server([]) as (url, requests, pending):
                with self.assertRaises(FileExistsError):
                    capture(url, 'existing', 'unused', output)
                self.assertFalse(requests)
            self.assertEqual(sentinel.read_bytes(), b'prior evidence')
            self.assertEqual(list(output.iterdir()), [sentinel])


if __name__ == '__main__':
    unittest.main()
