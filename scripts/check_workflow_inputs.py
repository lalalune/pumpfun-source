#!/usr/bin/env python3
"""Compare literal workflow script inputs against a Git baseline (never execute them)."""
import argparse
import itertools
import json
import posixpath
import re
import shlex
import subprocess
from pathlib import Path

import yaml

ROOTS = {'scripts', 'research', 'reconstruction'}
INTERPRETER = re.compile(r'^(?:python(?:3(?:\.\d+)?)?|bash|sh)$')
EXPRESSION = re.compile(r'\$\{\{\s*matrix\.(\w+)\s*\}\}')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def matrix_rows(job):
    matrix = job.get('strategy', {}).get('matrix', {})
    if not isinstance(matrix, dict):
        return [{}]
    axes = {k: v for k, v in matrix.items() if k not in ('include', 'exclude')}
    if not axes:
        return matrix.get('include', []) or [{}]
    if any(not isinstance(v, list) for v in axes.values()):
        return [{}]
    rows = [dict(zip(axes, values)) for values in itertools.product(*axes.values())] if axes else []
    rows = [r for r in rows if not any(all(r.get(k) == v for k, v in e.items()) for e in matrix.get('exclude', []))]
    # Added combinations never participate in later include matching. Original
    # rows may still receive successive updates to non-axis fields.
    additions = []
    for entry in matrix.get('include', []):
        matched = False
        for row in rows:
            if all(k not in axes or row[k] == v for k, v in entry.items()):
                row.update(entry)
                matched = True
        if not matched:
            additions.append(dict(entry))
    return rows + additions


def substitute(value, row):
    return EXPRESSION.sub(lambda m: str(row.get(m[1], m[0])), value)


def references(name, source):
    doc = yaml.safe_load(source)
    if not isinstance(doc, dict) or not isinstance(doc.get('jobs'), dict):
        raise ValueError(f'{name}: expected a workflow jobs mapping')
    found, unsupported = set(), set()
    default = doc.get('defaults', {}).get('run', {}).get('working-directory', '.')
    for job_id, job in doc['jobs'].items():
        directory = job.get('defaults', {}).get('run', {}).get('working-directory', default)
        for row in matrix_rows(job):
            for step in job.get('steps', []):
                if 'run' not in step:
                    continue
                command = substitute(str(step['run']), row)
                cwd = substitute(str(step.get('working-directory', directory)), row)
                if re.search(r'<<-?\s*[^\s<]', command):
                    unsupported.add((name, str(job_id), 'heredoc body requires shell parsing'))
                    continue
                for line in command.splitlines():
                    # Only literal, standalone interpreter commands. Shell programs
                    # and generated script bodies are not evaluated by this checker.
                    if not re.match(r'^\s*(python(?:3(?:\.\d+)?)?|bash|sh)\s', line):
                        continue
                    if '${{' in line or '$' in cwd or cwd.startswith('/'):
                        unsupported.add((name, job_id, 'dynamic command/directory'))
                        continue
                    try:
                        tokens = shlex.split(line, comments=True)
                    except ValueError:
                        unsupported.add((name, job_id, 'unparsed shell command'))
                        continue
                    if not tokens or not INTERPRETER.fullmatch(tokens[0]):
                        continue
                    index = 1
                    while index < len(tokens) and tokens[index].startswith('-'):
                        option = tokens[index]
                        python = tokens[0].startswith('python')
                        if option == '--':
                            index += 1
                            break
                        if (python and (option in ('-c', '-m', '-') or option.startswith(('-c', '-m')))
                                or not python and not option.startswith('--') and 'c' in option[1:]):
                            index = len(tokens)
                            break
                        takes_value = (option in ('-X', '-W', '--check-hash-based-pycs') if python else
                                       option in ('--rcfile', '--init-file') or
                                       not option.startswith('--') and option[-1:] in ('o', 'O'))
                        index += 2 if takes_value else 1
                    if index >= len(tokens):
                        continue
                    script = tokens[index]
                    if script.startswith(('/', '<')) or any(c in script for c in '$`*?'):
                        unsupported.add((name, job_id, 'nonliteral script'))
                        continue
                    path = posixpath.normpath(posixpath.join(cwd, script))
                    if path.split('/')[0] in ROOTS and path.endswith(('.py', '.sh')):
                        found.add((name, str(job_id), path))
                    else:
                        unsupported.add((name, str(job_id), f'outside checked roots: {path}'))
    return found, unsupported


def inventory(root, revision=None):
    if revision:
        files = set(git(root, 'ls-tree', '-rz', '--name-only', revision).decode().split('\0'))
        read = lambda path: git(root, 'show', f'{revision}:{path}').decode('utf-8')
    else:
        # Include untracked new workflows for local pre-push checks.
        files = set(git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').decode().split('\0'))
        files = {p for p in files if (root / p).is_file()}
        read = lambda path: (root / path).read_text(encoding='utf-8')
    refs, unsupported = set(), set()
    for name in sorted(files):
        if name.startswith('.github/workflows/') and name.endswith(('.yml', '.yaml')):
            found, skipped = references(name, read(name))
            refs.update(found)
            unsupported.update(skipped)
    return refs, {ref for ref in refs if ref[2] not in files}, unsupported


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path('.'))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--base', help='Git revision whose existing missing references are reported as debt')
    mode.add_argument('--all', action='store_true', help='fail on every missing literal input')
    parser.add_argument('--head', help='inspect a committed revision instead of the working tree')
    args = parser.parse_args(argv)
    try:
        refs, missing, unsupported = inventory(args.repo, args.head)
        old = inventory(args.repo, args.base)[1] if args.base else set()
    except (subprocess.CalledProcessError, ValueError, OSError, yaml.YAMLError) as error:
        parser.exit(2, f'workflow input inspection failed: {error}\n')
    new = missing - old
    print(json.dumps({'checked_references': len(refs), 'new_missing': sorted(new),
                      'existing_missing': sorted(missing & old),
                      'uninspected': sorted(unsupported)}, indent=2))
    return 1 if new else 0


if __name__ == '__main__':
    raise SystemExit(main())
