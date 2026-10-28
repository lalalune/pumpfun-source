# Main-Pump byte-matching lanes: shared rules (round 3, durable)

W = /Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work   (DURABLE work root; /private/tmp is wiped on reboot - never use it)

## Goal and metric
Reconstruct the lost Rust source of the main Pump Solana program (Anchor 0.31.1, crate `pump-recovered`) so the compiled ELF
matches the deployed original `W/base/original.so`. Metric: normalized function windows (1035 windows, functions.tsv
pump/selected). A window is matched when a candidate function symbol has the same length and identical bytes after masking ONLY
internal call immediates (op 0x85 src=1) and lddw values pointing into an ELF section. Everything else (registers, branch offsets,
stack offsets, constants, Source line numbers, filename lengths) must match. Raw matches (full bytes) are counted separately.

**Base = L06** (`W/base/L06`, `W/base/current` -> L06): the integrator's LAYOUT composite on Codex Round37 = all genuine lane
recoveries + the coordinate lanes' line positioning => **899 normalized / 165 raw / 136 unmatched** (identity recipe), unstripped
sha256 7bc1563b4965... (full hash in W/base/L06/inventory.json summary). Genuine-only twin: `W/base/g06` (811). Base source:
`W/base/current/pump`. Score with the default baseline (`W/base/current/inventory.json`). Categories: `W/base/L06/triage.json`.

**LINE-NEUTRAL EDITING (mandatory on L06).** Many files contain pad blocks introduced by `// layout-pad` comment lines; they hold
each error!/require! Source site on the line the original binary records. Your edits must keep every existing Source site on its
current line: change code within existing lines (statements may share a line), or if you add/remove N lines, remove/add the same
number of pad lines in the nearest `// layout-pad` block between your edit and the next Source site of that file. Re-score after
every build: a moved site shows up as a loss. If a window needs its own sites moved to their original lines, say so in
PROGRESS.md (the integrator re-runs the layout passes).

## Tools (W/harness, python3)
- `fastbuild.py --src <crate dir> --work <lane work dir> [--recipe identity|mac]`: faithful build. identity (default) = the
  original's toolchain (macOS v1.44 rustc + official Linux x86_64 v1.44 target libs, triple sbpf-solana-solana). Always recompiles
  the pump crate. Reports `runtime_valid` / `stack_warnings`. Shared build-slot pool W/locks (6 slots, shared with other sessions).
  ~40-90 s per build depending on machine load. Never run cargo directly.
- `score.py <unstripped.so> [--json out.json] [--quiet]`: exact replica of the Codex inventory; gains/losses vs the base. ~2 s.
- `win.py show <orig_start> [--cand so] [--sym REGEX] [--full]` aligned instruction diff vs the most similar candidate function;
  `win.py list|orig|sym`. `coords.py window <start>` / `coords.py fn <cand_addr>` decode Source {file,line} sites.
  `triage.py` re-categorizes. objdump: `~/.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objdump`.
- Targets: `W/targets/<lane>.json`.

## RUNTIME VALIDITY GATE (mandatory)
SBF stack frames are 4 KiB. A build whose log has "Stack offset of N exceeded max offset of 4096" is RUNTIME-INVALID (a corpus run
showed 482/827 migrate_v2 cases crashing for exactly that). Never deliver a build with stack warnings.

## Insights so far (apply them)
- `pub` items (external/hidden linkage) block LLVM ArgumentPromotion; `pub(crate)`/private helpers get by-reference params rewritten.
- `require_*!` evaluate operands twice: bind with `let` first when the original's with_values instantiation is const-propagated.
- The original uses Anchor library helpers and generated clients: system_program::transfer_with_seed,
  token_2022_extensions::harvest_withheld_tokens_to_mint, declare_program!(pump_amm)/(pump_fees) cpi clients and account types
  (the OLDER pump_amm IDL GlobalConfig ending at boost_enabled).
- Constructs the original lacks: runtime `pubkey!` (five8 decoding), u128 `Display` (require on u128). Removing such extras restores
  the library region's function set/order (raw).
- Source coordinates: the base already carries the integrator's line layout. If a target window becomes coordinate-only after your
  body fix, note its original vs current lines in PROGRESS.md and deliver the body fix; the integrator re-runs the layout passes.
- Original file tree (from .rodata): programs/pump/src/{lib.rs (~2,900 lines), admin_set_idl_authority.rs, buy.rs, buy_v2.rs,
  create_v2.rs, extend_account.rs, fee_recipient.rs, migrate.rs, migrate_v2.rs, multi_hop_curve_swap.rs, pump_quote.rs, sell.rs,
  sell_v2.rs, set_reserved_fee_recipients.rs, sweep_fees.rs, trade_v3.rs, creator/{admin_cto,collect_creator_fee,
  distribute_creator_fee_v2,distribute_creator_fees,distribute_fee_to_holders,migrate_bonding_curve_creator,set_creator,
  set_metaplex_creator}.rs, quote_control/{state,update_quote_control_mints,initialize_quote_control}.rs,
  token_incentives/{claim_token_incentives,volume_accumulator,init_user_volume_accumulator}.rs, util/{constant_product,fee,transfer_fee}.rs}.

## Working area and deliveries
- Lane dir `W/lanes/<lane>/` (cp -R W/base/current/pump W/lanes/<lane>/src; build with --work W/lanes/<lane>/work).
- NEVER modify: the primary checkout /Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source (read-only; `git -C <repo> show
  origin/main:<path>` is fine), W/base, W/harness, W/int, W/full, other lanes' dirs. No git commits/pushes (the coordinator does PRs).
- Stream deliveries: on every NET GAIN (gains>0, losses==[], raw_losses==[], runtime_valid true) write `W/deliveries/<lane>-NN/`
  (cumulative): `src/` crate snapshot, `patch.diff` (`diff -ruN W/base/current/pump W/lanes/<lane>/src`), `unstripped.so`,
  `candidate.so`, `build.log`, `score.json`, `delivery.json` {lane, base_round:"r37g4", base_unstripped_sha256, unstripped_sha256,
  normalized, raw, gains, losses, raw_gains, raw_losses, runtime_valid, synthetic_layout:false, files_changed, summary},
  `README.md` (what changed, binary evidence for each change). Log every experiment in `W/lanes/<lane>/PROGRESS.md`.
- Behaviour must stay equal to the original (byte-matched functions are correct by construction; for changed call paths confirm in
  the original disassembly that it performs the same calls/order). Never fabricate results.

## Peer-owned windows (parked; do not work on them, 2026-10-27 late)
- 0x47e28 base_token_program helper, 0x502f0 migrate_v2 create_pool helper, 0x43ea0 migrate v1 (peer lane pump-hi, migrate.rs/migrate_v2.rs).
- 0x38fc0 set_creator, 0x3a7b8 set_metaplex_creator (peer lane pump-big-lo, set_creator.rs).
- 0x746a8 admin_update_token_incentives (peer lane pump-big-lo, incentives.rs).

## Peer insight: data-first error path (llc-proven)
- `?` exits that share a StorageDead(event) drop-tree join: if only errors reach the join, InstCombine folds its phis into
  `phi {i64,ptr}` (result-first). An Ok return through the same join (e.g. an explicit `return Ok(())` inside the event's scope)
  stops the fold and gives data-first, as in the original.
- PER WINDOW ONLY, never as a sweep: apply it only where the ORIGINAL's error edge is data-first. A sweep over every
  emit_cpi! handler lost 9 result-first windows (0x662c8, 0x66fa8, 0x67c38, 0x6c160, 0x79bc0, 0x7a6c0, 0x1348c0, 0x135d60,
  0x137fc0). Candidates in the coordbody list: 0x138b20, 0x1557e8. Classify first with the peer's classifier:
  `git -C /Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source show claude/pump-big-lo-20261027:research/claude-pump-big-lo-20261027/tools/errpath.py`.
