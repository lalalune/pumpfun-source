## CrankDonationFeePda source recovery (window 147944) -- crank-transfer-g01

**DUPLICATE CONFIRMATION of crank-brute-g01** (harvested 1 min earlier; DIRECTIVES 21:08). Found independently by this
lane; `native-symbols.so` is byte-identical to crank-brute-g01's (sha256 e77815918e6e022dac1df0105084643458222cc2d4aa9204ce08ee1c8f1f6d0c),
`lib.rs` is identical, `donation.rs` differs only in formatting of the `invoke(...)` call (one line here, five lines there).
Use crank-brute-g01 as the canonical harvest; this entry is an independent reproduction of the same source fix.

The reconstructed `#[program]` handler `pump_fees_candidate::crank_donation_fee_pda` matches the complete original
window **147944 (1,950 instructions / 15,976 bytes)** under the repository normalizer (measure: gained_normalized
[147944], lost_normalized [], native 581 = 584 + Crank, the 4 unmatched are the native-only sysroot TypeId windows).
Base: RR/shared/frontier/w584. Changed files: `programs/pump-fees/src/lib.rs` (line 248, the crank body) and
`programs/pump-fees/src/donation.rs` (helper in the reserved blank lines 12..30; `DonationFeePdaCranked::data` at
line 182 in the anchor `#[event]` form, lines 183..196 left blank so later line numbers do not move). File line counts
are unchanged. Native build: `native-symbols.so` (sha e7781591...). fndiff's 3 remaining lines are lddw rodata
*previews* of the native (non-ordered.ld) layout; the same artifact appears for the already-matched 163920 in the
w584 native build. The lane's normalizer view (`ocmp.py`, lddw values + internal call targets masked) reports 0
differing instructions.

### Source form (ordinary safe Rust)
- Handler: disabled check; `config`/`base`/`creator` copies; `let amount = if ctx.accounts.quote_mint.key() ==
  native_mint::ID { let donation = ctx.accounts.donation_fee_pda.to_account_info(); match
  crate::donation::sync_native_excess(&donation, &mut ctx.accounts.donation_fee_pda_ata, &ctx.accounts.rent)? {
  Some(amount) => amount, None => return Ok(()) } } else { let amount = ...ata.amount; if amount == 0 {
  msg!("Nothing to donate"); return Ok(()); } amount };` then `relay_args` (with `format!`), `seeds`, the relay
  receiver struct literal used directly as the `invoke_signed` receiver, `total_donated` checked_add, `Clock::get()`,
  event with `quote_mint: ctx.accounts.quote_mint.key()`, `emit!` + `emit_cpi!`.
- Helper `fn sync_native_excess<'info>(donation: &AccountInfo<'info>, ata: &mut Account<'info, TokenAccount>,
  rent: &UncheckedAccount<'info>) -> Result<Option<u64>>` (plain fn, no attributes): `Rent::get()?`,
  `minimum_balance(218)`, `saturating_sub`, and if `excess > 0`: `ata.to_account_info()`, `sub_lamports`,
  `add_lamports`, `invoke(&Instruction { program_id: token::ID, accounts: vec![AccountMeta::new(ata.key(), false),
  AccountMeta::new_readonly(rent.key(), false), AccountMeta::new(donation.key(), false)], data: SyncNative.pack() },
  &[ata.to_account_info(), rent.to_account_info(), donation.clone()])?`, `ata.reload()?`; then
  `if ata.amount == 0 { msg!("Nothing to donate"); return Ok(None); } Ok(Some(amount))` -- the original's second
  "Nothing to donate" site.
- `impl Event for DonationFeePdaCranked { fn data(&self) -> Vec<u8> { Vec::with_capacity(256) + DISCRIMINATOR +
  AnchorSerialize::serialize(self, &mut data).unwrap() } }` (what `#[event]` generates).

### Why it reproduces the original (measured)
- Helper boundary (crank-a/crank-b/crank-c, round 2): optimized as its own function first, the SyncNative block is
  hot relative to the helper entry, so `exchange_malloc` (with the inline `handle_alloc_error(1,102)`),
  `AccountInfo::clone` and `Account::reload` are inlined (in the handler they sit below the 2% cold-callsite
  threshold); the inlined helper's allocas land at the top of the frame (= original slots, depth 2168).
  `Result<Option<u64>>` cannot niche-fill, so no Ok-tag re-checks appear at the helper exit (crank-b).
- The anchor `#[event]` data form gives the original emit_cpi region (`jslt 224,0`, bump form, 216-byte copy).
- **The last residual (this lane):** with `rent: &AccountInfo` (crank-b v08, 0.9641 masked) the param is
  `noalias readonly`; inlining turns that into scoped-noalias metadata, so GVN reuses the `rent.key` pointer
  loaded for the AccountMeta in the infos clone across `TokenInstruction::pack`. That one long-lived value changes
  the register assignment in the whole metas/infos region (heap pointer r6 vs r8, rent pointer reloaded 3x from
  -1408, permuted spill slots). Proven at IR level first: v08's IR with only a fresh `load ptr, ptr %rent` for the
  clone's key run through llc gives the exact original body (lanes/crank-transfer/ir/e1-MATCH.ll). Passing the
  accounts-struct field instead, `rent: &UncheckedAccount<'info>` (call site `&ctx.accounts.rent`), puts the
  noalias on the 8-byte UncheckedAccount wrapper, not on the AccountInfo it points to; the AccountInfo pointer is a
  loaded value (escape source), so its fields get no scope, the bump-allocator stores and the pack call may clobber
  them, and the clone re-loads `rent.key` (original `ldxdw r3,[r6+0]` @13264) with the AccountInfo pointer held in r6
  across pack. The [accts+656] load stays before Rent::get (@6904), as in the original.
  A named `let rent_info: &AccountInfo = rent.as_ref();` at the top of the helper builds a byte-identical ELF.

### Credits
Round-2 Crank lanes: crank-b (helper returning `Result<Option<u64>>`, anchor-form event data -> v08 15976B/1950i
near-miss), crank-a (cold-callsite/BFI analysis, helper inlining), crank-c (frame/IR llc loop technique); Codex
(canonical receiver-direct-mint body); layout-elf (whole-ELF end state, PR #317); create-g01 mechanisms. This lane
(crank-transfer): v08 reconstruction from findings, IR-level localization of the residual, the `&UncheckedAccount`
source fix.

### For qualification
Needs the Linux container build with a relayout'ed ordered.ld (new source: DonationFeePdaCranked::data body vanishes
into the handler as before; helper fully inlined) and elfinv class (b) empty; expected end state: 585/585.
