import unittest
from unittest.mock import patch
import capture_retry
import test_context_slot_admission as context_tests


class ContextSlotU64(unittest.TestCase):
    def test_out_of_range_context_cannot_publish_a_capture(self):
        # Reuse the full loopback capture fixture with retained Pump ELF bytes.
        context_tests.CaptureContextTests().exercise(2**64, False)

    def test_requested_minimum_must_fit_the_same_slot_type(self):
        for minimum in (2**64, 2**80):
            with self.subTest(minimum=minimum):
                response = {'context': {'slot': minimum}, 'value': None}
                with patch.object(capture_retry, '_archived_rpc', return_value=response):
                    with self.assertRaises(ValueError):
                        capture_retry.contextual_rpc('local', 'getAccountInfo', ['key', {'minContextSlot': minimum}])

    def test_u64_maximum_and_zero_are_admitted(self):
        for slot in (0, 2**64 - 1):
            response = {'context': {'slot': slot}, 'value': None}
            with self.subTest(slot=slot), patch.object(capture_retry, '_archived_rpc', return_value=response):
                self.assertEqual(capture_retry.contextual_rpc('local', 'getAccountInfo',
                                 ['key', {'minContextSlot': slot}]), response)


if __name__ == '__main__': unittest.main()
