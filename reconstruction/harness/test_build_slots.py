"""Invalid concurrency settings should fail instead of waiting forever."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fastbuild


class BuildSlotTests(unittest.TestCase):
    def test_nonpositive_slots_fail_before_waiting_or_writing(self):
        for count in (0, -1):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as directory:
                lockdir = Path(directory) / 'locks'
                with patch.object(fastbuild, 'SLOTS', count), \
                        patch.object(fastbuild, 'LOCKDIR', lockdir), \
                        patch.object(fastbuild.time, 'sleep', side_effect=AssertionError('would wait forever')):
                    with self.assertRaisesRegex(ValueError, 'PUMP_BUILD_SLOTS'):
                        fastbuild.acquire_slot()
                self.assertFalse(lockdir.exists())

    def test_positive_slot_can_be_released_and_reacquired(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(fastbuild, 'SLOTS', 1), \
                    patch.object(fastbuild, 'LOCKDIR', Path(directory)):
                first = fastbuild.acquire_slot()
                self.assertFalse(first.closed)
                first.close()
                second = fastbuild.acquire_slot()
                second.close()


if __name__ == '__main__':
    unittest.main()
