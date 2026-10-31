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


def cycle_regions(blocks):
    graph = {b['offset']: sorted({e['target'] for e in b['successors'] if e['internal']}) for b in blocks}
    reverse = {node: [] for node in graph}
    for source, targets in graph.items():
        for target in targets:
            reverse[target].append(source)
    seen, finished = set(), []
    for root in graph:
        if root in seen:
            continue
        seen.add(root)
        pending = [(root, iter(graph[root]))]
        while pending:
            node, children = pending[-1]
            child = next(children, None)
            if child is None:
                finished.append(node)
                pending.pop()
            elif child not in seen:
                seen.add(child)
                pending.append((child, iter(graph[child])))
    assigned, regions = set(), []
    reachable = {b['offset'] for b in blocks if b['reachable']}
    for root in reversed(finished):
        if root in assigned:
            continue
        component, pending = set(), [root]
        assigned.add(root)
        while pending:
            node = pending.pop()
            component.add(node)
            for parent in reverse[node]:
                if parent not in assigned:
                    assigned.add(parent)
                    pending.append(parent)
        if len(component) > 1 or root in graph[root]:
            regions.append({'blocks': sorted(component), 'reachable': bool(component & reachable),
                            'entry_blocks': sorted(node for node in component
                                                   if node == 0 or any(p not in component for p in reverse[node]))})
    return sorted(regions, key=lambda row: row['blocks'][0])


LEGACY_CONDITIONAL_JUMPS = frozenset({
    0x15, 0x1d, 0x25, 0x2d, 0x35, 0x3d, 0x45, 0x4d,
    0x55, 0x5d, 0x65, 0x6d, 0x75, 0x7d,
    0xa5, 0xad, 0xb5, 0xbd, 0xc5, 0xcd, 0xd5, 0xdd,
})


def analyze(raw, start=0):
    # This decoder uses the legacy SBPFv0/v1 instruction layout.
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
        if op & 7 == 6:
            diagnostics.append({'offset': offset, 'opcode': op, 'error': 'unsupported control-flow opcode'})
            continue
        if op & 7 != 5:
            continue
        if op in (0x85, 0x8d):
            if op == 0x8d and not 0 <= immediate <= 10:
                diagnostics.append({'offset': offset, 'register': immediate, 'error': 'invalid indirect call register'})
                continue
            call = {'offset': offset}
            if op == 0x85 and regs >> 4 == 1 and immediate != -1:
                call.update(kind='direct', target=start + offset + 8 + immediate * 8)
            elif op == 0x8d:
                call.update(kind='indirect', register=immediate)
            else:
                call.update(kind='syscall_or_relocated', immediate=immediate)
            calls.append(call)
            continue
        if op == 0x95:
            transfers[offset] = []
        elif op == 0x05 or op in LEGACY_CONDITIONAL_JUMPS:
            conditional = op != 0x05
            target = offset + 8 + displacement * 8
            edges = [(target, 'taken' if conditional else 'jump')]
            if conditional:
                edges.append((following, 'fallthrough'))
            transfers[offset] = edges
            if target in instructions:
                leaders.add(target)
            elif 0 <= target < len(raw):
                diagnostics.append({'offset': offset, 'target': target, 'error': 'branch enters lddw continuation'})
            else:
                diagnostics.append({'offset': offset, 'target': target, 'error': 'branch target outside function'})
            if conditional and following not in instructions:
                diagnostics.append({'offset': offset, 'target': following,
                                    'error': 'conditional fallthrough outside function'})
        else:
            diagnostics.append({'offset': offset, 'opcode': op, 'error': 'unsupported control-flow opcode'})
            continue
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
            'blocks': blocks, 'calls': calls, 'diagnostics': diagnostics,
            'cyclic_regions': cycle_regions(blocks)}


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
        if struct.unpack_from('<H', blob, 18)[0] not in (247, 263):
            raise ValueError('control-flow decoding expects an EM_BPF or EM_SBPF image')
        version = struct.unpack_from('<I', blob, 0x30)[0]
        if version not in (0, 1):
            raise ValueError('control-flow decoding supports legacy SBPFv0/v1 ELF inputs only')
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
