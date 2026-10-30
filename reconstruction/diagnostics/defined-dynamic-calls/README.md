# Defined dynamic calls in retained ELF diagnostics

The archived ELF reader excludes every type-10 relocated call from its graph.
The archived call-classification packet labels every such relocation external.
Each retained Pump, Pump AMM and Mayhem capture has one defined `.text` function
relocation to `custom_panic`, so those rules omit a real internal graph edge and
mislabel an internal hook as a runtime syscall.

```
python -B reconstruction/diagnostics/defined-dynamic-calls/generate.py --output work/defined-dynamic-calls-new
python -B reconstruction/diagnostics/defined-dynamic-calls/test_generate.py
```

This source-bound diagnostic successor reads the authoritative dynamic-symbol
section, function type, size and target address. Only undefined symbols become
external; admitted defined `.text` functions become internal graph edges. Other
defined dynamic targets remain explicitly unresolved. `callx` instructions count
as indirect calls so total calls include direct, dynamic and indirect categories.

On the retained corpus, external calls are 269/173/133 (575 total), one defined
hook per program is internal, and indirect calls are 144/123/93. Tests exercise
actual reader/callsites/forward/reverse graph APIs and the full generated CLI.
Normalized bytes, entry sets and relocation-pattern dictionaries remain exactly
unchanged; this cannot add scorer acceptance or matched-window claims.

Fixed reviewed source hashes are checked before loading the three archived
modules. Frozen scripts, original captures, archived packet files and old reports
are preserved; new reports bind their adapter/source hashes under the manifest.
This diagnostic is qualified only for the retained identity-mapped `.text`
layouts. It retains historical frontier/planning/attribution limitations and
does not claim dynamic reachability, semantic equality or security acceptance.
