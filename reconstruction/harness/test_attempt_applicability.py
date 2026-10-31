import contextlib
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import os
from attempt_applicability import FIELDS, address, classify, inspect
from test_support import directory_link


@contextlib.contextmanager
def decimal_digit_limit(limit):
    setter = getattr(sys, 'set_int_max_str_digits', None)
    if setter is None: raise unittest.SkipTest('interpreter has no decimal conversion limit')
    previous = sys.get_int_max_str_digits()
    setter(limit)
    try: yield
    finally: setter(previous)


class ApplicabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.context = {key: 'a'*64 for key in FIELDS}
        evidence = self.root/'result.json'; evidence.write_bytes(b'{}')
        self.row = {'target': '0x10', 'approach': 'shape-A', 'status': 'rejected',
                    'data': {'context': self.context.copy(), 'evidence': [{'path': 'result.json', 'sha256': hashlib.sha256(b'{}').hexdigest()}]}}

    def test_matching_context_and_intact_evidence(self):
        self.assertEqual(classify(self.row, self.context, self.root)['applicability'], 'compatible')

    def test_each_changed_input_is_stale(self):
        for field in FIELDS:
            context = dict(self.context, **{field: 'b'*64})
            result = classify(self.row, context, self.root)
            self.assertEqual(result['applicability'], 'stale'); self.assertEqual(result['reasons'], [field])

    def test_missing_context_and_changed_evidence_are_unverifiable(self):
        self.assertEqual(classify({'data': {}}, self.context, self.root)['applicability'], 'unverifiable')
        (self.root/'result.json').write_text('changed')
        self.assertEqual(classify(self.row, self.context, self.root)['applicability'], 'unverifiable')

    def test_escaping_paths_are_rejected(self):
        for name in ['../outside', '/absolute']:
            self.row['data']['evidence'][0]['path'] = name
            self.assertEqual(classify(self.row, self.context, self.root)['applicability'], 'unverifiable')

    def test_file_symlink_path_is_rejected(self):
        try:
            (self.root/'link').symlink_to(self.root/'result.json')
        except OSError as error:
            if os.name == 'nt' and error.winerror == 1314:
                self.skipTest('Windows file-symlink privilege unavailable')
            raise
        self.row['data']['evidence'][0]['path'] = 'link'
        self.assertEqual(classify(self.row, self.context, self.root)['applicability'], 'unverifiable')

    def test_directory_link_path_is_rejected(self):
        outside = self.root/'outside'; outside.mkdir()
        (outside/'result.json').write_bytes(b'{}')
        with directory_link(outside, self.root/'linked'):
            self.row['data']['evidence'][0]['path'] = 'linked/result.json'
            self.assertEqual(classify(self.row, self.context, self.root)['applicability'], 'unverifiable')

    def test_named_scopes_are_valid_and_selected_exactly(self):
        ledger = self.root/'ledger.jsonl'
        ledger.write_text(json.dumps(dict(self.row, target='all')) + '\n' + json.dumps(self.row))
        result = inspect(ledger, self.context, 'all', 'shape-A', self.root)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['parse_errors'], [])

    def test_exact_selection_errors_and_read_only_behavior(self):
        ledger = self.root/'ledger.jsonl'
        other = dict(self.row, approach='shape-B')
        raw = json.dumps(self.row)+'\n'+json.dumps(other)+'\n'+ '{"target":1,"target":2}\n'
        ledger.write_text(raw)
        result = inspect(ledger, self.context, '16', 'shape-A', self.root)
        self.assertEqual(result['counts'], {'compatible': 1})
        self.assertEqual(len(result['parse_errors']), 1)
        self.assertEqual(ledger.read_text(), raw)

    def test_zero_padded_decimal_targets_keep_numeric_equality(self):
        with decimal_digit_limit(640):
            self.assertEqual(address('0'*2000 + '16'), 16)
            self.assertEqual(address('0'*2000), 0)

    def test_zero_padded_ledger_target_is_selected_by_value(self):
        ledger = self.root/'ledger.jsonl'
        ledger.write_text(json.dumps(dict(self.row, target='0'*700 + '16')) + '\n')
        with decimal_digit_limit(640):
            result = inspect(ledger, self.context, '16', 'shape-A', self.root)
        self.assertEqual(result['counts'], {'compatible': 1})
        self.assertEqual(result['parse_errors'], [])

    def test_over_long_significant_decimal_targets_remain_named_scopes(self):
        with decimal_digit_limit(640):
            self.assertEqual(address('1'*700), '1'*700)


if __name__ == '__main__': unittest.main()
