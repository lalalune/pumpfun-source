# w6r1-sweep-ir: 0x72810 `sweep::execute` (IR-oracle lane)

Assigned lane name: `w6r1-execute-ir`. A create_v2::execute lane uses the same name, its
worktree, branch and cache dir, so this lane works under `w6r1-sweep-ir`
(branch `swarm/w6r1-sweep-ir`, cache `~/.cache/pumpfun-reconstruction/lanes/w6r1-sweep-ir`).
Ledger rows are recorded with `--lane w6r1-execute-ir` and keys `0x72810-main-099b0dd-*`.

Base: origin/main 099b0dd (s6 from #1548). Score 1027/1035 normalized, 276 raw. Target: ratio 0.88669,
7880 B (original 7832 B), 39/39 calls. There is no source change in this PR. It is analysis only.

## New tool: an exact LLVM 18.1.7 `opt`

`~/.rustup/toolchains/solana/lib/rustlib/aarch64-apple-darwin/bin/opt` reports "LLVM version
18.1.7-rust-dev", which is the same LLVM as the build. Run rustc with
`-C llvm-args=-print-before=memcpyopt -print-module-scope -filter-print-funcs=<execute>`, and
`opt -passes=memcpyopt` on that dump reproduces execute's MemCpyOpt result exactly in 0.8 s
(`scripts/mco.py`). Earlier lanes used homebrew opt 21/22, which differ. Inline remarks need
`RFLAGS=-Cremark=inline` in the capture, not only `-pass-remarks`.

## Rent region: why the `?` payload slice loses its lifetime markers

- e2 (`let rent=Rent::get()?` in the `#[inline(always)]` helper) is AlwaysInlined right after the
  early function passes, so the helper's unsimplified copy chain (`_15/_16/_17 -> _5.sroa.5 -> val/residual -> _18`)
  is optimized inside execute. Probes with volatile, capture and edits (`volscan.py`, `capscan.py`,
  `capmulti.py`) show that the eraser is the error path's stack-move of `residual`/`_18` into
  `_5.sroa.5`. LLVM 18 erases all lifetime markers of both allocas on a stack-move, so the slice
  cannot be coloured and takes the +24 B slot. Capturing both residual and `_18`, or calling From
  on `_5.sroa.5` directly, keeps all three markers.
- With `#[inline]` or no attribute (e2i/e2n), the helper is simplified on its own first. Its
  body is then exactly the original pattern: the payload is copied before the tag branch, the Ok
  path copies slice->rent, and the error path calls `From(&slice)`. The standalone
  `legacy_native_payments::ensure_rent_exempt` has the same pattern. But the helper is not
  inlined: cost=210 against the cold-call-site threshold of 45, because the call site's
  pre-inline frequency is 0.01602 of entry (less than 2%). That gives 35 calls and ratio 0.8032.
- IR oracle (post-simplify inline): in the e2i final module, mark that simplified helper
  alwaysinline and inline it. InlineFunction re-adds lifetime markers to the markerless slice,
  and the rent region then matches the original (958 insns, 39 calls). **Conclusion: the original
  rent helper was a normal (non-alwaysinline) function that the CGSCC inliner inlined after it
  had been simplified, so its call site was warm (at least 2%).**

## Splitting execute to warm the call site (rejected)

| trial | shape | ratio | bytes | calls |
|---|---|---:|---:|---:|
| e2i / e2n | plain or `#[inline]` rent helper | 0.8032 | 7568 | 35 |
| f1-f4 | `pay_out(a,creator,native,..)` holds the match (+transfer) | 0.23-0.37 | | 35/38 |
| f5/f6 | the tail from the fee take on in `fn sweep(ctx,creator)` | 0.4234 | 9320 | 36 |
| f7/f8 | `take_and_pay(a,creator,bump)->Result<u64>` | 0.2564 | 9400 | 36 |

- pay_out: native is a parameter, so MIR JumpThreading loses the per-bucket memcmp.
- tail fn: the rent helper inlines and the per-bucket memcmp stays, so the call sequence matches the
  original up to transfer_to_owned. But the event callees (Event::data, AccountInfo::clone,
  from_iter, exchange_malloc) are now warm and inline. In the original they are out of line,
  so in the original's execute the event sites were below 2% while the rent site was at or above 2%.

## Constraint for the next try

The rent call site must be at least 0.02 of execute's entry, and the event sites must stay below
0.02 (s6 values: rent 0.016, event block bb89 0.015). Rent is only on the creator path, while
the event join gets most of its mass from the protocol path. My estimate is that a factor of
about 1.33 on the creator path alone gives rent 0.021 and event 0.016. The creator-only
branches are: the creator-vault `require_keys_eq` (ZH 0.375 on success), the `let amount=if creator`
re-test (0.5), `amount==0` (0.625) and the duplicated native memcmp (0.375). No natural spelling
was found that changes one of them without breaking the MIR JT layout.

Tools: scripts/ (copies; paths point at the lane cache). v-files: e2n.rs.txt, f3.rs.txt, f5.rs.txt.
