#!/usr/bin/env python3
"""Compare captured Pump error payloads, preserving account names and operands.

This audits paired logs already present in a differential receipt. It excludes
source file/line coordinates, compute usage, and cases without paired logs.
It therefore strengthens the bounded oracle, not its input-space coverage.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re


def logs(value):
    result = []
    if isinstance(value, dict):
        direct_logs = False
        for key, item in value.items():
            if 'log' in key.lower() and isinstance(item, list):
                direct_logs = True
                result.extend(x for x in item if isinstance(x, str))
        # Some receipts retain LiteSVM's serialized transaction metadata.
        # A direct list, even an empty one, remains authoritative.
        if not direct_logs and isinstance(value.get('metadata'), dict):
            nested = value['metadata'].get('logs')
            if isinstance(nested, list):
                result.extend(x for x in nested if isinstance(x, str))
    return result


def messages(lines):
    panic, anchor, compared, origins = [], [], [], []
    pending = None
    for line in lines:
        if line.startswith(('Program log: Left:', 'Program log: Right:')):
            side = line.split('Program log: ', 1)[1].split(':', 1)[0]
            value = line.split(':', 2)[2].strip()
            if value:
                compared.append([side, value])
                pending = None
            else:
                pending = side
        elif pending is not None and line.startswith('Program log: '):
            compared.append([pending, line.removeprefix('Program log: ')])
            pending = None
        else:
            pending = None
        if 'panicked at ' in line:
            panic.append(line.split('\n', 1)[1] if '\n' in line else line)
        if 'AnchorError' in line:
            name = re.search(r'caused by account: ([^.]*)\.', line)
            origins.append(['account', name.group(1)] if name else
                           ['source'] if ' thrown in ' in line else ['none'])
            match = re.search(r'Error Code: (.*?)\. Error Number: (\d+)\. Error Message: (.*)', line)
            anchor.append(list(match.groups()) if match else line)
    return {'panic': panic, 'anchor': anchor, 'compared': compared, 'origins': origins}


def audit(suites):
    mismatches, coverage = [], Counter()

    def walk(value, path):
        if isinstance(value, dict):
            if isinstance(value.get('original'), dict) and isinstance(value.get('candidate'), dict):
                left, right = logs(value['original']), logs(value['candidate'])
                if left or right:
                    coverage[path.split('/')[0]] += 1
                    a, b = messages(left), messages(right)
                    if a != b:
                        mismatches.append({'path': path, 'case': value.get('case', value.get('name')),
                                           'original': a, 'candidate': b,
                                           'original_logs': left, 'candidate_logs': right})
            for key, item in value.items():
                if key not in ('original', 'candidate'):
                    walk(item, path + '/' + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, path + '/' + str(index))

    for name, suite in suites.items():
        walk(suite, name)
    return {'scope': __doc__, 'coverage': dict(coverage),
            'log_bearing_cases': sum(coverage.values()), 'mismatches': mismatches}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    report = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
    result = audit(report['suites'])
    result['source_report_sha256'] = hashlib.sha256(raw).hexdigest()
    result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'log_bearing_cases': result['log_bearing_cases'], 'mismatches': len(result['mismatches'])}))
    return bool(result['mismatches'])


if __name__ == '__main__':
    raise SystemExit(main())
