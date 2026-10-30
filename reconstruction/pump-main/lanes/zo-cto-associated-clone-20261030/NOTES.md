# Admin CTO: transfer CPI account-copy composition

Base: fresh main `4a7d4c8bf0495f5f906363b1efd6f029b74d00bc`, including #3039.

The `TransferCreatorFeesToPumpV2` quote mint, associated-token program,
creator-vault quote token account and AMM program accounts are copied explicitly.
The quote-mint key is read between its two `Rc` clones; the associated-token
program and creator-vault account keys follow both clones; the AMM program's
key/owner reads precede them. All field values and the lamports/data increment
order are preserved. Accounts, CPI arguments, signer seeds and state transitions
are unchanged. The system-program spelling merged in #3039 stays intact. Source
line count and error macro sites are preserved. This composes the first
associated-token candidate (0.58238) with additional copies in the same CPI.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| `admin_cto::execute` bytes | 27,400 | 27,400 |
| Target sequence similarity | 0.57669 | 0.59137 |
| Aligned normalized instruction tokens | 1,925 | 1,974 |
| Positional differing 8-byte slots | 3,312 | 3,311 |
| Raw exact windows | 1,034 | 1,034 |
| Normalized exact windows | 1,034 | 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls in handler | 154 / 3 | 154 / 3 |

This is partial handler similarity progress, not a new complete exact match.

## Validation

- Ordinary single-module identity build against the fresh main above; complete
  scoring retains all raw and normalized windows. Gain and loss lists are empty.
- Independent source build reproduces both candidate image hashes below. The
  multi-copy search binaries are not used as publication evidence.
- 363 signed synthetic `pump_admin_cto_differential.py` runtime cases against the
  captured original and genuine dependency CPIs, zero mismatches. This corpus
  does not prove full program equivalence.
- No stack warnings; runtime-valid build receipt; no build-input changes.

SHA-256:

- Fresh-main unstripped:
  `d87d0c699cf39396e5d0190fafe65245ad6b5db9a24a757859dde5f932d2982b`
- Candidate unstripped, two ordinary builds:
  `e6baa1d0a84a58c0e19c9161821c795775f756f1248bbb14832aedde607d8661`
- Candidate runtime image, two ordinary builds:
  `3c66d42338eff5ceab8ed720ffc011764292c979efd80aa8677121f4c0156072`
- Captured original:
  `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`

Use the pinned SDK and dependency cache documented by the harness:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

## Coordination

- [#3045](https://github.com/lalalune/pumpfun-source/pull/3045) changes explicit
  copies of system_program and coin_creator_vault_ata in the same transfer CPI
  and source line. This change retains the landed #3039 system-program copy and
  changes different accounts instead. Shared file and closely related
  scope; its alternate system-program spelling has not been composed here.
- [#3049](https://github.com/lalalune/pumpfun-source/pull/3049) changes the cashback
  Result tuple and sweep bump lifetime in the same source file. Shared file,
  distinct edits; integration has not been tested.
- Merged [#3039](https://github.com/lalalune/pumpfun-source/pull/3039),
  [#3019](https://github.com/lalalune/pumpfun-source/pull/3019) and
  [#3020](https://github.com/lalalune/pumpfun-source/pull/3020) are preserved.
  Related payer-first clone-run research is in
  [#3028](https://github.com/lalalune/pumpfun-source/pull/3028); initializer order
  remains unchanged here.
