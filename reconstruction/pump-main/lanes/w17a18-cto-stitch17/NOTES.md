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

## 3. Re-price after #4018 (w17a15 passthrough shims): the I01 pair now costs 6 M, so it is reverted (+6 M)

#4018 was measured by its lane on d5751b2 (without I01) at **0.68424** (M 2,284). land.py merged it onto 445fe14
(with I01) and measured 0.68244 (M 2,278), which was still closer than 0.68095, so it landed. On the shim-era main the
two I01 edits now interact with the passthrough shims:

| key (slim oracle on main 8330455) | edit | M | bytes |
| --- | --- | ---: | ---: |
| m0f | main 8330455 | 2,278 | 27,400 |
| unpcolf | `!collection_native` again | 2,283 | 27,392 |
| re334f | the 334 `holder_key` byte-read placeholder again (now marked `/*shim:*/`) | 2,279 | 27,408 |
| **unI01f** | **both** | **2,284** | **27,400** |

measure.sh on 8330455 + unI01f: **0.68424**, 3,313 slots, 27,400 B, 1034 / 1034, zero losses, unstripped
a950162cc7d5201c (byte-identical to w17a15's merged build on d5751b2). Differential 388 / 0. The placeholder comes
back as a marked shim (forcing +1, land with `--allow-forcing`).

**Landed: #4019 (merge ac37d7415):** 0.68244 -> 0.68424, 3,313 slots, zero losses, forcing_delta +1, differential 388/0.

## 4. Leave-one-out re-pricing of the landed shims on ac37d74 (`tools/loo.py`)

Every landing re-shuffles the near-tie landscape, so an earlier landing can turn neutral or harmful once later ones
are in (section 3 is one such case). `tools/loo.py N` builds, for each of the last N first-parent landings that touched
admin_cto.rs, a gene that reverts only that landing's changed segment on each changed line (common prefix/suffix
trimmed, with enough context to be unique on the current text); `looNNNN_k` reverts only its k-th changed line.
Slim oracle on main ac37d74 (M 2,284, oracle slots 3,312):

| revert | M | bytes | note |
| --- | ---: | ---: | --- |
| #3985 weighted pump_creator_vault_ata data clone (`rcincq`) | 2,284 | 27,400 | **byte-identical to main: the shim is now inert -> peeled** |
| #4018 site 298 (`pt1(3,new.is_some())`) | 2,284 | 27,392 | free -8 B knob (0 M) |
| #3936 sweep program-clone owner `read_volatile` pin | 2,284 | 27,400 | tie, different bytes, same slots |
| #3495 shared test as `creator==sk` key local | 2,284 | 27,400 | tie, different bytes |
| #3993 `sweep(&ctx,holder_key)` borrow | 2,284 | 27,400 | byte-identical (not a shim) |
| #4018 site 339 (`ptp(1,..)` on the shared-arm reload) | 2,282 | 27,408 | |
| #4018 sites 578 / 659 (`pt8` do_coin, `pt1` executable) | 2,279 | 27,400 | the two +5 cells still pay |
| #4011 sharing_config owner in the Rc increment | 2,282 | 27,400 | |
| #4000 owner-first pool gate | 2,283 | 27,400 | |
| #3992 default-quote weight / curve-box reload at the creator store | 2,283 @27,408 / 2,280 @27,392 | | |
| #3991 / #3969 / #3950 / #3934 weighted clones and the 312 expect_p | 2,282 / 2,273 / 2,278 / 2,274 | | still pay |
| #3666 CtoState fee_configurable first | 2,283 | 27,400 | |
| #3386 fee-Some exit edge | 2,257 | 27,400 | |

The free -8 B knob (revert the 298 passthrough) was paired with 17 +8 B partners (second placeholder copies at
284/289/296/306/307/314/326/330/338, wlwe, mapamt, the #3992 weight, pcol, gwclk, cb5, cumatch, shfk) and with
passthroughs of the accounts pointer at the CtoState loads and the shared owner test (`ptsh`, `ptmf`, `ptmy`, ...).
Best: ties at 2,284 (p2_284 / p2_289 / ptmf at 3,311 oracle slots, one fewer than main); nothing above main.

**Peel landed: #4025 (merge 8350fae5a):** the #3985 weighted data clone reverted, whole unstripped ELF identical
(a950162cc7d5201c), forcing_delta 0, differential 388/0.

## 5. LOO on 4d09af4 (#4026 passthrough-2, M 2,287) and on 2f3597f (#4040 lifetime shim, M 2,291)

On 4d09af4 three reverts turn into knobs: removing the 334 placeholder (`loo4019_0`) is +1 M at -8 B again, the
#4026 312 compare-byte passthrough revert is +1 M at -8 B, and the #4026 shared-owner/max_fee `ptp` pair revert is 0 M
at -16 B. The 298 passthrough revert stays a free -8 B knob. Paired with 8 B partners (slim oracle, main 2,287):

| composite | M | bytes | oracle slots |
| --- | ---: | ---: | ---: |
| remove the 334 placeholder + a placeholder copy before 284 (= the placeholder moved to the top of validate) | **2,288** | 27,400 | 3,095 |
| same, copy before 289 | 2,288 | 27,400 | 3,095 |
| revert the 312 compare-byte pt + placeholder before 284 / 289 | 2,288 | 27,400 | 3,095 |
| either +1 revert + placeholder before 306 / 307 / 338 | 2,287 | 27,400 | 3,091-3,093 |
| either + placeholder before 296 | 1,439 | 27,424 | collapse |
| both +1 reverts (-16 B) + w17a08 fence A (+16 B) | 2,284 | 27,400 | |

The move holds on 2f3597f (#4040): 2,292 @27,400 against main 2,291 (the 334 removal alone is 2,292 @27,392).
measure.sh on 2f3597f (programs = 638fce2): **0.68634 -> 0.68664**, 3,096 slots, 27,400 B, 1034 / 1034, zero losses,
unstripped 678b0ba01d847c33; differential 388 / 0. The placeholder count is unchanged (forcing delta 0).

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `cap.py <name> <genes> <slot>`: copy a pristine base crate, apply `genes17.py` genes (line count checked), capture
  pre-opt IR (capraw), preslim, fx; appends M/bytes/oracle slots to `res/cap.jsonl`. About 30-75 s per capture under
  load (the first capture in a work dir compiles the dependencies).
- `runq2.py <queue> [workers] [slot0]`: dynamic capture queue (re-read on every pop; `STOP` file pauses it).
- `genes17.py`: the library genes re-spelled for the shim-era source (bf01b5f/d5751b2).
- `tnew3.py`: w16a17 splice translation of the cached library onto the current baseline.
- `pairs18.py`: the same with cached `splice.Var`s, so size-complementary pairs/triples need no difflib.
- `rec.py`: ledger rows for every capture.
