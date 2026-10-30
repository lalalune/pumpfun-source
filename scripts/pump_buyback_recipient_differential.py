#!/usr/bin/env python3
"""Exercise buyback recipient lists using the unchanged configuration fixture."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import ast
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from pump_diagnostic_audit import bound_input_key

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'scripts/pump_validate_config_admin.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture():
    """Retain fixture setup/execution; add only remaining recipient accounts."""
    tree = ast.parse(HARNESS.read_text())
    body = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == 'p'
            for target in node.targets
        ):
            break
        if isinstance(node, ast.FunctionDef) and node.name == 'execute':
            node.args.args.append(ast.arg(arg='recipients'))
            node.args.defaults.append(ast.Tuple(elts=[], ctx=ast.Load()))
            insertion = next(i for i, statement in enumerate(node.body)
                             if isinstance(statement, ast.Assign)
                             and any(isinstance(target, ast.Name) and target.id == 'ix'
                                     for target in statement.targets))
            additions = ast.parse('''
for key in recipients:
    if vm.get_account(key) is None:
        vm.set_account(key, Account(1000000, b'', Pubkey.default()))
    metas.append(AccountMeta(key, False, False))
''').body
            node.body[insertion:insertion] = additions
        body.append(node)
    namespace = {'__file__': str(HARNESS), '__name__': 'buyback_fixture'}
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    exec(compile(module, str(HARNESS), 'exec'), namespace)
    return namespace


def compared_lines(logs):
    result = []
    for index, line in enumerate(logs):
        if line.startswith(('Program log: Left:', 'Program log: Right:')):
            result.append(line)
            if line in ('Program log: Left:', 'Program log: Right:'):
                result.extend(logs[index + 1:index + 2])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.candidate = args.candidate.resolve()
    assert not args.output.exists(), 'Use a fresh output path'
    original = ROOT / 'evidence/original/pump/deployed.so'
    inputs = [Path(__file__).resolve(), HARNESS, original,
              ROOT / 'scripts/pump_diagnostic_audit.py',
              args.candidate.resolve(), ROOT / 'evidence/upstream/pump.json',
              ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json']
    bound = {bound_input_key(path, ROOT): sha(path) for path in inputs}
    helpers = fixture()
    pubkey = helpers['Pubkey']
    keys = [pubkey(bytes([value]) * 32) for value in range(31, 39)]
    vectors = [('unique', keys), ('all_zero', [pubkey.default()] * 8)]
    for index in range(8):
        row = list(keys)
        row[index] = pubkey.default()
        vectors.append(('zero_' + str(index), row))
    for left in range(8):
        for right in range(left + 1, 8):
            row = list(keys)
            row[right] = row[left]
            vectors.append((f'duplicate_{left}_{right}', row))
    for count in (0, 1, 7, 9):
        vectors.append(('count_' + str(count),
                        (keys + [pubkey(bytes([99]) * 32)])[:count]))
    fields = ['error', 'data_hex', 'lamports', 'payer_lamports',
              'authority_lamports', 'event_payloads', 'inner_instructions',
              'comparison_lines']
    cases = []
    for name, recipients in vectors:
        results = [helpers['execute'](binary, 'update_buyback_config', b'\0',
                                      'none', recipients)
                   for binary in (original, args.candidate.resolve())]
        for result in results:
            result['comparison_lines'] = compared_lines(result['logs'])
        before, after = results
        cases.append({'case': name, 'instruction': 'update_buyback_config',
                      'recipients': [str(key) for key in recipients],
                      'different_fields': [key for key in fields
                                           if before[key] != after[key]],
                      'original': before, 'candidate': after})
    assert len(cases) == 42
    mismatches = [index for index, row in enumerate(cases)
                  if row['different_fields']]
    assert bound == {bound_input_key(path, ROOT): sha(path) for path in inputs}
    report = {'scope': __doc__ + ' Offline synthetic authority and accounts; no live transactions.',
              'original_sha256': sha(original),
              'candidate_sha256': sha(args.candidate),
              'harness_sha256': sha(Path(__file__)),
              'configuration_fixture_sha256': sha(HARNESS),
              'bound_inputs_sha256': bound,
              'runtime': {'python': sys.version,
                          'solders': importlib.metadata.version('solders'),
                          'pyelftools': importlib.metadata.version('pyelftools')},
              'case_count': len(cases), 'mismatches': mismatches, 'cases': cases}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'cases': len(cases), 'mismatches': mismatches}))
    return bool(mismatches)


if __name__ == '__main__':
    raise SystemExit(main())
