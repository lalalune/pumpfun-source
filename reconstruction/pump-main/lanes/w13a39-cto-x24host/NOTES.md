# w13a39-cto-x24host: the original's 24 B host at T 0x680 and the 0x630-0x6a0 block

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main fb8322295 / 16c10e631 (same admin_cto: 0.62043, 3,306 slots, 27,400 B, 1034/1034).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a39-cto-x24host/` (not in git).
Ledger keys: `0x22a10-w13-16c10e6-x24host-*`.

**Result: no zero-loss source change.** This PR only adds notes, the current bound, the object map and two small
oracle tools. Every gain found here needs a 33-40 B object that has no faithful source form yet.

## Current bound and object map (main 16c10e6, raw-IR capture + post-opt `llc` oracle, `eq_main=true`)

- Perfect-frame bound (`PF=1 iredit.py run`, w13a23 `framebound.py`): **0.64949** (0.617 on 06e6bb8, 0.6336 on d81d0f5).
- Bound for remapping **only** our offsets 0x538-0x6a0 (`tools/fbrange.py fn.bin 0x538 0x6a0`): **0.62582**, so
  this whole block is worth at most +0.0054. The rest of the 0.029 frame gap is elsewhere (deep spill slots and so on).
- `om/objmap-16c10e6.txt` and `om/layout-16c10e6.txt` (w13a23 `objmap.py`/`layout.py`). The block is unchanged
  from dfc3693:

| ours | object | size | original (votes / disassembly) |
| --- | --- | ---: | --- |
| 0x540 | `event_signers.i` + `target.i.sroa.0` | 16 | slice votes 0x680 (X24) |
| 0x560 | `sharing_update12.sroa.3` | 32 | bytes 0..24 vote 0x670/0x678/0x680: the payload tail lives in X24 in the original (orig 0x19a8 copies A 0x530 -> X24) |
| 0x630 | `old_creator` | 32 | 0x630, d=0 |
| 0x651 | `val6` | 33 | 0x651 (orig access pattern 0x631/0x639/0x641/0x649/0x64d) |
| 0x658 | `target.sroa.0` + `_116.i` | 7 | votes 0x538 (orig P1 7 B); the original's 7 B at 0x658 is `new`'s `[1,8)` entry piece |
| 0x679 | `hk` (PDA result, 33 B) | 33 | votes the 0x2d0 PDA temp: the original's sret is a short-lived temp in `_54.i`, seeds at 0x450 |
| 0x6a0 | `holder_key` | 32 | 0x6a0 (copy order differs: orig copies descending) |
| 0x6c0 | `mint` | 32 | 0x6c0, d=0 |

The original's 40 B between holder_key and the 7 B piece are **X24 (0x680, 24 B) + `new`'s 9 B piece (0x668)**.
Ours fills the same 40 B with `hk` (33 B + 7 B pad), which is why holder_key, val6 and mint already sit at the
original offsets.

## Oracle results (post-opt IR edits, `tools/x.py`; edit lists in `e/`)

| trial | edit | ratio | bytes | layout |
| --- | --- | ---: | ---: | --- |
| main | none | 0.62043 | 27,400 | as above |
| i1 | holder arm reads `holder_key` instead of `hk` (no lifetime change) | 0.62043 | 27,400 | hk stays conservative |
| i2 | i1 + `hk` lifetime ends after the holder_key copy (= "plain PDA") | 0.54584 | 27,400 | PDA sret 0x2d0 + seeds 0x450 as in the original, but everything below holder_key moves -40 B |
| c3/c4/f1/f3 | i2 + an unmerged stand-in of 33, 36 or 40 B where `hk` was | **0.62163** | 27,400 | holder_key 0x6a0, mint 0x6c0, stand-in at 0x679..0x680 |
| f2 / c1 | stand-in of 32 / 24 B | 0.53954 / 0.54224 | 27,400 | frame -8 / -16 |
| g1 | i2 + 24 B X24 + `target.i.sroa.9` (9 B piece) unmerged | 0.62133 | 27,400 | X24 0x680 and the 9 B piece at 0x668, both original offsets |
| g5 | i2 + `event_signers.i` as a 24 B X24 + 9 B piece + 16 B P1 at 0x540 | 0.40563 | 27,400 | every block object on the original offset, but `_11.i256` (0 B) merges into X24 and `_116.i` (1 B) loses its host: frame top -8 |
| g6 | g5 + `_11.i256` pinned | 0.51138 | 27,400 | `_116.i` alone at 0x451 shifts the frame +8 |
| n1 | i2 + an unsplit 33 B entry copy of `new` at the hk slot, read by the sharing arm | 0.60897 | 27,328 | copy at 0x680; abs ratio 0.71486 (> main 0.7124) but -72 B |

Mechanism: the only size-neutral gain in the block is the PDA temp. When the 33 B PDA result is a short-lived temp,
StackColoring puts its sret in `_54.i` at -0x2d0 and the seeds in `_128.i` at -0x450, which is the original's
`find_program_address` sequence (orig 0x22a90-0x22b48). That requires `hk` to die right after the holder_key copy.
The 40 B it vacates must then be refilled by an object that lives across the whole function and is not merged.
Anything smaller than 33 B shifts the frame below holder_key and costs about 0.08.

Faithful contents do not add to the opaque stand-in. With X24 and the 9 B piece at their original offsets (g1)
the ratio is 0.62133, below 0.62163. Putting the signer slice into X24 moves the 0x540 objects, and the 1 B and 0 B
allocas then lose their hosts.

## Why no source form was landed

- **Plain PDA** (`let (holder_key,_)=PDA` / `PDA.0` / a scoped `hk`) is i2. Earlier lanes measured it on several mains:
  entrycopy2 f6 0.51827, ctostatesroa k3, hkfirst2 hk3/hk4. They all lose the 40 B.
- The original's objects for those 40 B are `new`'s entry-copy pieces and X24. X24 holds the sharing/target tail of
  the 8/24 target split plus the wallet signer slice.
  - Entry copy: w13a28-cto-entrycopy2 (#3103). Any copy of `new` that validate does not read is removed by opt,
    because `new` is a noalias readonly argument. Forms where validate reads the copy lose 0.02-0.10 to register
    allocation.
  - 8/24 split: w13a02 (#2929) and w13a16 (#3009). Every fee-first form found so far is 8-104 B off size or loses ratio.
- The best natural 33 B candidate is the `args=&(new,)` temp. It sits at exactly the right MIR position, and n1
  emulates it. It survives only if `new` is written after the copy (the argument is then no longer readonly, so
  InstCombine keeps the copy). No faithful write to `new` exists in this handler.

## Next ideas (untried in source)

- `mut new` with a real later write, so the `args` copy survives as an unsplit 33 B object. n1 gives abs 0.71486
  but -72 B, so it would need size repair from the catalog.
- Restrict the next frame work to the region outside 0x538-0x6a0. Of the 0.029 frame gap, only 0.0054 is in this
  block.

## Tools

- `tools/x.py <post.ll> <name> <iredit spec> [edits.py]`: text edits (exact `(old,new)` pairs or callables) plus a w13a23
  `iredit.py` spec, then the `llc` oracle with `pf_ratio`. With `OM=1` it also runs `omap.sh` (debug llc layout + objmap)
  into `om/<name>`. It needs the w13a23/w13a35 tool set (`iredit.py`, `ctoracle.py`, `omap.sh`) next to it.
- `tools/fbrange.py <fn.bin> LO HI`: framebound restricted to our offsets in [LO,HI], with the remapped offsets and
  their votes.
