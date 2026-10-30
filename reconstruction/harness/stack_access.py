#!/usr/bin/env python3
"""Compare direct r10 stack accesses in two explicitly selected SBF function ranges.

Diagnostic only: does not infer alias-based accesses, liveness, safety or equivalence.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from score import sections, body
from instruction_stream import require_instruction_range

WIDTHS = {0x60: 4, 0x68: 2, 0x70: 1, 0x78: 8}


def accesses(raw):
    rows = []
    unknown = []
    pos = 0
    while pos < len(raw):
        if pos + 8 > len(raw):
            raise ValueError('truncated instruction')
        op, regs, offset, immediate = struct.unpack_from('<BBhi', raw, pos)
        size = 16 if op == 0x18 else 8
        if pos + size > len(raw):
            raise ValueError('truncated lddw')
        cls, src, dst = op & 7, regs >> 4, regs & 15
        width = WIDTHS.get(op & 0xf8)
        base = src if cls == 1 else dst
        if cls in (1, 2, 3) and base == 10:
            if width is None:
                unknown.append({'instruction_offset': pos, 'opcode': op})
            else:
                rows.append({'instruction_offset': pos, 'offset': offset, 'width': width,
                             'kind': 'read' if cls == 1 else 'write',
                             'end': offset + width})
        pos += size
    return {'accesses': rows, 'unclassified_direct_stack_operations': unknown}


def compare(original, candidate):
    reports = [accesses(raw) for raw in (original, candidate)]
    counts = [Counter((r['offset'], r['width'], r['kind']) for r in report['accesses']) for report in reports]
    differences = [{'offset': key[0], 'width': key[1], 'kind': key[2],
                    'original_count': counts[0][key], 'candidate_count': counts[1][key]}
                   for key in sorted(counts[0].keys() | counts[1].keys()) if counts[0][key] != counts[1][key]]
    return {'original': reports[0], 'candidate': reports[1], 'differences': differences}


def read_range(path, start, size):
    blob = Path(path).read_bytes()
    sec = sections(blob)['.text']
    if size <= 0 or size % 8 or (start - sec['addr']) % 8 or not sec['addr'] <= start < start + size <= sec['addr'] + sec['size']:
        raise ValueError('range must contain aligned complete instructions inside .text')
    text = body(blob, {'.text': sec}, sec['addr'], sec['size'])
    require_instruction_range(text, start - sec['addr'], size)
    raw = body(blob, {'.text': sec}, start, size)
    if len(raw) != size:
        raise ValueError('truncated .text payload')
    return raw, {'sha256': hashlib.sha256(blob).hexdigest(), 'start': start, 'bytes': size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for side in ('original', 'candidate'):
        parser.add_argument('--' + side, type=Path, required=True)
        parser.add_argument('--' + side + '-start', type=lambda x: int(x, 0), required=True)
        parser.add_argument('--' + side + '-bytes', type=lambda x: int(x, 0), required=True)
    args = parser.parse_args()
    left, left_id = read_range(args.original, args.original_start, args.original_bytes)
    right, right_id = read_range(args.candidate, args.candidate_start, args.candidate_bytes)
    print(json.dumps({'schema': 'stack-access-comparison-v1', 'scope': __doc__,
                      'original_input': left_id, 'candidate_input': right_id,
                      **compare(left, right)}, indent=2))


if __name__ == '__main__': main()
