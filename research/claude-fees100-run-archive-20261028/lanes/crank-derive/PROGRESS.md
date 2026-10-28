# crank-derive PROGRESS (window 147944 crank_donation_fee_pda) — re-derive from the original
Lane dir: RR/lanes/crank-derive. src/ = w584 clone, target/ = warm native.
- 20:55 lane set up.
- Tools: tools/mkvar.py NAME SPEC.py (variant tree v/NAME from src=w584; spec defines CRANK line-248 body, HELPER
  donation.rs 12..51, DATA donation.rs 182..196), tools/run.sh NAME SLOT (nbuild into t$SLOT + score), tools/score.py
  SYMBOLS [--diff masked|raw]. specs/common.py = shared fragments (PRE, MAIN=Codex receiver-direct-mint, HELPER_V07, DATA_ANCHOR).
- 21:10 v08 (crank-b's best, reconstructed from findings on w584): 15976B/1950i masked 0.9641 span 74 raw 0.9533 span 110,
  depth 2168, calls equal, 2 "Nothing to donate" sites. == crank-b's recorded numbers. Starting point.
- 21:25 KEY: llc loop (ir/v08.ll = v08 rustc --emit=llvm-ir; tools/irexp.py BASE.ll EDIT.py TAG; tools/ocmp.py raw compare)
  reproduces rustc crank exactly. IR edit irx/e_unmerge_rentkey.py (re-load rent AccountInfo.key for the infos clone
  instead of reusing the SyncNative meta's GVN-merged key load %_72.i) => crank IDENTICAL to original (raw span 0).
  => Source must stop GVN from merging rent.key loads across pack(): rent must not be a direct noalias `&AccountInfo`
  param of the inlined helper (scope makes pack() provably non-clobbering). R must still be loaded at the call site.
- (clock correction: real times ~21:05-21:14; earlier "21:10/21:25" stamps were estimates)
- 21:13 a3 (helper param rent: &UncheckedAccount, call site &ctx.accounts.rent, infos rent.to_account_info()) and a4
  (helper takes accounts: &mut CrankDonationFeePda, first stmt `let rent: &AccountInfo = accounts.rent.as_ref();`)
  BOTH build the same .so (sha e7781591...): measure gained_normalized [147944], lost []; raw crank body identical.
  a1 (by-value struct of refs) is worse (masked 0.8682).
- 21:14 harvested as RR/shared/harvest/crank-derive-g01 (duplicate confirmation; same sha as crank-brute-g01 which
  closed Crank at 21:08 per DIRECTIVES). Lane STOPPED per DIRECTIVES 21:08.
