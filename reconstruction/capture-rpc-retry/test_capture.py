#!/usr/bin/env python3
"""Exercise capture failure/retry over HTTP with unchanged retained account bytes."""
import base64
import copy
from contextlib import contextmanager
from contextlib import redirect_stdout
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from capture_retry import SOURCE_SHA256, capture, module

ROOT = Path(__file__).resolve().parents[2]
MODES = (
    ('ordinary', (), None),
    ('-O', ('-O',), None),
    ('-OO', ('-OO',), None),
    ('PYTHONOPTIMIZE=1', (), '1'),
    ('PYTHONOPTIMIZE=2', (), '2'),
)
MUTATIONS = {
    'associated_token': (
        'program_not_executable', 'payload_not_elf', 'program_reread_mismatch',
    ),
    'spl_token': (
        'program_not_executable', 'wrong_program_owner', 'invalid_program_header',
        'wrong_programdata_owner', 'programdata_executable', 'invalid_programdata_header',
        'invalid_authority_tag', 'payload_not_elf', 'program_reread_mismatch',
        'programdata_metadata_mismatch',
    ),
}


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


def mutate_data(response, edit):
    value = response['result']['value']
    raw = bytearray(base64.b64decode(value['data'][0]))
    edit(raw)
    value['data'][0] = base64.b64encode(raw).decode()


def invalid_responses(name, mutation):
    _, _, original = capture_responses(name)
    responses = [copy.deepcopy(response) for response in original]
    legacy = name == 'associated_token'
    reread = 1 if legacy else 2
    if mutation == 'program_not_executable':
        responses[0]['result']['value']['executable'] = False
    elif mutation == 'wrong_program_owner':
        responses[0]['result']['value']['owner'] = '11111111111111111111111111111111'
    elif mutation == 'invalid_program_header':
        for index in (0, reread):
            mutate_data(responses[index], lambda raw: raw.__setitem__(slice(0, 4), b'\x01\0\0\0'))
    elif mutation == 'wrong_programdata_owner':
        responses[1]['result']['value']['owner'] = '11111111111111111111111111111111'
    elif mutation == 'programdata_executable':
        responses[1]['result']['value']['executable'] = True
    elif mutation == 'invalid_programdata_header':
        mutate_data(responses[1], lambda raw: raw.__setitem__(slice(0, 4), b'\x02\0\0\0'))
        mutate_data(responses[3], lambda raw: raw.__setitem__(slice(0, 4), b'\x02\0\0\0'))
    elif mutation == 'invalid_authority_tag':
        mutate_data(responses[1], lambda raw: raw.__setitem__(12, 2))
        mutate_data(responses[3], lambda raw: raw.__setitem__(12, 2))
    elif mutation == 'payload_not_elf':
        offset = 0 if legacy else 45
        mutate_data(responses[0 if legacy else 1], lambda raw: raw.__setitem__(offset, 0))
    elif mutation == 'program_reread_mismatch':
        mutate_data(responses[reread], lambda raw: raw.__setitem__(-1, raw[-1] ^ 1))
    elif mutation == 'programdata_metadata_mismatch':
        mutate_data(responses[3], lambda raw: raw.__setitem__(-1, raw[-1] ^ 1))
    else:
        raise ValueError('unknown capture mutation: ' + mutation)
    return responses


def run_probe(name, mutation):
    folder, manifest, responses = capture_responses(name)
    if mutation != 'valid':
        responses = invalid_responses(name, mutation)
    with tempfile.TemporaryDirectory(prefix='capture-optimization-probe-') as temporary:
        output = Path(temporary) / 'capture'
        error = None
        log = io.StringIO()
        with rpc_server(responses) as (url, requests, pending):
            try:
                with redirect_stdout(log):
                    capture(url, name, manifest['program'], output)
            except Exception as exception:
                error = type(exception).__name__
        result = {
            'accepted': error is None,
            'error': error,
            'output_exists': output.exists(),
            'request_count': len(requests),
            'pending_count': len(pending),
            'log': log.getvalue(),
        }
        if output.exists():
            result['file_sha256'] = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in output.iterdir() if path.name != 'capture.json'
            }
            saved = json.loads((output / 'capture.json').read_text())
            keys = ('program', 'owner', 'genesis_hash', 'payload_sha256', 'payload_bytes',
                    'program_sha256', 'last_deploy_slot', 'upgrade_authority')
            result['report'] = {key: saved[key] for key in keys}
        print(json.dumps(result, sort_keys=True))


def subprocess_probe(mode, name, mutation):
    label, flags, optimization = mode
    environment = os.environ.copy()
    environment.pop('PYTHONOPTIMIZE', None)
    if optimization is not None:
        environment['PYTHONOPTIMIZE'] = optimization
    result = subprocess.run(
        [sys.executable, *flags, '-B', str(Path(__file__)), '--probe', name, mutation],
        capture_output=True, text=True, env=environment,
    )
    if result.returncode:
        raise AssertionError(f'{label} probe failed:\n{result.stderr}')
    return json.loads(result.stdout)


class CaptureRetryTests(unittest.TestCase):
    def test_source_binding_matches_the_reviewed_archive(self):
        self.assertEqual(hashlib.sha256((ROOT / 'scripts/capture.py').read_bytes()).hexdigest(),
                         SOURCE_SHA256)

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

    def run_adapter_with_rename_module(self, deep_text):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'scripts').mkdir()
            (root / 'scripts/capture.py').write_bytes((ROOT / 'scripts/capture.py').read_bytes())
            (root / 'scripts/deep_disassembly.py').write_text(deep_text, encoding='utf-8')
            adapter = root / 'reconstruction/capture-rpc-retry/capture_retry.py'
            adapter.parent.mkdir(parents=True)
            adapter.write_bytes(Path(__file__).with_name('capture_retry.py').read_bytes())
            return subprocess.run([sys.executable, '-B', str(adapter)], capture_output=True, text=True)

    def test_changed_rename_is_rejected_before_execution(self):
        deep = (ROOT / 'scripts/deep_disassembly.py').read_text(encoding='utf-8')
        anchor = '    if os.name == "nt" and not exchange:\n'
        self.assertEqual(deep.count(anchor), 1)
        changed = deep.replace(anchor, "    raise RuntimeError('untrusted rename executed')\n" + anchor)
        result = self.run_adapter_with_rename_module(changed)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('reviewed no-replace rename changed', result.stderr)
        self.assertNotIn('untrusted rename executed', result.stderr)

    def test_rename_binding_ignores_the_rest_of_the_analysis_module(self):
        deep = (ROOT / 'scripts/deep_disassembly.py').read_text(encoding='utf-8')
        # Only rename_directory is admitted; the module's own imports never run.
        changed = "raise RuntimeError('analysis module executed')\n" + deep
        result = self.run_adapter_with_rename_module(changed)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_admitted_rename_refuses_an_existing_empty_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage, destination = Path(temporary) / 'stage', Path(temporary) / 'capture'
            stage.mkdir(); (stage / 'manifest.json').write_text('{}')
            destination.mkdir()
            with self.assertRaises(OSError):
                module.rename_directory(stage, destination)
            self.assertTrue((stage / 'manifest.json').exists())
            self.assertEqual(list(destination.iterdir()), [])

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

    def test_validation_mutations_are_rejected_in_every_optimization_mode(self):
        for name, mutations in MUTATIONS.items():
            for mutation in mutations:
                for mode in MODES:
                    with self.subTest(loader=name, mutation=mutation, mode=mode[0]):
                        result = subprocess_probe(mode, name, mutation)
                        self.assertFalse(result['accepted'])
                        self.assertEqual(result['error'], 'AssertionError')
                        self.assertFalse(result['output_exists'])

    def test_valid_captures_are_identical_in_every_optimization_mode(self):
        for name in MUTATIONS:
            folder, manifest, _ = capture_responses(name)
            expected_files = {'program-account.bin', 'deployed.so'}
            if manifest.get('loader') != 'legacy-v2':
                expected_files.add('programdata-account.bin')
            expected_hashes = {
                filename: hashlib.sha256((folder / filename).read_bytes()).hexdigest()
                for filename in expected_files
            }
            keys = ('program', 'owner', 'genesis_hash', 'payload_sha256', 'payload_bytes',
                    'program_sha256', 'last_deploy_slot', 'upgrade_authority')
            expected_report = {key: manifest[key] for key in keys}
            for mode in MODES:
                with self.subTest(loader=name, mode=mode[0]):
                    result = subprocess_probe(mode, name, 'valid')
                    self.assertTrue(result['accepted'])
                    self.assertTrue(result['output_exists'])
                    self.assertEqual(result['pending_count'], 0)
                    self.assertEqual(result['file_sha256'], expected_hashes)
                    self.assertEqual(result['report'], expected_report)


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--probe':
        run_probe(sys.argv[2], sys.argv[3])
    else:
        unittest.main()
