#!/usr/bin/env python3
"""Verify the public fixture ledger against captured evidence and the coverage ledger.

Public fixtures are historical replay snapshots, not live behavior. The backend
registration gate accepts the documented record shape but treats the provenance
source as an opaque string; this offline gate binds each fixture's source to a
captured evidence object that exists, matches its recorded SHA-256, status and
JSON body, and requires coverage.json to count the snapshots exactly. Every
check raises ValueError so that `python -O` cannot disable it. No network access.
"""
import hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = {'method', 'path', 'status', 'body', 'source'}
OPTIONAL_FIELDS = {'query', 'headers'}
HTTP_FIELD_NAME = re.compile(r"[!#$%&'*+.^_|~0-9A-Za-z-]+")
EVIDENCE_LEDGERS = ('evidence/web/manifest.json', 'evidence/api-probes.json', 'evidence/source-map-probes.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(root, path):
    return json.loads((root / path).read_text(encoding='utf-8'))


def captured_records(root):
    records = {}
    for ledger in EVIDENCE_LEDGERS:
        document = read_json(root, ledger)
        entries = document['records'] if isinstance(document, dict) else document
        require(isinstance(entries, list), f'{ledger}: capture records must be a list')
        for record in entries:
            path, digest = record['path'], record['sha256']
            require(path not in records or records[path]['sha256'] == digest,
                    f'{ledger}: conflicting sha256 for captured object {path}')
            records.setdefault(path, record)
    return records


def canonical_key(fixture):
    query = fixture.get('query') or {}
    return (fixture['method'], fixture['path'], tuple(sorted(query)))


def verify(root=ROOT, fixtures=None, coverage=None):
    fixtures = read_json(root, 'contracts/public-fixtures.json') if fixtures is None else fixtures
    coverage = read_json(root, 'contracts/coverage.json') if coverage is None else coverage
    records = captured_records(root)
    require(isinstance(fixtures, list), 'public-fixtures.json must be a list of snapshots')
    seen = set()
    for fixture in fixtures:
        require(isinstance(fixture, dict) and REQUIRED_FIELDS <= set(fixture)
                and not (set(fixture) - REQUIRED_FIELDS - OPTIONAL_FIELDS),
                'public fixture must carry exactly the documented registration fields '
                '(method, path, status, body, source, optional query and headers)')
        key = canonical_key(fixture)
        label = f'{fixture["method"]} {fixture["path"]}'
        require(fixture['method'] in ('GET', 'HEAD'), f'{label}: public fixtures are GET/HEAD only')
        require(key not in seen, f'{label}: duplicate public fixture')
        seen.add(key)
        path = fixture['path']
        require(isinstance(path, str) and path.startswith('/') and '?' not in path and '#' not in path
                and '\\' not in path and all(0x21 <= ord(c) <= 0x7e for c in path),
                f'{label}: path must be a local absolute request target without a query or fragment')
        query = fixture.get('query')
        require(query is None or (isinstance(query, dict)
                and all(isinstance(name, str) and isinstance(value, str) for name, value in query.items())),
                f'{label}: query must be a plain map of string values')
        status = fixture['status']
        require(isinstance(status, int) and not isinstance(status, bool) and 200 <= status < 600,
                f'{label}: status must be a final integer response status (200 through 599)')
        headers = fixture.get('headers')
        require(headers is None or (isinstance(headers, dict) and all(
                isinstance(name, str) and HTTP_FIELD_NAME.fullmatch(name) and isinstance(value, str)
                for name, value in headers.items())),
                f'{label}: headers must be a plain map of valid HTTP field names to string values')
        source = fixture['source']
        require(isinstance(source, str) and source and not source.startswith('/')
                and '..' not in source.split('/'),
                f'{label}: source must be a non-empty repository-relative captured object path')
        require(source in records, f'{label}: source is not a captured evidence object')
        record = records[source]
        target = root / source
        require(target.is_file(), f'{label}: captured object {source} is missing')
        raw = target.read_bytes()
        require(record['sha256'] == hashlib.sha256(raw).hexdigest(),
                f'{label}: captured object {source} does not match its recorded sha256')
        require(record.get('bytes', len(raw)) == len(raw),
                f'{label}: captured object {source} differs from its recorded length')
        require(record.get('status') == status,
                f'{label}: fixture status differs from the captured status of {source}')
        try:
            captured = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError(f'{label}: captured object {source} is not UTF-8 JSON') from None
        require(fixture['body'] == captured, f'{label}: fixture body differs from the captured object {source}')
    fixtures_coverage = coverage.get('fixtures')
    require(isinstance(fixtures_coverage, dict), 'coverage.json must carry a fixtures ledger')
    require(fixtures_coverage.get('publicSnapshots') == len(fixtures),
            'coverage.json fixtures.publicSnapshots differs from the public fixture ledger')
    return len(fixtures)


def main():
    count = verify()
    print(f'Public fixture ledger verified: {count} snapshot(s) backed by captured evidence; '
          f'coverage.json fixtures.publicSnapshots matches; 0 implemented, 0 qualified')


if __name__ == '__main__':
    try:
        main()
    except ValueError as error:
        print(f'Fixture verification failed: {error}', file=sys.stderr)
        sys.exit(1)
