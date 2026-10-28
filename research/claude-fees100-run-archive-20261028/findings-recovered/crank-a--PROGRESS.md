# recovered from the transcript of lane crank-a (PROGRESS.md); entries in order

# crank-a PROGRESS (window 147944 crank_donation_fee_pda)
- src/ = pristine w582 clone; src-safe/ = Codex safe-context body ported (include! instructions/fee_sharing/crank_donation_fee_pda.rs).
- Variants: inc/<name>.rs (include-file bodies) built by tools/runvar.sh NAME INC SLOT [BASE_SRC] into vars/src-NAME,
  target-pSLOT (SLOT 1-4), outputs out/v-NAME-*; results appended to results.tsv.
- tools/crankstat.py SYMBOLS.so [--calls] gives crank metrics.
- Analysis files in an/ (orig-147944.txt original listing; safe-crank.txt; safe-preinline.ll pre-inliner IR).
- Findings log: R/shared/findings/crank-a.md (E1..). No harvest yet.