# crank-brute findings (round 3; window 147944)

## Best available tree = crank-b's v08 (previous round), reconstructed on w584 from the crank-b transcript
- Spec: RR/lanes/crank-brute/specs/v08.py (+ specs/common.py); materialized files: RR/lanes/crank-brute/v/v08/programs/pump-fees/src/{lib.rs,donation.rs}.
  = w584 + crank handler line 248 (native arm calls a plain helper `donation::sync_native_excess(&donation, &mut ata, rent)
  -> Result<Option<u64>>` holding Rent::get..reload + the native "Nothing to donate") + Event::data in #[event] form.
- Native: 15976 B / 1950 insns (exact size), fndiff masked 0.9641 span 74; normalizer-like raw ratio 0.9549 span 107.
  measure vs native w584: lost [] (no loss). Symbols: RR/lanes/crank-brute/out/v08-symbols.so.
- The ONLY residual: register allocation in orig offsets 12352..14016 (SyncNative vec alloc diamond -> metas -> pack ->
  infos clone). Original reloads the rent AccountInfo ptr (spill slot -1408) into r6 at 12352 and keeps it in r6 across
  TokenInstruction::pack into the infos clone; heap ptr in r8. v08: heap ptr in r6, rent ptr reloaded per use.
- llc loop on v08's crank IR reproduces the rustc body EXACTLY (llc/v08.ll; 0.07 s per compile).

## KEY IR RESULT (21:05): the whole residual = GVN CSE of rent.key across TokenInstruction::pack
- In v08 IR the infos-array rent clone reuses the key pointer loaded for the SyncNative meta BEFORE pack (`%_72.i`),
  because `rent: &AccountInfo` is a noalias readonly helper param -> after inlining, scoped-noalias metadata tells GVN
  that pack cannot clobber it. That value then lives across pack in r8 and the RA spills the rent AccountInfo ptr.
- IR edit llc/e1.ll = v08.ll + ONE fresh `load ptr, ptr %_17` (rent.key) at the start of the rent clone (after pack),
  stored into infos[1].key instead of %_72.i  ==> llc output is EXACTLY the original 147944 body
  (normalizer-equal: raw 1.0000 span 0, 1950 insns). Tool: RR/lanes/crank-brute/tools/oscore.py llc/e1.o.
- => Source target: keep v08 everything, but the rent AccountInfo pointer must reach the helper WITHOUT noalias
  (e.g. passed as &UncheckedAccount / via the accounts struct and deref'd inside), while still being loaded early
  (orig `ldxdw r6,[r8+656]` @6904 before Rent::get). Testing source forms now.

## MATCH (21:07): HARVESTED RR/shared/harvest/crank-brute-g01 — Crank 147944 normalized-identical, no loss
- v08 + helper param `rent: &UncheckedAccount<'info>` (call site `&ctx.accounts.rent`) + `rent.to_account_info()` in infos.
- measure vs native w584: 580 -> 581, gained [147944], lost []; remaining native-unmatched = the 4 sysroot TypeId windows
  (45432/702656/756232/767336, 56 B each) = native-only. fndiff's 3 diffs are rodata-neighbor previews only.
- Same crank body also from g1a/g1b/g1f (identical .so) and g1e1 (method on CrankDonationFeePda). See NOTES.md there.
- NEXT (coordinator): Linux/ordered.ld build + elfinv whole-ELF check.
- 21:15 independent clean rebuild of w584+source.patch reproduces sha e7781591.. and gained [147944]. Native .text now has
  the original's 585 windows at the original addresses (only the 4 native TypeId windows unmatched, same addresses).
  Full tree for the coordinator's Linux build: RR/lanes/crank-brute/verify-g01/src.
- 21:18 runtime: fees-crank-native-order/crank_cases.py (304 strict signed LiteSVM cases, logs+CU) on g01 native .so:
  0 mismatches vs original (control: native w584 = 164 mismatches). Receipt in the harvest dir.
- 21:19 FINAL: lane stopped per DIRECTIVES 21:08. Harvest RR/shared/harvest/crank-brute-g01 (g1c form). Equivalent forms
  g1a/g1b/g1f (same .so) and g1e1 kept under RR/lanes/crank-brute/v/. Not equivalent: g1e2 (lazy self.rent in a method).
