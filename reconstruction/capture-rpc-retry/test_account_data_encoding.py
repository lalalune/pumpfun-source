import copy
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import capture_retry
from test_capture import capture_responses, rpc_server


class AccountDataEncodingTests(unittest.TestCase):
    def test_wrong_encoding_on_each_account_read_cannot_publish(self):
        for program in ('associated_token', 'spl_token'):
            _, manifest, originals = capture_responses(program)
            for index in range(len(originals) - 1):
                with self.subTest(program=program, response=index):
                    responses = [copy.deepcopy(row) for row in originals]
                    responses[index]['result']['value']['data'][1] = 'base64+zstd'
                    with tempfile.TemporaryDirectory() as temporary:
                        output = Path(temporary) / 'capture'
                        with rpc_server(responses) as (url, _, _), redirect_stdout(io.StringIO()):
                            with self.assertRaisesRegex(ValueError, 'base64 data tuple'):
                                capture_retry.capture(url, program, manifest['program'], output)
                        self.assertFalse(output.exists())
                        self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_valid_encoding_preserves_retained_capture_bytes(self):
        for program in ('associated_token', 'spl_token'):
            folder, manifest, responses = capture_responses(program)
            with self.subTest(program=program), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'capture'
                with rpc_server(responses) as (url, _, _), redirect_stdout(io.StringIO()):
                    capture_retry.capture(url, program, manifest['program'], output)
                self.assertEqual((output / 'deployed.so').read_bytes(), (folder / 'deployed.so').read_bytes())

    def test_data_shape_is_checked_before_archived_indexing(self):
        for data in (None, {}, 'base64', [], ['encoded'], [1, 'base64'], ['encoded', 'base58'], ['encoded', 'base64', 'extra']):
            response = {'context': {'slot': 100}, 'value': {'data': data}}
            with self.subTest(data=data), patch.object(capture_retry, '_archived_rpc', return_value=response):
                with self.assertRaisesRegex(ValueError, 'base64 data tuple'):
                    capture_retry.contextual_rpc('unused', 'getAccountInfo', ['key', {}])


if __name__ == '__main__':
    unittest.main()
