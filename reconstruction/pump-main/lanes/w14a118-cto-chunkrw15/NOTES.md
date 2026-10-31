# w14a118-cto-chunkrw15: per-chunk residual table on ebe5387 (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main ebe5387 (#3495): ratio 0.67316, M 2,247, 3,123 slots, 27,400 B, 1034/1034. Ledger approach `chunkrw15`,
keys `0x22a10-w14-ebe5387-chunkrw15-<trial>-v1`.

## 1. Residual table (tools/chunkprof.py, tools/labels.py)

`chunkprof.py <cand> [--ref <cand>] [--sz 0x200]` aligns the whole function against the original four times (difflib, no
autojunk) and counts the ORIGINAL tokens left unmatched in each orig chunk:

| column | mask |
| --- | --- |
| `M_oo` | the scorer's mask (call imm, lddw imm). This is the loss the ratio sees |
| `rM_oo` | + registers masked |
| `fM_oo` | + r10 frame offsets masked (registers kept) |
| `sk_oo` | skeleton: registers, frame offsets, jump offsets, lea and call immediates masked (w14a108 `xled.fmask`) |

`labels.py` names each orig chunk by its error-line immediates and its resolved callees (main's symtab, the other 1,034
functions sit at the original addresses). `side.py <cand> <lo> <hi>` prints a skeleton-aligned side-by-side of one orig
range, marking each pair ` ` (scorer-equal), `r` (equal with registers masked), `s` (skeleton-equal only), `-`/`+`.

Main ebe5387, per orig 0x200 chunk (`table_ebe5387.md`, raw `prof_main_200.txt`, 0x800 view `prof_main_800.txt`):

| orig chunk | tok | M_oo | rM_oo | fM_oo | sk_oo | region | owner |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 0x0000 | 62 | 35 | 29 | 22 | 23 | validate | validate head (w14a104/107/112/113) |
| 0x0200 | 62 | 24 | 17 | 34 | 25 | validate | validate head (w14a104/107/112/113) |
| 0x0400 | 64 | 60 | 41 | 56 | 29 | validate | validate head (w14a104/107/112/113) |
| 0x0600 | 58 | 24 | 21 | 18 | 9 | validate | validate head (w14a104/107/112/113) |
| 0x0800 | 60 | 16 | 16 | 12 | 27 | validate | validate head (w14a104/107/112/113) |
| 0x0a00 | 60 | 25 | 25 | 60 | 32 | validate | validate head (w14a104/107/112/113) |
| 0x0c00 | 64 | 37 | 36 | 64 | 26 | validate | validate head (w14a104/107/112/113) |
| 0x0e00 | 60 | 44 | 44 | 14 | 39 | validate | validate head (w14a104/107/112/113) |
| 0x1000 | 62 | 30 | 29 | 40 | 24 | validate | validate head (w14a104/107/112/113) |
| 0x1200 | 58 | 13 | 9 | 55 | 3 | validate | validate head (w14a104/107/112/113) |
| 0x1400 | 61 | 30 | 28 | 27 | 21 | validate | validate head (w14a104/107/112/113) |
| 0x1600 | 58 | 9 | 5 | 8 | 0 | validate | validate head (w14a104/107/112/113) |
| 0x1800 | 64 | 42 | 40 | 23 | 22 | validate join, tuple/target copy |  |
| 0x1a00 | 61 | 15 | 14 | 12 | 7 | prepare_bonding_curve, 410 |  |
| 0x1c00 | 59 | 11 | 7 | 11 | 4 | sweep head: dest PDA, 648 |  |
| 0x1e00 | 62 | 7 | 4 | 6 | 2 | sweep: dest PDA, amm_present |  |
| 0x2000 | 60 | 11 | 9 | 11 | 4 | sweep: amm frozen/raw amount, 719? |  |
| 0x2200 | 60 | 4 | 2 | 4 | 1 | sweep: 648 ConstraintSeeds |  |
| 0x2400 | 61 | 9 | 7 | 9 | 3 | sweep: 660 / frozen |  |
| 0x2600 | 63 | 21 | 13 | 20 | 5 | TCF head + clone run |  |
| 0x2800 | 64 | 15 | 5 | 14 | 2 | TCF clone run |  |
| 0x2a00 | 64 | 16 | 8 | 12 | 1 | TCF clone run |  |
| 0x2c00 | 64 | 22 | 7 | 17 | 0 | TCF clone run |  |
| 0x2e00 | 64 | 23 | 10 | 18 | 2 | TCF clone run |  |
| 0x3000 | 64 | 36 | 16 | 34 | 7 | TCF clone run |  |
| 0x3200 | 64 | 41 | 7 | 40 | 3 | TCF clone run |  |
| 0x3400 | 64 | 13 | 8 | 8 | 2 | TCF clone run |  |
| 0x3600 | 64 | 8 | 8 | 0 | 0 | TCF clone run |  |
| 0x3800 | 64 | 6 | 3 | 3 | 0 | TCF clone run |  |
| 0x3a00 | 64 | 15 | 12 | 8 | 4 | TCF call, Rent::get |  |
| 0x3c00 | 63 | 25 | 17 | 19 | 9 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x3e00 | 64 | 31 | 36 | 26 | 36 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4000 | 64 | 34 | 30 | 27 | 34 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4200 | 64 | 33 | 22 | 26 | 54 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4400 | 64 | 54 | 43 | 57 | 35 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4600 | 64 | 27 | 20 | 16 | 1 | sharing CPI clones | sharing CPI clone run (w14a114) |
| 0x4800 | 64 | 26 | 26 | 0 | 0 | sharing CPI tail |  |
| 0x4a00 | 63 | 19 | 7 | 15 | 4 | sharing call, curve store | curve store (w14a91) |
| 0x4c00 | 63 | 7 | 6 | 6 | 5 | pool test + pool CPI clones | curve store (w14a91) |
| 0x4e00 | 64 | 13 | 5 | 13 | 3 | pool CPI call, Clock | curve store (w14a91) |
| 0x5000 | 62 | 11 | 2 | 9 | 1 | event data / emit | curve store (w14a91) |
| 0x5200 | 61 | 3 | 2 | 3 | 1 | emit_cpi invoke |  |
| 0x5400 | 63 | 16 | 5 | 15 | 2 | cold: ProgramError exits |  |
| 0x5600 | 55 | 4 | 4 | 0 | 0 | cold: error fmt |  |
| 0x5800 | 63 | 6 | 4 | 6 | 3 | cold: 284/556, native Rent |  |
| 0x5a00 | 63 | 20 | 15 | 11 | 1 | cold: native ensure_rent/transfer |  |
| 0x5c00 | 64 | 22 | 6 | 21 | 0 | cold: wallet token_frozen, coin clones |  |
| 0x5e00 | 64 | 9 | 8 | 8 | 4 | cold: create_idempotent x2 |  |
| 0x6000 | 64 | 14 | 9 | 12 | 4 | cold: transfer_vault_tokens, collect |  |
| 0x6200 | 64 | 20 | 16 | 18 | 4 | cold: Clock, frozen |  |
| 0x6400 | 62 | 11 | 2 | 9 | 0 | cold: collect event emit |  |
| 0x6600 | 61 | 14 | 8 | 7 | 0 | cold: collect emit_cpi |  |
| 0x6800 | 64 | 8 | 3 | 6 | 1 | cold: coin fee CPI clones |  |
| 0x6a00 | 33 | 3 | 1 | 3 | 0 | cold: collect_coin_creator_fee |  |
| total | 3,325 | 1,092 | 777 | 993 | 529 | | |

Totals: 1,092 orig tokens unmatched under the scorer mask; masking registers recovers 315, masking the frame recovers 99,
masking everything (skeleton) recovers 563 and leaves 529.

## 2. What the table says about the unowned regions

Owned regions at this lane's start: validate head 0x0-0x1800 (w14a104/107/112/113), 660/648 sweep tag sites (w14a111),
the sharing-CPI clone run 0x3c00-0x4800 (w14a114), the curve store 0x4a80-0x5030 (w14a91).

| unowned region | M_oo | rM_oo | sk_oo | what is left |
| --- | ---: | ---: | ---: | --- |
| 0x1800-0x1c00 validate join + prepare_bonding_curve | 57 | 54 | 29 | the original's three-exit target flow (orig 0x1100/0x1800/0x18b0); threehop/jtnodup (#3405, #3435) priced every faithful form at -0.1..-0.4 |
| 0x1c00-0x2600 sweep head (dest PDA, amm frozen, 648/660) | 42 | 29 | 14 | sweep `?` edges: the original threads each Err straight to the exit `jne r7,2,0x5868` with the payload in r9; ours funnels them through the sweep join `jne r7,2,..` + `mov r8,r3` (tailerr #3356 bound < main) |
| 0x2600-0x3c00 TCF clone run | 216 | 97 | 26 | **skeleton is matched**; 119 tokens are register names only, frame masking alone recovers 42. Orig has r6/r7/r9 free over the run (spills them as clone temps); ours keeps a value live in r6 to 0x30a0 and in r9 to 0x2e80 |
| 0x4800-0x4a00 sharing CPI tail | 26 | 26 | 0 | **pure frame**: 21 reloads of the clone-run spill slots (`ldxdw r1,[r10-X]` before the Rc drops) with a different slot permutation |
| 0x5000-0x6c00 event, emit_cpi and the cold wallet/sweep arms | 161 | 85 | 21 | skeleton matched; mostly the function-exit Err payload register (orig r9, ours r8 or r3 + a copy) and its spill slots |

So in every unowned region the skeleton (instruction selection + block structure) is already within 30 tokens of the original
per region. The loss there is register and spill-slot naming that follows from live ranges set elsewhere. w14a84's RA-only bound
(+0.0066 at 27,400, #3419) says those names cannot be fixed by colouring alone.

## 3. Priced region rewrites (raw-IR oracle on ebe5387; none beats main)

Oracle: `tools/cs.sh <name> e/<name>.py <slot>` copies the worktree crate, applies the `EDITS` (exact replacements, line count
and error lines kept), captures the pre-opt IR with an identity build (`capraw.py`) and runs `rx.py` (opt -O3 + llc, as
fastbuild). The unedited capture `m0` reproduces main exactly (`eq_main`, 0.67316, M 2,247, skM 2,810). `tools/q.sh` runs a
list two at a time and `tools/rec.py` records each row (ledger approach `chunkrw15`, keys
`0x22a10-w14-ebe5387-chunkrw15-<trial>-v1`, 28 rows). M = matched masked tokens, skM = skeleton-masked matches (`mm.py`).

| trial | rewrite | bytes | M (Δ) | ratio | skM (Δ) | note |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| rw1 | sweep head sibling style: (dest,_) destructure + require_keys_eq! ConstraintSeeds + amm_frozen as if-expr | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| rw2 | sweep token arm plain ? sequence: create_idempotent(..)?;transfer_vault_tokens(..)?;return Ok(amount) | 27,456 | 2,133 (-114) | 0.63834 | 2,712 (-98) |  |
| rw3 | sweep native arm collect_creator_fee sibling style: let rent=Rent::get()?;let min=..;if amount>0{ensure?;transfer_native?;}Ok(amount) | 27,400 | 1,349 (-898) | 0.40413 | 2,425 (-385) |  |
| rw6 | post-validate tuple join as match (shared,holder){(true,true),(true,false),(false,_)} | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| rw6b | post-validate tuple join with !shared arm first (if !shared{..}else if holder{..}else{..}) | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| rw7 | wallet coin CPI gate as if do_coin | 27,400 | 2,239 (-8) | 0.67076 | 2,811 (+1) |  |
| rw5 | whole sweep clean-room sibling style: rw1+rw2+rw3 | 27,432 | 1,289 (-958) | 0.38593 | 2,347 (-463) |  |
| rw8 | whole sweep clean-room (rw5) + wallet if do_coin | 27,440 | 1,289 (-958) | 0.38587 | 2,348 (-462) |  |
| rw1a | sweep dest check as (dest,_) + require_keys_eq! | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| rw3a | sweep native arm: let rent=Rent::get()?;let min=rent.minimum_balance(0) (no block) | 27,368 | 1,956 (-291) | 0.58633 | 2,473 (-337) |  |
| t1 | t1 (w14a89/w14a109) re-run: shared-arm test new.is_none() | 27,376 | 2,246 (-1) | 0.67316 | 2,807 (-3) |  |
| t1rw7 | t1 + wallet coin CPI gate as if do_coin | 27,376 | 2,241 (-6) | 0.67166 | 2,808 (-2) |  |
| rw7b | wallet coin region: do_coin as if coin_present{!frozen?}else{false} + gate if do_coin | 27,400 | 2,239 (-8) | 0.67076 | 2,811 (+1) |  |
| rw7c | wallet do_coin as if coin_present{!frozen?}else{false} (gate kept coin_present&do_coin) | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| n5 | native arm: Rent::get() as explicit match Ok/Err(e.into()) | 27,352 | 2,221 (-26) | 0.66597 | 2,804 (-6) |  |
| n3 | native arm: amount computed in one block {let min={rent..};lamports.saturating_sub(min)} | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| n8 | native arm: lamports bound to a local before saturating_sub | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| n7 | native arm: Rent::get().map(\|rent\|rent.minimum_balance(0))? | 27,416 | 2,225 (-22) | 0.66637 | 2,805 (-5) |  |
| n9 | native arm: checked_sub(min).unwrap_or(0) instead of saturating_sub | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| ev2 | event sharing_config_reset bound before the sharing match (is_some at the match site) | 27,392 | 2,242 (-5) | 0.67176 | 2,810 (+0) |  |
| ev1 | event: curve fields through let curve=&a.bonding_curve | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| s1 | sweep native test computed after the dest check | 27,392 | 2,225 (-22) | 0.66667 | 2,793 (-17) |  |
| s1b | sweep native test computed after the amm/TCF block, before vsigner | 27,376 | 2,021 (-226) | 0.60572 | 2,788 (-22) |  |
| j1 | drop the Ok::<_,Error>((target,sharing_update,cashback))? hop after the tuple block | 27,400 | 1,838 (-409) | 0.55063 | 2,807 (-3) |  |
| w3 | wallet create_idempotent gate as coin_present\|\|!collection_native | 27,400 | 2,229 (-18) | 0.66777 | 2,789 (-21) |  |
| w4 | wallet coin_present computed before collection_native | 27,408 | 2,209 (-38) | 0.66167 | 2,781 (-29) |  |
| pa1 | pool CPI args passed directly (no pargs tuple): target, curve.is_holder_reward, fee | 27,432 | 2,108 (-139) | 0.63114 | 2,706 (-104) |  |
| k1 | swept as a plain let at the sweep call (no deferred init) | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |

The 28 rewrites fall into three groups:
1. **Folds (10).** rw1, rw1a, rw6, rw6b, rw7c, n3, n8, n9, ev1 and k1 are token-identical to main. In the unowned regions, the
   sibling-style spellings (`(dest,_)`+`require_keys_eq!`, a `match (shared,holder)` tree, `!shared`-first, a scoped `curve`
   binding, a non-deferred `swept`) reach the same MIR/IR.
2. **Cascades (8).** rw2, rw3, rw3a, rw5, rw8, s1b, j1 and pa1 cost 114-958 M, usually for a change of only a few skeleton
   tokens. Two show it most clearly:
   - j1, dropping the `Ok::<_,Error>((..))?` hop, keeps skM within 3 but loses 409 M: frame and RA alone.
   - rw3a, removing the `let min={let rent=..}` block scope, loses 291 M.
   Those two constructs are frame-shaping, not code-shaping. The original's native arm and the hop shape its frame the same way.
3. **Small losses (10).** rw7, rw7b, t1rw7, ev2, n5, n7, s1, w3, w4 and t1 lose 1-38 M. rw7 (`if do_coin`) is the only
   skeleton gain (+1 skM, ours-only -9, orig-only -9), but it loses 8 M through RA: the wallet do_collect flag lives in r8 in the
   original (`mov r8,0/1` at orig 0x5c30/0x5ca0/0x5cb8) and is spilled to `[r10-0x928]` in ours (the w14a35/w14a46 wallet-r8 finding).

## 4. Conclusion

The angle assumed that a large unowned chunk would show a skeleton gap that a clean-room re-derivation could close. On ebe5387 it
does not. Every unowned region already has the original's block outline, branch polarity and call order (sk_oo <= 30 per region,
section 2). The loss there (TCF run 216 M_oo, cold tail 161, join 57, sweep head 42, sharing tail 26) is register and spill-slot
naming, decided by live ranges set in the owned regions and by the frame-shaping constructs above. Region rewrites either fold
or cascade. The skeleton work that remains is in the owned regions: validate 0x0-0x1800 (sk_oo 258) and the sharing clone
run 0x3c00-0x4800 (sk_oo 169).

Next ideas:
- t1 (27,376 B, M 2,246, ratio = main) needs a +24 B fill worth >= +2 M. No unowned-region rewrite here provides it; the
  junk bound (w14a109) is +1.
- The rw7 skeleton gain (+1 skM) is worth testing together with a wallet-r8 RA partner (the do_collect flag kept in a register).
- The 0x4800-0x4a00 sharing-tail chunk is pure frame (26 tokens): 21 reloads of the clone-run spill slots in a different slot
  order. It belongs to the sharing clone-run owner (w14a114).
