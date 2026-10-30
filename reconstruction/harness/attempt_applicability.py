#!/usr/bin/env python3
"""Read-only applicability checks for explicitly attributed experiment evidence.

Compatibility means recorded identities agree and evidence hashes verify, not that
an experiment was independently reproduced or its conclusion is correct.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

FIELDS = ('source_sha256', 'toolchain_sha256', 'original_sha256', 'inventory_sha256', 'command_sha256')


def unique(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError(f'duplicate JSON field: {key}')
        result[key] = value
    return result


def parse(text): return json.loads(text, object_pairs_hook=unique)


def valid_context(context):
    return isinstance(context, dict) and all(isinstance(context.get(k), str) and re.fullmatch('[0-9a-f]{64}', context[k]) for k in FIELDS)


def address(value):
    if isinstance(value, bool): raise ValueError('boolean target')
    if isinstance(value, int): result = value
    elif isinstance(value, str):
        if not value or value != value.strip(): raise ValueError('blank or padded target')
        try: result = int(value, 0)
        except ValueError: return value  # ledger also supports named scopes such as all
    else: raise ValueError('invalid target')
    if result < 0: raise ValueError('negative target')
    return result


def classify(row, context, evidence_root):
    data = row.get('data')
    if not isinstance(data, dict) or not valid_context(data.get('context')):
        return {'applicability': 'unverifiable', 'reasons': ['missing or invalid recorded context']}
    changed = [key for key in FIELDS if data['context'][key] != context[key]]
    if changed: return {'applicability': 'stale', 'reasons': changed}
    evidence = data.get('evidence')
    if not isinstance(evidence, list) or not evidence:
        return {'applicability': 'unverifiable', 'reasons': ['no hash-bound evidence files']}
    reasons = []
    root = Path(evidence_root).resolve()
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not isinstance(item.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            reasons.append('invalid evidence descriptor'); continue
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            reasons.append('evidence path must remain within evidence root'); continue
        path = root / relative
        if any(p.is_symlink() for p in [path, *path.parents] if p != root and root in p.parents):
            reasons.append('symlinked evidence is not admitted'); continue
        try:
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                reasons.append('missing or changed evidence: ' + relative.as_posix())
        except OSError:
            reasons.append('unreadable evidence: ' + relative.as_posix())
    return {'applicability': 'unverifiable' if reasons else 'compatible', 'reasons': reasons}


def inspect(ledger, context, target, approach, evidence_root):
    if not valid_context(context): raise ValueError('requested context requires five lowercase SHA-256 fields')
    target = address(target)
    rows, errors = [], []
    for number, line in enumerate(Path(ledger).read_text().splitlines(), 1):
        if not line.strip(): continue
        try:
            row = parse(line)
            if not isinstance(row, dict): raise ValueError('record must be an object')
            recorded_target = address(row.get('target'))
        except (ValueError, TypeError) as exc:
            errors.append({'line': number, 'error': str(exc)}); continue
        if recorded_target != target or row.get('approach') != approach: continue
        rows.append({'line': number, 'attempt_id': row.get('attempt_id'), 'status': row.get('status'),
                     'hypothesis': row.get('hypothesis'), **classify(row, context, evidence_root)})
    return {'schema': 'attempt-applicability-v1', 'target': target, 'approach': approach,
            'rows': rows, 'counts': dict(Counter(r['applicability'] for r in rows)), 'parse_errors': errors,
            'scope': __doc__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--context', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--approach', required=True, help='exact recorded approach, never fuzzy mechanism matching')
    args = parser.parse_args()
    result = inspect(args.ledger, parse(args.context.read_text()), args.target, args.approach, args.evidence_root)
    print(json.dumps(result, indent=2))
    return 2 if result['parse_errors'] else 0


if __name__ == '__main__': raise SystemExit(main())
