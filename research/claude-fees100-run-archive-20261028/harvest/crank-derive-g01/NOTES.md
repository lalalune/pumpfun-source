## CrankDonationFeePda handler (window 147944) — source match (crank-derive-g01)

**DUPLICATE CONFIRMATION of crank-brute-g01** (DIRECTIVES 21:08 closed Crank with crank-brute-g01; crank-transfer-g01
is a second reproduction). Found independently by lane crank-derive (IR-level root cause first, then source):
native-symbols.so is byte-identical to crank-brute-g01 / crank-transfer-g01 (sha256 e77815918e6e...8f1f6d0c). Use
crank-brute-g01 as the canonical harvest; this entry adds the independent IR proof and one more equivalent form.

`pump_fees_candidate::crank_donation_fee_pda` now matches original window **147944 (1,950 insns / 15,976 B)**:
- `measure.py` (repo window_map normalizer) vs native w584: normalized 581, **gained_normalized [147944]**,
  lost_normalized [] (also 23 raw-local gains, no raw loss). sha256 e77815918e6e022dac1df0105084643458222cc2d4aa9204ce08ee1c8f1f6d0c.
- Raw body (registers, stack offsets, branch offsets; only call/lddw immediates masked): **identical** to the
  original (tools in lanes/crank-derive: `ocmp.py`, `score.py` -> raw 1.0000 span 0).
- `fndiff.py` prints identical=False ONLY because of 3 lddw string *previews* ("Nothing to donate" x2,
  "__event_authority"): the native build's .rodata neighbours differ (no ordered.ld). Masked span is exactly those 3.
  A Linux/container build with the w584 ordered.ld (+relayout if needed) is required for the whole-ELF check.

Changed files: programs/pump-fees/src/lib.rs (crank line 248 only) and programs/pump-fees/src/donation.rs
(new helper in the blank lines 12..29; DonationFeePdaCranked Event::data in the #[event] form on line 182, line count kept).

### Source form (ordinary safe Rust, no anchor patch, no unsafe)
- Handler: Codex's canonical receiver-direct-mint main path (direct mint condition, `relay_args` built first with
  `format!` inline, seeds with inline bump, direct `DonatePubkeyConfigIdWithPayerV1{..}.invoke_signed(..)`, event with
  `ctx.accounts.quote_mint.key()`); amount =
  `if native { let donation = ctx.accounts.donation_fee_pda.to_account_info(); match sync_native_excess(&donation, &mut ctx.accounts.donation_fee_pda_ata, &ctx.accounts.rent)? { Some(a) => a, None => return Ok(()) } } else { let amount = ata.amount; if amount == 0 { msg!("Nothing to donate"); return Ok(()); } amount }`.
- Helper `fn sync_native_excess<'info>(donation: &AccountInfo<'info>, ata: &mut Account<'info, TokenAccount>,
  rent: &UncheckedAccount<'info>) -> Result<Option<u64>>`: `Rent::get()?`, `minimum_balance(218)`, saturating excess,
  `if excess > 0 { ata_info = ata.to_account_info(); donation.sub_lamports; ata_info.add_lamports;
  invoke(&Instruction { program_id: token::ID, accounts: vec![new(ata.key()), new_readonly(rent.key()), new(donation.key())],
  data: SyncNative.pack() }, &[ata.to_account_info(), rent.to_account_info(), donation.clone()])?; ata.reload()?; }`,
  then the second `msg!("Nothing to donate")` site returning `Ok(None)`.
- `impl Event for DonationFeePdaCranked { fn data(&self) -> Vec<u8> { Vec::with_capacity(256) + DISCRIMINATOR +
  AnchorSerialize::serialize(self, &mut data).unwrap() } }` (the #[event]-generated shape).

### The last residual and why `rent: &UncheckedAccount` fixes it (measured)
- The previous best (crank-b v08, rebuilt here: masked 0.9641, the only diff a register permutation in 12352..14080)
  took `rent: &AccountInfo<'info>`. That parameter is noalias+readonly, so after inlining the scope metadata proves that
  `TokenInstruction::pack` and the heap stores cannot clobber `rent.key`; GVN then reuses the SyncNative meta's key
  load for the infos clone. The merged key pointer stays live across `pack` in a callee-saved register, which pushes the
  rent AccountInfo pointer out of r6 and permutes the whole metas/infos region.
- IR proof (llc loop on rustc's own --emit=llvm-ir, which reproduces rustc's crank exactly): re-loading `rent.key` for
  the infos clone, and nothing else, makes the crank body identical to the original.
- With `rent: &UncheckedAccount<'info>` (the account wrapper, as the handler's other accounts are passed), the
  AccountInfo pointer is loaded from the wrapper, so `rent.key` is not covered by a noalias scope and the clone reloads
  it, exactly like the original (the ATA, passed as `&mut Account`, already behaved this way). The pointer load still
  happens before `Rent::get` like the original. (A variant passing `accounts: &mut CrankDonationFeePda` with
  `let rent = accounts.rent.as_ref();` first builds a byte-identical ELF.)

### Credits
Built directly on fees100 round-2 lane findings: crank-b (v07/v08: Result<Option<u64>> helper, call-site rent load,
anchor-form Event::data), crank-a (helper boundary vs cold call sites, named Rent), crank-c (frame/alloca analysis,
llc loop technique), Codex's canonical receiver-direct-mint main path (PR #304 lineage), and CreateDonation g01.
