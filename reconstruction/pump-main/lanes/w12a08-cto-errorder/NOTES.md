# admin_cto validation-order hypothesis

The remaining window is `0x22a10 admin_cto::execute` (27,400 bytes). The original
Source-line immediates appear in this layout order:

```
289 298 306 296 326 312 307 330 338 334 410 719 648 660 284 556
```

The 20a1ae9 candidate and the later k4 candidate place the validation errors as:

```
298 289 330 296 326 306 312 307 338 410 334 719 648 660 284 556
```

These order observations agree with the retained structural and call-sequence
packets. The candidate also inlines `to_string` at 307/312, where the original
has calls. A useful source experiment is to change how the `holder` and `new`
Option tags reach the validation branches, then inspect pre-inliner block
frequencies before building. The retained
[frequency diagnostic](../w12a10-cto-optoracle/NOTES.md) provides that measurement.

The lane reported that changing tag tests in raw IR moved the first error blocks,
and that a source `holder.unwrap_or(false)` trial reproduced its IR oracle at
27,128 bytes / 0.44986. That trial changes the window size and is not admissible
against the exact-size main. The historical raw IR and full compiler receipts
are not retained here, so this review does not certify those experimental results.

Branch-probability heuristics and Option range metadata are hypotheses for the
observed order, not recovered probabilities of the original program. A future
candidate must preserve all existing raw/normalized matches under the official
scorer. No source or completion gain is claimed by this packet.

Private cache-dependent oracle runners and duplicate display helpers are omitted.
