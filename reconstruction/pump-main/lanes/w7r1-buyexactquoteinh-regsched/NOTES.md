# w7r1-buyexactquoteinh-regsched

Target `0x13f630`, `buy_v2::buy_exact_quote_in_handler` (original 20,184 B). Angle: register
allocation and scheduling residuals, worked through an llc oracle on our IR.

Base: PR #2240 head `d946fdfea` (w7r1-buyexactquoteinh-sibling: program-fn form plus inline Complete
tail). That head is 20,184 B, ratio 0.99959, and leaves one residual: `mov r7,2` at orig `0x1430d0`
is scheduled two slots late.

## Result

| | origin/main 6edd839 | PR #2240 head | this branch |
| --- | --- | --- | --- |
| eq body bytes (orig 20184) | 20216 | 20184 | 20184 |
| target_metric ratio | 0.99635 | 0.99959 | **1.0 (normalized_equal)** |
| llc-oracle dist | 11 | 2 | 0 |
| official normalized / raw | 1027 / 276 | 1027 / 276 | **1028 / 276** |
| gains / losses / raw losses | - | none | `0x13f630` / none / none |
| unstripped sha256 | c2531dc0... | 72ffe9d7... | bd7cb4247cf730fb4cd5b540eb7be44d815fdd096d4166f2be639db8b72c0537 |

Source change (3 lines in `buy_v2.rs`, no line-count change): `buy_exact_quote_in_handler` now takes
`partial:&bool` (and reads `*partial`), and `execute` passes `&partial`. Runtime behaviour is unchanged.

## Mechanism

1. **The residual comes from the order of the phis.** The `mov r7,2`, the `0` store at `-0x8d0` and
   `mov r9,0` are phi copies for `shareholders` (the `Vec` from
   `sharing_config_shareholders(..)?.unwrap_or_default()`: cap, ptr=2 dangling, len) on the None
   edge. In the llc oracle (our IR, phis permuted in place), our order `[sroa.7 ptr, sroa.0 cap,
   sroa.10 len]` gives the late `mov r7,2`. Both orders that put cap first (`[0,7,10]` or `[0,10,7]`)
   give the original schedule; the other orders are worse.
2. **The phi order is set by SROA's PromoteMem2Reg.** The phis are created in the post-inline SROA
   run. PromoteMem2Reg inserts each new phi at the front of its block, so phi order is the reverse of
   processing order. While it processes the promotable list, it removes each trivially promotable
   alloca (single store, or single block) by moving the last list element into its slot. In that run
   every promotable alloca except the three shareholders slices is removable. The shareholders slices
   sit just before the tail, and the tail is the later MIR locals plus inlined callee allocas, all
   removable. So the number R of removable allocas processed before shareholders decides the phi
   order:
   R=1 (ours: only the `gross_total` closure env) puts s10 into the hole and gives phis `[7,0,10]`.
   R>=2 gives processing order s10, s7, s0, which gives phis `[0,7,10]`, the original order.
   `buy_handler` gets `[0,7,10]` because its `_193` (the `Error` temp across the `?` in the
   `require_gte!` at line 494) adds two removable slices.
3. **Fix:** add one removable alloca that is processed first. A program-fn local whose address
   escapes into the (always-inline) handler call survives the early SROA, then becomes a single-store
   promotable alloca after inlining. The program fn's own allocas sit below the inlined ones in the
   entry block, so SROA (worklist `pop_back`) processes them first. `&partial` does exactly that and
   leaves no code behind.

Diagnostics that confirm the mechanism (not proposed): adding an `Error` temp across a `?` inside any
`require_*!` argument also flips the phis to `[0,7,10]` and fixes `mov r7,2`. But each time it adds a
`with_values` result load swap at that require site. The extractvalue order becomes `.1, .0`.

## Tools (outside git, `~/.cache/pumpfun-reconstruction/lanes/w7r1-buyexactquoteinh-regsched/scripts`)

- `fastbuild_ir.py` + `irwrap.py`: fastbuild copy that also emits LLVM IR / MIR. With
  `PUMP_LLVM_ARGS` + `PUMP_DUMP_FILTER` it captures filtered `-print-before/after=sroa` dumps.
- `extract.py`: keeps one function body, turns the other defines into declares and drops aliases.
  llc then takes about 0.1 s.
- `orc.py`: llc the function and diff it against `win.py orig`, with jump offsets masked
  (`FN=` selects the function).
- `phiperm.py`: the phi-permutation oracle. `var.sh`/`batch.sh`: patch, IR build, oracle, metric
  and phi order, two builds at a time.

## Ledger attempts (all `w7r1-buyexactquoteinh-regsched`)

- oracle-shareholders-phi-order (analysis)
- shareholders spellings: unwrap_or_else(Vec::new), unwrap_or(Vec::new()), split let, match, if-let,
  closure. These were byte-identical or worse, and the phi order did not move.
- is_native_quote by-value spellings (q1 byte-identical, q2 worse)
- diag-require-*-question-arg (d1-d9): phi order fixed, site-local load swap
- snapshot block-scoped temp (s1, s2): worse
- by-ref-partial-into-inlined-handler-on-pr2240: **normalized match**, 1028/276, no losses
