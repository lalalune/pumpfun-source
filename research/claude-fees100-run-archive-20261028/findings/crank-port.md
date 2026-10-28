# crank-port findings (window 147944 crank_donation_fee_pda)
Lane dir: RR/lanes/crank-port. Scorer: lanes/crank-port/tools/cs.py (mask ratio/span == fndiff masking; raw keeps stack
offsets + branch targets; depth = deepest r10 offset). Baseline w584 native: 1862i/15224B mask 0.6348 raw 0.2760 depth 2512.

## 21:05 PR #304 port, source-only (p0)
PR #304's crank line + its anchor-form Event::data + an in-crate trait `CrankInfoExt` (donation.rs tail:
`borrowed_info()` = unsafe lifetime-extended `as_ref()`, `reload_from_info()` = try_borrow_data + try_deserialize + set_inner)
reproduces PR #304 with NO anchor patch: 1947i/15952B mask 0.9494 raw 0.5876 depth 2464, measure 580 (w584 native), lost [].
(Same conclusion as crank-c E1: the patch is not needed for that codegen.) But the natural crank-b v08 form below is far better.

## 21:08 crank-b v08 reconstructed on w584 (v08b) = best start point
Exact source (lanes/crank-port/v/v08b): lib.rs:248 = w584 prefix (disable check, config/base/creator locals) +
`let amount=if ctx.accounts.quote_mint.key()==native_mint::ID { let donation=ctx.accounts.donation_fee_pda.to_account_info();
match crate::donation::sync_native_excess(&donation,&mut ctx.accounts.donation_fee_pda_ata,ctx.accounts.rent.as_ref())?
{ Some(amount)=>amount, None=>return Ok(()) } } else { let amount=ctx.accounts.donation_fee_pda_ata.amount; if amount==0
{msg!("Nothing to donate");return Ok(());} amount };` + PR #304 main path but with the receiver as a TEMPORARY
(`crate::relay_cpi::DonatePubkeyConfigIdWithPayerV1 {..}.invoke_signed(relay_args,seeds)?;`); donation.rs:12 = plain helper
`pub(crate) fn sync_native_excess<'info>(donation:&AccountInfo<'info>, ata:&mut Account<'info,TokenAccount>, rent:&AccountInfo<'info>)
-> Result<Option<u64>>` (Rent::get()?, minimum_balance(218), saturating_sub, `if excess>0 { ata.to_account_info(); sub/add_lamports;
invoke(&Instruction{.., accounts: vec![..3 metas..], data: SyncNative.pack()}, &[ata.to_account_info(), rent.clone(), donation.clone()])?;
ata.reload()?; }`, amount check with msg + Ok(None)); Event::data in the anchor form (PR #304's line).
Result: 1950i/15976B (exact size) mask 0.9641/74 raw 0.9533/110 depth 2168, measure 580, lost [].
Note: with `let mint=..` and `let relay_accounts=..` (PR #304 style) the 192-B event cannot share the receiver's slot:
depth 2392, mask 0.9421. The temporary receiver + direct mint condition is what gives the original frame.

## 21:20 IR-level proof: v08b + one un-CSE'd load == ORIGINAL (exact)
llc loop (lanes/crank-port/tools/llcx.py: extract crank from --emit=llvm-ir, llc -O3 pic +store-imm,+jmp-ext, reproduces rustc's
crank byte-exactly). In v08b's IR the infos[1] (rent clone) key is the SAME SSA value as the SyncNative meta's rent key
(`%_72.i = load ptr, ptr %_17`), CSE'd across the TokenInstruction::pack call thanks to the helper's `rent: &AccountInfo`
noalias readonly param. Inserting a separate `load ptr, ptr %_17` at the start of the rent clone (lanes/crank-port/llc/x/x6.ll)
makes llc output the ORIGINAL window 147944 byte-exactly (call/lddw imm masked). Original asm confirms: rent key re-loaded
`ldxdw r3,[r6+0]` at 13264 while the donation key (noalias param) is loaded once (12560) and reused via spill -1400.
=> source: rent's &AccountInfo must not be a noalias fn param of the inlined helper, but still be loaded early (6904).

## 21:22 Source-level match (independent confirmation; window already closed by crank-brute-g01 at 21:08)
Guided by the IR proof above, two minimal edits of v08b (rent no longer a noalias `&AccountInfo` param) both MATCH 147944:
- v09b (natural form): helper param `rent:&UncheckedAccount<'info>`, call site `&ctx.accounts.rent`, uses `rent.key()` and
  `rent.to_account_info()`; everything else = v08b.
- v09a: same param + `let rent:&AccountInfo<'info>=rent;` at the helper top.
measure: 581 native, gained [147944], lost []; fndiff: 1950/1950 insns, only lddw rodata-preview text differs (native rodata
order). Whole symbols ELF sha256 e77815918e6e022dac1df0105084643458222cc2d4aa9204ce08ee1c8f1f6d0c — byte-identical to
crank-brute-g01 and crank-transfer-g01, so three lanes converged on the same source independently. Not re-harvested
(DIRECTIVES 21:08: stop and report).
Lane files: lanes/crank-port/v/{p0,v08,v08b,v09a,v09b}, out/*-symbols.so, llc/x/x6.ll (IR proof), tools/{cs,llcx,irx,odiff}.py.
