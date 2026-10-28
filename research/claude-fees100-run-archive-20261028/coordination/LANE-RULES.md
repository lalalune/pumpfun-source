# fees100 lane rules — round 3: the LAST Pump Fees window (Crank 147944)

RR = /Users/shawwalters/fees100-run   (persistent; the old /private/tmp run root was wiped by a reboot)
REPO (primary checkout, READ-ONLY) = /Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source
BASE (sparse worktree of origin/main, READ-ONLY, shared) = RR/base

## Goal and state
Byte-identical reconstruction of the pump_fees program (`RR/base/evidence/original/pump_fees/deployed.so`).
- **584/585 functions are matched** once our CreateDonation recovery lands (RR/shared/frontier/w584 = w583 + the
  recovered `instructions/fee_sharing/create_donation_fee_pda.rs`). w583 = PR #301 (qualified Sweep, 583/585, raw 200).
- **The only remaining original window: 147944 = the #[program] handler `crank_donation_fee_pda`**
  (15,976 B / 1,950 insns). Our base candidate is 15,224 B / 1,862 insns.
- Whole-ELF end state is PROVEN (PR #317, research/claude-fees100-whole-elf-endstate-20261027): once Crank matches
  WITH THE ORIGINAL call/data targets, the existing recipe yields the complete original ELF. So a Crank match = 100%.

## What is known about Crank (read all of these first)
- RR/shared/findings-recovered/crank-{a,b,c}--*.md — the previous round's three Crank lanes (frame slot maps, callee
  order, the "Nothing to donate" scoping, error-copy and lifetime experiments). Do not repeat their dead ends.
- Best public trees: RR/shared/frontier-alt/pr304-crank (PR #304: 15,952 B / 1,947 insns, callee multiset equal, BUT it
  patches anchor-lang — RR/shared/frontier-alt/pr304-crank-anchor — exposing a borrowed account-info + reload with an inline
  hint; a source-only equivalent is required). RR/base/research/fees-crank-safe-context-source (PR #271, 15,688 B).
  RR/shared/prs/302/research/fees-causal582-source (typed try-result region keeps the 24-byte ProgramError copy).
  Codex's private best (15,960 B / 1,948 insns, exact call multiset) notes: REPO/work/fees-next-trial/parallel-donation/
  continue15-progress.md and newer files (read-only).
- Whole-ELF facts (layout-elf): the original has a SECOND `msg!("Nothing to donate")` site (rodata 803046 loaded at body
  offsets 7336 AND 11528; PR #304 has only 7336) -> one extra sol_log_ + one extra RELATIVE reloc; the original calls
  `alloc::alloc::handle_alloc_error` where candidates call `exchange_malloc`.
- Mechanisms that just closed CreateDonation (RR/shared/harvest/create-g01/NOTES.md) and probably transfer:
  LLVM's cold-callsite inliner (BFI < 2% of caller entry -> threshold 45) decides what gets inlined into the handler, and
  helper boundaries change block frequencies; SBF `analyzeBranch` cannot analyze conditional branches so block order
  follows IR order; tuple bindings let SROA place pair fields in adjacent original slots; a named slice local escapes
  StackColoring merges; helper parameter order controls ArgumentPromotion load order.

## Hard rules
1. REPO is read-only (you may READ REPO/work/* Codex notes). Never touch ~/.codex. Never kill processes/containers you did
   not start. BASE, RR/shared/frontier*, RR/shared/prs are read-only — copy into your lane before editing; never apply a
   patch outside your lane dir (use relative paths and `-d <your tree>`).
2. Work in RR/lanes/<lane>/: `cp -c -R RR/shared/frontier/w584 RR/lanes/<lane>/src && cp -c -R RR/shared/target-native-warm RR/lanes/<lane>/target`.
   Clone more src-*/target-* pairs for parallel variants. Never share a CARGO_TARGET_DIR between concurrent builds.
3. Every build goes through the slot lock (the build scripts do this).
4. No git push/PR/merge. The coordinator integrates and opens PRs.
5. Python: run tools with `python3 -I`. Runtime suites: REPO/work/test-env/bin/python.
6. PERSISTENCE: everything you need to resume must be in RR (persistent), not /tmp: PROGRESS.md after every experiment,
   findings in RR/shared/findings/<lane>.md, and harvest immediately.

## Build + measure
- Native (iteration; = Linux except 4 sysroot TypeId windows): `RR/shared/tools/nbuild.sh <src> <target> <out_prefix>`
  -> `<out_prefix>-symbols.so`. Native baseline: RR/shared/frontier/native/w583-symbols.so (579 natively; w584 adds 163920).
- `python3 -I RR/shared/tools/measure.py <symbols.so> --baseline <baseline symbols>` (gained/lost; windows cached).
- `python3 -I RR/shared/tools/fndiff.py 147944 <symbols.so> [--full] [--raw]` (masked diff; identical=True = match).
- `python3 -I RR/shared/tools/dis.py <image> <addr> [--names-from <cand symbols>] [--mask]`; original image
  RR/base/evidence/original/pump_fees/deployed.so.
- Whole-ELF check: `python3 -I RR/shared/tools/elfinv.py CAND.so --symbols SYM.so` (needs a Linux build; class (b) must be empty).
- Linux (coordinator; 2 slots): `python3 -I RR/shared/tools/cbuild.py <src with ordered.ld> <out_prefix>`.
- RR/shared/tools/speed-recovered/ holds the previous round's fast tools (dbuild/farm/fastdiff/fastwin) reconstructed from
  transcripts — NOT yet validated; only the speed lane may use them until it announces them as verified.

## Admission bar
Ordinary Rust source only (no asm, no padding, no post-link patching, no dead operations); behavior preserved; never
lose an existing match. A framework (anchor-lang) patch is only admissible if it is plausibly what the original used —
prefer a source-only form. Do not move statements to pad line numbers.

## Harvest protocol
When fndiff 147944 says identical=True and measure shows no loss: `H=RR/shared/harvest/<lane>-gNN` with `src/` (full
changed files relative to the tree root), `source.patch` (vs RR/shared/frontier/w584), `native-symbols.so`, `measure.json`,
`fndiff.txt`, `NOTES.md` (what/why/credits). Append `<lane>-gNN 147944 <normalized> w584` to RR/shared/harvest/INDEX.log.
Near-misses that are clearly better than anything before may be harvested as `<lane>-nNN`.

## Coordination
RR/shared/DIRECTIVES.md (coordinator; re-read every ~20 min), RR/shared/findings/<lane>.md (yours; read the others).
