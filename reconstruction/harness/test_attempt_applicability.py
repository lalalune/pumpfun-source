import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from attempt_applicability import FIELDS, classify, inspect


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

    def test_escaping_and_symlink_paths_are_rejected(self):
        for name in ['../outside', '/absolute', 'link']:
            if name == 'link': (self.root/'link').symlink_to(self.root/'result.json')
            self.row['data']['evidence'][0]['path'] = name
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


if __name__ == '__main__': unittest.main()
