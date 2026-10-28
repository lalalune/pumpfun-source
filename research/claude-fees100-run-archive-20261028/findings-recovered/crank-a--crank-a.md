# recovered from the transcript of lane crank-a (crank-a.md); entries in order

# crank-a findings (window 147944 crank_donation_fee_pda)

Lane dir: R/lanes/crank-a. Tools: R/lanes/crank-a/tools/{crankstat.py,runvar.sh}. Variant include files: R/lanes/crank-a/inc/.
Metrics: insns/bytes of candidate crank, depth = deepest r10 offset (<4000), ratio_mask = fndiff masked ratio,
ratio_rawstack = ratio keeping stack offsets (branch targets masked), calls_ratio over ordered call list.
Original: 1950 insns / 15976 B / depth 2168.

## E1 baseline w582 (native): 1862 insns, depth 2512, ratio_mask 0.6348.
## E2 Codex safe-context body ported onto w582 (src-safe; include! of fee-sharing/crank_donation_fee_pda.rs, exact sha b8c834db...)
- builds, measure 578 native (= baseline), lost_normalized=[], raw unchanged.
- crank 1915 insns / 15664 B, depth 2592, ratio_mask 0.6701; ordered call list differs from original ONLY in
  exchange_malloc (cand) vs inlined bump alloc + handle_alloc_error (orig) for the 3-meta SyncNative vec!.

## E3 WHY exchange_malloc is not inlined (measured with -Cremark=inline -Zremark-dir and -Cllvm-args=-print-bfi)
- remark: `exchange_malloc TooCostly cost=45 threshold=45` -> the vec! call site is COLD (inlinecold threshold 45,
  bonuses disabled). The later emit_cpi vec! site inlines exchange_malloc at threshold 325 (hot).
- BFI of the vec! block at decision time = 0.01373 of entry (< 2% ColdCallSiteRelFreq):
  0.5 (disable&8, pow2 mask -> no heuristic) x 0.375 (memcmp==0, lib-call zero heuristic) x 0.375 (Rent::get Ok tag==0)
  x 0.5 (balance>minimum) x 0.625 (inlined sub_lamports) x 0.625 (inlined add_lamports) = 0.01373.
  Needs a factor >= 1.457 to become non-cold (=> exchange_malloc AND a plain Account::reload() would inline).
- Same cold-site mechanism explains why plain `donation_fee_pda_ata.reload()` stays outlined (no LastCallToStatic bonus at cold sites).

## E4 A1: transfer+sync+reload moved into a plain nested helper fn (called from the native block)
- exchange_malloc inlined (alloc callee fixed: 0 exchange_malloc, 2 handle_alloc_error), plain reload() inlined too,
  1931 insns, but block layout reorders (calls_ratio 0.974 -> 0.769), depth unchanged 2592. Rejected as-is.


## E5 KEY RESULT: native block as an ordinary (non-annotated) helper fn => natural code everywhere
Variant N1e (inc/N1e.rs, generator tools/gen2.py): native-SOL block moved into a nested plain `fn wrap_native(accounts: &mut CrankDonationFeePda) -> Result<Option<u64>>`
(includes the inner "Nothing to donate" check, returns Ok(None)), called as `if wrap_native(ctx.accounts)?.is_none() { return Ok(()); }`;
inside it NATURAL code: `to_account_info()`, `donation.clone()`, `invoke(&Instruction{..vec![..]..}, &[ata.to_account_info(), rent.to_account_info(), donation.clone()])?`,
PLAIN `accounts.donation_fee_pda_ata.reload()?` (no inline(always), no patched anchor, no struct-literal clones);
plus direct receiver `DonatePubkeyConfigIdWithPayerV1{..}.invoke_signed(..)` and direct mint condition.
- measure 578 native, lost_normalized=[]; crank: ORDERED CALL LIST == ORIGINAL (calls_ratio 1.0, exchange_malloc inlined),
  1963 insns (orig 1950), depth 2152 (orig 2168), ratio_mask 0.7851 (safe-context 0.6701).
- Why: inside the helper the vec!/reload sites are hot (BFI computed relative to helper entry), so exchange_malloc,
  AccountInfo::clone and Account::reload inline there; the helper itself is inlined into crank (hot site, LastCallToStatic).
  Its allocas land at the TOP of crank's frame (inlined allocas go to entry-block start) = the original's frame order
  (donation clone -280, Rent -232, reload copies -120/-160 are the shallowest objects in the original).
- N1 (ix as `let` in the if-block) is worse (calls_ratio 0.95, depth 2200): ix must die before reload (ix merges into reload copy slot in orig).
- N0e (no helper, same natural code) collapses: cold sites => outlined clones/exchange_malloc, 41 calls.


## E6 N2r = N1e + named `let rent=Rent::get()?; let minimum=rent.minimum_balance(218);` inside the helper
- depth 2168 == ORIGINAL, calls_ratio 1.0, ratio_mask 0.8122, ratio_rawstack 0.7048 (stack offsets now largely aligned), 1963 insns (+13).
- The named Rent value lives to the helper's end, so it no longer merges into the 120-B reload copy slot; it becomes the
  original's -232 slot (which also absorbs the seeds bump byte). N2x (`excess>0`) == N1e (InstCombine folds it).
- Remaining diff classes: accounts ptr in r7 (orig r8) / amount r8 (orig r7) permutation; original loads rent info ptr
  ([r8+656]) before Rent::get and keeps it in r6; Rent::get error path in orig drops the donation clone inline;
  disabled-path return tail-duplicated in orig; event creator copy (cand copies state.creator).


## E7 frame + helper-protocol experiments (all measure 578, lost=[])
- N3c (= N2r + event `creator` local): frame live-slot table IDENTICAL to original (-120/-160/-184/-208/-232/-280/-304/
  -928 receiver/-992 seeds/-1096 args/-1128/-1160/-1192), 1961 insns, ratio_mask 0.8371, rawstack 0.7308.
- P1u (donation clone in crank, Rent+transfer in helper(&donation, &mut ata, &UncheckedAccount rent)): 1952 insns, mask 0.859, raw 0.686; frame also exact.
- H1 (helper returns Result<bool>, `if !sync_native(ctx.accounts)? {return Ok(())}`): 1959 insns, mask 0.8534, raw 0.7465 (best raw).
- H3/H4/H5 (Result<u64>, Ok(0) sentinel, Option<Result<()>>+try): worse layout (calls_ratio 0.67-0.86).
- D0 (crank-direct natural code, no helper): cold => 41 calls, 1704 insns. D1 = D0 + core::intrinsics::unlikely(disable):
  BYTE-IDENTICAL to D0 (no !prof emitted; unlikely is a no-op for branch weights in this toolchain).
- H2a (#[inline(always)] helper): cold like D0 (always-inline happens before the helper's own callees are inlined).
- Residual vs original in helper variants: (1) after the shared donation-drop block the helper result is re-dispatched
  (orig: drop -> return directly; i.e. orig's Rent/invoke `?` and the native "Nothing to donate" return look crank-level),
  (2) accounts ptr r7 vs r8 register permutation, (3) orig loads rent info ptr ([r8+656]) before Rent::get.