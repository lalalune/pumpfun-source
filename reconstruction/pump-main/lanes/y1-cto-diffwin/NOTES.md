# Lane y1-cto-diffwin: admin_cto::execute (0x22a10), minimal-delta bisection

Family: combine source hunks from the open admin_cto candidates (PR #2524, #2528, #2509,
#2515, #2518 and the 63-gene pool of `w10r1-admincto-hillclimb`), one hunk set at a time,
then hill-climb from the best equal-size combination.

## Result

| metric | baseline 0bcf7223c | main 45dbbc019 (#2524 merged) | this branch | original |
| --- | ---: | ---: | ---: | ---: |
| admin_cto bytes | 27,344 | 27,400 | **27,400** | 27,400 |
| target_metric ratio | 0.37637 | 0.36010 | **0.38616** | 1 |
| slots_diff (equal size) | n/a | 3,297 | **3,189** | 0 |
| calls (internal + syscall) | 154 + 3 | 154 + 3 | 154 + 3 | 154 + 3 |
| official normalized / raw | 1032 / 347 | 1033 / 1033 | 1033 / 1033 | 1035 |
| losses vs baseline / vs main | | | 0 / 0 (norm and raw) | |

Unstripped sha256: main `89f80699...`, this branch `9203948e...` (build `fastbuild.py`, identity recipe, no stack warnings).

The window is still unmatched. This branch keeps the original size (so every raw window that
main has stays raw) and moves admin_cto closer than main by both measures.

## Source (admin_cto.rs only, line count unchanged, no `line!()` site moved)

The merged #2524 hunks (validate keys by reference, TransferCreatorFeesToPumpV2 field order) are
replaced by:

1. `to_ifexpr`: `let target=if shared&&!holder{st.creator}else{target};` instead of a `mut target` override.
2. `H_wallet_flags` (#2518): wallet `do_collect` / `do_coin` flags computed before the ATA create.
3. `sweep_native_late`: the sweep's `native` check is computed next to the vault bump, not at sweep entry.
4. `curve_swap_755_756`: `is_cashback_coin` stored before `is_holder_reward` on the curve.
5. `seeds_after_su`, `sweep_frozen_first` (hill-climb genes): +0.0003 each.

Same calls in the same order; behaviour is unchanged.

## What the bisection showed

- Sizes are not additive. On main: A(valref) +96, B(field order) -40, A+B = 27400; to_ifexpr +56,
  H +32, but to_ifexpr+H = +96 and +B makes it +120. Each hunk reshapes the frame, so every
  combination has to be built.
- `validate` keys by reference (A, `validate_keys_ref`, `validate_sharing_ref`) combined with
  `to_ifexpr` collapses the ratio to 0.21-0.25 (a large block-placement flip). The two families
  (#2524 vs to_ifexpr+H) are alternatives, not composable.
- At equal size `slots_diff` saturates (~93% of slots differ from the prologue on), so it barely
  separates candidates; the alignment ratio does. Per-0x800 alignment (tools/region.py) shows orig
  0x2800-0x37ff (the inlined TransferCreatorFeesToPumpV2 account clones and the spills after them)
  matches 0-3 instructions in every variant: that block is placed elsewhere in ours, which is the
  biggest remaining residual and is not moved by any hunk in the pool.
- `with_signer` (C/D), `ql_before_shared` (E) reach 27400 alone but lose ratio (0.33-0.36).

## Files

- `results.tsv`: every built variant (K+ rows are relative to the k6_snl base = 1+2+3, AB+ rows to #2524).
- `tools/hunks.py` (named hunks + `g:<gene>` from `tools/genes1.py`, copied from
  `w10r1-admincto-hillclimb`), `tools/run.sh`, `tools/queue.sh`, `tools/region.py`, `tools/slotb.py`.

Ledger: approach `diffwin`, keys `0x22a10-43daa2043-diffwin-<name>-v1`.
