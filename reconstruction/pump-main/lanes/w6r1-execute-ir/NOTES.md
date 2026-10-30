# Lane w6r1-execute-ir (wave 6, round 1)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Approach: IR oracle (llc from the SDK on rustc's IR of the target reproduces fastbuild exactly), then
the Rust spelling that makes rustc emit the winning IR.

Base: origin/main 099b0dd (1027/1035 normalized, 276 raw), target 0.80237 at 15,584 B. During the
lane, #2154 (sibling lane w6r1-execute-sem) merged the w4 `g7` form (0.82553, 15,544 B); this branch
is rebased on that main and only adds the two edits below.

## Result

| Build | Bytes | Ratio | Official | Notes |
| --- | ---: | ---: | --- | --- |
| main 099b0dd | 15,584 | 0.80237 | 1027 / 276 | v13 store order |
| g7 (= main after #2154) | 15,544 | 0.82553 | 1027 / 276 | |
| d1 = g7 + exhaustive depth match | 15,560 | 0.82400 | 1027 / 276 | orig `jlt tag,3` form, RA worse |
| c1b = d1 + explicit `Result` match on `control_account` | 15,592 | 0.84194 | 1027 / 276, 0 losses | is_holder_reward=r6, ctx=r7 as orig |
| t6 = c1b + depth computed inside `init_curve` from `source` | 15,592 | 0.84516 | 1027 / 276, 0 losses | on main f101886 |
| **p1 = t6 + `validate_quote_mint(accounts:&CreateV2, ..)`** | **15,576 (= orig)** | **0.85100** | **1027 / 276, 0 losses** | slots_diff 1489 |

unstripped sha256 (p1, main f101886) `a12ccddaa866c017bd7f3e282c0badf5c639109c3f5614d97fc8f1176035ac6e`.

## Mechanisms

1. **Depth select polarity (d1).** The original computes depth as `jlt tag,3; mov r9,r5`, i.e.
   `select (icmp ult tag,3), 0, payload`. `if let Nested(d)=source {d} else {0}` gives
   `icmp eq tag,3` (`jeq`/`jgt` forms). IR oracle edit `dult` (ult 3 with swapped select operands)
   gives the jlt form; the Rust spelling is the exhaustive match
   `match source {Sol|Whitelisted|Controlled=>0, Nested(d)=>d}`: MIR emits a 4-way switch whose three
   0-arms SimplifyCFG folds into a range check `icmp ult tag,3` (byte-identical to the oracle edit).
   Arm order is irrelevant. Alone it costs 0.0015 (register allocation), but it is the original shape.
2. **Error block placement drives greedy RA (c1b).** Greedy RA runs on the pre-layout block order, so
   slot-index distances (live-range sizes, hence queue priority) depend on where cold blocks sit. An
   IR-mutation hill-climb (`scripts/irsearch.py`: block moves and intra-block instruction moves,
   scored by the llc oracle) found one dominant move: the `Err` arm of `control_account(..)?`
   (`bb91.i`, a 2-instruction "load error ptr; br to return" block) moved anywhere after the
   validate join block `bb43.i` lifts d1 from 0.82400 to 0.84485 and flips the r6/r7 rotation that w4
   identified (is_holder_reward now r6, ctx/accounts r7, as in the original). Positions before
   `bb43.i` give 0.77-0.81. The Rust spelling: replace `?` with an explicit three-arm match
   `match control_account(..) { Ok(Some(r))=>.., Ok(None)=>{walk..}, Err(e)=>return Err(e) }`;
   rustc then emits the Err arm after the Ok(None)/walk blocks. (Arm order of the two Ok arms is
   byte-identical.) A blank `// layout-pad`-style line below is removed to keep every later
   `line!()` immediate unchanged (the first attempt without it lost 6 normalized windows).

3. **Depth inside the helper (t6).** Passing `source: QuoteSource` to `init_curve` and evaluating the
   same exhaustive match there (at the top or at the store: byte-identical) shortens the depth live
   range across the vqr diamond; the select is now formed next to its store and kept in a register
   (`jlt tag,3; mov r5,r0; ... stxb [curve+0xa0],r5`): 0.84194 -> 0.84516.

4. **Validate takes `&CreateV2` (p1).** With `validate_quote_mint(ctx:&Context, ..)` the accounts
   struct is reached through `ctx.accounts`, which carries no noalias/readonly guarantee, so every
   `a.global` after an opaque call (quote_control, control_account) is a fresh load of
   `accounts+0xf8`. Passing `ctx.accounts` as a `&CreateV2` parameter makes it noalias readonly after
   LLVM inlining; GVN reuses execute's global pointer and `walk` gets it from the spill slot
   (`ldxdw r4,[r10-0x728]; add64 r4,8`) as in the original. Size is now exactly the original 15,576 B.

All edits are behaviour-preserving (`?` on `anchor_lang::Result` is `From::from` identity; the depth
match is exhaustive over the same variants).

## IR-oracle findings not yet expressed in source

- `lategep`: creator destination GEP (curve+8) defined in the memcmp block and the creator memcpy after
  the token_total_supply store reproduces the original store sequence exactly (vqr, ivqr, vtr, rtr, rqr,
  tts, creator via a separate pointer, mayhem, ...), 0.83718 alone, 0.85046 with block moves. Spelling
  attempts (`let creator_slot=&mut bonding_curve.creator` early, `*creator_slot=creator` late) are
  byte-identical to c1b: MIR ReferencePropagation removes the early borrow.
- `v2`: binding `let global=&a.global` before `quote_control` in validate makes `walk` take the global
  pointer from the spill slot as in the original and reaches the exact original size (15,576 B), but
  RA elsewhere drops the ratio to 0.83217.
- In the original the `walk` block is laid out directly after the control_account test (fall-through
  on None, Some values hoisted before the Option test); in ours `walk` is placed at the function end.
  Speculating the Some reserves load in IR alone (0.81077) does not fix the placement.

## Tools

`scripts/`: `build.sh` (fastbuild or IR capture + score + target metric), `capmir.py` (IR/MIR capture,
hooking `fastbuild.run_compiler`), `trial.sh`, `irsearch.py` (IR-mutation hill climb on the llc
oracle; research only). Other helpers are the w4-createv2 scripts with lane paths.

## Ledger

Attempts are recorded under lane `w6r1-execute-ir`, dedupe keys `0x1e7c0-main-099b0dd-*`.
