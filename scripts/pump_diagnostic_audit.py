#!/usr/bin/env python3
"""Compare captured Pump error payloads, preserving account names and operands.

This audits paired logs already present in a differential receipt. It excludes
source file/line coordinates, compute usage, and cases without paired logs.
It therefore strengthens the bounded oracle, not its input-space coverage.
Once published, a complete receipt is retained if a subsequent source check
fails; its digest still identifies the audited bytes, and another writer may
already have replaced the output.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import secrets
import re


def bound_input_key(path, root):
    """Keep repository labels stable while admitting explicit external inputs.

    POSIX spelling on every host: ``str(Path)`` yields backslashes on Windows,
    so the published ``bound_*`` receipt keys would differ between hosts for
    identical inputs.
    """
    path, root = Path(path).resolve(), Path(root).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _log_data(value):
    """Keep an absent log source distinct from an explicitly empty list."""
    result = []
    available = False
    if isinstance(value, dict):
        for key, item in value.items():
            if 'log' in key.lower() and isinstance(item, list):
                available = True
                result.extend(x for x in item if isinstance(x, str))
        # Some receipts retain LiteSVM's serialized transaction metadata.
        # A direct list, even an empty one, remains authoritative.
        if not available and isinstance(value.get('metadata'), dict):
            nested = value['metadata'].get('logs')
            if isinstance(nested, list):
                available = True
                result.extend(x for x in nested if isinstance(x, str))
    return result if available else None


def logs(value):
    return _log_data(value) or []


def panic_message(line):
    """Remove only recognized Rust PanicInfo location syntax, never an arbitrary line."""
    prefix = 'Program log: panicked at '
    if not line.startswith(prefix):
        return line
    text = line.removeprefix(prefix)
    source, separator, message = text.partition('\n')
    # Rust's location-first form: file:line:column:\nmessage.
    if re.fullmatch(r"(?!['\"])[^\r\n]+:[0-9]+:[0-9]+:", source):
        return message if separator else ''
    # Earlier Rust displays quote the message before the source location.
    legacy = re.fullmatch(r"'(.*)', [^\r\n]+:[0-9]+:[0-9]+", text, re.S)
    if legacy:
        return legacy.group(1)
    return line


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
            panic.append(panic_message(line))
        if 'AnchorError' in line:
            name = re.search(r'caused by account: ([^.]*)\.', line)
            origins.append(['account', name.group(1)] if name else
                           ['source'] if ' thrown in ' in line else ['none'])
            match = re.search(r'Error Code: (.*?)\. Error Number: (\d+)\. Error Message: (.*)', line)
            anchor.append(list(match.groups()) if match else line)
    return {'panic': panic, 'anchor': anchor, 'compared': compared, 'origins': origins}


def audit(suites):
    """Audit available pairs, rejecting a log source present on only one side."""
    if not isinstance(suites, dict):
        raise ValueError('report suites must be a mapping')
    mismatches, coverage = [], Counter()

    def walk(value, path):
        if isinstance(value, dict):
            left, right = _log_data(value.get('original')), _log_data(value.get('candidate'))
            # Original-only calibration and candidate=None are supported. A
            # supplied non-null opposite outcome, however, must be an object.
            for side, opposite_logs in (('original', right), ('candidate', left)):
                if (opposite_logs is not None and side in value
                        and value[side] is not None and not isinstance(value[side], dict)):
                    raise ValueError(f'{path}: execution pair has malformed {side} outcome')
            if isinstance(value.get('original'), dict) and isinstance(value.get('candidate'), dict):
                if (left is None) != (right is None):
                    missing = 'original' if left is None else 'candidate'
                    raise ValueError(f'{path}: execution pair is missing {missing} logs')
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


def publish_file(staged, output):
    """Publish without replacement; return whether staging was consumed."""
    if os.name == 'nt':
        # Windows rename refuses an existing destination without hard links.
        os.rename(staged, output)
        return True
    os.link(staged, output)
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    report = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
    result = audit(report['suites'])
    if not result['log_bearing_cases']:
        raise ValueError('report has no paired logs to audit')
    result['source_report_sha256'] = hashlib.sha256(raw).hexdigest()
    result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    # Stage beside the destination; a fresh destination root is the caller's to
    # name, so its parent must exist before the staged file can be created.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Audits are new evidence: never replace an input or a prior receipt.
    staged = None
    published = False
    try:
        # A plain exclusive open keeps the umask mode of the published audit.
        # The hidden staged name is unique and links into an absent output
        # only, preserving the no-replace and no-aliasing guarantees.
        temporary = args.output.with_name('.' + args.output.name[:32] + '.' + secrets.token_hex(8) + '.tmp')
        with open(temporary, 'x', encoding='utf-8', newline='\n') as stream:
            staged = temporary
            stream.write(json.dumps(result, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        if args.report.read_bytes() != raw:
            raise ValueError('source report changed during audit')
        if publish_file(staged, args.output):
            # The former pathname no longer belongs to us after rename.
            staged = None
        published = True
        if args.report.read_bytes() != raw:
            raise ValueError('source report changed during audit')
    except BaseException as error:
        if published:
            error.add_note('Audit output was already published; leaving output path untouched: ' + str(args.output))
        raise
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
    print(json.dumps({'log_bearing_cases': result['log_bearing_cases'], 'mismatches': len(result['mismatches'])}))
    return bool(result['mismatches'])


if __name__ == '__main__':
    raise SystemExit(main())
