# recovered from the transcript of lane crank-c (PROGRESS.md); entries in order

# crank-c PROGRESS (resume point)
- Lane set up 12:00. base0 = w582 native reproduces baseline (578, no loss).
- Step 1 (in progress): port Codex canonical crank (receiver-direct-mint) to w582 WITHOUT the anchor-lang patch
  (local trait CrankInfoExt in donation.rs tail: borrowed_info via unsafe lifetime-extended as_ref, reload_from_info via **self = ...).
  Variants canonA (w582 event data impl) and canonB (Codex event data impl).

# crank-c PROGRESS (resume point) — window 147944 crank_donation_fee_pda
Frontier: w583 (lane src = w583 clone; src-w582 = old). Slots: slots/s0..s3 (fixed-path src+target; runv.sh rsyncs a variant in + touches lib.rs).

## Tools (lanes/crank-c/tools)
- mkvariant.py NAME LINEFILE [--helpers] [--data codex] [--extra-donation FILE]: variant = w583 + replaced crank line 248
  (+ CrankInfoExt trait helpers.rs appended to donation.rs; --data codex = Codex event data impl).
- runv.sh SLOT NAME / runva.sh SLOT NAME (adds frame dump + llvm-ir; writes out/NAME-{symbols.so,crank.ll,frame.txt}).
- ocmp.py FILE(.o|.so): EXACT/raw/frame-masked compare vs original 147944. fastdiff.py: fndiff-like masked compare.
- extract_fn.py MODULE.ll SUBSTR OUT.ll + irrun.sh OUT.ll: llc loop (0.5 s) reproducing rustc crank codegen exactly.
- nsc.sh / allocmap.py: no-stack-coloring build -> per-alloca original slot map. reorder.py: reorder allocas in IR.

## State (12:55)
- canonB = Codex canonical (receiver-direct-mint) on w583 with source-only CrankInfoExt (no anchor patch): byte-identical to
  Codex's patched build. 15952B/1947, depth 2240, raw 0.6123 (span 919), frame-masked 0.9792 (span 75).
- IR proof (llc/e9.ll): original frame reproduced exactly by (a) native-block allocas before crank's own (= inlined helper),
  (b) lifetime markers on meta-key temps, (c) long-lived Rent::get payload markers. Remaining = block layout.
- Source probes: h1{a,i,n} = native excess block moved to helper fn sync_native_excess(&donation,&mut ata,native_rent)
  (donation.rs tail): alloca order now correct, meta temps get inline-scoped (too long) markers, depth 2232, fmasked worse (0.8937).
  h2{n,a} = h1 + vec![] metas; canonvec = canonB + vec![] (no helper). Running.