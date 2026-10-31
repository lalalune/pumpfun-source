import copy
from contextlib import redirect_stdout
import io
from pathlib import Path
import struct
import tempfile
import unittest

import capture_retry
from test_capture import capture_responses, mutate_data, rpc_server


class DeploymentSlotContextTests(unittest.TestCase):
    def exercise(self, relation, valid):
        folder, manifest, original = capture_responses('spl_token')
        responses = [copy.deepcopy(row) for row in original]
        context = responses[0]['result']['context']['slot']
        slot = context + relation
        # The two full/metadata reads agree, so byte reread equality alone
        # cannot catch a slot that lies beyond this capture's initial context.
        for index in (1, 3):
            mutate_data(responses[index], lambda raw: struct.pack_into('<Q', raw, 4, slot))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'capture'
            with rpc_server(responses) as (url, _, _), redirect_stdout(io.StringIO()):
                if valid:
                    capture_retry.capture(url, 'spl_token', manifest['program'], output)
                else:
                    with self.assertRaisesRegex(AssertionError, 'deployment slot is newer'):
                        capture_retry.capture(url, 'spl_token', manifest['program'], output)
            if valid:
                self.assertEqual((output / 'deployed.so').read_bytes(), (folder / 'deployed.so').read_bytes())
            else:
                self.assertEqual(list(root.iterdir()), [])

    def test_future_deployment_slot_cannot_publish(self):
        self.exercise(1, False)

    def test_equal_and_older_deployment_slots_keep_payload_bytes(self):
        for relation in (0, -1):
            with self.subTest(relation=relation):
                self.exercise(relation, True)


if __name__ == '__main__':
    unittest.main()
