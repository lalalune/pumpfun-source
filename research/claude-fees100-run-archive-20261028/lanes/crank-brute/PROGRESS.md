# crank-brute PROGRESS (window 147944 crank_donation_fee_pda) — round 3
Lane dir: RR/lanes/crank-brute. src/ = w584 clone (verified: lane rebuild sha 45d10d76.. = native w584).
slots/s{1,2,3}/{src,target} = fixed-path build slots. v/<name>/ = variant (changed files only + spec.json + FILES).
specs/common.py + specs/v08.py = crank-b's v08 (previous round) reconstructed from its transcript.
Tools: tools/mkvar.py NAME SPEC.py | tools/run.sh NAME SLOT [rustc args] (reset slot, overlay, nbuild, score -> leaderboard.tsv)
       tools/batch.sh n1 n2 ... (3 slots) | tools/score.py SYM.so [--diff --raw] (masked = fndiff-like with rodata previews
       truncated to 8 chars; raw = normalizer-like, lddw ptr fully masked) | tools/side.py SYM.so I0 I1 (side-by-side)
       tools/extract_fn.py + tools/objeq.py: llc loop (llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext) on the
       crank fn extracted from --emit=llvm-ir (an/v08-full.ll -> llc/v08.ll), verified EQUAL to the rustc body (0.07 s/compile).
       recovered/crank-{a,b,c}/events.txt = previous round transcripts (tool calls), for reference.

## Log
- 20:58 v08 rebuilt on w584: 15976B/1950i masked 0.9656 span 71 | raw 0.9549 span 107 (identical numbers to crank-b's).
  measure vs native w584: normalized 580, gained [], lost [] (no loss).
  Residual = ONLY register allocation in orig 12352..14016 (bump-alloc diamond .. infos clone): orig keeps the rent
  AccountInfo ptr (spill -1408) reloaded into r6 at 12352 and live across TokenInstruction::pack into the infos clone;
  heap ptr r8. v08: heap ptr r6, rent reloaded from -1408 per use.
- 21:05 IR proof: llc/e1.ll (v08 IR + fresh rent.key load in the rent clone after pack) == ORIGINAL exactly.
  => need a source form where rent's AccountInfo is not a noalias param of the inlined helper, but loaded early.
- 21:06 g1 batch: g1a/g1b/g1c/g1f (same .so sha e7781591..) and g1e1 => crank masked+raw EXACT; g1e2 (lazy self.rent) 15952B.
- 21:07 HARVESTED g1c as RR/shared/harvest/crank-brute-g01 (measure gained [147944], lost []); INDEX.log appended.
- 21:15 independent clean rebuild (verify-g01/: fresh w584 + source.patch) -> same sha e7781591.., gained [147944].
- 21:18 runtime crank_cases.py: g01 0/304 mismatches (w584 control 164/304). Receipt copied to harvest dir.
- STATE: window 147944 CLOSED natively (harvest crank-brute-g01). Linux/ordered.ld + elfinv = coordinator.
- 21:19 DIRECTIVES 21:08: Crank closed by crank-brute-g01; coordinator qualifying on Linux. Lane stopped; final result returned (closed).
