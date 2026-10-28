# recovered from the transcript of lane crank-b (crank-b.md); entries in order

# crank-b findings (window 147944 crank_donation_fee_pda; re-derive from original)

Scoring tool: `lanes/crank-b/tools/cx.py <symbols.so>` (cached original listing; prints masked ratio
like fndiff plus a raw ratio where stack offsets/branch targets are kept, i.e. the repo normalizer).

## Baselines
- w582 frontier (lane rebuild, sha e6849af5... = native baseline): 15224B/1862i masked 0.6348.
- Codex best numeric (crank578-continue13-receiver-direct-mint): 15952B/1947i masked 0.9494, raw 0.6107.
  NOTE: it depends on a PATCHED anchor-lang (`anchor-dependencies/reload-borrowed-info`: adds
  `Account::borrowed_info()` + `reload_from_info()`), and on unsafe std::alloc for the SyncNative metas.

## Original structure facts (from disassembly, see lanes/crank-b/an/orig-147944.txt)
- ata info ptr [accts+720] is loaded ONCE (7640, start of excess path) and reused for meta key, infos clone
  AND the reload's try_borrow_data (14536) across opaque calls => source must not re-read ctx.accounts...info
  (Codex emulates with patched anchor). Same for rent info [accts+656]: loaded once at 6904, BEFORE Rent::get.
- SyncNative metas Vec: alloc (inline bump, handle_alloc_error(1,102) laid out INLINE/fall-through like the
  emit_cpi 34-byte vec!) happens before the 3 key reads => vec![...] (Box::new aggregate) with exchange_malloc
  inlined. Codex's unsafe alloc puts handle_alloc_error at the function end instead.
- Native path: "Nothing to donate" msg runs while `donation` (to_account_info clone at -280) is alive; donation
  dropped after the amount check, amount register reused in main path (no reload) => amount check inside the
  native block, value flows out.


## Experiments (12:00-12:40)
- v01: native excess work moved into a NON-inline helper `donation::sync_native_excess(&donation, &mut Account<TokenAccount>,
  rent: &AccountInfo) -> Result<()>` holding Rent::get..reload; handler keeps if/else amount checks + Codex main path.
  => 15976B/1950i (EXACT original size, first natural/unpatched source to hit it), masked 0.7923. Helper boundary gives:
  exchange_malloc inlined with handle_alloc_error(1,102) inline (like original), [accts+720] loaded once + [accts+656]
  once before Rent::get (noalias param => same as original). Remaining: extra Ok-tag re-checks at the helper exit
  (Rent error path and merged ata-drop exit: original has NO check there), block placement, frame (+32/+48 shifts).
- v02: helper narrowed to the excess body (ata clone..reload), Rent in handler: 15936B/1945i masked 0.7759; return block
  placed like original (exit@1096) but Rent err fall-through polarity inverted; helper-exit re-check still present.
- v05: no helper, shared `&Account` capture: 13984B/1706i 0.6581. MIR GVN does dedupe info loads through `&Account`,
  but the excess path is "cold" in the handler: exchange_malloc, AccountInfo::clone, drop_in_place<[AccountInfo;3]> and
  Account::reload all stay OUTLINED (same failure Codex saw). => the original optimized the excess body in a non-cold
  context (separately-optimized function, i.e. a helper), consistent with v01.
- Frame insight (post-PEI MIR dump, -C llvm-args=-print-after=prologepilog -filter-print-funcs=<mangled>): original slot
  order = [120 reload copy+ix][36 reload tail][24][24][24][48 emit-infos+donation][24][624 receiver..][64 seeds+ata]
  [104 args][creator][base][config][12x16B sret From slots]. Needs: SyncNative ix lifetime ending BEFORE reload (merges
  into 120B slot), ata merged into seeds slot, named Rent value living across excess path (24B slot at -232).


## KEY STRUCTURAL FINDING (12:55): helper-exit "Ok-tag re-check" vs return type
- Original error-path facts: Rent::get()? and the SyncNative invoke()? error paths run From<ProgramError> then drops
  (infos -> ata clone -> donation) straight to the shared return block with NO `jeq/jne r8,2` re-check; only the anchor
  library callees (sub_lamports, add_lamports x2 separately, reload x2) leave re-checks.
- Any helper returning `Result<()>` (v01/v02, crank-c h3n/n5/n9, Codex) adds a re-check at the helper exit: Result<(),Error>
  encodes Ok in Error's tag niche (tag==2), and on the From<ProgramError> paths the tag is an opaque call result, so LLVM
  JumpThreading cannot fold it (h3n/n9: extra checks at ~7376 and ~15100). #[inline(always)] (MIR-inlined) helpers do
  NOT fix it either (v03/v04 keep the Rent re-check) and collapse to cold outlining.
- crank-a's N2r helper returns `Result<Option<u64>>`: Result<Option<u64>,Error> cannot niche-fill (both variants dataful)
  so it carries an explicit tag that is a constant on every path (`mov r2,0` on errors) -> JumpThreading removes every
  helper-exit check -> re-check sites == original. => the helper must return a non-niche type (natural: Option amount).
- Rent info ptr: loading it at the helper CALL SITE (param `rent: &AccountInfo`, donation clone made by the caller) puts
  `ldxdw [accts+656]` between the donation clone and Rent::get exactly like the original (v01: 6888 vs orig 6904);
  with `accounts: &mut CrankDonationFeePda` + noalias LLVM sinks/delays it (N2r loads it at 12368).


## v07 (13:00) BEST SO FAR: 15952B/1947i, masked 0.8935, RAW 0.8478 (span 408) — first 890 insns (0..7184) RAW-EXACT
Source (spec lanes/crank-b/specs/v07.py; tree lanes/crank-b/v/v07, w582 base, crank-only edits in lib.rs:248 + donation.rs 12..):
- handler native arm: `let donation=ctx.accounts.donation_fee_pda.to_account_info(); match crate::donation::sync_native_excess(
  &donation,&mut ctx.accounts.donation_fee_pda_ata,ctx.accounts.rent.as_ref())? { Some(amount)=>amount, None=>return Ok(()) }`
  (non-native arm: amount check + msg; main path = Codex direct receiver; event uses ctx.accounts.quote_mint.key()).
- helper (plain fn, no attrs) `fn sync_native_excess(donation:&AccountInfo, ata:&mut Account<TokenAccount>, rent:&AccountInfo)
  -> Result<Option<u64>>`: `let rent_sysvar=Rent::get()?; let minimum=rent_sysvar.minimum_balance(218); let excess=
  donation.lamports().saturating_sub(minimum); if excess>0 { let ata_info=ata.to_account_info(); donation.sub_lamports(excess)?;
  ata_info.add_lamports(excess)?; invoke(&Instruction{program_id:token::ID, accounts:vec![AccountMeta::new(ata.key(),false),
  AccountMeta::new_readonly(rent.key(),false), AccountMeta::new(donation.key(),false)], data:SyncNative.pack()},
  &[ata.to_account_info(), rent.clone(), donation.clone()])?; ata.reload()?; } let amount=ata.amount; if amount==0
  {msg!("Nothing to donate"); return Ok(None);} Ok(Some(amount))`.
- Features now == original: re-check sites (7, same shape incl. split add_lamports checks), ld [accts+720] once @7640,
  ld [accts+656] @6904 (before Rent::get), single exit @1096, handle_alloc_error(1,102) inline, 39 calls same order.
- v07b (`balance>minimum`) == v07 (identical binary). v07c (named `let ix`) worse (raw 0.4988): ix must be a temporary.
- Remaining diffs: (a) emit_cpi region 9296..10900: register choice + the 224-B ix_data collect alloc (original keeps a
  `jslt 224,0` capacity check + different bump-alloc form + 216-byte copy loop) -> event data() impl (testing anchor-style
  `serialize(self,&mut data).unwrap()` as v08); (b) native excess path 11344.. (3 insns short) — analysing.


## v08 (13:10) NEAR-MISS: 15976B/1950i (exact size), masked 0.9641 span 74, RAW 0.9533 span 110; w583 base,
   measure: 579 native = baseline, lost_normalized=[] (no gain yet). Tree: lanes/crank-b/v/v08, spec specs/v08.py.
= v07 + the DonationFeePdaCranked Event::data impl in the #[event]/anchor form (no inline attr):
  `impl anchor_lang::Event for DonationFeePdaCranked { fn data(&self)->Vec<u8>{let mut data=Vec::with_capacity(256);
   data.extend_from_slice(Self::DISCRIMINATOR);anchor_lang::AnchorSerialize::serialize(self,&mut data).unwrap();data} }`
  (replaces w583's #[inline(always)] per-field extend_from_slice impl; line count kept). This fixed the whole emit_cpi
  region (original's `jslt 224,0` capacity check + bump-alloc form + 216-byte copy loop now identical).
- ALL structural features identical to original: re-check offsets 6392/11848/12168/12264/14696/14736/15328, exit@1096,
  "Nothing to donate"@7336/11528, handle_alloc_error 34@10664, ld[accts+720]@7640, ld[accts+656]@6904.
- ONLY residual (offsets 12352..13900, SyncNative metas/infos region): register allocation. Original reloads the rent
  AccountInfo ptr from its spill slot -1408 into r6 at 12352 (inside the bump-alloc select diamond) and keeps it in r6
  across TokenInstruction::pack until the infos clone; heap ptr in r8. v08 puts the heap ptr in r6 and reloads rent from
  -1408 at each use (r2/r3), which then permutes the infos-clone spill slots (-1416..-1496). Everything else raw-exact.
- Brute-forcing source variants of the metas/infos expressions (batch v09a..h) to flip that RA choice.