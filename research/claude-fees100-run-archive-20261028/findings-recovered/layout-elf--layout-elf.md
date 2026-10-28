# recovered from the transcript of lane layout-elf (layout-elf.md); entries in order

# layout-elf findings (lane log; newest last)

- 11:50 start. Frontier w582 (582/585, raw 200). Linux baseline w582-container-symbols.so ca9e6a93.

- 12:00 lanes/layout-elf/tools/lbuild.py (= cbuild.py + keeps link inputs: root .rcgu.o, symbols.o, version
  script, effective args) reproduces w582 EXACTLY (symbols ca9e6a93, stripped 7fdeefd6; 270 s, slot 0).
- 12:05 tools/relink.py replays ONLY the container rust-lld step of a saved lbuild (optionally with a new
  ordered.ld and/or a substituted root object): 2-3 s per link. Controls: plain replay -> ca9e6a93/7fdeefd6;
  object round-trip through tools/relobj.py serializer -> ca9e6a93/7fdeefd6 (both byte-identical).
- 12:08 ELF inventory tools/elfinv.py on w582 stripped candidate: under the positional window correspondence
  every difference is a CONSEQUENCE of the 3 bodies + extra event fn: .text gap 2768 = -24+752+2688-648;
  all 582 matched windows byte-equal after translating 4437 call displacements + 2138 lddw; .rodata identical;
  .data.rel.ro equal after translating 379 pointers; .rel.dyn 2664 outside-body entries equal in content AND
  order; .dynsym (custom_panic, entrypoint values), .dynamic (REL/SYMTAB/STRTAB/RELSZ/RELCOUNT), e_entry,
  e_shoff, phdrs, shdr addr/offsets all pure shifts; padding identical. INDEPENDENT residuals: NONE.
  Inside bodies: orig {R_RELATIVE:76, abort:3, sol_log_:5} vs cand {75, 3, 4}: original crank has a 2nd
  msg!("Nothing to donate") site (lddw 803046 at crank offsets 7336 AND 11528; candidate only 7336) -> one
  more sol_log_ + one more relocation. Original create calls handle_alloc_error, raw_vec::handle_error x2,
  memcpy x2, FeeError::fmt x2 and loads .data.rel.ro 821240 x2; candidate create instead calls to_string x2,
  exchange_malloc, AccountInfo::clone, Vec::from_iter and loads rodata 802239 x2.
- 12:12 DIAGNOSTIC-ONLY END-STATE PROOF (never harvestable: copies original machine code):
  tools/transplant.py replaced the 3 candidate bodies in the w582 root object by the ORIGINAL window bytes,
  re-expressing every call/lddw/syscall as an ordinary relocation to the candidate's corresponding
  symbol (37+35+77 calls, 66 lddw, 8 imports; no new symbols needed), then relink.py with the UNCHANGED
  w582 ordered.ld. Result: stripped = 873,256 B sha 5b6ceda5... == original meaningful ELF extent EXACTLY
  (0 differing bytes; original tail 75,688 B all zero). Symbols ELF: 585/585 normalized, 585/585 raw-local;
  the extra DonationFeePdaCreated::data body disappears by --gc-sections (its selector is harmless).
  => Whole-ELF identity needs NOTHING beyond the three bodies, provided (i) their call and lddw TARGETS equal
  the original's (normalization masks them), (ii) the data set/order stays as-is, (iii) ordered.ld selectors
  still name the same input sections after the source change (relayout.py, in progress).

- 12:16 relayout.py (lanes/layout-elf/tools, copied to shared/tools) validated on THREE real transitions; each
  output is BYTE-IDENTICAL to the layout the integrators produced by hand/with PR-specific scripts:
  T1 w580->w582 (Extend; .L__unnamed_86/87 swapped between .rodata/.data.rel.ro: bound by content identity) ==
     shared/frontier/w582/ordered.ld. Stale w580 ld on w582 source: .rodata 21086 B (!= original 21079).
  T2 w582->w583 (Sweep; 8 state.rs impl hashes changed: bound by dehashed alias names) == frontier/w583/ordered.ld.
     Stale w582 ld on w583 source: raw-local 195 (-5), 202 windows displaced, entry moved.
  T3 PR #301 build (crate hash 363d1ec1, /workspace paths) -> our container w583 (85ade9ce): 964 atoms renamed
     (every root symbol hash), output == frontier/w583/ordered.ld.  Runtime ~1-5 s.
  Reference builds reproduced with lbuild: w580 (08c8b0d3), w583 (f150b4c6 / stripped e5c3d298 = PR #301).

- 12:20 SYNTHETIC PROOFS on w583 (built with the STALE w583 ld, then relayout, then relink / full cbuild):
  S1 = rename sharing_update::legacy_distribute_creator_fees -> ..._feez (same length, no Location change) +
       `impl BuybackVault {}` on blank line 2 of state.rs (shifts every state.rs impl disambiguator).
       Stale: 583 norm, raw 195 (lost 235304 236240 280976 295376 380864). relayout: 11 renamed (10 impl methods via
       dehashed aliases, 1 via unique identity), --check 1474/1474 matched, 0 fell through, order ok. Relinked AND full
       cbuild.py: symbols 725ab649 (same both ways), stripped e5c3d298 == w583 frontier; 583 norm, raw 200, 0 lost.
  S2 = ` msg!("synthetic layout probe");` appended to create line 113 (new 22-B string, 215 .L__unnamed renumbered).
       Stale: .rodata 21096 B scrambled, 314 matched windows + 832 .data.rel.ro fields wrong after translation.
       relayout: 215 renamed by identity, 1 new atom appended; relinked: .rodata = original 21,079 B exact prefix +
       "synthetic layout probe"; 583 matched windows translation-equal; .rel.dyn/.data.rel.ro translation-equal;
       583 norm, raw 200.
- 12:21 elfinv on w583 frontier (e5c3d298): (b) none; Sweep's new match is translation-equal (raw-ready).
  Remaining body deltas unchanged from w582: crank orig {RELATIVE 59, abort 2, sol_log_ 5} vs cand {58, 2, 4}.
- 12:22 tools installed in R/shared/tools: relayout.py, relayout_build.py, lbuild.py, relink.py, elfinv.py.

- 12:27 T4 = PR #304 create tree (frontier-alt/pr304-create) on the container recipe. In that tree the handler body
  moved into pump_fees_candidate::pump_fees_candidate::create_donation_fee_pda (the old
  instructions::...::create section vanished) and DonationFeePdaCreated::data is gone. relayout v2 adds a
  "call-site successor" pass (same call offset in an UNCHANGED caller -> __global::create_donation_fee_pda+424) and an
  empty-window similarity fallback; result: the new function sits in window 163920, 585 compiled windows, 0 extras,
  --check perfect, ELF independent residuals NONE, .rodata == original, 583 norm / raw 200 (0 lost).
  Regression T1/T2/T3/S1/S2 still byte-identical (tools/regress.sh).
  CREATE TARGET FACTS (PR #304 body, what normalization hides): callees differ only by orig
  <FeeError as Display>::fmt x2 (290384) vs cand ToString::to_string x2 (38848); orig create loads the
  <String as fmt::Write> vtable (.data.rel.ro 821240: drop, size 24, align 8, write_str/char/fmt) at offsets
  2232/2912/5112/5320 and the "a Display implementation returned an error unexpectedly" message at 5472 => the
  original has ToString::to_string INLINED (String + Formatter + direct Display::fmt + expect). Program-id refs: orig
  loads the FIRST of each equal pair (PUMP id 806605, PUMP_AMM id 806716 x2 = public `ID` statics), PR #304 loads the
  copies 32 B later (806637, 806748 x2 = private `__ID`) -> use the public-static borrow form (cf.
  research/fees-program-id-references) at create offsets 440 / 10368 / 11808.

- 12:30 S3 (old = w582 layout, new = w583 with the now-MATCHING sweep handler renamed sweep_buybacq): call-site
  successor pass binds it (__global::sweep_buyback+688); with that pass disabled the signature-move fallback puts it
  into window 120816 -> identical ld; relinked stripped e5c3d298 == w583. T4 likewise identical via the similarity
  fallback (0.54). relayout_build.py smoke-tested (--stale reuse): T4 ld, check ok, 583/200, no loss.
- 12:31 FINAL: WHOLE-ELF-PLAN.md written (lanes/layout-elf). No (b) residuals => nothing to harvest from this lane
  (no raw/normalized gain is possible by layout alone: the 2,792-B body gap cannot be absorbed without padding).