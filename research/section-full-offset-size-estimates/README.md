# Full observed offsets in the existing size heuristic

The archived section analyzer caps displayed field offsets at twenty and also
uses that capped list as the input to its maximum-offset-plus-eight heuristic.
Later observed loads disappear from the estimate. Pump's window `0xfbc0`, base
register 3, for example reports 215 although the same window's full observed
offset list gives 231 under that heuristic.

This source-bound successor changes only the heuristic input to the complete
offset list. The twenty-field display cap stays intact, and other qualifiers,
instruction scans and output fields retain their old meaning. Original scripts
and historical packets remain intact. Reviewed LF/CRLF hashes work and other
source drift is rejected.

```sh
python research/section-full-offset-size-estimates/test_generate.py
python research/section-full-offset-size-estimates/generate.py --program mayhem --output work/mayhem-full-offset-estimates
python work/mayhem-full-offset-estimates/verify.py
python scripts/verify_evidence.py
python scripts/test_tooling.py
```

Use a fresh output directory. Tests examine all original windows and aggregate
estimates, including thirteen changed displayed records. `validation.json`
binds complete before/after reports for all three programs.

The existing max-offset-plus-eight formula is still only a heuristic. Offsets
can be negative and register bases are not proven account/struct starts. These
values do not establish actual struct sizes, an IDL, source recovery or runtime
behavior; the fix only stops truncating known inputs before computing them.
