# Main Pump matching swarm

Goal: compiler-produced Rust source in `programs/pump` whose build matches every
function of the deployed program, first after the scorer's masking (normalized) and
finally byte for byte (raw), ending in whole-ELF identity.

## Measured state (origin/main 9b216213, 2026-10-30)

A fresh identity-recipe build of upstream `9b216213` has **1,032/1,035 normalized
windows and 347 raw windows**. This is a pinned measurement, not a claim about
later main. The three remaining windows are:

| Original | Bytes | Function | Remaining difference |
| --- | ---: | --- | --- |
| `0x1e7c0` | 15,576 | `create_v2::execute` | Four normalized 8-byte slots; ratio 0.99892 |
| `0x22a10` | 27,400 | `admin_cto::execute` | Candidate 27,344 bytes; ratio 0.37637 |
| `0x5b3b0` | 18,584 | `multi_hop_curve::swap_hop` | Candidate 18,584 bytes; ratio 0.85352 |

The [five-area follow-up packet](lanes/five-bytecode-followups/README.md) pins the
full revision, source and tool fingerprints, full window membership and runtime
comparison limits. It claims no new matches; the ten raw additions since its
historical 1,032/337 baseline were already merged upstream through #2403.
The older [native-6a checkpoint](checkpoints/native-6a1d23a-20261030/README.md)
remains a historical 1,027-normalized / 276-raw measurement.

Similarity is a diagnostic, not acceptance or proof of runtime equivalence.

## Acceptance

Only `reconstruction/harness/score.py` decides. A window is done when the scorer says
`normalized: true` (then `raw: true`); the end goal is whole meaningful-ELF identity. A change
is acceptable only if it keeps every baseline normalized and raw membership. Line numbers are
part of the code (`line!()` immediates), so keep the `// layout-pad` comment lines balanced
when you move code. Similarity is evidence, not acceptance.

### Build inputs are in scope (2026-10-30)

Anything that is an input to the build may change if it gets closer to the deployed bytes:

- crate and workspace metadata: package name, version, edition, authors, features,
  workspace layout and paths, `[lib]` settings — everything that feeds `-C metadata`
  and symbol hashes;
- `Cargo.lock`, dependency versions, sources and features, vendored or patched dependencies;
- `[profile.*]` settings, `RUSTFLAGS`/`-C`/`-Z` options, `cargo build-sbf` options, linker
  arguments and linker scripts;
- toolchain choice and version (rustc, platform-tools, LLVM, target libraries), and the
  build recipe itself (`fastbuild.py`, `toolchain/`), as long as it stays pinned.

`programs/pump/link/ordered.ld` is such an input: it puts the upstream-generic instances
of the root crate and all dependency code in the original's order (the AMM/Fees/Mayhem recipe),
while local items keep rustc's def order. After a source change that adds or renames generic
instances, regenerate it with `lanes/w8-sibling-recipes/tools/regen.sh`.

Every such change must be committed, pinned (versions and hashes) and reproducible from a
clean checkout with the documented recipe, so anyone can rebuild the same bytes.

Still not allowed, because the output would be copied rather than rebuilt:

- inserting original machine code or data (byte blobs, `global_asm!`/inline asm that
  transcribes original instructions, `include_bytes!` of original sections);
- patching, padding or rewriting the emitted ELF after the linker;
- changing the scorer or its normalization (bug fixes reviewed separately are fine).

## Working rules

- One lane per agent, one git worktree per lane, branched from `origin/main`:
  `git worktree add -b swarm/<lane> /Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/<lane> origin/main`
- Build outputs stay out of git, under `~/.cache/pumpfun-reconstruction/lanes/<lane>/`.
- Before every trial, check the ledger for the mechanism; after every trial (including
  compile failures and byte-identical results), record it:
  `python3 reconstruction/pump-main/log_attempt.py check|search|summary|record ...`
  The live ledger is shared by all worktrees; `ATTEMPTS.jsonl` here is its committed snapshot.
- Progress means either an official gain with no loss, or a target window that gets
  measurably closer (fewer differing normalized slots, or a higher ratio with the same
  callee multiset) with no loss anywhere. On the first progress open a draft PR from
  `swarm/<lane>`; on each later improvement push to the same branch and update the PR
  body's metrics table. Analysis-only progress goes in
  `reconstruction/pump-main/lanes/<lane>/NOTES.md`.
- Prior work to read first: `prior-swarm/` (15 lane summaries and source patches from the
  2026-10-29 swarm) and, in git history, `b4448f7bc^:research/goal-pump-*-recovery-*`
  (each has a README or CONTINUATION.json listing rejected mechanisms).
