#!/usr/bin/env python3
"""Execute the serial validator's actual final total guard, without a build."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    source = root / 'scripts/pump_validate_all.py'
    text = source.read_text(encoding='utf-8')
    tree = ast.parse(text)
    main_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    guards = [node for node in ast.walk(main_node) if isinstance(node, ast.Assert)
              and ast.get_source_segment(text, node).startswith("assert sum(s['case_count'] for s in suites.values())")]
    if len(guards) != 1:
        raise ValueError('expected exactly one actual final case-total guard')
    guard = guards[0]
    sys.path.insert(0, str(root / 'scripts'))
    import pump_validate_all as validator
    if {name for name, _ in validator.SUITES} != set(validator.EXPECTED_CASES):
        raise ValueError('suite schedule and expected counts differ')
    admitted = {name: {'case_count': count} for name, count in validator.EXPECTED_CASES.items()}
    code = compile(ast.Module(body=[guard], type_ignores=[]), str(source), 'exec')
    outcomes = []
    for change in ('current-catalogue', 'missing-suite', 'wrong-count'):
        suites = copy.deepcopy(admitted)
        if change == 'missing-suite':
            del suites['administration']
        elif change == 'wrong-count':
            suites['administration']['case_count'] += 1
        try:
            exec(code, {'suites': suites, 'EXPECTED_CASES': validator.EXPECTED_CASES})
            accepted = True
        except AssertionError:
            accepted = False
        outcomes.append({'change': change, 'accepted': accepted,
                         'case_total': sum(row['case_count'] for row in suites.values())})
    result = {'scope': 'Actual final production assertion executed in isolation; catalogue counts only, not a full serial CLI or a compiled candidate.',
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'guard': ast.get_source_segment(text, guard), 'guard_line': guard.lineno,
              'suite_count': len(admitted), 'catalogue_total': sum(validator.EXPECTED_CASES.values()),
              'case_counts': validator.EXPECTED_CASES, 'outcomes': outcomes}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
