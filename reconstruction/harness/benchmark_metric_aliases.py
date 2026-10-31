#!/usr/bin/env python3
"""Measure diagnostic reuse on retained body bytes with synthetic alias names."""
import hashlib
import json
import re
import time

import target_metric
import win


class Candidate:
    def __init__(self, window, aliases):
        self.secs = win.ORIG_SECS
        self.funcs = [(window['start'], window['bytes'], f'alias-{i:03d}') for i in range(aliases)]
        self.reads = 0

    def fn(self, start, size):
        self.reads += 1
        return win.body(win.ORIG, self.secs, start, size)


def main():
    window = max((w for w in win.original_windows() if w['bytes'] <= 2048), key=lambda w: w['bytes'])
    candidate = Candidate(window, 100)
    started = time.perf_counter()
    rows = target_metric.measure_window(window, candidate, re.compile('alias-'))
    elapsed = time.perf_counter() - started
    if [row['symbol'] for row in rows] != [f'alias-{i:03d}' for i in range(100)]:
        raise RuntimeError('alias inventory/order changed')
    if not all(row['raw_equal'] and row['normalized_equal'] for row in rows):
        raise RuntimeError('identical retained-body diagnostics changed')
    checksum = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    # Reused calculations must not make caller-mutable report rows aliases.
    rows[0]['normalized_field_differences']['field_counts']['probe'] = 1
    if 'probe' in rows[1]['normalized_field_differences']['field_counts']:
        raise RuntimeError('alias rows share mutable diagnostic state')
    print(json.dumps({'body_bytes': window['bytes'], 'aliases': len(rows),
                      'body_reads': candidate.reads, 'seconds': elapsed,
                      'diagnostic_sha256': checksum}, indent=2))


if __name__ == '__main__':
    main()
