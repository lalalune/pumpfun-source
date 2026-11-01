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

The complete roadmap and dynamic-call attribution are now staged beside the
destination and published through the shared native no-replace helper. An
ordinary write failure removes the private stage and leaves the final output
absent, so the same command can be retried. Existing directories, dangling output
links and destinations claimed while generation is running are preserved.
Parent-directory aliases remain supported. This follows the publication fixes
in [#3002](https://github.com/lalalune/pumpfun-source/pull/3002) and
[#3006](https://github.com/lalalune/pumpfun-source/pull/3006), which explicitly left
this sibling generator for a follow-up. It does not change the defined-call
classifier, source admission, captured inputs or historical packets.

The [real CLI proof](../../../research/defined-calls-publication-20261101/README.md)
uses all three retained captures, an actual POSIX file-size limit and an observer
that claims the destination after the roadmap is generated. The guarantee is
complete publication under ordinary failures on supported hosts, not power-loss
durability or cleanup after an uncatchable process kill.
