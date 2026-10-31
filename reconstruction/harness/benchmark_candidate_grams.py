#!/usr/bin/env python3
"""Compare ranking on retained Pump bodies; no build/score acceptance claim."""
import difflib
import hashlib
import json
import statistics
import time

import win


def reference(window, candidate, top=3):
    """Pre-change Counter intersection/union ranking, including its shortlist."""
    original = win.opgrams(window['raw'])
    scored = []
    for start, size, name in candidate.funcs:
        if not 0.4 * window['bytes'] <= size <= 2.5 * window['bytes']:
            continue
        grams = candidate.grams(start, size)
        intersection = sum((original & grams).values())
        union = sum((original | grams).values()) or 1
        scored.append((intersection / union, start, size, name))
    scored.sort(reverse=True)
    tokens = [row[2] for row in win.insns(window['raw'], window['start'], win.ORIG_SECS)]
    shortlist = scored[:max(8, top)] if original else scored
    rows = [(difflib.SequenceMatcher(None, tokens, candidate.tokens(start, size), autojunk=False).ratio(),
             similarity, start, size, name) for similarity, start, size, name in shortlist]
    rows.sort(reverse=True)
    return rows[:top]


def main():
    windows = [window for window in win.original_windows() if window['bytes'] <= 8192]
    # These are body fixtures from the retained original, not invented ELF
    # function symbols or a claim about a fresh compiled candidate inventory.
    candidate = win.Cand.__new__(win.Cand)
    candidate.blob, candidate.secs = win.ORIG, win.ORIG_SECS
    candidate.funcs = [(window['start'], window['bytes'], f'window-{index}')
                       for index, window in enumerate(windows)]
    candidate._opgrams, candidate._tokens = {}, {}
    queries = windows[::max(1, len(windows) // 20)][:20]
    results = []
    for label, rank in [('reference', reference), ('current', win.best_candidates)]:
        samples = []
        for repeat in range(4):
            started = time.perf_counter()
            rows = [rank(window, candidate, 3) for window in queries]
            elapsed = time.perf_counter() - started
            if repeat:  # Warm both gram and token caches before measurement.
                samples.append(elapsed)
        results.append({'implementation': label, 'median_seconds': statistics.median(samples),
                        'ranking_sha256': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()})
    if results[0]['ranking_sha256'] != results[1]['ranking_sha256']:
        raise RuntimeError('candidate ranking differs from the retained reference')
    print(json.dumps({'candidate_body_fixtures': len(windows), 'queries': len(queries),
                      'results': results}, indent=2))


if __name__ == '__main__':
    main()
