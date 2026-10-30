# Lane w7r1-execute-inline (wave 7, round 1)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Angle: inlining boundary and callee-multiset census.
Base: origin/main 2b85821 (1027/1035 normalized, 276 raw), target 0.96854 at 15,584 B.

## Callee census (analysis)

`tools/census.py` (lane cache) decodes every `call` in the original window and in our function,
resolves original targets through the scorer's window->symbol map and ours through the symtab,
and diffs the sequences. Result on main 2b85821: 125/125 direct calls, identical callee
sequence (error-path `PumpError::name`/`Display::fmt`/`From`/`with_*`, memcmp/memcpy,
`find_program_address`, `get_associated_token_address_with_program_id`,
`nested_create::{quote_control,control_account,walk}`, `check_quote_mint_extensions`,
`initialize_metadata`, `initialize_mayhem`, `mint_supply`, `create_event`, event/CPI path,
ATA creation and `invoke` + `drop_in_place<[AccountInfo;6]>`). Every helper's
inline/outline decision already matches the original; no syscalls in the window. The
remaining differences are inside inlined bodies.

## Results

| Build | Bytes | Ratio | Official | Notes |
| --- | ---: | ---: | --- | --- |
| main 2b85821 | 15,584 | 0.96854 | 1027 / 276 | |
| t1 | 15,584 | 0.97284 | 1027 / 276, 0 losses, 0 raw losses | creator store after token_total_supply |
| t2 | 15,576 | 0.98763 (slots_diff 42) | 1027 / 276, 0 losses, 0 raw losses | t1 + fee `if/else` expression (found by w7r1-execute-blockorder-b / -frame) |
| t3 | 15,576 | 0.98870 (slots_diff 43) | 1027 / 276, 0 losses, 0 raw losses | t2 + vqr, ivqr, vtr store order (w7r1-execute-frame `o2`) |
| **d1** | 15,576 | **0.99892 (slots_diff 4)** | 1027 / 276, 0 losses, 0 raw losses | t3 + store helper `write_curve` called in both arms of the vqr `if` |

## t1: `bonding_curve.creator=creator` after `token_total_supply`

The original's curve-store block writes, in order: initial_vqr/vqr, vtr, rtr, rqr=0, tts, then
the 32-byte creator through the separate `&mut BondingCurve` pointer (`stxdw [r4+0x18..0]`),
then mayhem, cashback, quote_mint, ... Since #2229 the creator destination is an SSA pointer
(init_curve takes `&mut BondingCurve`), so the creator memcpy is no longer re-scheduled by the
DAG and its IR position now decides its place. IR oracle (memcpy moved after the tts store):
0.97284; the source move reproduces it exactly. (w4 `v5` tried the same move when the GEP was
still folded into the Account pointer and saw no change.) init_curve has no `line!()` sites,
so moving a line inside it changes no immediates.

## t2: t1 + `let fee=if .. {require..; creator_fee_bps.0} else {0};`

Sibling lanes w7r1-execute-blockorder-b and w7r1-execute-frame found (ledger
`*-e1-fee-if-else-expr-v1`, `*-t1-let-fee-if-else-v1`) that the `mut fee` form puts the fee check
blocks between the `validate_metadata` exit and its `?` Ok target in IR order, so ISel emits
`jeq ->Ok; ja ->Err` (BPF cannot reverse a branch later) instead of the original `jne ->Err`.
The if/else expression creates the join after the then-chain. The two changes are independent
and stack: 0.98763 at the original's exact size (15,576 B). Line count unchanged.

Remaining (oracle diff, 46 lines): `mov r7,0`/`mov r2,0` order in the two `Sol` returns of
validate_quote_mint, and the creator pointer in r2 instead of r4 with the `[r10-0x718]` (name) reload
placed after the stores instead of before.

## t3: store order vqr, ivqr, vtr (w7r1-execute-frame `o2`)

Writing `virtual_quote_reserves` before `initial_virtual_quote_reserves` and `virtual_token_reserves`
moves the `[r5+0x3e8]` load to the original position. 0.98870 on top of t2.

## d1: the field stores live in a helper called from both arms (residual B solved)

Residual B was the creator pointer in r2 instead of r4 and the `[r10-0x718]` (name) reload
placed right before `name.len` instead of at the top of the store block. No single in-block IR
move (20,951 candidates), block move (7,267), branch weight or GEP/memcpy placement reproduced it
(here and in sibling lanes). The tell is the original's layout: the Sol arm falls through into the
store block and both non-Sol paths jump to its first instruction, the reload. That is what a
post-RA tail merge of two identical store sequences leaves behind: register allocation sees two
copies of the stores, the name pointer is live through each copy with no use (greedy "spill on
entry": reload at the copy's top) and the creator pointer gets r4; branch folding then merges the
identical tails.

Source: `init_curve` keeps the `quote_mint==sol` test but calls a plain helper
`write_curve(bonding_curve, global, virtual_quote_reserves, creator, quote_mint, depth, fee,
is_mayhem_mode, is_holder_reward)` (all 16 field stores, unchanged order) in both arms, with
`global.initial_virtual_sol_reserves` and `reserves.unwrap_or(initial_virtual_quote_reserves)`.
LLVM inlines both copies (no extra call: 125/125). `#[inline(always)]` on the helper is
byte-identical. Behaviour is identical (same stores, same value). Line count of the region is
unchanged (the blank line after the signature and the closing brace absorb the new `fn` line).
Result: 0.99892, slots_diff 4; the IR oracle with the bb112 phi fix on top gives 1.00000, so
residual A is now the only difference.

## Residual A: `mov r7,0`/`mov r2,0` (bb112 phi order), root cause

IR oracle: in bb112 (join of the two `Sol` returns and the main Ok path of the inlined
validate_quote_mint) the quote_mint first-qword phi (`_84.sroa.31`, ptr) comes last; placing it
before the QuoteSource phis fixes both swaps (t2: 0.98870, t3: 0.98978).
Cause, reproduced with `opt -passes=sroa` (Homebrew LLVM 21) on the module dumped right after the
CGSCC inliner ran on execute (`-print-after=inline -print-module-scope`): partition [16,24) of the
inlined result `_84` is ptr-typed (Err `Box` pointer stores, and execute's pre-inline SROA reuses the
Err-payload `load ptr` for quote word 0), and both Sol returns write the quote with one 32-byte
memset over [16,48). SROA cannot rewrite the split memset slice as a ptr store, keeps a memset on the
new alloca and re-queues it, so that slice is promoted (its phis created) after all others;
JumpThreading then builds bb112's phis in that order. On the pre-SROA module, splitting both
memsets (store word0 + memset 24) or replacing them with a memcpy from a zero constant gives the
original order; splitting only one does not; changing the main path's memcpy source does nothing.
So the source has to deliver the Sol-path zero quote as something other than a single memset at
inline time (or make word0 integer-typed). Every zero spelling tried (Pubkey::default,
new_from_array, system_program::ID, `let sol`, Default::default) folds to the same memset.

### Residual A, follow-up (on d1)

- Which zero write fixes it (opt -passes=sroa on the post-inliner module, Sol paths written as one
  memset of N bytes from offset 16): N=32 (ours) and N=33 keep the ptr phi last; N=34 (also covering
  the QuoteSource payload byte 49) or N=8 (word 0 only) give an order the llc oracle scores 1.00000
  (0,18,31,47,51 / 0,18,31,51,47 / 0,18,51,31,47 all match). Equivalently, any slice touched by a
  multi-partition memset is promoted in a later SROA round, so the source-tag slice must be delayed
  together with the quote slice, or the quote slice must not be.
- Why `Pubkey::default()` gives a 32-byte memset and no merge: at validate's MemCpyOpt the memset
  (from `<[u8;32] as Default>::default` into a temp) is followed by `lifetime.end` of the Pubkey
  temps before the tag stores. A const Pubkey (`system_program::ID`, z1) removes the temps and
  MemCpyOpt merges the quote memset with the QuoteSource tag store into a 33-byte memset, but the
  payload byte (undef for `Sol`) is never written, so it is still 33, not 34: byte-identical code.
- Rejected source spellings (all on d1): wrapper fn around the validate body (0.70952), Sol tuple
  chosen in execute for empty remaining accounts (0.6265/0.58777), shared `let sol` local in
  validate (0.56/0.55), `Default` derive on QuoteSource with `Ok(Default::default())` (identical),
  `#[repr(u8)]`, `#[repr(C,u8)]`, `#[derive(Clone,Copy)]` on QuoteSource (identical), const Sol tuple
  in both/one return (0.949/0.950/0.976).

## Ledger

Lane `w7r1-execute-inline`, keys `0x1e7c0-main-2b85821-*`.

## Merge status (2026-10-30)

Source superseded by main #2386 (80393778f, w6r3-execute-ir), which reaches the same create_v2::execute result: merged PR side and main build to identical unstripped sha256 3ca6911a..., ratio 0.99892, 15,576 B, slots_diff 4, official 1032/347 with zero gains/losses. Recorded as notes only; programs/pump is main's.
