import copy
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_fixtures', ROOT / 'scripts/verify-fixtures.py')
verify_fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_fixtures)


def load(name):
    return json.loads((ROOT / 'contracts' / name).read_text(encoding='utf-8'))


class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load('public-fixtures.json')
        cls.coverage = load('coverage.json')

    def mutated(self):
        return copy.deepcopy(self.fixtures), copy.deepcopy(self.coverage)

    def assertRejects(self, fixtures, coverage, message):
        with self.assertRaisesRegex(ValueError, message):
            verify_fixtures.verify(fixtures=fixtures, coverage=coverage)

    def test_checked_in_ledger_verifies(self):
        self.assertEqual(verify_fixtures.verify(), len(self.fixtures))

    def test_rejects_public_snapshot_count_drift(self):
        fixtures, coverage = self.mutated()
        coverage['fixtures']['publicSnapshots'] += 1
        self.assertRejects(fixtures, coverage, 'publicSnapshots')

    def test_rejects_unbacked_fixture_source(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['source'] = 'evidence/web/objects/0000000000000000'
        self.assertRejects(fixtures, coverage, 'not a captured evidence object')

    def test_rejects_fixture_body_drift(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['body']['solPrice'] = 0
        self.assertRejects(fixtures, coverage, 'body differs')

    def test_rejects_status_drift(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['status'] = 500
        self.assertRejects(fixtures, coverage, 'status differs')

    def test_rejects_captured_status_drift(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['status'] = 404
        self.assertRejects(fixtures, coverage, 'status differs')

    def test_rejects_informational_status(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['status'] = 100
        self.assertRejects(fixtures, coverage, 'final integer response status')

    def test_rejects_non_readonly_fixture(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['method'] = 'POST'
        self.assertRejects(fixtures, coverage, 'GET/HEAD')

    def test_rejects_duplicate_fixture(self):
        fixtures, coverage = self.mutated()
        fixtures.append(copy.deepcopy(fixtures[0]))
        coverage['fixtures']['publicSnapshots'] = len(fixtures)
        self.assertRejects(fixtures, coverage, 'duplicate')

    def test_rejects_missing_provenance_field(self):
        fixtures, coverage = self.mutated()
        del fixtures[0]['source']
        self.assertRejects(fixtures, coverage, 'registration fields')

    def test_rejects_unknown_fixture_field(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['extra'] = 1
        self.assertRejects(fixtures, coverage, 'registration fields')

    def test_accepts_documented_optional_fields(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['query'] = {'stale': 'false'}
        self.assertEqual(verify_fixtures.verify(fixtures=fixtures, coverage=coverage), 1)

    def test_rejects_query_string_in_path(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['path'] = '/services/frontend/sol-price?stale=1'
        self.assertRejects(fixtures, coverage, 'without a query or fragment')

    def test_rejects_fragment_in_path(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['path'] = '/services/frontend/sol-price#top'
        self.assertRejects(fixtures, coverage, 'without a query or fragment')

    def test_rejects_escaping_source_path(self):
        fixtures, coverage = self.mutated()
        fixtures[0]['source'] = 'evidence/web/objects/../../contracts/coverage.json'
        self.assertRejects(fixtures, coverage, 'repository-relative')

    def test_rejects_captured_object_hash_drift(self):
        fixture, coverage = self.mutated()
        fixture = fixture[0]
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'contracts').mkdir()
            (root / 'evidence/web/objects').mkdir(parents=True)
            record = {'url': 'https://example.invalid/sol-price', 'final_url': 'https://example.invalid/sol-price',
                      'status': fixture['status'], 'path': fixture['source'],
                      'bytes': 63, 'sha256': 'ec5b492ad94042c21399e80f4d0ff501ed5be4b6d461888549f4b23cae8384df',
                      'headers': {}}
            (root / 'contracts/public-fixtures.json').write_text(json.dumps([fixture]), encoding='utf-8')
            (root / 'contracts/coverage.json').write_text(json.dumps(coverage), encoding='utf-8')
            (root / 'evidence/web/manifest.json').write_text(json.dumps({'records': []}), encoding='utf-8')
            (root / 'evidence/api-probes.json').write_text(json.dumps([record]), encoding='utf-8')
            (root / 'evidence/source-map-probes.json').write_text(json.dumps([]), encoding='utf-8')
            # Same JSON value, different bytes: the recorded sha256 no longer matches the file.
            (root / fixture['source']).write_text(json.dumps(fixture['body'], indent=1), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'sha256'):
                verify_fixtures.verify(root=root)
            # Matching bytes verify against the same ledgers.
            (root / fixture['source']).write_text(json.dumps(fixture['body'], separators=(',', ':')), encoding='utf-8')
            record['sha256'] = hashlib.sha256((root / fixture['source']).read_bytes()).hexdigest()
            record['bytes'] = (root / fixture['source']).stat().st_size
            (root / 'evidence/api-probes.json').write_text(json.dumps([record]), encoding='utf-8')
            self.assertEqual(verify_fixtures.verify(root=root), 1)


if __name__ == '__main__':
    unittest.main()
