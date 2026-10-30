# FINDINGS — window attribution (kept findings, corrections, experiment matrix)

All measurements below were taken on the pre-#1191 qualification candidate
(Pump `0f50faa8…`, AMM `86dbc2c6…`) with the repository window metric
(`scripts/window_measure.py`, candidate symbol build). Findings marked
*superseded* no longer describe current main.

## 1. Metric-neutral symbol pairs (validated)

`transfer_to_user` / `transfer_to_recipient` and `transfer_from_user` /
`transfer_from_recipient` compile to **identical normalized bytes**; only
relocation-backed operands differ. Exchanging their call sites is therefore
invisible to the window metric: it cannot gain or lose a window. This is a
useful negative constraint for future reconstruction attempts.

## 2. Call graph among the target windows (validated, with caveat)

The 16 unmatched Pump windows of the snapshot are whole function bodies called
from the Anchor dispatcher at `0x11b758`; 96 baked `(path,line,code)` tuples
identify their modules (`create_v2`, `admin_cto`, `migrate_v2` helper,
`multi_hop_swap`, `sell`, `sweep`, `claim_token_incentives`, `sell_v2`,
`buy_v2`×2, `trade_v3`×3 + 2 helpers, legacy `buy_exact_sol_in`).

Helper dependency measured among them: `0x147ba0` calls `0x80df8`, and
`0x1489f8` calls `0x83c00` (the two `trade_v3` helpers
`v3_buy_costs` / `v3_execute_buy`, see §4). **Caveat (correction):** call
immediates are masked by the metric, so closing a helper does *not* by itself
prove the caller windows will match; the dependency is real, the cascade is
not established.

## 3. Experiment matrix (negative methodology evidence, pre-#1191 snapshot)

Measured one edit at a time, deterministic Linux rebuild, repo metric against
the symbol build. Full patches and per-variant measurements are in the PR #1172
branch.

| # | Target | Edit class | Measured effect | Verdict |
|---|---|---|---|---|
| 1 | Pump `0x14f4e0` | early-return spelling of a guard (v1) | −200 B (unfaithful: `require_gt!` carries `.with_values`) | rejected |
| 2 | Pump `0x14f4e0` | inverted `if cond {} else {}` vs `if !cond {}` (v1c/v1d) | byte-identical output | LLVM canonicalizes condition inversions |
| 3 | Pump `0x14f4e0` | inverted guard at line 92 (v2c/v3c) | −8 B, further from target | no effect on target encodings |
| 4 | Pump `0x14f4e0` | `#[inline(never)]` / attribute removal (a1/a3) | one identical binary; **loses 5 matched windows** | `#[inline]` is load-bearing elsewhere |
| 5 | Pump `0x14f4e0` | `#[cold]` variant (a2) | loses 6 windows | rejected |
| 6 | Pump `0x14f4e0` | `#[inline(always)]` (a4) | keeps 1,019; further from target | no effect |
| 7 | Pump `0x14f4e0` | cold error-arm helpers (e1/e3) | adds a call absent from the deployed (callee multiset already equal) | structurally incompatible |
| 8 | Pump `0x14f4e0` | cold pass-through helper (e2) | byte-identical output | eliminated by LLVM |
| 9 | Pump helpers | `and_then` → equivalent `match` (g1) | byte-identical output | MIR canonicalizes |
| 10 | AMM `0x4c750` | 10 frontend condition rewrites (v1–v12, ctl) | v1/v2/v4/v5/v7/v9/v10 byte-identical; v12 perturbs layout (raw 784→257); ctl confirms loop; **v8 environment-dependent** (our build identical, maintainer rebuild 9,032 B) | frontend canonicalizes condition forms |
| 11 | AMM `0x4c750` | `#[cold] #[inline(never)]` error-arm helper (a1) | arm outlined **outside** the 9,024-byte window (tuple preserved at `0x11bd30`) | excluded by target size |
| 12 | AMM `0x4c750` | `#[inline(always)]` / check helper (a2/a3) | byte-identical output | no-ops |
| 13 | AMM `0x4c750` | `#[cold]` on `fn cashback` (a4) | caller window `0x49b50` lost (783/785) | rejected |
| 14 | AMM `0x4c750` | conversion respellings of `try_borrow_data` (c1/c2) | target encoding `jeqr+ja` never emitted | encoding follows block order, not control-flow form |
| 15 | AMM `0x4c750` | combined (a1c1) | size mismatch | rejected |

*Superseded:* the matrix only proves that these source shapes and attributes
cannot reach the snapshot targets. #1191 (Pump) and #1195/#1205 (AMM) have
since closed those targets by other source changes.

## 4. Helper-body classification (`0x80df8`, `0x83c00`) — measured

| Window | Symbol | Deployed / candidate bytes | Δ | Tuples | Norm. multiset D/C | Opcodes only in D | Stack symdiff |
|---|---|---:|---:|---|---:|---|---:|
| `0x80df8` | `trade::v3_buy_costs` | 2,120 / 2,056 | −64 | equal (371, 375) | 48 / 40 | `ja`, `call`, `ldxdw`, `stxw`, 4×`stxdw` | 2 |
| `0x83c00` | `trade::v3_execute_buy` | 3,440 / 3,408 | −32 | equal (691) | 107 / 103 | 3×`ldxdw`, `mov64` | 13 |

Classification: **intra-body error-block duplication/sharing plus register
allocation** — not pure block ordering (sizes and instruction contents differ),
not sub-function decomposition (callee multisets and `9999`/`10000` constants
identical). Deployed-only blocks recorded (e.g. `D[59:75]` 16 instructions vs
`C[60:62]` 2). No source form is proven to reproduce this shape on that
snapshot.

## 5. AMM gap framing — corrected

The snapshot gap for `0x4c750` had **two** independent causes (our earlier
"one block-placement decision" framing is withdrawn):

1. the borrow-test fold at sell+0xd00 — 10 relocation rows uniformly −0x8;
   fixed upstream by respelling the line-444 owner check (**#1195**);
2. the line-467 cold-queue reorder (error arm at `0x4e718` deployed vs inlined
   candidate) — resolved upstream (**#1205**).

Current main: AMM **785/785 raw-equal**, whole meaningful ELF equal.
