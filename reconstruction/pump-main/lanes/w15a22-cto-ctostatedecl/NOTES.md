# w15a22-cto-ctostatedecl: CtoState declaration order (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs` line 100), pinned at 27,400 B.
Base: main 86e2a6b74 (program source unchanged through 9120883a9): 0.67376, 3,124 slots, M 2,249.
Ledger approach `ctostatedecl`, keys `0x22a10-w15-86e2a6b-ctostatedecl-{layoutmap,sweep720,d014523}-v1`.

**Result: no faithful gain, so nothing is landed. Main's declaration already gives the original's CtoState layout for all
8 fields.** Every other bool order moves at least two stores away from the original's offsets. Cause class G
(w15a11) is store order and register assignment, not layout. The best zero-loss build (0.67406 / 3,123 slots) gets
its gain from a register number that happens to match. The lane did not land it (see "Sweep").

## 1. Layout table: original vs main (`st` lives at r10-0x38, 48 B)

The store values come from orig 0x22e30-0x22ee0 and main 0x22df0-0x22f00. The original loads the curve bools early,
at orig 0x22ca0-0x22cc0, and keeps them in spill slots or r8 until these stores.

| field | loaded from | st offset | orig store | main store |
| --- | --- | ---: | --- | --- |
| creator | bonding_curve+8 (32 B) | 0 | [r10-0x38..-0x20] from r9+0..0x18 | same offsets, from r7+8..0x20 |
| max_fee | global+0x430 | 32 | `stxdw [r10-0x18], r4` | `stxdw [r10-0x18], r6` |
| mayhem | bonding_curve+0xa2 | 40 | `stxb [r10-0x10], r8` (held in r8) | `stxb [r10-0x10], r2` |
| holder_reward | bonding_curve+0xa5 | 41 | `stxb [r10-0xf], r0` (spill -0x8e0) | `stxb [r10-0xf], r4` |
| cashback | bonding_curve+0xa3 | 42 | `stxb [r10-0xe], r2` (spill -0x8e8) | `stxb [r10-0xe], r1` |
| quote_locked | memcmp chain | 43 | `stxb [r10-0xd], r2` (r3&1) | `stxb [r10-0xd], r3` |
| holder_enabled | global+0x43f | 44 | `stxb [r10-0xc], r1` | `stxb [r10-0xc], r9` |
| fee_configurable | global+0x43e | 45 | `stxb [r10-0xb], r5` | `stxb [r10-0xb], r0` |

repr(Rust) sorts by effective alignment. With a niche present, `[u8;32]` and `u64` both fall in group 3, and the
bools in group 0. The sort is stable, so rustc keeps declaration order within a group. The bools' relative
declaration order therefore fixes their offsets, and only main's order (mayhem, holder_reward, cashback,
quote_locked, holder_enabled, fee_configurable) reproduces the original's. Declaring max_fee before creator, or
creator last, makes no difference: w15a01's real captures `dc_last`, `dm_first` and `dm_last` are `eq_main`.
Interleaving the bools between creator and max_fee leaves the layout unchanged.

## 2. Mechanism: declaration order only remaps the six byte stores

rustc's Aggregate codegen stores fields in declaration order. Here that is always ascending offset, st+40..45. After
`opt -O3`, validate is inlined and every validate read of `st` is forwarded from the loaded values. The only post-opt
effect of the declaration is therefore which SSA value is stored at st+40..45. Both oracles below reproduce real
builds byte for byte:

- `tools/declperm.py` (raw-IR EDITS for `rx.py`, `ORDER=` env): rewrites the `gep i8, ptr %st, i64 40..45` offsets
  and alignments in execute and validate, plus the aggregate store slots. For `dl_mayhem`, `fn.bin` equals w15a01's
  real capture (`N_dl_mayhem`).
- `tools/postperm.py <m0 m.ll> <outdir> <workers> [orders]`: edits the post-opt slim `m.ll` and runs only `llc`, about
  0.5 s per variant instead of about 17 s for `rx.py`'s whole-module `opt`. It equals the `declperm` result, and
  measure.sh for 014523. **Any lever that lives entirely below opt (a post-opt store or value mapping) can be swept
  in seconds this way:** capture once with `rx.py <name> --base <raw.ll> --keep`, then edit `rx/<name>/m.ll`.

## 3. Sweep of all 720 bool declaration orders (post-opt oracle)

Names list the declared bool order as indices into (0 mayhem, 1 holder_reward, 2 cashback, 3 quote_locked,
4 holder_enabled, 5 fee_configurable). `012345` is main. Full table: `sweep720.json`.

| class | count | M | ratio | slots |
| --- | ---: | ---: | ---: | ---: |
| tie (includes main) | 532 | 2,249 | 0.67376 | 3,124 |
| tie, one slot fewer | 8 | 2,249 | 0.67376 | 3,123 |
| +1 | 164 | 2,250 | 0.67406 | 3,124 |
| +1, one slot fewer | 16 | 2,250 | 0.67406 | 3,123 |

Size is 27,400 B in every case, and no schedule or register assignment changes. The token diff touches only the
offsets of the stxb stores. Measured with measure.sh: `014523` (mayhem, holder_reward, holder_enabled,
fee_configurable, cashback, quote_locked) gives **0.67406 / 3,123 @ 27,400, 1034/1034, zero losses**.

It was not landed because the gained token, `stxb [r10-0xc], r1`, matches by coincidence. In the candidate, r1
holds cashback (bonding_curve+0xa3) stored at st+44. In the original, r1 holds holder_enabled (global+0x43f) at st+44.
Landing it would trade the original's provable field layout for one register-number match. Any later fix to the
register assignment would then have to undo it. This is the owner's call: the build is ordinary source (a plain
struct declaration, no forcing construct), and the one-line change is in ledger row `...-ctostatedecl-d014523-v1`.

## 4. What class G actually needs

The original's store sequence (cb, hr, my, creator ascending, ql, fc, he, max_fee) and its registers come from loading
the three curve bools before the quote_locked memcmps and holding them across them (class B). Source flag hoisting
does reproduce those load positions, but it costs 48 B and RA elsewhere. See `...-hkclone-flaghoist-v1`,
`...-faf9962-derefreread-flaghoist-gbind-v1` and `...-13fe453-earlyload-F0-v1`: skeleton L2 +62 tokens, but M 2,112 against main 2,245 on 13fe453. Layout
cannot move any of this.

## Next ideas

- Flaghoist F0 as a base, with the 48 B repaid by faithful data flow (spill-held curve bools, as in the original),
  then a register-assignment pass. Of the known class-B/G levers, only this one moves the skeleton.
- Use `postperm.py`-style post-opt llc-only sweeps for other levers that act below opt. They are about 30x faster than
  `rx.py`.
