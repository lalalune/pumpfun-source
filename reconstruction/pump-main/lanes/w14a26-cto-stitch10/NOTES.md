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
