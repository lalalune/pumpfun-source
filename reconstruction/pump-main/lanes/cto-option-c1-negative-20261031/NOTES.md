# Non-leaf Option carrier: preserved C1 negative

Changing `validate` from `Result<Pubkey>` to `Result<Option<Pubkey>>` did not
produce the desired private fee-Some shared join. The genuine C1 build enlarged
CTO by 216 bytes and failed the raw no-loss guard. This packet preserves that
negative and identifies its raw control-flow and address consequences.

This is an exact **historical pair**, not a measurement of latest main:

| | Control | C1 |
|---|---|---|
| source | `39eb377aa6c6ce4aacff273aa13732abb0c0078a` | `0fc50efbc599fa1e025169c8db06fceb25c9c192` |
| native run / artifact | `41159607118` / `13026402898` | `41162533835` / `13027638017` |
| raw ZIP members | 43 | 45 |
| normalized / raw matches | 1034 / 1034 | 1034 / 347 |
| CTO bytes | 27,400 | 27,616 |

C1 compiled in **87.8 seconds**, with no stack warnings. The inner build and
saved score commands succeeded; the subsequent no-loss guard correctly failed:
**687 raw losses, zero normalized losses**. Its original `FAILURE.json` remains
inside the untouched C1 ZIP; no success receipt replaces it. No source gain,
semantic equivalence, new runtime result or latest-main qualification is claimed.

The idea predates this measurement. [w13a42's retained suggestion](https://github.com/lalalune/pumpfun-source/blob/faf99624250b4e60107790f7edabf6609f709885/reconstruction/pump-main/lanes/w13a42-cto-entrycopy3/NOTES.md#L71)
proposed a non-cold, non-leaf helper returning `Result<Option<Pubkey>>`, after
leaf wrappers had folded. C1 measures that carrier in the existing non-leaf
validator. `source.patch` is the exact frozen-pair change: holder success returns
None; other success returns Some(target); the caller retains the Option through
the shared override and projects it afterward. Existing fee validation,
including 39eb's fee-Some volatile byte read, is unchanged. C1 introduces no new
volatile/unsafe or codegen device.

## What the raw code established

Offsets below are bytes relative to CTO VA `0x22a10`.

- **The private Some gate did not appear.** C1's range-success edge reaches
  `+1d68`. A holder test at `+1d88` routes directly to common `+0a70`, or through
  a 6/10-byte fragment-copy block at `+1d98` and back to `+0a70`. Both fee-None
  exits reach those same common blocks. The shared flag is loaded at `+0ab0`
  and tested at `+0ac8`. C1 retains its Option selector in r8 through that fork
  and tests it again at `+12f8` for fallback projection. C1 and control have two
  validation reads of the incoming fee tag; original has three. The C1 fee tag
  still passes unchanged to mutation and pool CPI.
- **Original ordering remains distinct.** Original first tests shared at
  `+0dc0`, then loads selected creator words from its saved state at
  `+0dc8/+0de0/+0df8/+0e10`, before the fee test `+0e20/+0e28`. A second
  shared/flag choice follows fee-Some success at `+1818/+1820`.
  `original-order.json` points to the independent original-flow query and
  preserves the exact raw witnesses, which this verifier recomputes. These
  machine selections do not prove two literal Rust trees or a unique helper
  boundary. C1 preserves current reconstruction effects; it supplies no
  original-source-order provenance.
- **The exterior raw churn is bounded.** CTO growth moves following allocated
  section addresses by 216 bytes. Across the complete `.text` outside CTO,
  every remaining changed instruction has the same opcode, registers and
  displacement: 5,196 LDDW addresses shift by 216 bytes, 827 internal-call
  immediates change by +27 and 2,143 by -27. Targets are checked against the
  same piecewise insertion mapping, including unnamed/padding text. All other
  exterior text bytes are identical. `.rodata` bytes are identical. Of 1,060
  named functions, only CTO changes size; 904 addresses shift and 156 do not.
  This explains the address-operand changes behind the exterior raw losses;
  it is not a machine-semantic equivalence claim.
- **One local allocation moves toward original.** C1 spills the event clone
  destination pointer at `+5580` to FP-920, reloads it at `+5760`, and keeps
  the bump in r6 from `+55a0` through seed store `+57c0`. Original also keeps
  bump in r6 and spills the clone pointer, while control makes the opposite
  choice. The raw sharing-tag predicate remains after pool CPI
  (`+5390..+53a8`). This is a bounded allocation observation, not a match gain.

## Preserved evidence and replay

`captures.tar.xz` holds the two exact provider ZIPs together, unchanged transport
and admission receipts, and the common frozen CORE source-text leaves. Each ZIP
contains its full 141-file source archive, 142-file compiled workspace archive,
236-file CORE manifest, native build/link provenance, both ELFs and full saved
score. The 28 pinned binary CORE inputs are read from the repository; the
checked-in original is independently hash-bound. Frozen source text is archived
so later harness changes do not rewrite this measurement.

From the research lane in a checkout containing the pinned binary inputs:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B verify.py
```

For a packet outside the checkout, add `--repo /path/to/pumpfun-source`.
`verification.json` records a genuine replay using the prepared `0d04cf4`
checkout's binary inputs, not a program build on that revision. The verifier
recomputes declarations, source/stage bytes, CORE identities, exact patch,
referenced control members, saved 1,035-row arithmetic, raw CFG witnesses and
the full exterior text census. It does **not** compile, invoke IR/VM tools or
rerun the full scorer. The positive verifier result means the historical
negative remains reproducible, not that C1 passed its no-loss guard.
