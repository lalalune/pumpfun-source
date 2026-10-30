# w7r1-execute-blockorder: 0x72810 `sweep::execute` (block order / branch sense)

Base: origin/main 2b85821 (s6 sweep), 1027/1035 normalized, 276 raw. Target ratio 0.88669, 7880 B (orig 7832), 39/39 calls.
Analysis only: no source change beats s6. Trial sources and outputs: `~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-blockorder/{v,out}`.

## Findings
- Admit branch polarity (orig `jeq r1,2,+1; ja` / `jne r1,2`): BPF cannot reverse branches, so polarity is fixed at ISel by IR block order. The two admits inline in execute (q01) give both polarities right, but the join clone call site stays cold (pre-inline freq 0.01669 < 2%), giving 40 calls.
- The arm order of `match (creator,native)` picks the 1.79 match decision tree. RTN (main) sends the protocol path through a shared "remaining" native test (a phi, so 50/50 BPI). RNT/NRT, `(_,true)`, `_` wildcard and or-pattern variants (q03, q04, q07, q09, r01) give direct per-bucket ZH tests: token freq 0.0534, join warm, 39 calls with inline admits, both polarities right. But the empty `(false,true)` arm is collapsed into the join, so MIR JumpThreading no longer threads the Option switch through the recipient clone (orig +0x604..0x646 chain is missing; fullmask diff 109, ratio 0.743).
- Why: in 1.79 JumpThreading a SwitchInt predecessor is only processed when it is the *single* predecessor. The N edge has to pass through a non-empty goto block. On main that block is the `assume(!creator)` from UnreachablePropagation.
- TRN/TNR and `match (native,creator)` with `Pubkey::default()` stop at MAX_BACKTRACK (one memcmp, 38 calls). `Pubkey::new_from_array([0;32])` emits the same code but removes one MIR block, so creator threads through the native switch (t02 = RNT result).
- Merging admit results before `?` (match / and_then; at arm level or match level, m01-m06) never keeps the merge: the `Err(e)` aggregate is always threaded. With a match-level `?`, N's `Ok(())` is threaded too, and the Option-switch threading for N is lost.

## Next ideas
1. An RNT tree whose protocol-native arm block survives as a non-empty single-predecessor goto block, with no Ok constant flowing into a `?`.
2. A merge whose Err path is more than 5 MIR blocks away from the `?` switch (MAX_BACKTRACK), so JT cannot thread it.
3. The IR oracle (w4 mv2 42:46:40) still bounds the polarity gain at 0.8898.

Ledger keys: `0x72810-main-2b85821-*` (lane w7r1-execute-blockorder).
