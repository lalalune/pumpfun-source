# crank-brute-g01 — Crank 147944 (crank_donation_fee_pda) MATCHED (native, repo normalizer)

Base: RR/shared/frontier/w584. Files: programs/pump-fees/src/{lib.rs,donation.rs} (src/ + source.patch, patch verified to
apply to w584 and reproduce src/). Native build: RR/shared/tools/nbuild.sh -> native-symbols.so.

## Result
- measure.py vs native w584: normalized 580 -> 581, gained_normalized [147944], lost_normalized [] (no loss).
  unmatched_original is now empty except windows already unmatched natively (see measure.json).
- fndiff 147944: 1950/1950 insns, 15976 B; the ONLY 3 differing lines are rodata *preview text* of lddw pointers
  ("Nothing to donate" x2 and "__event_authority" — the bytes AFTER the string differ because native rodata order
  differs). Under the repo normalizer (lddw/call imm masked) the body is identical -> gained 147944.
  A Linux/ordered.ld build is needed for the whole-ELF check (elfinv).

## Source (what)
= crank-b's v08 (previous round; reconstructed from its transcript) + ONE change:
the native helper takes the rent account as `&UncheckedAccount<'info>` (call site `&ctx.accounts.rent`) instead of
`&AccountInfo<'info>` (`ctx.accounts.rent.as_ref()`), and clones it with `rent.to_account_info()`.
- handler (lib.rs:248): native arm `let donation=ctx.accounts.donation_fee_pda.to_account_info();
  match crate::donation::sync_native_excess(&donation,&mut ctx.accounts.donation_fee_pda_ata,&ctx.accounts.rent)?
  { Some(amount)=>amount, None=>return Ok(()) }`; non-native arm: amount + "Nothing to donate"; direct relay receiver.
- helper (donation.rs, plain fn, no attributes) `sync_native_excess(donation:&AccountInfo, ata:&mut Account<TokenAccount>,
  rent:&UncheckedAccount) -> Result<Option<u64>>`: Rent::get()?; minimum_balance(218); saturating_sub; if excess>0 {
  ata_info=ata.to_account_info(); sub_lamports; add_lamports; invoke(&Instruction{token::ID, vec![3 metas], SyncNative.pack()},
  &[ata.to_account_info(), rent.to_account_info(), donation.clone()])?; ata.reload()?; } amount==0 -> msg + Ok(None).
- DonationFeePdaCranked Event::data in the anchor #[event] form (serialize(..).unwrap()), as in v08.
Behavior: identical to w584 (same checks/CPIs/events/bytes; reload == try_borrow_data+try_deserialize+set_inner;
Borsh serialize of the event == the per-field extend).

## Why (mechanism)
The last residual of v08 was register allocation around the SyncNative vec/pack/infos-clone region. Root cause (proved
with the llc loop on v08's IR, RR/lanes/crank-brute/llc/e1.ll): with `rent: &AccountInfo` as a noalias readonly param of
the inlined helper, LLVM adds scoped-noalias metadata, so GVN reuses the rent.key pointer loaded for the AccountMeta
(before TokenInstruction::pack) in the infos clone (after pack); that value then occupies a callee-saved register across
pack and the rent AccountInfo pointer gets spilled/reloaded. The original reloads rent.key after pack (`ldxdw r3,[r6+0]`
@13264) — i.e. the rent AccountInfo was NOT behind a noalias param. Passing the Anchor wrapper `&UncheckedAccount`
(the AccountInfo pointer is loaded from it, so it carries no noalias scope) gives exactly the original codegen.

## Equivalent forms (same crank body; RR/lanes/crank-brute/v/<name>)
- g1a: `rent:&UncheckedAccount` + `let rent:&AccountInfo<'info>=rent.as_ref();` at helper top  (same .so sha as g01)
- g1b: same with deref coercion `let rent:&AccountInfo<'info>=rent;`                      (same .so sha as g01)
- g1f: free fn `sync_native_excess(donation, accounts:&mut CrankDonationFeePda)` binding rent/ata at top (same .so sha)
- g1e1: method `impl CrankDonationFeePda { fn sync_native_excess(&mut self, donation) }` binding rent/ata at top
  (crank identical; whole .so differs slightly — different sha).
- NOT equivalent: g1e2 (method with lazy `self.rent` uses) 15952B.

## Notes for whole-ELF
- The Event::data `.unwrap()` adds a panic Location + "called `Result::unwrap()`..." use (as in the anchor #[event] macro);
  rodata/Location placement is for the layout/whole-ELF step.
Credits: crank-b v08 (previous round) for the helper/event structure; crank-a/c for the helper-boundary/frame findings;
crank-brute (this round) for the noalias/GVN diagnosis (IR loop) and the source form.

## Extra checks (21:15)
- Independent clean rebuild (fresh w584 copy + source.patch + fresh warm target, RR/lanes/crank-brute/verify-g01/src)
  reproduces the same native .so (sha e77815918e6e022d...) and measure gained [147944], lost [].
- Native .text now has exactly the original's 585 windows at the original addresses; the only unmatched windows are the
  4 native-only sysroot TypeId windows at the SAME addresses as in the original (45432/702656/756232/767336).
- Crank ordered call list == original (39 calls); the 10 relocated lddw data refs point to the same items (same string
  contents; only rodata order differs natively). Event::data's unwrap is fully optimized out (no Location ref in crank).
- Ready-to-build full tree for the Linux/ordered.ld check: RR/lanes/crank-brute/verify-g01/src (w584 + source.patch).
- Runtime (LiteSVM, REPO/work/test-env python): RR/base/research/fees-crank-native-order/crank_cases.py --candidate
  native-symbols.so -> "strict Crank 304 cases 0 mismatches" (every retained field incl. raw logs + compute units vs the
  original deployed.so; 304/304 cases carry CU logs). Controls: native w584 = 164 mismatches; v08 = 0. Receipt:
  runtime-crank-cases.json.
