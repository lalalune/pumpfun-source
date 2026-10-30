#!/usr/bin/env python3
"""Measure the named swap_hop function against its captured original window.

Exit 1 while normalized differences remain, 0 for a normalized match, and 2
for rejected inputs. Candidate addresses come from the unstripped symbol table.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import score
from elf_symbols import function_symbols

ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
# Full captured allocation hash, including the retained zero allocation tail.
ORIGINAL_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
TARGET = 0x5B3B0
WINDOW_BYTES = 18584
SYMBOL = re.compile(r'^_ZN14pump_recovered15multi_hop_curve8swap_hop17h[0-9a-f]{16}E$')


def clusters(positions, gap=16):
    out = []
    for position in positions:
        if out and position - out[-1][-1] <= gap:
            out[-1].append(position)
        else:
            out.append([position])
    return out


def original_window():
    image = ORIGINAL.read_bytes()
    if hashlib.sha256(image).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('captured Pump image hash differs')
    rows = [row for row in score.original_windows() if row['start'] == TARGET]
    if len(rows) != 1 or rows[0]['bytes'] != WINDOW_BYTES:
        raise ValueError('original window identity or size differs')
    sections = score.sections(image)
    raw = score.body(image, sections, TARGET, WINDOW_BYTES)
    norm = score.normalize(raw, TARGET, sections)
    if rows[0]['raw'] != raw or rows[0]['norm'] != norm:
        raise ValueError('original window inventory does not bind captured bytes')
    return raw, norm


def measure(candidate):
    image = Path(candidate).read_bytes()
    sections = score.sections(image)
    functions = [row for row in function_symbols(image) if SYMBOL.fullmatch(row[2])]
    if len(functions) != 1:
        raise ValueError('candidate requires exactly one unstripped swap_hop function symbol')
    start, size, symbol = functions[0]
    if size != WINDOW_BYTES:
        raise ValueError(f'candidate swap_hop size {size} differs from required {WINDOW_BYTES}')
    original_raw, original_norm = original_window()
    raw = score.body(image, sections, start, size)
    if len(raw) != WINDOW_BYTES:
        raise ValueError('candidate swap_hop body is incomplete')
    norm = score.normalize(raw, start, sections)
    positions = [index for index in range(size) if norm[index] != original_norm[index]]
    return {
        'original_sha256': ORIGINAL_SHA256,
        'candidate_unstripped_sha256': hashlib.sha256(image).hexdigest(),
        'original_start': hex(TARGET), 'candidate_start': hex(start),
        'symbol': symbol, 'bytes': size,
        'raw_diff_bytes': sum(a != b for a, b in zip(raw, original_raw)),
        'normalized_diff_bytes': len(positions),
        'positions': [hex(position) for position in positions],
        'clusters': [{'first_offset': hex(group[0]), 'last_offset': hex(group[-1]),
                      'diff_bytes': len(group)} for group in clusters(positions)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    try:
        result = measure(args.candidate)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1 if result['normalized_diff_bytes'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
