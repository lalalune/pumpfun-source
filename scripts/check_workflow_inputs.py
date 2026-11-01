#!/usr/bin/env python3
"""Compare literal workflow script inputs against a Git baseline (never execute them)."""
import argparse
import itertools
import json
import os
import posixpath
import re
import shlex
import subprocess
from pathlib import Path

import yaml

ROOTS = {'scripts', 'research', 'reconstruction', 'tests'}
INTERPRETER = re.compile(r'^(?:python(?:3(?:\.\d+)?)?|bash|sh)$')
EXPRESSION = re.compile(r'\$\{\{\s*matrix\.(\w+)\s*\}\}')
ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
COMMAND_PREFIX = re.compile(r'^\s*(?:[A-Za-z_][A-Za-z0-9_]*=|env(?:\s|$)|python|bash|sh)')
# An interpreter invoked through an absolute path (/usr/bin/python3,
# /bin/bash, /usr/bin/env) is still that interpreter; resolve such tokens to
# their basename so literal-command inspection covers absolute spellings too.
ABSOLUTE_INTERPRETER = re.compile(r'^/(.*/)*(?:python(?:3(?:\.\d+)?)?|bash|sh|env)$')


def resolved_interpreter(token):
    """Return the interpreter name for a bare or absolute interpreter token."""
    if INTERPRETER.fullmatch(token):
        return token
    if ABSOLUTE_INTERPRETER.fullmatch(token):
        name = token.rsplit('/', 1)[-1]
        return None if name == 'env' else name
    return None


def strip_comment(line):
    """Drop a shell comment; '#' starts one only at the start of a word.

    shlex's comment mode also cuts at a '#' inside a word, so
    `python3 scripts/issue#12.py` would lose the rest of its script path.
    """
    quote = None
    word_start = True
    index = 0
    while index < len(line):
        char = line[index]
        if quote == "'":
            if char == "'":
                quote = None
        elif char == '\\':
            index += 1
            word_start = False
        elif quote == '"':
            if char == '"':
                quote = None
        elif char in ("'", '"'):
            quote = char
            word_start = False
        elif char == '#' and word_start:
            return line[:index]
        else:
            word_start = char.isspace() or char in ';&|()<>'
        index += 1
    return line


def git(root, *args):
    # Hooks and enclosing Git commands export repository-local routing. Those
    # variables override -C, so baseline/head reads could inspect another repo.
    environment = dict(os.environ)
    local = subprocess.check_output(['git', 'rev-parse', '--local-env-vars'],
                                    text=True).splitlines()
    for name in local:
        environment.pop(name, None)
    return subprocess.check_output(['git', '-C', str(root), *args], env=environment)


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
    def render(match):
        item = row.get(match[1], match[0])
        if isinstance(item, bool):
            return 'true' if item else 'false'
        return str(item)
    return EXPRESSION.sub(render, value)


def join_line_continuations(command):
    """Remove shell backslash-newline pairs outside single quotes/comments.

    This only reconstructs logical lines for the existing literal-command
    checker; it does not evaluate expansions or compound shell commands.
    """
    result = []
    quote = None
    comment = False
    word_start = True
    index = 0
    while index < len(command):
        char = command[index]
        if comment:
            result.append(char)
            if char == '\n':
                comment = False
                word_start = True
        elif quote == "'":
            result.append(char)
            if char == "'":
                quote = None
        elif char == '\\' and index + 1 < len(command):
            following = command[index + 1]
            if following != '\n':
                result.extend((char, following))
                word_start = False
            index += 1
        else:
            result.append(char)
            if char == quote:
                quote = None
            elif quote is None:
                if char in ("'", '"'):
                    quote = char
                    word_start = False
                elif char == '#' and word_start:
                    comment = True
                else:
                    word_start = char.isspace() or char in ';&|()<>'
        index += 1
    return ''.join(result)


def has_heredoc(command):
    """Return whether command contains an unquoted, uncommented shell heredoc."""
    quote = None
    comment = False
    word_start = True
    index = 0
    while index < len(command):
        char = command[index]
        if comment:
            if char == '\n':
                comment = False
                word_start = True
            index += 1
        elif quote == "'":
            if char == "'":
                quote = None
            index += 1
        elif quote == '"':
            if char == '\\' and index + 1 < len(command):
                index += 2
            else:
                if char == '"':
                    quote = None
                index += 1
        elif char == '\\' and index + 1 < len(command):
            word_start = False
            index += 2
        elif char in ("'", '"'):
            quote = char
            word_start = False
            index += 1
        elif char == '#' and word_start:
            comment = True
            index += 1
        elif char == '<':
            end = index
            while end < len(command) and command[end] == '<':
                end += 1
            if end - index == 2:
                pos = end
                if pos < len(command) and command[pos] == '-':
                    pos += 1
                while pos < len(command) and command[pos] in (' ', '\t'):
                    pos += 1
                if pos < len(command) and command[pos] not in '\r\n;&|()<>#':
                    return True
            word_start = True
            index = end
        else:
            word_start = char.isspace() or char in ';&|()<>'
            index += 1
    return False


def python_option(option):
    """Return (inline mode, separate value) for one Python option token."""
    if option == '-':
        return True, False
    if option.startswith('--'):
        return False, option == '--check-hash-based-pycs'
    for consumed, flag in enumerate(option[1:], 2):
        if flag in ('c', 'm'):
            return True, False
        if flag in ('W', 'X'):
            # The remainder belongs to this option's value, not more flags:
            # -IWmodule must not be mistaken for inline module mode.
            return False, consumed == len(option)
    return False, False


def shell_option(option):
    """Return (non-file input mode, separate value) for a shell option."""
    if option.startswith('--'):
        return False, option in ('--rcfile', '--init-file')
    for consumed, flag in enumerate(option[1:], 2):
        if flag in ('c', 's'):
            # -c reads a command string; -s reads stdin. Remaining operands
            # name positional parameters, not a script file.
            return True, False
        if flag in ('o', 'O'):
            # Do not search through a value-taking option for incidental
            # c/s letters. A separate option name is consumed by the caller.
            return False, consumed == len(option)
    return False, False


def command_start(tokens):
    """Return the interpreter index after shell assignments and env options."""
    return command_context(tokens, '.')[0]


def _parse_command_context(tokens, directory):
    """Resolve env options, chdir, assignments, and uninspectable split-strings."""
    index = 0
    change_directory = None
    split_string = False
    while index < len(tokens) and ASSIGNMENT.match(tokens[index]):
        index += 1
    if index < len(tokens) and (tokens[index] == 'env'
                                or (ABSOLUTE_INTERPRETER.fullmatch(tokens[index])
                                    and tokens[index].rsplit('/', 1)[-1] == 'env')):
        index += 1
        while index < len(tokens):
            token = tokens[index]
            if token == '--':
                index += 1
                while index < len(tokens) and ASSIGNMENT.match(tokens[index]):
                    index += 1
                break
            if token == '-':
                index += 1
                continue
            if token in ('-C', '--chdir'):
                if index + 1 >= len(tokens):
                    raise ValueError('env chdir option requires a directory')
                change_directory = tokens[index + 1]
                index += 2
                continue
            if token.startswith('--chdir='):
                value = token.partition('=')[2]
                if not value:
                    raise ValueError('env chdir option requires a directory')
                change_directory = value
                index += 1
                continue
            if token in ('-u', '--unset', '--argv0', '--file'):
                if index + 1 >= len(tokens):
                    raise ValueError(f'env {token} option requires an argument')
                index += 2
                continue
            if token in ('-S', '--split-string'):
                if index + 1 >= len(tokens):
                    raise ValueError(f'env {token} option requires an argument')
                split_string = True
                index += 2
                continue
            if token.startswith('--split-string='):
                split_string = True
                index += 1
                continue
            if token.startswith('--'):
                index += 1
                continue
            if token.startswith('-'):
                step = 1
                for offset, flag in enumerate(token[1:], 1):
                    rest = token[offset + 1:]
                    if flag == 'C':
                        if rest:
                            change_directory = rest
                        else:
                            if index + 1 >= len(tokens):
                                raise ValueError('env chdir option requires a directory')
                            change_directory = tokens[index + 1]
                            step = 2
                        break
                    if flag in ('u', 'a', 'f'):
                        if not rest:
                            if index + 1 >= len(tokens):
                                raise ValueError(f'env -{flag} option requires an argument')
                            step = 2
                        break
                    if flag == 'S':
                        split_string = True
                        if not rest:
                            if index + 1 >= len(tokens):
                                raise ValueError('env -S option requires an argument')
                            step = 2
                        break
                index += step
                continue
            if ASSIGNMENT.match(token):
                index += 1
                continue
            break
    if change_directory is not None:
        # Keep expansions visible until the caller's nonliteral-directory
        # check; normpath('$DIR/..') would otherwise erase the variable.
        directory = posixpath.join(directory, change_directory)
    return index, directory, split_string


def command_context(tokens, directory):
    """Resolve env's command-local chdir relative to the step directory."""
    index, resolved_directory, _ = _parse_command_context(tokens, directory)
    return index, resolved_directory


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
                command = join_line_continuations(substitute(str(step['run']), row))
                cwd = substitute(str(step.get('working-directory', directory)), row)
                if has_heredoc(command):
                    unsupported.add((name, str(job_id), 'heredoc body requires shell parsing'))
                    continue
                for line in command.splitlines():
                    # Only literal, standalone interpreter commands. Shell programs
                    # and generated script bodies are not evaluated by this checker.
                    try:
                        tokens = shlex.split(strip_comment(line))
                    except ValueError:
                        if COMMAND_PREFIX.match(line):
                            unsupported.add((name, str(job_id), 'unparsed shell command'))
                        continue
                    index, command_directory, split_string = _parse_command_context(tokens, cwd)
                    if split_string:
                        unsupported.add((name, str(job_id), 'env split-string requires shell parsing'))
                        continue
                    interpreter = resolved_interpreter(tokens[index]) if index < len(tokens) else None
                    if interpreter is None:
                        continue
                    if '${{' in line or '$' in command_directory or command_directory.startswith('/'):
                        unsupported.add((name, str(job_id), 'dynamic command/directory'))
                        continue
                    index += 1
                    python = interpreter.startswith('python')
                    # Shells also accept +-prefixed options (bash +e, +o pipefail).
                    prefixes = ('-',) if python else ('-', '+')
                    while index < len(tokens) and tokens[index].startswith(prefixes) and tokens[index] != '+':
                        option = tokens[index]
                        if option == '--':
                            index += 1
                            break
                        if python:
                            inline, takes_value = python_option(option)
                        else:
                            inline, takes_value = shell_option(option)
                        if inline:
                            index = len(tokens)
                            break
                        index += 2 if takes_value else 1
                    if index >= len(tokens):
                        continue
                    script = tokens[index]
                    if script.startswith(('/', '<')) or any(c in script for c in '$`*?'):
                        unsupported.add((name, str(job_id), 'nonliteral script'))
                        continue
                    path = posixpath.normpath(posixpath.join(command_directory, script))
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
