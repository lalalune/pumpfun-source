# crank-frame PROGRESS (window 147944 crank_donation_fee_pda) — round 3
Lane dir: RR/lanes/crank-frame. src/ = w584 clone (pristine), target/ = warm native clone.
out/ = build outputs, v/<name>/ = variant trees (each with own target-*), an/ = analysis, tools/ = scripts.

## Plan
1. Reconstruct crank-b v08 (best near-miss of round 2: 15976B/1950i masked 0.9641 raw 0.9533, only RA residual
   in SyncNative metas/infos region 12352..13900) on w584 from findings-recovered/crank-b.
2. Frame/RA analysis with --emit=llvm-ir + llc loop; enumerate source forms of metas/infos/ix construction.

## Log
- 20:55 lane set up.
- 21:02 tools: tools/mkvar.py NAME SPEC (variant tree v/NAME/src from src + spec HANDLER/HELPER/EVENT/EXTRA),
  tools/run.sh NAME SLOT [rustc args] (build in t/SLOT, score -> out/scores.log), tools/cx.py (masked/raw/depth),
  tools/fmask.py (frame-masked compare), tools/extract_fn.py + llc loop (an/*.ll -> .o EXACT vs rustc build, 0.1 s),
  tools/ocmp.py (.o/.so vs original or vs --so).
- 21:03 v08 RECONSTRUCTED on w584 = specs/v08r.py (direct mint cond + direct receiver temporary + helper
  sync_native_excess -> Result<Option<u64>> + anchor-form Event::data): 1950i/15976B masked 0.9641 span 74,
  raw 0.9508 span 115, depth 2168 == orig. (specs/v08.py with named `mint` + named relay_accounts = depth 2392:
  mint slot 32B + event.sroa.0 192B not merged into receiver.)
- 21:20 KEY: llc loop on v08r IR. ONE IR edit makes llc emit the ORIGINAL crank body EXACTLY (ocmp EXACT=True,
  raw 1.0000 vs original window, call/lddw imm masked): the rent-AccountInfo clone in the SyncNative infos must
  RE-LOAD the key ptr `load ptr, ptr %_17` (rent info ptr) instead of reusing the AccountMeta key-ptr load %_72.i
  (GVN merges them in v08r because `rent: &AccountInfo` is a noalias-readonly helper param). File an/e1.ll / e1.o.
  => need a source form where the two loads of rent.key are NOT GVN-merged (rent access not noalias-scoped),
     while the rent info ptr is still loaded at the call site (orig 6904, before Rent::get).
- 21:08 w01 (`rent: &UncheckedAccount` helper param, `rent.to_account_info()`) = EXACT vs original (ocmp), measure
  gained [147944], lost []. w02 same sha. w03 (UncheckedAccount by value) no fix.
- 21:10 DIRECTIVES 21:08: Crank CLOSED by crank-brute-g01 (same fix). My w01 sha e7781591... == crank-brute-g01 ==
  crank-transfer-g01. Not harvested (duplicate). STOPPED per directive; final notes in shared/findings/crank-frame.md.
