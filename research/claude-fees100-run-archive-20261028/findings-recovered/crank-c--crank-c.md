# recovered from the transcript of lane crank-c (crank-c.md); entries in order

# crank-c findings (frame/allocation specialist, window 147944 crank_donation_fee_pda)

Lane dir: R/lanes/crank-c (src = w582 clone; slots/s0..s3 = fixed-path build slots; v/<name>/src = variants; out/ = builds).
Tools: lanes/crank-c/tools/fastdiff.py (cached-original one-window diff, 0.5 s; prints masked+raw ratio, frame depth),
mkvariant.py (variant from a replacement crank line 248), runv.sh SLOT NAME (build variant in slot + fastdiff).

## Baseline
- base0 (w582 unchanged): 15224 B / 1862 insns, depth 2512 (orig 2168); masked ratio 0.6348, raw ratio 0.2728. measure 578 native, no loss.
- Codex direct-native screens (578 parent, PATCHED anchor-lang reload-borrowed-info, not admissible):
  canonical receiver-direct-mint 15952B/1947/depth 2240 masked 0.9494 raw 0.6071;
  vec-try-capacity 15960B/1948/depth 2176 masked 0.9379; seeds-question-inside 15976B/1950/depth 2152 masked 0.9359.

## Experiments

- E1 canonA/canonB (12:03): Codex canonical receiver-direct-mint crank line ported onto w582 with NO anchor patch: an in-crate
  trait `CrankInfoExt` (donation.rs tail) gives `borrowed_info()` = unsafe lifetime-extended `as_ref()` and
  `reload_from_info(info)` = `{ let mut data: &[u8] = &info.try_borrow_data()?; **self = TokenAccount::try_deserialize(&mut data)?; Ok(()) }`,
  both #[inline(always)]. canonB (+ Codex event data impl `AnchorSerialize::serialize(self,&mut data).unwrap()`) is
  BYTE-IDENTICAL (call/lddw masked) to Codex's patched-anchor canonical: 15952B/1947, depth 2240, masked 0.9494.
  canonA (w582's #[inline(always)] manual extend_from_slice data impl) is worse: 15928B/1944, masked 0.8788.
  => the anchor-lang registry patch is NOT needed for Codex's canonical codegen.

- TOOL (12:25): fast IR->machine-code loop. `llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext` (platform-tools v1.44
  llc, LLVM 18.1.7) on the crank function extracted from the build's --emit=llvm-ir module (tools/extract_fn.py: fn + referenced
  globals/decls + all type/attribute/metadata lines) reproduces the rustc crank body EXACTLY (0 differing insns, 0.5 s).
  NOTE: -mattr is required (function attrs alone do not enable store-imm in llc); -trap-unreachable must NOT be passed.
  tools/ocmp.py compares an .o/.so crank body with original 147944: EXACT (repo-normalizer-equivalent), raw ratio, and a
  frame-masked ratio. canonB: raw 0.6123 span 919, frame-masked 0.9792 span 75, depth 2240 (orig 2168).
- Frame table (print-after=prologepilog joined with IR allocas, tools/frametab.py): canonB live objects fi7 120@-120, fi8 36@-160,
  fi17 48@-208, fi18 24@-232 (no markers), fi26 receiver 624@-856, fi27 bump 1@-857, fi28 seeds 64@-928, fi31 relay_args 104
  (no markers), fi32 _61 invoke ProgramResult 24, fi36/fi37 sync_metas.sroa.{4,5}.sroa.0 32+32 (NO lifetime markers),
  fi40 _15.sroa.5 Rent payload 24 (NO markers), fi41 rent_value 24, fi44-46 creator/base/config, 12x16B Error sret slots, spills.
  Original (inferred from slot map): three extra live 24-B objects at -184/-208/-232 BETWEEN fi8 and fi17 holding
  {invoke ProgramResult, data.i, emit_cpi outer seeds}, {Rent payload, late event bump}, {Rent value, signer bump};
  rent-meta key inside fi8 (-160), donor-meta key inside receiver (-928); nothing between relay_args and creator.

- E2 IR-level frame solution (12:45, llc loop on canonB IR; NOT yet a source change):
  tools/allocmap.py on a `-no-stack-coloring` llc build maps every canonB IR alloca to its ORIGINAL frame slot (unambiguous):
  orig -120 {val.sroa.3.i, ix, ix10, _147, _90, _122.sroa.11}, -160 {val.sroa.5.i, _230, _182, RENT meta key}, -184 {_61 invoke
  ProgramResult, data.i, _179}, -208 {_15.sroa.5 Rent::get payload, _186 late event bump}, -232 {rent_value, _105 signer bump},
  -280 {_176/donation, _164, _121.sroa.11}, -304 {_172}, -928 {receiver _109 + fi0-6, _10.i, _6.i, _294, event, _133, _86, infos,
  _52, DONOR meta key, _16, _11}, -992 {seeds _99, native_credit}, -1096 relay_args, -1128/-1160/-1192 creator/base/config.
  Three IR edits make llc reproduce the ORIGINAL FRAME EXACTLY (depth 2168, every survivor at its original offset; raw ratio
  0.61 -> 0.939, raw span 919 -> 158):
   (a) move the native-branch allocas {_230,_61,infos,_52,ix,sync_metas.*,native_credit,_16,_15.sroa.5,rent_value,donation} to just
       after the inlined reload allocas (data.i) = BEFORE crank's own allocas  [this is exactly the order an INLINED HELPER
       FUNCTION holding the native/sync block would produce: callee allocas are spliced to the top of the caller entry block];
   (b) lifetime markers on the two SROA'd meta-key temps (sync_metas.sroa.{4,5}.sroa.0);
   (c) lifetime markers on the Rent::get payload temp _15.sroa.5 with a LONG range (start at Rent::get, end where rent_value ends).
  Remaining raw diffs after that are block-layout only (Rent::get error block placement, the two `jeq r8,2; ja` add_lamports tails,
  inline handle_alloc_error) — inherited from canonB's CFG. Files: lanes/crank-c/llc/e9.ll (+e9.o).

- E3 SOURCE-LEVEL FRAME MATCH (13:00): variant h2n = canonB + the native excess/SyncNative block moved into an ordinary
  helper `fn sync_native_excess<'info>(donation:&AccountInfo<'info>, ata:&mut Account<'info,TokenAccount>,
  native_rent:&AccountInfo<'info>) -> Result<()>` (no inline attribute; donation.rs tail) + `vec![AccountMeta::new(..),
  AccountMeta::new_readonly(..), AccountMeta::new(..)]` for the 3 metas (no unsafe alloc). The crank frame now matches the
  ORIGINAL survivor layout exactly: depth 2168, -120/-160/-184(invoke ProgramResult)/-208(Rent payload)/-232(Rent value)/
  -280/-304/-928 receiver/-992 seeds/-1096 relay_args/-1128.. creator/base/config. 16000B/1953 (orig 15976/1950);
  raw 0.6482, fmasked 0.8932 (code-shape diffs elsewhere, being worked). h1n (helper + Codex raw alloc): depth 2232 (meta
  temps get inline-scoped markers). h2a (#[inline(always)] helper): depth 2176. canonvec (vec! without helper): depth 2176.

- E4 (12:35 real clock; earlier E-labels' times were estimates) h3n = h2n with the vec! INSIDE the Instruction literal
  (`Instruction{program_id, accounts: vec![...], data: SyncNative.pack()}`): EVERY IR alloca now maps to the same frame slot as
  the original (allocmap on no-stack-coloring build vs original AND vs the colored build agree for all 47 allocas; the rent
  meta-key temp now merges into the -160 group because ix's StorageLive precedes the vec!). Depth 2168. Frame problem solved
  at source level. Remaining: code shape (register allocation / block layout), fmasked span 320 (canonB: 75).
  crank-a E3/E4 independently: helper makes exchange_malloc and plain reload() inline (cold-callsite threshold no longer hit).