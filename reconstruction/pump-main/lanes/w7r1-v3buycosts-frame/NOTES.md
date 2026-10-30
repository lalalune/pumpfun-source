# Lane w7r1-v3buycosts-frame: stack-frame / slot oracle for `trade::v3_buy_costs` (0x80df8)

Base: origin/main a418dd3f1 (official 1027 normalized / 276 raw, unstripped sha256 15ef746e4fca...).
**No source change.** Every frame-family source trial builds a byte-identical ELF or a worse target.
This lane rules out the stack frame as the place where the residual lives.

| Build | Bytes | ratio | diff lines (orig/cand) | calls | official |
| --- | ---: | ---: | ---: | ---: | --- |
| base a418dd3 | 2,136 | 0.920 | 9 / 11 | 17/17 | 1027 / 276 |
| t01 t02 t03 t04 t06 t07 t09 | byte-identical ELF (sha 15ef746e) | | | | 1027 / 276 |
| t08 add3#1 by-value `match` | 2,176 | 0.741 | | 17/17 | 1027 / 276 |

## 1. The frame already matches

* Every `r10` offset in the window is the same in the original and in our build: 26 frame objects
  from 0x1 to 0x1c0, including the 7 spill slots 0x190..0x1c0. The ZST at `r10-1` is used by
  exactly two `unwrap_failed` tails in both.
* `w4-frame-oracle/frameoracle.py` on the base IR (llc reproduces the fastbuild bytes): 0 delta
  breaks, 0 StackColoring group mismatches, 0 alloca-order violations. StackColoring groups:
  {formatter x2}, {buf x2}, {_3 x2}, {_2.i33, _2.i, _83, _30, _24} at 0x118, the same as the
  original's implied groups.
* The whole residual is the register allocation of the sret pointer. The original spills it at
  entry (`stxdw [r10-0x190], r1` as its third instruction) and reloads it into `r3` at both tails.
  We store it after `and64` and reload it into `r6` before the net check, and we duplicate one
  `ldxdw r2/ja` block. The spill slot (FI19, 0x190) is the same.

## 2. Frame-family levers on the IR oracle (one-function module, SDK llc, ~0.1 s per run)

| Scan | Runs | Result |
| --- | ---: | --- |
| Swap any two of the 12 allocas (MIR local order / inlined-callee order) | 66 | always 2136 B; only stack offsets move; RA never changes |
| Split the merged ZST `%_11.i.i29` per inlined body (s2 / c371 / c375 and combinations) | 15 valid | 2136-2184 B, 35-128 lines worse |
| Empty block carrying only ZST lifetime markers on one CFG edge (a bb4-like MBB) | 43 + 903 pairs | none better than base |
| Same on top of the bb4-marker deletion | 43 | none restores the front |
| Move one lifetime marker (StorageLive/StorageDead placement) to the top or bottom of any block | 2,366 | none better; only moves that empty bb4 give the known e1 state (2120 B, sret like the original, front -51/+51) |
| Same 2,366 moves on top of the bb4 deletion | 2,366 | none restores the front; any marker put back in bb4 gives the base exactly |
| 1-8 extra entry-block lifetime.starts (the prologue-placement lever proven elsewhere) | 80 | ZST: identical to base at every count; non-ZST markers only break StackColoring |
| Store the Result tag in each `bb15` predecessor instead of the sunk `.sink` phi | 63 subsets | 2128-2224 B, none matches |
| Branch weights 3:5/5:3/1:1 (zero/pointer heuristic or none), plus 1:2..1:2^20 singles | 208 singles, 1,080 pairs, 15,120 triples | every 0-diff result has a weight on `%43` (the 375 `to_string` fmt panic edge); 0 without it |

What this shows:

1. bb4 is the empty block, with only a ZST lifetime marker, on the mayhem && post-Some path of the
   second split. Whether it exists as an MBB decides the front's register assignment and the sret
   split together. The original has the base's front, so it keeps bb4 (or an equivalent block).
   No other marker placement or empty block separates the two decisions.
2. Pre-greedy MIR of the base and of the `%43 1:2000` variant (which is a 0-diff 2120 B match) is
   identical except for one successor probability (`bb.31 0x800` vs `0x106035`). If the original's
   pre-RA MIR is ours, it differs only in that probability. Frame objects, lifetime pseudos and
   alloca order cannot produce it.
3. Source spellings in the frame family (MIR local order, scoping blocks, destructuring, deferred
   init, by-value helpers, return-tuple locals) are all erased by SROA/CopyProp before llc. They
   produce the same IR and so the same ELF.

## 3. Source trials (ledger keys `0x80df8-main-a418dd3-<key>-v1`, `trial.sh`)

* scope-block-split (t01), split-destructure (t02), post-fee-byvalue-map (t03), split-tuple-locals (t04),
  post-buyback-deferred-init (t06), mayhem-flag-byvalue-helper (t07), ok-tuple-local-out (t09):
  byte-identical ELF.
* first-match-byvalue (t08): 2176 B, 0.741. This is the same mechanism as w7r1-v3buycosts-sibling's
  sib-first-match, which ran at the same time.

Analysis rows: frame-slot-map, alloca-order-swap-scan, zst-alloca-split-scan,
zst-edge-marker-block-scan, lifetime-marker-move-scan, sret-tag-unsink-scan, heuristic-weight-scan,
heuristic-weight-triple-scan, entry-lifetime-count-scan.

## Tools (`oracle/`)

* `capture_full.py`: IR capture build. It now hooks `fastbuild.run_compiler`; fastbuild no longer
  calls `subprocess.run` for cargo, so the w4 hook silently captured nothing.
* `irlib.py`: one-function llc runner with a diff against `win.py orig`. Thread-safe; `suffix=`
  appends metadata.
* `allocascan.py`, `zstsplit.py`, `edgescan.py [pre.py] [pair]`, `ltmove.py` (`PRE=edit.py`),
  `unsink.py`, `bwscan.py single|pair|triple` (`PRE=`).
* `trial.sh <name> <patch.py> <slot>`: source trial. It patches trade_v3.rs (line count is
  asserted), builds, scores against the base and prints the target metric.

## Next ideas (outside this lane's angle)

* The frame and lifetime layer is closed for this window. What remains is the `%43` probability, or
  a pre-RA MIR change elsewhere that is code-neutral and not a frame object. Examples: IR block
  order and SlotIndex numbering (the blockorder lane), or instruction order inside blocks that
  changes ISel scheduling and vreg numbering (the regsched lane).
* Under the 2026-10-30 build-inputs rule (not allowed in this lane's prompt), the check would be a
  toolchain whose to_string `expect` lowering gives the fmt branch metadata in this function only.
  w4's global-weighting census shows a uniform policy breaks 7 matched windows.
