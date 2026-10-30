#!/usr/bin/env python3
"""Verify developer API bindings against checked-in contracts and captured bytes.

Contract-bound is not implementation, qualification, website origin binding or
feature credit. Every critical check raises explicitly, so Python -O/-OO cannot
disable validation. This verifier performs no network access.
"""

import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
METHODS = {'get', 'put', 'post', 'delete', 'patch', 'head', 'options'}
PUBLIC_READ_PATTERN = re.compile(
    r'"((?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) [^"]+)"'
    r':\(0,[A-Za-z_$][\w$]*\.publicRead\)\("([a-z.]+)"'
)
FEATURE_BY_SCOPE = {
    'content.read': 'content',
    'graph.read': 'profile',
    'leaderboards.read': 'leaderboard',
    'moderation.read': 'profile',
    'positions.read': 'portfolio',
    'profiles.read': 'profile',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(root, path):
    target = root / path
    require(target.is_file(), f'Missing required file: {path}')
    return json.loads(target.read_text(encoding='utf-8'))


def utf16_length(text):
    return len(text.encode('utf-16-le')) // 2


def utf16_slice(text, start, end):
    require(
        type(start) is int and type(end) is int and 0 <= start < end,
        f'Invalid range {start}..{end}',
    )
    units = text.encode('utf-16-le')
    require(2 * end <= len(units), f'Range {start}..{end} exceeds source')
    return units[2 * start:2 * end].decode('utf-16-le', errors='strict')


def resolve_pointer(document, pointer):
    require(pointer.startswith('#/'), f'Unsupported JSON pointer {pointer}')
    node = document
    for token in pointer[2:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        if isinstance(node, list):
            require(
                token.isdigit() and int(token) < len(node),
                f'Unresolved JSON pointer {pointer}',
            )
            node = node[int(token)]
        else:
            require(
                isinstance(node, dict) and token in node,
                f'Unresolved JSON pointer {pointer}',
            )
            node = node[token]
    return node


def spec_operations(spec):
    return {
        f'{method.upper()} {path}': (path, method, operation)
        for path, path_item in spec['paths'].items()
        for method, operation in path_item.items()
        if method in METHODS
    }


def quoted_strings(source):
    return [
        json.loads(f'"{value}"')
        for value in re.findall(r'"((?:\\.|[^"\\])*)"', source)
    ]


def route_object(source, offset, operation):
    require(source[offset:offset + 2] == ',{', f'{operation}: missing captured route object')
    start = offset + 1
    depth = 0
    quote = None
    escaped = False
    for index in range(start, len(source)):
        character = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == quote:
                quote = None
        elif character in {'"', "'", '`'}:
            quote = character
        elif character == '{':
            depth += 1
        elif character == '}':
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise ValueError(f'{operation}: unterminated captured route object')


def captured_routes(source):
    keyed = re.search(r'KEYED_ROUTE_CODES=\[([^\]]*)\]', source)
    require(keyed is not None, 'Captured contract lacks KEYED_ROUTE_CODES')
    keyed_codes = quoted_strings(keyed.group(1))
    require(len(keyed_codes) == len(set(keyed_codes)), 'Captured KEYED_ROUTE_CODES contains duplicates')

    routes = {}
    for match in PUBLIC_READ_PATTERN.finditer(source):
        operation, scope = match.groups()
        require(operation not in routes, f'{operation}: duplicate captured publicRead route')
        body = route_object(source, match.end(), operation)
        emits_match = re.search(r'(?:\{|,)emits:\[([^\]]*)\]', body)
        emits = [] if emits_match is None else quoted_strings(emits_match.group(1))
        error_codes = keyed_codes + emits
        require(
            len(error_codes) == len(set(error_codes)),
            f'{operation}: captured error-code contract contains duplicates',
        )
        routes[operation] = {
            'scope': scope,
            'start': utf16_length(source[:match.start()]),
            'end': utf16_length(source[:match.end()]),
            'errorCodes': sorted(error_codes),
        }
    return routes


def manifest_index(manifest):
    hashes = {}
    for record in manifest['records']:
        if record.get('status') != 200:
            continue
        path = record['path']
        require(path not in hashes, f'Duplicate successful manifest path: {path}')
        hashes[path] = record['sha256']
    return hashes


def source_text(root, manifest_hashes, source_cache, source, operation):
    require(source in manifest_hashes, f'{operation}: source is not a captured manifest object')
    path = root / source
    require(path.is_file(), f'{operation}: captured source is missing')
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    require(actual == manifest_hashes[source], f'{operation}: captured source sha256 differs from manifest')
    if source not in source_cache:
        source_cache[source] = raw.decode('utf-8')
    return source_cache[source]


def verify_contract(root, manifest_hashes, source_cache, route_cache, operation, scope, contract):
    source = contract['source']
    text = source_text(root, manifest_hashes, source_cache, source, operation)
    require(
        contract['sha256'] == manifest_hashes[source],
        f'{operation}: contract sha256 does not match captured manifest',
    )
    if source not in route_cache:
        route_cache[source] = captured_routes(text)
    require(operation in route_cache[source], f'{operation}: absent from captured publicRead contract')
    captured = route_cache[source][operation]
    require(captured['scope'] == scope, f'{operation}: captured scope differs from {scope}')
    require(
        contract['start'] == captured['start'] and contract['end'] == captured['end'],
        f'{operation}: contract UTF-16 range differs from captured literal boundaries',
    )
    literal = utf16_slice(text, contract['start'], contract['end'])
    pattern = (
        r'"' + re.escape(operation)
        + r'":\(0,[A-Za-z_$][\w$]*\.publicRead\)\("'
        + re.escape(scope) + r'"'
    )
    require(
        re.fullmatch(pattern, literal) is not None,
        f'{operation}: contract range does not hold its publicRead({scope}) literal',
    )
    return captured


def verify_call_sites(root, manifest_hashes, source_cache, occurrences, operation, contract, sites):
    require(isinstance(sites, list), f'{operation}: clientCallSites must be a list')
    reported = set()
    for site in sites:
        key = (site['source'], site['start'], site['end'])
        require(key not in reported, f'{operation}: duplicate client call site')
        reported.add(key)
        text = source_text(root, manifest_hashes, source_cache, site['source'], operation)
        require(
            utf16_slice(text, site['start'], site['end']) == f'"{operation}"',
            f'{operation}: call-site range does not hold the operation literal',
        )

    expected = {
        occurrence
        for occurrence in occurrences.get(operation, set())
        if not (
            occurrence[0] == contract['source']
            and occurrence[1] == contract['start']
        )
    }
    require(
        reported == expected,
        f'{operation}: client call sites differ from internal-operations inventory',
    )


def require_unqualified(entry, status):
    operation = entry.get('operation')
    require(entry.get('status') == status, f'{operation}: status must be {status}')
    require(entry.get('implemented') is False, f'{operation}: bindings must not claim native implementation')
    require(entry.get('qualified') is False, f'{operation}: bindings must not claim compatibility qualification')


def verify(root=ROOT, bindings=None, coverage=None):
    spec = read_json(root, 'contracts/developer.openapi.json')
    inventory = read_json(root, 'contracts/internal-operations.json')
    manifest = read_json(root, 'evidence/web/manifest.json')
    bindings = read_json(root, 'contracts/developer-bindings.json') if bindings is None else bindings
    coverage = read_json(root, 'contracts/coverage.json') if coverage is None else coverage
    manifest_hashes = manifest_index(manifest)
    occurrences = {}
    for occurrence in inventory['occurrences']:
        key = (occurrence['source'], occurrence['start'], occurrence['end'])
        occurrences.setdefault(occurrence['operation'], set()).add(key)
    operations = spec_operations(spec)
    source_cache = {}
    route_cache = {}

    require(type(bindings.get('schemaVersion')) in (int, float)
            and bindings.get('schemaVersion') == 1, 'Unsupported bindings schema')
    require(bindings.get('specVersion') == spec['info']['version'], 'Bindings were made against a different spec version')
    scopes = bindings.get('boundScopes')
    require(
        isinstance(scopes, list)
        and scopes
        and scopes == sorted(scopes)
        and len(set(scopes)) == len(scopes),
        'boundScopes must be a sorted, non-empty unique list',
    )
    known_scopes = {operation.get('x-api-scope') for _, _, operation in operations.values()}
    require(set(scopes) <= known_scopes, 'boundScopes contains a scope absent from the spec')
    require(set(scopes) <= FEATURE_BY_SCOPE.keys(), 'boundScopes contains an unmapped feature scope')

    entries = bindings.get('bindings')
    require(isinstance(entries, list), 'bindings must be a list')
    seen = set()
    entry_scopes = set()
    contract_sources = set()
    for entry in entries:
        operation = entry['operation']
        require(operation not in seen, f'{operation}: duplicate binding')
        seen.add(operation)
        require(operation in operations, f'{operation}: not a documented developer operation')
        _, _, spec_operation = operations[operation]
        scope = spec_operation['x-api-scope']
        entry_scopes.add(scope)
        require(entry['scope'] == scope, f'{operation}: scope differs from spec')
        require(scope in scopes, f'{operation}: scope {scope} is not declared in boundScopes')
        require(entry['operationId'] == spec_operation['operationId'], f'{operation}: operationId differs from spec')

        spec_reference = entry['evidence']['spec']
        require(spec_reference.startswith('contracts/developer.openapi.json#'), f'{operation}: spec evidence must point into the checked-in spec')
        pointer = '#' + spec_reference.split('#', 1)[1]
        require(resolve_pointer(spec, pointer) is spec_operation, f'{operation}: spec pointer resolves to a different operation')

        origin = entry['origin']
        require(origin['declaredBy'] == 'contracts/developer.openapi.json#/servers/0', f'{operation}: declared origin evidence must use the first OpenAPI server')
        require(origin['declared'] == spec['servers'][0]['url'], f'{operation}: declared origin differs from spec')
        require(origin['websiteCallOrigin'] == 'unresolved', f'{operation}: website call origin is not bound by this evidence')

        auth = entry['auth']
        auth_pointer = 'contracts/developer.openapi.json#/components/securitySchemes/' + auth['declared']
        require(auth['declaredBy'] == auth_pointer, f'{operation}: auth evidence pointer differs from declared scheme')
        schemes = spec['components']['securitySchemes']
        require(auth['declared'] in schemes, f'{operation}: auth scheme absent from spec')
        declared_scheme = schemes[auth['declared']]
        require(
            declared_scheme.get('type') == 'http' and declared_scheme.get('scheme') == 'bearer',
            f'{operation}: declared auth is not the OpenAPI bearer scheme',
        )
        security = spec_operation.get('security', spec.get('security', []))
        require(any(auth['declared'] in requirement for requirement in security), f'{operation}: operation does not require the declared auth')

        require(entry['feature'] == FEATURE_BY_SCOPE[scope], f'{operation}: feature category differs from reviewed scope mapping')
        require(entry['productScope'] == 'included', f'{operation}: product scope differs from reviewed developer binding scope')
        contract = entry['evidence']['contract']
        captured = verify_contract(
            root, manifest_hashes, source_cache, route_cache, operation, scope, contract
        )
        contract_sources.add(contract['source'])
        require(
            auth['keyedErrorCodesMatchCapturedContract'] is True
            and sorted(spec_operation['x-error-codes']) == captured['errorCodes'],
            f'{operation}: error-code list differs from captured route contract',
        )
        verify_call_sites(
            root,
            manifest_hashes,
            source_cache,
            occurrences,
            operation,
            contract,
            entry['evidence']['clientCallSites'],
        )
        require_unqualified(entry, 'contract-bound')

    require(entry_scopes == set(scopes), 'boundScopes inventory differs from binding scopes')
    for scope in scopes:
        expected = {
            key for key, (_, _, operation) in operations.items()
            if operation['x-api-scope'] == scope
        }
        require(expected <= seen, f'Scope {scope} is missing bindings: {sorted(expected - seen)}')

    observed_entries = bindings.get('observedNotDeclared', [])
    require(isinstance(observed_entries, list), 'observedNotDeclared must be a list')
    observed_seen = set()
    for entry in observed_entries:
        operation = entry['operation']
        require(operation not in operations and entry.get('declaredInSpec') is False, f'{operation}: observed-not-declared operation is in the spec')
        require(operation not in observed_seen, f'{operation}: duplicate observed operation')
        observed_seen.add(operation)
        require(entry['scope'] in scopes, f'{operation}: observed scope is not bound')
        require(entry.get('countedInDeveloperDenominator') is False, f'{operation}: undeclared operations stay outside the documented denominator')
        contract = entry['evidence']['contract']
        verify_contract(
            root,
            manifest_hashes,
            source_cache,
            route_cache,
            operation,
            entry['scope'],
            contract,
        )
        contract_sources.add(contract['source'])
        verify_call_sites(
            root,
            manifest_hashes,
            source_cache,
            occurrences,
            operation,
            contract,
            entry['evidence']['clientCallSites'],
        )
        require_unqualified(entry, 'observed-not-declared')

    for source in contract_sources:
        for operation, captured in route_cache[source].items():
            if captured['scope'] not in scopes:
                continue
            if operation in operations:
                require(operation in seen, f'{operation}: captured documented publicRead route is unbound')
            else:
                require(operation in observed_seen, f'{operation}: captured publicRead route is neither bound nor recorded as undeclared')

    api = coverage['developerApi']
    # bool subclasses int in Python, but JSON false/true are not numeric claims.
    for field in ('contractBound', 'documentedOperations', 'implementedNatively', 'qualified'):
        require(type(api.get(field)) in (int, float), f'coverage.json {field} must be numeric')
    require(api.get('bindings') == 'developer-bindings.json', 'coverage.json developerApi.bindings must point to developer-bindings.json')
    require(api.get('contractBound') == len(seen), 'coverage.json contractBound differs from the bindings ledger')
    require(api.get('documentedOperations') == len(operations), 'coverage.json documentedOperations differs from the spec')
    require(api.get('implementedNatively') == 0, 'coverage.json must not claim native developer API implementations')
    require(api.get('qualified') == 0, 'coverage.json must not claim qualified developer API operations')
    require(coverage['internalApi'].get('candidateDenominatorReviewed') is False, 'Internal candidate denominator review is outside this binding ledger')
    if api.get('contractBound') == api.get('documentedOperations'):
        require(seen == set(operations), 'Full binding claim does not cover every documented operation')
        require(set(scopes) == known_scopes, 'Full binding claim does not cover every declared scope')

    return len(seen), len(operations), len(observed_seen)


def main():
    bound, documented, observed = verify()
    print(
        f'Developer API contract bindings verified: {bound}/{documented} documented '
        f'operations contract-bound, {observed} captured publicRead route(s) recorded '
        'as not declared; 0 implemented, 0 qualified'
    )


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f'Binding verification failed: {error}', file=sys.stderr)
        sys.exit(1)
