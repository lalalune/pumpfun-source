# Admin CTO: transfer CPI system-program account copy

Compared against main `99fda0f85cf737fa975570bfe42d3b66688e3700`.
Fresh main `6edf34bf2d1e25531a69475aad6a908007c8983b` has identical Pump
program source. Both merged #3019 and #3020 are retained.

The `TransferCreatorFeesToPumpV2` system-program account is copied explicitly.
Both `Rc` increments still occur in lamports/data order; all eight fields retain
their original values. Reading the key after the other metadata changes the
inlined clone's load scheduling. CPI account order, signer seeds, arguments,
validation and state transitions remain the same. Source line count and error
macro sites are preserved.

| Identity build measurement | Main | Candidate |
| --- | ---: | ---: |
| `admin_cto::execute` bytes | 27,400 | 27,400 |
| Target sequence similarity | 0.57100 | 0.57669 |
| Aligned normalized instruction tokens | 1,906 | 1,925 |
| Positional differing 8-byte slots | 3,312 | 3,312 |
| Raw exact windows | 1,034 | 1,034 |
| Normalized exact windows | 1,034 | 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls in handler | 154 / 3 | 154 / 3 |

This is a partial handler similarity gain, not a new complete-window match.
The remaining handler is still unmatched.

## Validation

- Two ordinary, single-module source builds using the pinned identity recipe
  reproduced identical unstripped and runtime binary hashes. Multi-copy screens
  were used only to find the source spelling; they are not the scored artifacts.
- Full `score.py` comparison preserves every baseline raw and normalized match;
  all gain and loss lists are empty.
- `scripts/pump_admin_cto_differential.py`: 363 signed synthetic cases against
  the captured original and genuine dependency CPIs, zero mismatches. This
  corpus is runtime evidence, not a proof of complete program equivalence.
- No stack warnings; build reports runtime-valid. No build-input changes.

Hashes (SHA-256):

- Original captured Pump image:
  `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
- Candidate unstripped, both ordinary builds:
  `d87d0c699cf39396e5d0190fafe65245ad6b5db9a24a757859dde5f932d2982b`
- Candidate runtime image, both ordinary builds:
  `3894b6ff39374c07e0bbc35994283ffa3e6bfc7e1f85bbdd7c5ae242a76bc8a6`

Reproduce with the pinned SDK/dependency cache configured as documented by the
harness:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

## Related work

- [#3028](https://github.com/lalalune/pumpfun-source/pull/3028) studies this same
  transfer CPI's account clone run and payer-first literal order. It is currently
  notes-only; this change retains main's account initializer order and changes
  only the system-program clone's metadata read order. Related scope, not a
  source-file conflict or an integration claim.
- [#3027](https://github.com/lalalune/pumpfun-source/pull/3027) studies sweep CFG
  layout and return threading; no source-file overlap in its current notes-only
  diff. No composition with those proposed experiments was tested.
- Merged [#3019](https://github.com/lalalune/pumpfun-source/pull/3019) introduced
  explicit sharing-CPI account clones; this applies the same reconstruction
  technique to a different CPI and retains its landed changes.
- Merged [#3020](https://github.com/lalalune/pumpfun-source/pull/3020) changed event
  account-info and sweep-signer lifetimes in the same source file; preserved.
