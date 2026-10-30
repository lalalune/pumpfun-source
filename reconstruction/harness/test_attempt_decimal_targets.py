import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from attempt_applicability import address, inspect, FIELDS


class DecimalTargetTests(unittest.TestCase):
    def test_padded_decimal_address_matches_the_same_recorded_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = {key: 'a' * 64 for key in FIELDS}
            (root / 'result.json').write_bytes(b'{}')
            ledger = root / 'attempts.jsonl'
            row = {'target': '0016', 'approach': 'same', 'data': {
                'context': context, 'evidence': [{'path': 'result.json',
                'sha256': hashlib.sha256(b'{}').hexdigest()}]}}
            ledger.write_text(json.dumps(row), encoding='utf-8')
            before = ledger.read_bytes()
            for target in (16, '16', '0016', '0x10'):
                result = inspect(ledger, context, target, 'same', root)
                self.assertEqual(result['counts'], {'compatible': 1})
            self.assertEqual(ledger.read_bytes(), before)

    def test_negative_decimal_spelling_cannot_become_a_named_scope(self):
        with self.assertRaises(ValueError): address('-0016')
        self.assertEqual(address('all'), 'all')
        self.assertEqual(address('000'), 0)


if __name__ == '__main__': unittest.main()
