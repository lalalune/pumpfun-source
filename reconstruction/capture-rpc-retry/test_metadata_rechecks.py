"""Serve retained accounts over loopback; no external RPC or transactions."""
import contextlib
import copy
import io
from pathlib import Path
import tempfile
import unittest
import capture_retry
from test_capture import capture_responses, rpc_server


class MetadataRechecks(unittest.TestCase):
    def test_changed_recheck_metadata_cannot_publish(self):
        for name, index in (('associated_token', 1), ('spl_token', 2), ('spl_token', 3)):
            for field, value in (('owner', 'different-owner'), ('executable', index == 3)):
                with self.subTest(name=name, index=index, field=field):
                    folder, manifest, responses = capture_responses(name)
                    responses = [copy.deepcopy(response) for response in responses]
                    responses[index]['result']['value'][field] = value
                    with tempfile.TemporaryDirectory() as temporary, rpc_server(responses) as (url, requests, pending):
                        output = Path(temporary) / 'capture'
                        with contextlib.redirect_stdout(io.StringIO()):
                            with self.assertRaisesRegex(AssertionError, 'account metadata changed'):
                                capture_retry.capture(url, name, manifest['program'], output)
                        self.assertFalse(output.exists())
                        self.assertFalse(list(Path(temporary).iterdir()))
                        self.assertTrue(all(request['method'] == 'getAccountInfo' for request in requests))

    def test_unchanged_metadata_keeps_the_exact_retained_payload(self):
        for name in ('associated_token', 'spl_token'):
            with self.subTest(name=name):
                folder, manifest, responses = capture_responses(name)
                with tempfile.TemporaryDirectory() as temporary, rpc_server(responses) as (url, requests, pending):
                    output = Path(temporary) / 'capture'
                    with contextlib.redirect_stdout(io.StringIO()):
                        capture_retry.capture(url, name, manifest['program'], output)
                    self.assertEqual((output / 'deployed.so').read_bytes(), (folder / 'deployed.so').read_bytes())
                    self.assertEqual(pending, [])


if __name__ == '__main__': unittest.main()
