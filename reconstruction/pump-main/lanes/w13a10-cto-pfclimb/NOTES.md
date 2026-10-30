# Lane w13a10-cto-pfclimb (wave 13): pf-guided hill-climb of admin_cto::execute

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 3912c47ac (admin_cto 0.48772 / 3,273 slots, pf 0.59916).

## Method

- `scripts/pfboard.py` (copied from w12a02-cto-iroracle-3, with its `ctoracle.py`/`framebound.py` deps) ranked 239 cached
  w12/w13 admin_cto builds by heuristic perfect-frame score `pf`. The top real-size family was w12a07-cto-sweepthread
  `n_skip_vsig` (pf 0.6146, ratio 0.49035 at 27,440 B on main 1905fba): it was never landed because it was 40 B too big.
- Hill-climb engine: w12a14-cto-hillclimb `hc12.py` (gene = exact newline-preserving substitutions), re-pointed at main
  3912c47, recording `pf` for every build next to ratio/bytes/slots. Genes: w12a07 sweepthread variants (`s7_*`), the
  w12a14 library (120 still apply on top of skip+vsig) and new gate/binding genes (`n_*`).

## Result (landable step 1)

| build | bytes | ratio | slots | pf | norm/raw |
| --- | ---: | ---: | ---: | ---: | --- |
| main 3912c47 | 27,400 | 0.48772 | 3,273 | 0.59916 | 1034/1034 |
| + skip tree + vsigner (w12a07 n_skip_vsig) | 27,440 | 0.49065 | | 0.61488 | 1034/347 |
| + gate `if !skip{sweep(..)}else{Ok(0)}?` (`n_gate_mapor`) | 27,432 | 0.49102 | | 0.61527 | 1034/347 |
| + `bump` before `old` in the sweep seeds | **27,400** | **0.48951** | 3,303 | 0.61474 | **1034/1034, 0 losses** |

Runtime differential: 363/363 cases match. Unstripped sha 4de947501b4f87f3.

Source changes:
1. The sharing tree also yields `skip` (a phi of constants: false only on shared&&holder), and the sweep gate tests it, as
   the original gates the sweep on one spilled phi-of-constants flag.
2. `let vsigner:&[&[&[u8]];1]=&[vaultseeds];` bound once with the seeds and passed to both transfers.
3. Gate as `if !skip{sweep(&ctx,&holder_key)}else{Ok(0)}?` (Result-valued if, one `?`): -8 B and +0.0004 vs `.then().transpose()`.
   The `if skip{0}else{sweep(..)?}` / `match skip` forms are 0.41264 (Err-return block moves).
4. `let bump=..;let old=..` order: -32 B, the size companion.

Ledger: approach `pf-hillclimb`, keys `0x22a10-w13-3912c47-hc-<variant sha12>-v1`.

## Step 1 outcome

PR #2888 was closed elsewhere. Its Result-valued gate (`n_gate_mapor`) reached main through #2892 (w13a11-cto-stitch-2, 0.49071).

## Step 2 (branch swarm/w13a10-cto-pfclimb-2, base main 4394685: 0.49071 / 3,313 slots, pf 0.61534)

The single-gene screen on 4394685 (141 genes, results in the ledger) gave these useful deltas:

| gene | bytes | ratio | pf |
| --- | ---: | ---: | ---: |
| `m_oldbump` (`old` before `bump` again) | +32 | 0.49162 | 0.61557 |
| `m_ev_hr_curve` (event `is_holder_reward:a.bonding_curve.is_holder_reward`) | -8 | 0.49109 | 0.61603 |
| `cashback_rev` (`let cashback=st.cashback&&!holder;`) | +8 | 0.49064 | 0.61525 |
| `m_tree_co_rev` (collect_old operands swapped) | -40 | 0.48209 | **0.6164** |
| `m_oldbump`+`m_ev_hr_curve` | +24 | 0.49169 | 0.61566 |
| **`m_ev_hr_curve`+`cashback_rev`** | **0** | **0.49101** | 0.61594 |

The last row is landable: 27,400 B, 3,280 slots, 0 losses, 1034/1034, and the runtime differential matches all 363 cases.
