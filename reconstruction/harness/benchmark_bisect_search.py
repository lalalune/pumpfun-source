"""Bounded midpoint benchmark; no builds or experiment commands are launched."""
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time
import types
from unittest.mock import patch


def load():
    with patch.dict(sys.modules, {'fcntl': types.ModuleType('fcntl')}):
        import bisect_membership
    return bisect_membership.narrow


def reference(revisions, evaluate, budget):
    # Retain the previous selection rule as an independent small-input oracle.
    low, high, seen = 0, len(revisions) - 1, {}
    for index in (low, high): seen[index] = evaluate(revisions[index])
    while high - low > 1 and len(seen) < budget:
        choices = [i for i in range(low + 1, high) if i not in seen]
        if not choices: break
        index = min(choices, key=lambda i: (abs(i - (low + high) / 2), i))
        seen[index] = evaluate(revisions[index])
        if seen[index] == 'pass': low = index
        elif seen[index] == 'fail': high = index
    return seen, low, high


def main():
    narrow = load()
    cases = 0
    for size in range(2, 9):
        for interior in itertools.product(('pass', 'fail', 'error'), repeat=size - 2):
            statuses = ('pass', *interior, 'fail')
            for budget in (2, 4, 10):
                seen, low, high = reference(list(range(size)), statuses.__getitem__, budget)
                result = narrow(list(range(size)), statuses.__getitem__, budget)
                assert result['tested'] == dict(sorted(seen.items()))
                assert (result['last_passing'], result['first_failing_bound']) == (low, high)
                cases += 1
    revisions = list(range(1_000_000))
    evaluate = lambda i: 'pass' if i < 654321 else 'fail'
    started = time.perf_counter()
    result = narrow(revisions, evaluate, 24)
    elapsed = time.perf_counter() - started
    assert result['last_passing'] == 654320 and result['first_failing_bound'] == 654321
    print(json.dumps({'equivalent_small_cases': cases, 'revisions': len(revisions),
                      'trials': len(result['tested']), 'seconds': elapsed}))


if __name__ == '__main__': main()
