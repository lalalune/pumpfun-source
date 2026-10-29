# Lane exactsol-introspection: why the loads after `with_values` swap

Target: `0x14f4e0` `buy_exact_sol_in` (13,224 B). On main d2cb88d it is size-equal with 2
differing normalized slots (window offsets 0x1f58/0x1f60). The source fix was found by sibling lane
`exactsol-sibling-analogy` (PR #1191: write the `checked_add` chain inline as `require_gte!`'s second
argument; 1020/188, no losses). This lane gives the compiler mechanism behind that fix, plus a
fast IR-level test loop that siblings and other windows can reuse.

## 1. The return join and its predecessors

The `ja` after the call goes to window 0x480 (`0x14f960`), the function's `Err` return join:
`ldxdw r2,[r10-0x740]; stxdw [r2+8],r1; stxdw [r2+0],r3; exit` (r3 = Error tag, r1 = Box ptr).
It has 32 machine predecessors (`scripts/preds.py`). In the original, 31 of them set r1 (ptr)
before r3 (tag). Only the TooMuchSolRequired edge (0x1f68) loads r3 before r1. In optimized IR all
29 IR predecessors feed one block, `bb185.i`, whose PHIs are in the order (ptr, i64). So the PHI order
is shared by every edge and is not what makes this edge different.

## 2. What fixes the order: the order of the two `extractvalue`s

- The SDK `llc` reproduces the built function exactly from rustc's emitted IR:
  `llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext pump_recovered.ll` gives 0 differing
  instructions against the fastbuild output. Each run takes about 4 s, against 30 s for a build.
- In baseline IR, block `bb63.i` has `%_208.0 = extractvalue %r, 0` and then `%_208.1 = extractvalue %r, 1`.
  If only those two lines are swapped (`scripts/edit_swap_extractvalue.py`, run with `scripts/irexp.py`),
  llc output is **identical to the original function (0 differing instructions)**.
- So SelectionDAG emits the demoted-sret load for the *later* `extractvalue` first: extract order
  (0,1) gives ptr then tag, and (1,0) gives tag then ptr. The prior lane saw the reversal by
  finalize-isel; this is where it comes from.

## 3. Which source shape produces (1,0): InstCombine sinking

Traced with `-print-changed` filtered to the pre-inline function
`legacy_buy::buy_exact_sol_in` (`scripts/trace_ev.py`):

- Unoptimized IR has the order (0,1) at every `with_values` site in both the baseline and the PR #1191 source.
- Baseline: after the first InstCombine, the call and both extractvalues stay in one block with
  `br label %bb174`, so the order stays (0,1).
- PR #1191 source: `require_gte!` evaluates value2 again inside the error branch. Because of that
  extra `?` chain, the `Error::from(..)` temp lives in an alloca across control flow, and the
  `with_values` call ends in its own block (`bb255`: loads of the temp, the call, `lifetime.end`,
  then `br bb174`). The extractvalues are only used in the single-predecessor successor `bb174`, so
  **InstCombine sinks them there one at a time, each to the block's first insertion point. That
  reverses them to (1,0).** After inlining, the order survives as `%_208.1` then `%_208.0`
  (verified in the matched build's IR).

General rule for other windows: tag-before-ptr after a `{i64,ptr}`-returning call (`with_values`,
`From<AnchorError>`, etc.) means the call's extractvalues were sunk into a single-predecessor
successor block. In source, look for an error value that lives across later control flow: a
`?` evaluated after the error is built, such as a `require_*!` operand containing `?`, or a drop or
StorageDead edge between the call and the merge. Ptr-before-tag means the extractvalues stayed
next to the call.

## Ledger

- `58737f4699ce417381c000c7d49da736`: analyzed, `0x14f4e0-main-d2cb88d-ir-extractvalue-order-llc-v1`
  (llc differential: the extractvalue swap gives the original function exactly).
- `29d4f6d7885f496cb1f925c500aa0ebc`: analyzed, `0x14f4e0-main-d2cb88d-instcombine-sink-reversal-trace-v1` (pass trace above).

## Tools (`scripts/`)

- `capture.py <src> <work> <out> [llvm-args...]`: fastbuild of a scratch copy with `--emit=link,llvm-ir,llvm-bc`.
- `irexp.py <name> <edit.py>`: applies `edit(text)` to the captured IR, runs llc, and diffs the function against the original.
- `fn.sh <obj> <symbol>`: listing of one function by symbol range.
- `preds.py <listing> <join addr>`: predecessors of a join block, with their last instructions.
- `trace_ev.py <print-changed log> <fn> <call regex>`: extractvalue order at each pass that changes it.

## Cross-window scan

`scripts/errscan.py <cand.so>` counts, in each unmatched window, error-return pairs of the form
`call; ldxdw r1/r3,[r10-N]; ldxdw r3/r1,[r10-N±8]; ja`, split into tag-first (T) and
ptr-first (P), for the original and the best candidate. On main, buy_exact_sol_in (orig T=1 P=15,
cand T=0 P=16) is the only window with a T/P mismatch in this exact shape. `trade::buy_exact_quote`
has one extra ptr-first pair in the candidate (orig P=0, cand P=1), which is a structural difference,
not an order difference. So this mechanism does not directly unlock another window today. It is still
the explanation to reach for whenever a residual is a swapped pair of loads right after a call.
