#!/usr/bin/env python3
"""Compare saved score reports without rebuilding or changing matching rules.

Exit 0: all baseline memberships preserved; 1: regression; 2: invalid reports.
"""
import argparse
import json
from pathlib import Path


def unique_fields(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f'duplicate score report field: {key}')
        result[key] = value
    return result


def load_report(path):
    document = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_fields)
    windows = document.get('windows') if isinstance(document, dict) else None
    if not isinstance(windows, (dict, list)) or not windows:
        raise ValueError('report must contain a nonempty windows object or inventory list')
    rows = windows.items() if isinstance(windows, dict) else ((row.get('start'), row) for row in windows)
    result = {}
    for key, row in rows:
        if isinstance(key, bool) or not isinstance(key, (int, str)):
            raise ValueError('window start must be an integer or decimal/hex string')
        start = int(key, 16 if isinstance(key, str) and key.startswith('0x') else 10) if isinstance(key, str) else key
        if start < 0 or start % 8 or start in result:
            raise ValueError(f'invalid or duplicate window start: {key}')
        if not isinstance(row, dict):
            raise ValueError(f'window {key} must be an object')
        size = row.get('bytes')
        if type(size) is not int or size <= 0 or size % 8:
            raise ValueError(f'window {key} has invalid byte length')
        if isinstance(windows, list):
            matches = row.get('normalized_matches')
            if not isinstance(matches, list):
                raise ValueError(f'window {key} has invalid normalized_matches')
            normalized, raw = bool(matches), row.get('raw_match')
        else:
            normalized, raw = row.get('normalized'), row.get('raw')
        if type(normalized) is not bool or type(raw) is not bool or (raw and not normalized):
            raise ValueError(f'window {key} has inconsistent match flags')
        result[start] = {'bytes': size, 'normalized': normalized, 'raw': raw}
    return result


def compare(before, after):
    missing = sorted(before.keys() - after.keys())
    added = sorted(after.keys() - before.keys())
    resized = sorted(k for k in before.keys() & after.keys() if before[k]['bytes'] != after[k]['bytes'])
    shared = before.keys() & after.keys() - set(resized)
    report = {'missing': missing, 'added': added, 'resized': resized}
    for flag in ('normalized', 'raw'):
        report[flag + '_gains'] = sorted(k for k in shared if after[k][flag] and not before[k][flag])
        report[flag + '_losses'] = sorted(k for k in shared if before[k][flag] and not after[k][flag])
        report[flag + '_gained_bytes'] = sum(after[k]['bytes'] for k in report[flag + '_gains'])
        report[flag + '_lost_bytes'] = sum(before[k]['bytes'] for k in report[flag + '_losses'])
    # A changed inventory cannot establish preservation, even for previously unmatched windows.
    report['accepted'] = not any(report[k] for k in ('missing', 'added', 'resized', 'normalized_losses', 'raw_losses'))
    return {key: [hex(v) for v in value] if isinstance(value, list) else value for key, value in report.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--json', type=Path, help='also save the comparison report')
    args = parser.parse_args(argv)
    try:
        report = compare(load_report(args.baseline), load_report(args.candidate))
    except (OSError, ValueError, TypeError, AttributeError) as error:
        parser.exit(2, f'invalid score report: {error}\n')
    output = json.dumps(report, indent=2) + '\n'
    if args.json:
        try:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation also protects aliased inputs and concurrent receipts.
            with args.json.open('x', encoding='utf-8') as stream:
                stream.write(output)
        except OSError as error:
            parser.exit(2, f'cannot create comparison report: {error}\n')
    print(output, end='')
    return 0 if report['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
