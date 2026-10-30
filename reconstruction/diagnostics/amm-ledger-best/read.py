#!/usr/bin/env python3
"""Read saved AMM attempts using the retained canonical no-normalized-loss rank."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RANK_SOURCE = 'scripts/amm_sell/sell_score.py'
REVIEWED_RANK = '8ea31923d34a776e1034da79ebf7eee6145eb8469a079e098177b976f619ddf7'


def _first_line(node):
    """First physical line of a statement, including any decorators above it."""
    decorators = [item.lineno for item in getattr(node, 'decorator_list', [])]
    return min([node.lineno, *decorators])


def canonical_rank():
    raw = (ROOT / RANK_SOURCE).read_bytes()
    source = raw.decode('utf-8').replace('\r\n', '\n')
    parsed = ast.parse(source)
    functions = [node for node in parsed.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'rank']
    if len(functions) != 1 or not isinstance(functions[0], ast.FunctionDef):
        raise ValueError('expected one reviewed rank function')
    function = functions[0]
    # rank reads module-level constants (SELL_SIZE), so they are part of the
    # reviewed slice: a changed constant must not silently re-rank the ledger.
    loaded = {node.id for node in ast.walk(function)
              if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    constants = [node for node in parsed.body
                 if isinstance(node, ast.Assign) and len(node.targets) == 1
                 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in loaded]
    # Bind the entire signature/body (and any decorators) plus those constants,
    # excluding unrelated module statements. Physical LF lines avoid
    # Python-version AST differences.
    lines = source.split('\n')
    reviewed = b'\0'.join('\n'.join(lines[_first_line(node) - 1:node.end_lineno]).encode('utf-8')
                          for node in [function, *sorted(constants, key=lambda node: node.lineno)])
    if hashlib.sha256(reviewed).hexdigest() != REVIEWED_RANK:
        raise ValueError('reviewed AMM rank function changed')
    namespace = {}
    exec(compile(ast.Module(body=[*constants, function], type_ignores=[]),
                 str(ROOT / RANK_SOURCE), 'exec'), namespace)
    return namespace['rank'], hashlib.sha256(raw).hexdigest()


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field in ledger')
        result[key] = value
    return result


def read_best(path, limit):
    if type(limit) is not int or limit < 1:
        raise ValueError('limit must be a positive integer')
    rank, source_sha = canonical_rank()
    raw = Path(path).read_bytes()
    counters, eligible = Counter(), []
    for number, line in enumerate(raw.decode('utf-8').split('\n'), 1):
        if not line.strip():
            continue
        record = json.loads(line, object_pairs_hook=unique_fields)
        if not isinstance(record, dict):
            raise ValueError(f'ledger line {number} must be an object')
        counters['record_lines'] += 1
        if record.get('schema') != 'amm-sell-attempt-v1':
            counters['notes_or_other_records'] += 1
            continue
        counters['build_record_lines'] += 1
        if record.get('status') not in ['scored', 'GOAL_SELL_RAW_EQUAL']:
            counters['failed_or_unscored'] += 1
            continue
        metrics = record.get('metrics')
        numeric = ['lost_windows_count', 'lost_windows_normalized_count', 'sell_size', 'align_distance', 'slot_diffs']
        if (not isinstance(metrics, dict) or not isinstance(record.get('attempt_id'), str)
                or not record['attempt_id'] or type(metrics.get('sell_raw_equal')) is not bool
                or any(type(metrics.get(key)) is not int or metrics[key] < 0 for key in numeric)
                or metrics['sell_size'] == 0):
            counters['incomplete_metrics'] += 1
            continue
        value = rank(record)
        if value is None:
            counters['normalized_regression'] += 1
            continue
        eligible.append({'line': number, 'rank': list(value), 'raw_loss_count': metrics['lost_windows_count'],
                         'normalized_loss_count': metrics['lost_windows_normalized_count'], 'record': record})
    eligible.sort(key=lambda entry: entry['rank'])  # Preserve ledger order on equal ranks.
    counters['eligible_record_lines'] = len(eligible)
    return {'scope': 'Saved-record query only; no compiler, VM, fresh scoring or acceptance claim.',
            'ledger_sha256': hashlib.sha256(raw).hexdigest(),
            'canonical_rank_source': RANK_SOURCE, 'rank_source_sha256': source_sha,
            'counts': dict(counters), 'best': eligible[:limit]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    try:
        print(json.dumps(read_best(args.ledger, args.limit), indent=2))
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, str(error) + '\n')
