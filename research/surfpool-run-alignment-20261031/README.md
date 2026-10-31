# Surfpool differentials compare a prefix when a run is short

Each `scripts/*_surfpool.py` runner prepares one fixture per selected case, runs
Surfpool twice (captured original and candidate), and compares the results
positionally:

```python
left = run(original, prepared, args.surfpool, args.output)
right = run(candidate, prepared, args.surfpool, args.output)
unexpected = [i for i,(row,fixture) in enumerate(zip(left,prepared)) if ...]
mismatches = [i for i,(x,y) in enumerate(zip(left,right)) if normalized(x) != normalized(y)]
```

`zip` stops at the shortest sequence. Nothing bound `len(prepared)`,
`len(left)` and `len(right)`; the runners exit 0 when `mismatches` and
`unexpected_original_errors` are empty. A run that returned fewer rows than it
was given — a dropped response, a runner that skips a case, a future refactor —
would therefore compare only a prefix and still report a clean differential. The
receipt's `signed_transactions` would be the only witness, and no assertion
reads it.

## Change

`scripts/surfpool_recording_vm.py` gains one helper:

```python
def require_aligned_runs(prepared, left, right):
    lengths = {'prepared': len(prepared), 'original': len(left), 'candidate': len(right)}
    if len(set(lengths.values())) != 1:
        raise ValueError(f'surfpool runs do not cover the same cases: {lengths}')
```

All sixteen `scripts/*_surfpool.py` call it once, immediately after the
candidate run and before any comparison or raw-transaction receipt:

```python
right = run(candidate, prepared, args.surfpool, args.output)
require_aligned_runs(prepared, left, right)
```

Case preparation, the Surfpool invocation, normalization, mismatch
classification, receipt fields and exit statuses are unchanged.

## Tests

`tests/test_surfpool_run_alignment.py`:

- equal runs (including empty runs) are admitted;
- a short candidate run, a short original run and an empty original run are
  refused with `surfpool runs do not cover the same cases`;
- every `scripts/*_surfpool.py` calls the guard exactly once.

```
$ python -B -m unittest tests.test_surfpool_run_alignment
base 963d1eefb: FAILED (errors=1)   # helper absent
change:         Ran 3 tests ... OK
```

## Limits

This refuses a comparison the runners already could not support. It adds no
case, no run and no Surfpool behavior, changes no capture or prior receipt, and
does not claim that a failed Surfpool request can be recovered — the refusal is
the intended outcome.
