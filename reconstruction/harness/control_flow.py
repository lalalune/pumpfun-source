#!/usr/bin/env python3
"""Inspect an SBF function's control flow; diagnostic only, never an acceptance score."""
import argparse
from bisect import bisect_left
import hashlib
import json
import struct
from pathlib import Path
from score import sections, body
from instruction_stream import require_instruction_range


def analyze(raw, start=0):
    if start < 0 or start % 8 or not raw or len(raw) % 8:
        raise ValueError('function must have a nonempty, 8-byte aligned range')
    instructions = {}
    offset = 0
    while offset < len(raw):
        op, regs, displacement, immediate = struct.unpack_from('<BBhi', raw, offset)
        width = 16 if op == 0x18 else 8
        if offset + width > len(raw):
            raise ValueError('truncated lddw instruction')
        instructions[offset] = (op, regs, displacement, immediate, width)
        offset += width
    leaders = {0}
    transfers, calls, diagnostics = {}, [], []
    for offset, (op, regs, displacement, immediate, width) in instructions.items():
        following = offset + width
        if op & 7 not in (5, 6):
            continue
        kind = op & 0xf0
        if kind == 0x80:
            call = {'offset': offset}
            if op == 0x85 and regs >> 4 == 1 and immediate != -1:
                call.update(kind='direct', target=start + offset + 8 + immediate * 8)
            elif op == 0x8d:
                call.update(kind='indirect', register=immediate)
            else:
                call.update(kind='syscall_or_relocated', immediate=immediate)
            calls.append(call)
            continue
        if kind == 0x90:
            transfers[offset] = []
        else:
            target = offset + 8 + displacement * 8
            edges = [(target, 'jump' if kind == 0 else 'taken')]
            if kind != 0:
                edges.append((following, 'fallthrough'))
            transfers[offset] = edges
            if target in instructions:
                leaders.add(target)
            elif 0 <= target < len(raw):
                diagnostics.append({'offset': offset, 'target': target, 'error': 'branch enters lddw continuation'})
        if following in instructions:
            leaders.add(following)
    ordered = sorted(leaders)
    blocks = []
    offsets = list(instructions)
    for index, leader in enumerate(ordered):
        end = ordered[index + 1] if index + 1 < len(ordered) else len(raw)
        first_index, end_index = bisect_left(offsets, leader), bisect_left(offsets, end)
        last = offsets[end_index - 1]
        outgoing = transfers.get(last, [(end, 'fallthrough')])
        blocks.append({'offset': leader, 'bytes': end - leader, 'instructions': end_index - first_index,
                       'successors': [{'target': target, 'kind': kind, 'internal': target in leaders}
                                      for target, kind in outgoing]})
    by_offset = {block['offset']: block for block in blocks}
    reachable, pending = set(), [0]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(edge['target'] for edge in by_offset[current]['successors'] if edge['internal'])
    for block in blocks:
        block['reachable'] = block['offset'] in reachable
    return {'start': start, 'bytes': len(raw), 'instruction_count': len(instructions),
            'blocks': blocks, 'calls': calls, 'diagnostics': diagnostics}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--start', required=True, type=lambda value: int(value, 0))
    parser.add_argument('--size', required=True, type=lambda value: int(value, 0))
    parser.add_argument('--json', type=Path)
    args = parser.parse_args(argv)
    try:
        blob = args.binary.read_bytes()
        secs = sections(blob)
        text = secs['.text']
        if args.size <= 0 or args.start < text['addr'] or args.start + args.size > text['addr'] + text['size']:
            raise ValueError('requested range is outside .text')
        text_bytes = body(blob, secs, text['addr'], text['size'])
        require_instruction_range(text_bytes, args.start - text['addr'], args.size)
        raw = body(blob, secs, args.start, args.size)
        if len(raw) != args.size:
            raise ValueError('truncated function bytes')
        report = analyze(raw, args.start)
        report['binary_sha256'] = hashlib.sha256(blob).hexdigest()
    except (OSError, ValueError, KeyError, struct.error) as error:
        parser.error(str(error))
    output = json.dumps(report, indent=2) + '\n'
    if args.json:
        try:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            with args.json.open('x', encoding='utf-8') as stream:
                stream.write(output)
        except OSError as error:
            parser.error(f'cannot create diagnostic report: {error}')
    print(output, end='')
    return 1 if report['diagnostics'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
