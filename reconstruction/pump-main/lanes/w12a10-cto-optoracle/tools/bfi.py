#!/usr/bin/env python3
"""Inspect pre-inliner block frequencies in caller-supplied LLVM IR.

This is a compiler diagnostic, not a source reconstruction or equivalence test.
The opt executable must support the pinned build's SBF pipeline and diagnostics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


def select_function(text, pattern):
    matches = re.findall(r'\ndefine [^\n]*@("?[^\n(]*' + pattern + r'[^\n(]*"?)\(', text)
    if len(matches) != 1:
        raise ValueError(f'function pattern matched {len(matches)} definitions; require one')
    return matches[0].strip('"')


def frequency_rows(module, function, diagnostic):
    marker = 'block-frequency-info: ' + function
    if marker not in diagnostic:
        raise ValueError('missing block-frequency diagnostic for selected function')
    section = diagnostic.split(marker, 1)[1].split('Printing analysis', 1)[0]
    frequencies = {m[0]: float(m[1]) for m in re.findall(r' - ([^:]+): float = ([0-9.e+-]+)', section)}
    match = re.search(r'\ndefine [^\n]*@"?' + re.escape(function) + r'"?\(', module)
    if not match:
        raise ValueError('selected function missing from pre-inliner dump')
    lines = module[match.start():module.index('\n}\n', match.start())].splitlines()
    block = 'start'; rows = []
    for index, line in enumerate(lines):
        label = re.match(r'^([\w.\-$"]+):', line)
        if label:
            block = label[1].strip('"')
        if 'to_string17h' not in line or not line.strip().startswith('call'):
            continue
        source_line = next((re.search(r'store i32 (\d+),', value)
                            for value in lines[index + 1:index + 15]
                            if re.search(r'store i32 (\d+),', value)), None)
        if source_line is None:
            raise ValueError('to_string call has no nearby source-line store')
        if block not in frequencies:
            raise ValueError('frequency missing for block ' + block)
        value = frequencies[block]
        rows.append({'line': int(source_line[1]), 'block': block,
                     'relative_frequency': value, 'below_2_percent': value < .02})
    if not rows:
        raise ValueError('no annotated to_string calls found')
    return sorted(rows, key=lambda row: row['line'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--opt', type=Path, required=True)
    parser.add_argument('--function', default=r'admin_cto8validate17h')
    args = parser.parse_args()
    opt = str(args.opt.resolve(strict=True))
    source_bytes = args.input.read_bytes()
    def run(*arguments):
        return subprocess.run([opt, *arguments], check=True, capture_output=True, text=True)
    with tempfile.TemporaryDirectory(prefix='pump-bfi-') as directory:
        source_copy = Path(directory)/('input' + args.input.suffix)
        source_copy.write_bytes(source_bytes)
        source = str(source_copy)
        text = run('-S', source, '-o', '-').stdout
        function = select_function(text, args.function)
        dump = run('-O3', '-print-before=inline', '-print-module-scope',
                   '-filter-print-funcs=' + function, source, '-o', str(Path(directory)/'discard.bc')).stderr
        if not dump.startswith('; *** IR Dump'):
            raise ValueError('missing pre-inliner IR diagnostic')
        module = dump.split('\n', 1)[1].split('\n; *** IR Dump', 1)[0]
        path = Path(directory)/'pre-inline.ll'; path.write_text(module, encoding='utf-8')
        diagnostic = run('-passes=function(print<block-freq>)', str(path), '-o', str(Path(directory)/'discard.bc')).stderr
        print(json.dumps({'function': function, 'input_sha256': hashlib.sha256(source_bytes).hexdigest(),
                          'opt_sha256': hashlib.sha256(Path(opt).read_bytes()).hexdigest(),
                          'rows': frequency_rows(module, function, diagnostic)}, indent=2))



if __name__ == '__main__':
    main()
