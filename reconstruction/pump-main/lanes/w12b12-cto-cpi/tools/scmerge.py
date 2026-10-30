#!/usr/bin/env python3
"""Inspect one function's StackColoring trace using an explicit debug LLVM build.

The output directory must be new. This is an IR experiment, not evidence that a
source candidate matches the deployed program. No input is modified.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess


def parse_trace(log):
    names = {int(i): name for i, name in re.findall(r'slot #(\d+) with allocation: (\S+)', log)}
    sizes = {int(i): int(size) for i, size in re.findall(r'^Slot #(\d+) - (\d+) bytes\.', log, re.M)}
    if not names or set(names) - set(sizes):
        raise ValueError('missing complete StackColoring allocation diagnostics')
    parent = {index: index for index in names}
    def root(index):
        if index not in parent:
            raise ValueError('merge references an unknown allocation')
        while parent[index] != index:
            index = parent[index]
        return index
    for left, right in re.findall(r'Merging #(\d+) and slots #(\d+) together', log):
        left, right = root(int(left)), root(int(right))
        if left != right:
            parent[right] = left
    groups = defaultdict(list)
    for index in names:
        groups[root(index)].append(index)
    return [{'representative': index, 'name': names[index], 'bytes': sizes[index],
             'members': [{'slot': member, 'name': names[member], 'bytes': sizes[member]}
                         for member in sorted(members)]}
            for index, members in sorted(groups.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ll', required=True, type=Path)
    parser.add_argument('--sym', required=True)
    parser.add_argument('--llvm-bin', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--edit', type=Path)
    parser.add_argument('--slot', action='append', default=[])
    args = parser.parse_args()
    source = args.ll.read_bytes(); text = source.decode('utf-8')
    matches = re.findall(r'define [^\n]*@(\S*' + args.sym + r'\S*)\(', text)
    if len(matches) != 1:
        parser.error(f'function pattern matched {len(matches)} definitions; require one')
    args.out.mkdir(parents=True, exist_ok=False)
    source_copy = args.out/'input.ll'; source_copy.write_bytes(source)
    extracted = args.out/'fn.ll'
    extract = args.llvm_bin/'llvm-extract'; llc = args.llvm_bin/'llc'
    subprocess.run([str(extract), '-S', '-func=' + matches[0], str(source_copy), '-o', str(extracted)], check=True)
    if args.edit:
        before = extracted.read_text(encoding='utf-8')
        after = runpy.run_path(str(args.edit))['edit'](before)
        if not isinstance(after, str) or after == before:
            raise ValueError('edit must return changed IR text')
        extracted.write_text(after, encoding='utf-8')
    result = subprocess.run([str(llc), '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext',
                             str(extracted), '-filetype=obj', '-o', str(args.out/'fn.o'),
                             '-debug-only=stack-coloring'], capture_output=True, text=True)
    (args.out/'sc.log').write_text(result.stderr, encoding='utf-8')
    result.check_returncode()
    groups = parse_trace(result.stderr)
    present = {member['name'] for group in groups for member in group['members']}
    if set(args.slot) - present:
        raise ValueError('requested allocation not present in trace')
    report = {'input_sha256': hashlib.sha256(source).hexdigest(),
              'llvm_extract_sha256': hashlib.sha256(extract.read_bytes()).hexdigest(),
              'llc_sha256': hashlib.sha256(llc.read_bytes()).hexdigest(),
              'function': matches[0], 'groups': groups,
              'selected': [group for group in groups if any(m['name'] in args.slot for m in group['members'])]}
    (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
