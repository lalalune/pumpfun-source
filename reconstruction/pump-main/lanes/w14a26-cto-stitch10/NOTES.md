# w14a26-cto-stitch10: integrator lane for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Ledger approach `stitch10`, keys `0x22a10-w14-<main7>-stitch10-<variant>-v1`.

## Step 1 (stack #3267 + #3272)

Already done on main before this lane started: #3272 (w14a23-cto-tcflit, mechanism from #3260 w14a18-cto-vaultata) and
#3267 (w14a20-cto-reloadarm) landed back to back as 7e6aa9c (0.6414, 3,174 slots). This lane reproduced 0.6414 with
`measure.sh` (`main` row). #3281 (w14a24-cto-walletlit) then took main to d2d1875 (0.6417, 3,173).

## Result (on main d2d1875)

| build | bytes | ratio | slots | norm/raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main d2d1875 | 27,400 | 0.6417 | 3,173 | 1034/1034 | |
| `ev_hr_local + cu_iflet` | 27,400 | **0.6423** | 3,173 | 1034/1034 | none |

Same pair on main 7e6aa9c: 0.6414 -> 0.6420 (`p_hr_cuif`). Two tail knobs that each change size by 8 B:
- `ev_hr_local` (+8 B): the event's `is_holder_reward:holder` instead of `a.bonding_curve.is_holder_reward`
  (#3267 had switched it to the curve read to pay for its event_authority reloads).
- `cu_iflet` (-8 B): curve update `if let Some(f)=fee{curve.creator_fee_bps=f;}` instead of
  `fee.unwrap_or(curve.creator_fee_bps)` (#3257 had switched it the other way).
With #3267's event_authority reload form in place, this pair (the pre-#3257 tail) beats both single forms.

## Screens on 7e6aa9c (measure.sh, `genes.py` / `run.py` in this folder)

- (a) sibclone subset (`tai_*` = plain `to_account_info()` in the sharing CPI): pa 0.63841, gl 0.63481, pa+gl 0.63541
  (all 27,400); ea 0.62159 @27,352, mi 0.6276 @27,376, pa+ea 0.62599 @27,360, gl+ea 0.62189, pa+gl+ea 0.62749 @27,360.
  `ea_xbind` (back to the `let x=&*..` form) 0.6373 @27,392. **Dead on the stack.**
- (b) field orders (43 variants: LKDORSWE, KLDORSWE, kL, kD, kF and every adjacent swap on pa, gl, mi, ea).
  Best are ties at 0.6414: gl `WSRLDOEK`, gl `SWRLDOKE`, ea `DLKORSWE`. Nothing beats main.
- (c) tail knobs, singles: pu_amm_key 0.64071, ev_auth_deref = main, ev_ts_map = main, ev_ts_clockvar 0.63841,
  cu_oldunwrap 0.63781, ev_nf_unwrap 0.63301 (all 27,400). Size knobs: pu_amm_keyfn +80 B, ev_mint_key +16,
  ev_cb_local +8, ev_hr_local +8, pargs_hr_local +24, pargs_tgt_curve +160, ev_nc_target +72, ev_nf_inline -24,
  ev_ts_prepool -16, cu_iflet -8, nf_old -8, ea_xbind -8, tai_ea -48, tai_mi -24.
- size-balanced pairs: **hr+cuif 0.6420**, cb+cuif 0.6411, hr+eax 0.63871, cb+eax 0.63781, cb+nfold 0.63751,
  mk+tsp 0.61564 (all 27,400).

## Landing 2 (branch swarm/w14a26-cto-stitch10-2): #3277's sharing authority clone on the stack

#3277 (w14a24-cto-shareauth, by kutluhaneth46) writes the sharing CPI `authority` as an explicit clone with the two Rc
clones bound first: `{let x=..as_ref();let lamports=x.lamports.clone();let data=x.data.clone();AccountInfo{rent_epoch,owner,lamports,key,is_writable,is_signer,executable,data}}`.
It measured 0.6414 -> 0.6426 on 7e6aa9c. Re-verified on the stack:

| base | main | + sh_auth |
| --- | ---: | ---: |
| f100a59 (#3287) | 0.6423 | 0.6435 |
| ca03a2b (#3289) | 0.6432 | **0.6444** (3,173 slots, 27,400 B, 0 losses) |

On f100a59, sh_auth with the old tail (ev_hr_curve + cu_unwrapcur) is 0.6429 and with ev_hr_curve + ev_cb_local 0.6426,
so #3287's tail and sh_auth add.

AdminCtoEvent literal evaluation order (f100a59): moving timestamp last +256 B (0.49761), timestamp after bonding_curve
+200 B, bonding_curve first +72 B, mint first +64 B. Every reorder of the event literal grows the function.

## Rc-locals-first clone class (#3277's form) on every other CPI account (main b2e90aa, 0.6444)

`lf_<acct>` = `{let x:&AccountInfo=<acct>.as_ref();let lamports=x.lamports.clone();let data=x.data.clone();AccountInfo{..}}`
(`_R` = field order ROLKWSED as in #3277, `_dl` = data clone bound first). Gene `lfx_<site>_<field>` applies it to a
`to_account_info()` field of another CPI.

- Sharing CPI: pa -32 B (0.63549), gl +24 B (0.63782; `_R` 0 B 0.63721), mi -24 B (0.6339), ea -8 B (0.6394),
  sharing_config +8 B (0.62333), program +8 B (0.64191, `_dl` 0.6425), CpiContext program -16 B (0.62242).
  Size-balanced pairs are all below main: prdl+hr_curve 0.6441, ea+cuunwrap 0.6405, ea+cb 0.63901, mi+gl 0.62193.
  Sizes are not additive (ea + pr_dl = -24 B, not 0).
- Authority read order inside the locals form: ROKLWSED, RLOKWSED, LDROKWSE, ROKWSELD, ROLKWSDE, ROLWKSED tie main
  (0.6444; one distinct sha); ORLKWSED 0.6408, ROLKSWED/ROLKWESD 0.6429, KLDORSWE/LKDORSWE 0.6393, data-first 0.6393.
- TCF (sweep), wallet create_idempotent, collect_coin_creator_fee, pool CPI and sweep create_idempotent fields: every
  site loses (0.33-0.63; the wallet/pool/holder-vault sites grow by 370-700 B). The class only pays on the sharing authority.

## Zero-size knob re-screen on b2e90aa

AdminCtoEvent literal moves that keep size (old first, cashback last, flags first, holder/cashback swap, new_creator/holder
swap) are byte-identical to main (same sha). The others lose: authority last 0.63361, bonding_curve last 0.63751, new_creator
last 0.63751, authority/bonding_curve swap 0.63421, timestamp/authority swap +64 B. pu_amm_key 0.6437, cu_iflet_old 0.6432,
cu_fee_first 0.6414, ev_ts_clockvar 0.6414, tai_pa 0.63601, gl WSRLDOEK 0.63841 (all 27,400 B, below 0.6444).

## Curve-store and tail statement order (main 65df90f, 0.6453)

Curve update stores (creator, cashback, holder, fee, can_edit), adjacent swaps: (creator,cashback) 0.6441,
(cashback,holder) +8 B 0.64041, (holder,fee) 0.6447, (fee,can_edit) 0.645; can_edit first 0.6441, reversed 0.6423,
creator last +8 B 0.63771. None above main. `old_fee` read before `old_creator` 0.6441. Tail statements
`nf` / `pool_updated` / `pargs` in any other order grow 16-56 B (0.638-0.6416). `nf` read just before the event:
-16 B (0.64429 @27,384); with +16 B partners (ev_cb_local + cu_unwrapcur, lf_pr_dl + ev_cb_local) 0.6447 at 27,400 on
06967d3 (main 0.64649), slots 3,163/3,167 against main's 3,170.

## v7c (w14a21 validate closure) size repay with tail knobs (main 06967d3, 0.64649)

v7c alone: +32 B, 0.63204. Repaid to 27,400 B with tail knobs: lf_pa + ev_hr_curve 0.62193 (3,133 slots, 37 fewer
than main), tl_nf_late + tai_mi 0.62073 (3,140), tl_nf_late + lf_mi 0.62043, tai_mi + ev_ts_prepool 0.60485.
Tail repay recovers slots but not ratio: the 32 B must come out before the sharing region, not after it.

## Sweep native arm vs the original (for the threading residual)

Original (orig 0x28448-0x28548): every native-arm exit jumps back to ONE join at orig 0x26660, which also takes the
token arm's fallthrough and tests the tag once (`jne r7,0x2,+0x380`):
- amount==0: `mov r7,2; jgt r0,r3,+1; ja join`;
- ensure_rent_exempt Err: `jne r1,0x2,+0x10a` forward to a cold 3-insn block (`ldxdw r9,[..-0x838]; mov r7,r1; ja join`);
- transfer_native Ok: `mov r9,r6; jeq r1,2,join`; Err: `ldxdw r9,[..-0x848]; mov r7,r1; ja join`.
Main instead joins the native arm locally (payload through a stack slot), re-tests the tag there
(`jne r7,2 -> Err; ja Ok`) and sends the ensure_rent_exempt Err straight to the token arm's tag test with the payload
load hoisted above the branch (`jeq r1,2,+1; ja`). The constant Ok tags are threaded; the original's are not.
