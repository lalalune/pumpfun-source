# Lane w7r1-buyexactquoteinh-hillclimb

Target `0x13f630` `buy_v2::buy_exact_quote_in_handler` (original 20,184 B). Approach: an automated
source-mutation hill-climb. Fitness was the masked instruction distance to the original listing
(`dist`, computed like w6r1 `sodist.py`) plus `target_metric.py` ratio, gated on score.py showing zero losses.

Baseline: origin/main 6edd839 (1027 normalized / 276 raw), eq 20,216 B, ratio 0.99635, dist 11 (5 hunks:
mov r7,2 schedule, Complete-if sense, terminal `jne r7,2`, Rc drop-tail duplication).

Result: no source change from this lane beat the baseline (dist 11). The target is normalized by another
lane, PR #2269 (`w7r1-buyexactquoteinh-regsched`, built on #2240). I rebuilt that PR head (0c5b0033a)
myself and got unstripped sha256 `bd7cb4247cf730fb4cd5b540eb7be44d815fdd096d4166f2be639db8b72c0537`, 1028/276,
gain 0x13f630, no normalized or raw losses. Because of that match, I stopped this lane.

Engine (outside git): `~/.cache/pumpfun-reconstruction/lanes/w7r1-buyexactquoteinh-hillclimb/engine/`
(`engine.py` makes trial crates and builds them 2 at a time with the slot locks respected; `tail.py` renders
the tail genome; `gen1..gen7.py` are the generations; `results.jsonl` holds every trial).

## Generations (about 130 builds)

| gen | mechanism family | trials | best | notes |
| --- | --- | ---: | --- | --- |
| 1 | Complete CPI in a ProgramResult helper (invoke tail, caller `.map_err(Error::from)?`) | 6 | e2 repro 20184/dist 15 | the helper drops the authority_info Rc before the tag test; the original tests first. plain/#[inline] helpers are outlined |
| 2 | tail-structure grid: helper scope {cpi, body, if, if+prepare, trade+if+prepare} x consume {?, if-let, match, map_err, tail} x drop(ev) x ctx by &mut/value | 46 | trade-tail 20200/dist 14 | `?`/match/qmap byte-identical; if-let adds a call; by-ref == by-value ctx |
| 3 | shareholders `unwrap_or_default` respellings (mov r7,2 phi order) | 13 | = base | 10 are byte-identical to base |
| 4 | manual emit_cpi expansion helper endings (map_err tail, Into, `?;Ok(())`) | 13 | 20088/dist 33 | |
| 5 | plain/#[inline] helpers; authority_info borrowed (slice::from_ref) | 10 | none | borrowing drops one call (129 vs the original's 130) and shifts the whole frame |
| 6 | single mutations on the trade-tail and ifprep-tail seeds (prepare spelling, Complete condition, complete=true placement, ctx paths, mayhem bbp) | 33 | trade 14, ifprep 17 | most are byte-identical to the seed |
| 7 | shareholders statement / TradeEvent field position sweep | 2 | none | stopped once PR #2269 normalized the target |

## Key observations
- rustc/LLVM gives the same bytes for most spellings: `?`, `match`, and `map_err(|e|e)?` on a helper
  Result all produce identical code, and so do the shareholders default spellings and the Complete
  conditions `0==x`, `!=0 {} else`, and the ctx path.
- `if let Err(e)=helper(..){return Err(e);}` always adds a call (131) and recolors the frame.
- A ProgramResult-returning CPI helper can't match: the original tests the invoke result before it drops
  the authority_info Rc (the macro's `?` runs while the statement temporaries are still alive).
- Plain and `#[inline]` single-call-site helpers holding emit_cpi are never LLVM-inlined into this handler,
  so only `#[inline(always)]` (the AlwaysInliner) can supply call-scoped lifetime markers.

Ledger rows: lane `w7r1-buyexactquoteinh-hillclimb`, dedupe keys `0x13f630-main-6edd839-hc-*`.
