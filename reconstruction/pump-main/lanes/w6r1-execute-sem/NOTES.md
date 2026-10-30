# Lane w6r1-execute-sem: 0x22a10 `admin_cto::execute` (assembly-first semantic reconstruction)

Base: origin/main 099b0dd (1027 normalized / 276 raw). Target on base: 27,416 B (orig 27,400), ratio 0.36328, calls 154/3 (= orig).

## Trials

| trial | mechanism | bytes | ratio | normalized/raw | losses | ledger |
|---|---|---:|---:|---|---|---|
| base | origin/main 099b0dd | 27,416 | 0.36328 | 1027/276 | | |
| **t1** | sweep body as nested `fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)` (w4-admincto t1, ported) | 27,424 | **0.36952** | 1027/276 | none (no raw 0xa868 loss on current main) | 50ed472b |
| t2 | t1 + `holder.unwrap_or(false)`, `cashback=!holder&st.cashback` | 27,400 | 0.34871 | 1027/276 | none | ad8c526d |

## Mechanism (t1)

The original reloads `holder_creator_vault.key` in the 648 dest-check error path after the `error!` calls: the
sweep body reads the accounts through `&Context`, not through a closure environment that LLVM marks noalias.
A nested fn taking `&Context<AdminCto>` reproduces the reload.

## IR oracle findings (on t1; llc reproduces t1 exactly)

- brscan on t1: `%330` (648 to_string fmt-failure branch) at 1:1 gives 0.4075; the 648 dest check at 3:2 gives 0.4068.
- The original's sweep exit is not jump-threaded: Ok and Err returns share one tag-check merge (orig 0x3c50/0x3c58, ~10 preds).
  Ours threads Ok returns into `sweep.exit.thread`, and some Err returns into `exit.thread323`.
- Unthreading both into `sweep.exit` (edit in `~/.cache/.../w6r1-execute-sem/edits/unthread.py`) puts the AMM transfer CPI block
  right after the 648 tail, as in the original. On its own it scores 0.3183, because the native/token sweep paths then follow it.
- Unthread plus the native-mint branch (`%317`, quote_mint == native mint) at 3:2 or 1:1 gives **0.4531** (27,496 B). Unthread plus `%_50.i` at 2:3 gives 0.4438.
- No source spelling is known yet that blocks the threading or neutralises the zero heuristic on the native compare. Ledger d552ca4d.
