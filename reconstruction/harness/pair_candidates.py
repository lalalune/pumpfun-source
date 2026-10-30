#!/usr/bin/env python3
"""Report heuristic pairing ambiguity without changing official score acceptance."""
import argparse
from collections import defaultdict
import hashlib
import json
import tempfile
from pathlib import Path


def report(ranked, groups, selected_symbol=None):
    rows = []
    for ratio, grams, start, size, name in ranked:
        rows.append({'start': start, 'bytes': size, 'symbol': name, 'ratio': ratio,
                     'ngram_similarity': grams, 'normalized_alternatives': groups[(start, size)]})
    if not rows:
        raise ValueError('no candidates in the requested search scope')
    selected = rows[0]
    if selected_symbol is not None:
        matches = [row for row in rows if row['symbol'] == selected_symbol]
        if len(matches) != 1:
            raise ValueError('explicit symbol must identify exactly one candidate in this report')
        selected = matches[0]
    margin = None if len(rows) < 2 else rows[0]['ratio'] - rows[1]['ratio']
    return {'candidates': rows, 'selected': selected,
            'selection': 'explicit-symbol' if selected_symbol is not None else 'heuristic-first',
            'top_ratio_margin': margin, 'top_ratio_tied': margin == 0,
            'selected_body_ambiguous': len(selected['normalized_alternatives']) > 1,
            'scope': 'Ranking is bounded by best_candidates; margin is not confidence or equivalence.'}


def body_groups(candidate):
    from score import normalize
    by_digest = defaultdict(list)
    key_for_range = {}
    for start, size, name in candidate.funcs:
        location = (start, size)
        key = key_for_range.get(location)
        if key is None:
            key = (size, hashlib.sha256(normalize(candidate.fn(start, size), start, candidate.secs)).digest())
            key_for_range[location] = key
        by_digest[key].append({'start': start, 'bytes': size, 'symbol': name})
    return {key: by_digest[digest] for key, digest in key_for_range.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('start', type=lambda x: int(x, 0))
    parser.add_argument('--top', type=int, default=8)
    parser.add_argument('--select-symbol', help='exact mangled symbol within the returned candidate set')
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error('--top must be positive')
    from score import original_windows
    from win import Cand, best_candidates
    window = next((w for w in original_windows() if w['start'] == args.start), None)
    if window is None:
        parser.error('original address is absent from the selected inventory')
    with tempfile.TemporaryDirectory(prefix='pump-pair-') as temporary:
        snapshot = Path(temporary) / 'candidate.so'
        snapshot.write_bytes(args.candidate.read_bytes())
        candidate = Cand(snapshot)
    try:
        result = report(best_candidates(window, candidate, args.top), body_groups(candidate), args.select_symbol)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps({'schema': 'candidate-pairing-v1', 'window': hex(args.start),
                      'candidate_sha256': hashlib.sha256(candidate.blob).hexdigest(), **result}, indent=2))


if __name__ == '__main__': main()
