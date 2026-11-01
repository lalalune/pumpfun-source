# w17a18-cto-stitch17: wave-17 integrator for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Successor of w16a17-cto-stitch16 (#3974). Base: main bf01b5fd9 (0.68005, M 2,270, 3,170 slots), then d5751b26e
(#4011, 0.68065) during the lane. Ledger approach `stitch17`, keys `0x22a10-w17-bf01b5f-stitch17-<name>-v1`.

M is the masked difflib match count of measure.sh: ratio = 2M / (6676 + (bytes - 27400)/8), so +1 M = +0.0003.

## 1. Result: drop the 334 placeholder and repay its 8 B with an ordinary create guard (+1 M)

Two edits on existing lines (no line added, no new steering construct; one `read_volatile` fewer):

- line 334 (validate, fee arm): remove the `read_volatile(holder_key as *const Pubkey as *const u8)` placeholder before
  the `fee_configurable` test (`vol334b`, w15a16 `vol334_back` / w15a03 `m_dv334`). Alone: M +1 at -8 B.
- line 561 (wallet): `if collection_native==false||coin_present{` instead of `if !collection_native||coin_present{`
  (`pcol`, w15a03 `p_colnat`). Alone: M +0 at +8 B. Together they are size-complementary: +1 M at exactly 27,400 B.

| build | admin_cto ratio | M | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| main bf01b5fd9 | 0.68005 | 2,270 | 3,170 | 27,400 | 1034 / 1034 | - |
| bf01b5fd9 + vol334b + pcol (measure.sh, unstripped d67b75c0e8cf2aba) | **0.68035** | 2,271 | 3,183 | 27,400 | 1034 / 1034 | 0 / 0 |
| main d5751b26e (#4011 landed meanwhile) | 0.68065 | 2,272 | 3,170 | 27,400 | 1034 / 1034 | - |
| d5751b26e + vol334b + pcol (merged branch, measure.sh, unstripped 579a64db3a5e152d) | **0.68095** | 2,273 | 3,183 | 27,400 | 1034 / 1034 | 0 / 0 |

Runtime differential on both builds: 388 cases, 0 mismatches. Calls stay 154 / 3.

How it was found: the w16a17 splice translation (`tools/tnew3.py`) of the cached w15/w16 library onto bf01b5f
(393 unique captures, 287 conflict with the w17 shim hunks, 106 translate) priced w15a03's `I_01`
(`vol334_back + p_colnat`) at +1 at 27,400 B, the only translated single above main. The slim pre-opt oracle
(w17a06 `preslim.py` + `fx.py`, `tools/cap.py`) reproduced it on the real source (2,271 @27,400, oracle slots 3,183) and
measure.sh confirmed it.

## 2. Singles on bf01b5f (slim pre-opt oracle; main oracle M 2,270 @27,400, oracle slots 3,169)

| key | edit | M | bytes | dM / dB |
| --- | --- | ---: | ---: | --- |
| m0 | main | 2,270 | 27,400 | reproduces measure.sh (0.68005) |
| kcb | `cashback:read_volatile(&a.bonding_curve.is_cashback_coin)` in the CtoState literal | 1,770 | 27,400 | collapse (not the IR cell's -16 B pin) |
| khe | `holder_enabled:read_volatile(&a.global.is_holder_reward_enabled)` | 2,100 | 27,448 | collapse |
| kacc | shared-arm `ctx.accounts` volatile reload on top of the landed curve-box reload | 2,262 | 27,408 | -8 / +8 |
| crl3 | entry `let cr=a.bonding_curve.creator;cr==a.sharing_config.key()` | 2,270 | 27,472 | 0 / +72 (was +1 on 5998913) |
| g1 | `let creator=st.creator;` before validate, shared-arm `target=creator` (replaces the curve-box reload shim) | 2,272 | 27,544 | +2 / +144 |
| t1n | shared arm tests `new.is_none()` instead of `holder` | 2,268 | 27,344 | -2 / -56 |
| I6n | shared-arm target before `sharing_update` | 2,257 | 27,400 | -13 / 0 |
| vol334b | remove the 334 placeholder | 2,271 | 27,392 | **+1 / -8** |
| vol334b + I6n | | 2,271 | 27,392 | I6n's loss vanishes |
| pcol | `collection_native==false` in the wallet create guard | 2,270 | 27,408 | 0 / +8 |
| a1 | sweep reads the token amount before the frozen flag | 2,270 | 27,376 | **0 / -24 (free repay knob)** |
| **I01** | **vol334b + pcol** | **2,271** | **27,400** | **+1 / 0** |
| I01 + vol338b | also remove the 338 placeholder | 2,246 | 27,392 | -25 / -8 vs I01 |
| I01 + wlwe | `is_writable==false` | 2,268 | 27,408 | -3 / +8 vs I01 |

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `cap.py <name> <genes> <slot>`: copy a pristine base crate, apply `genes17.py` genes (line count checked), capture
  pre-opt IR (capraw), preslim, fx; appends M/bytes/oracle slots to `res/cap.jsonl`. About 30-75 s per capture under
  load (the first capture in a work dir compiles the dependencies).
- `runq2.py <queue> [workers] [slot0]`: dynamic capture queue (re-read on every pop; `STOP` file pauses it).
- `genes17.py`: the library genes re-spelled for the shim-era source (bf01b5f/d5751b2).
- `tnew3.py`: w16a17 splice translation of the cached library onto the current baseline.
- `pairs18.py`: the same with cached `splice.Var`s, so size-complementary pairs/triples need no difflib.
- `rec.py`: ledger rows for every capture.
