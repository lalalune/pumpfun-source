"""A certificate name the filesystem admits must survive its staging prefix."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_data_order as gate


class DataOrderLongNameTests(unittest.TestCase):
    def test_longest_valid_name_publishes(self):
        with tempfile.TemporaryDirectory() as directory:
            limit = os.pathconf(directory, 'PC_NAME_MAX')
            output = Path(directory)/('c' * (limit - len('.json')) + '.json')
            output.write_bytes(b'')  # The filesystem admits this exact name.
            output.unlink()
            try:
                gate.publish_certificate(output, {'schema': 1})
            except OSError as error:
                self.fail(f'valid output name was refused: {error}')
            self.assertEqual(json.loads(output.read_bytes()), {'schema': 1})
            self.assertEqual([path.name for path in Path(directory).iterdir()], [output.name])


if __name__ == '__main__':
    unittest.main()
