# w14a77-cto-entrykeycopy: entry key-copy / PDA-input spelling screen (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 0d04cf460 (#3393), admin_cto 0.66507 / 3,228 slots, 1034/1034. The oracle reproduces it (`main0`, `eq_main: true`).
Angle: clean-room screen of the entry region (orig 0x0-0x800). Find which entry comparison or PDA input gives the
original's copy-then-memcmp idiom at orig 0x148-0x1c8, keeping main's shared-first call order.
Ledger: approach `entry-key-spelling`, keys `0x22a10-w14-0d04cf4-entrykeycopy-<trial>-v1`.

**Result: no zero-loss gain and no source change.** Every shared-first spelling either compiles to main's bytes or loses.
The copy-then-memcmp idiom is already main's shared test. What the original does differently in 0x0-0x800 comes from
three faithful entry forms. Each one loses alone, and together they lose more:
- the PDA first (`pda`);
- the curve bools read before `quote_locked` (`fl`);
- the holder_key copy to -0x518 (`hkc`).

## Mechanism: where the copy-then-memcmp idiom comes from

- The original's orig 0x148-0x1c8 is the `shared` test:
  - `ldxdw r1,[r8+0x90]`: sharing_config AccountInfo, spilled to -0x8e0;
  - `ldxdw r1,[r1+0]`, then 4 ldxdw/stxdw pairs: key copy to -0x2d0;
  - `bcmp(curve+8, -0x2d0, 32)`.
- Main produces the same 10-instruction copy plus memcmp at cand 0x88-0xf8 with the by-value `a.sharing_config.key()`.
- Every deref or reference spelling (`*key`, `key==&creator`, `&creator==key`, and an `&AccountInfo` binding) removes the
  copy. That is exactly -80 B: 8 ldx/stx plus the 2-instruction `-0x2d0` lea. So the original compared a by-value
  `.key()` temporary, as main does. Main's spelling is the original one.
- The original's other two differences at this site are register and order effects, not spelling effects:
  - The curve pointer is loaded first into r9 and kept, giving the `mov r1,r9; add r1,8` left operand (creator on the left).
  - The sharing pointer is spilled.
  - On main, the creator-on-the-left spelling `hL` loads the curve first as the original does, but into r1. It costs 0.0018.
  - The original keeps r9 because the curve bools are read right after the chain (`ldxb [r9+0xa3]`). In main, the PDA
    call comes in between.
- The 36-instruction run the brief calls "different" (cand 0x80-0x1a8) is the shared chain itself, aligned against the
  original's PDA block. The original runs the holder_key PDA (orig 0x80-0x140) before the chain. Main runs it after
  (cand 0x1a8-0x268). A local alignment can match only one of the two blocks, so the shared-first order caps the local
  rm at 150/246, whatever the spelling.

## Tools (`tools/`, `e/`)

The tools run next to w14a02's `slots.py`, `abs.py`, `oracle.py`, `rx.py` and `capraw.py`
(`origin/swarm/w14a02-cto-validatecr`, copied into `$OUT/tools`).
- `entry.py <m.o|so> [--show]`: local rm/fm/exact alignment of orig 0x0-0x800 against cand [0,0xa00), plus the
  global rm count for 0x0-0x800 and for the whole window. `--show` prints the miss table.
- `reg8.py`: per-0x800 exact/fm/rm matched counts.
- `spans.py A B`: orig spans rm-matched in B but not in A, and the reverse.
- `batch.sh g1+g2 ...`: 2-wide capvar+rx runner over `e/genes.py`. Gene names joined by `+` compose. `e/knobs.json`
  holds the 43 size knobs that still apply, as `k_<name>`.
- `rec.py`: ledger recorder.

## Entry miss table (main 0d04cf4, register-masked local alignment of orig 0x0-0x800)

The full instruction table is `entry_miss_0d04cf4.txt`: each orig instruction with its aligned cand instruction or `--`.
The unmatched orig runs, in order:

| orig | n | what | why main misses it |
| --- | ---: | --- | --- |
| 0x0d0-0x0d8 | 2 | PDA arg lea r2=-0x450 | the seeds slice is at -0x2d0 in main (frame); the PDA sret goes to -0x679, not -0x2d0 |
| 0x148-0x2b0 | 46 | shared chain (sharing ptr spill -0x8e0, key copy, memcmp, owner memcmp, data_is_empty) + curve reload + bool loads 0xa3/0xa5/0xa2 | order: aligned to the PDA block instead (PDA-first); bools: main reads them after quote_locked |
| 0x358 | 1 | `add64 r9,8` (curve+8 creator base) | main copies creator from curve+8..+0x20 descending, before the bools |
| 0x440 | 1 | reload of the spilled 0xa3 bool | bools not hoisted (`fl`) |
| 0x468-0x4b0 | 10 | CtoState.creator copy, ascending from r9=curve+8 | main copies it descending at cand 0x3d8 (the copy exists, at another place and in another order) |
| 0x4e0-0x538 | 12 | `new` Option entry copy (tag, [1..9), [8], [16], [24], [32]) | not source-expressible on main (w14a67 h7, w13a41) |
| 0x5a0-0x5d0 | 7 | holder_key copy -0x6a0 -> -0x518 | `&{holder_key}` reproduces it (`hkc`, w14a63) but cascades |
| 0x5e0-0x618 | 8 | mayhem jne into the tail; spill reloads; `and r8,1` holder | validate-head register/order (w14a02, w14a10) |
| 0x718-0x740 | 5 | 289/306 and-1 tests | validate outline (w14a10 and-1) |

## Trials (raw-IR capture + rx opt/llc oracle, main 0d04cf4)

L = local alignment of orig [0,0x800) against cand [0,0xa00). G = global difflib alignment, the one score.py uses.
"rm" masks registers, frame offsets and jump targets. "exact" masks only call and lddw immediates.

| trial | bytes | ratio | eq main | L rm | L exact | G rm 0x0-0x800 | G rm total |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| main0 | 27,400 | **0.66507** | yes | 150 | 78 | 131 | 2,782 |
| hL (creator on the left) | 27,400 | 0.66327 | no | 150 | 73 | 131 | 2,782 |
| kd `*key==creator` | 27,320 | 0.66367 | no | 150 | 73 | 131 | 2,782 |
| kdL `creator==*key` | 27,320 | 0.66397 | no | 150 | 73 | 131 | 2,782 |
| kr `key==&creator` | 27,320 | 0.66367 | no | 150 | 73 | 131 | 2,782 |
| krL `&creator==key` | 27,320 | 0.66397 | no | 150 | 73 | 131 | 2,782 |
| sciL (`&AccountInfo` binding, creator left) | 27,320 | 0.66397 | no | 150 | 73 | 131 | 2,782 |
| sci / ownd / skl / peq / mintd / seeda / hkb / hkty / hkpair / hkcp | 27,400 | 0.66507 | yes | 150 | 78 | 131 | 2,782 |
| crl (curve creator local) | 27,472 | 0.66477 | no | 150 | 79 | 131 | 2,782 |
| crr (curve creator ref local) | 27,400 | 0.66327 | no | 150 | 73 | 131 | 2,782 |
| hklate (`holder_key=hk.0` after quote_locked) | 27,400 | 0.66507 (slots 3,232) | no | 159 | 78 | 140 | 2,791 |
| hkmut | 27,432 | 0.66467 | no | 150 | 78 | 131 | 2,782 |
| seedk (`a.mint.key.as_ref()` seed) | 27,400 | 0.65908 | no | 149 | 77 | 130 | 2,781 |
| seedr (`&mint.to_bytes()` seed) | 27,464 | 0.66038 | no | 150 | 82 | 131 | 2,782 |
| mintlate | 27,416 | 0.63971 | no | 150 | 73 | 131 | 2,787 |
| qlr (`&quote_mint` ref) | 27,184 | 0.62295 | no | 103 | 68 | 75 | 2,718 |
| shqm (shared after quote_locked) | 27,304 | 0.58013 | no | 142 | 69 | 122 | 2,770 |
| sdl / sda (named seeds local / array) | 27,400 | 0.5722 | no | 149 | 77 | 130 | 2,672 |
| hkd / hkt (`let holder_key=..0` / `let (holder_key,_)=..`, the AMM sibling's form) | 27,400 | 0.55992 | no | 151 | 76 | 132 | 2,674 |
| hkblk / hkblk2 (PDA in a block) | 27,400 | 0.55902 | no | 151 | 73 | 132 | 2,674 |
| mintk (`to_account_info().key`) | 27,648 | 0.57522 | no | 142 | 71 | 129 | 2,670 |
| mintpid (`ctx.program_id`) | 27,576 | 0.47201 | no | 147 | 74 | 126 | 2,172 |
| **fl** (curve bools into locals before quote_locked) | 27,408 | 0.64071 | no | 155 | **89** | 134 | **2,852** |
| fl+hL | 27,408 | 0.63891 | no | 155 | 83 | 134 | 2,852 |
| hkc (`&{holder_key}`) | 27,464 | 0.54159 | no | 157 | 80 | 137 | 2,677 |
| fl+hkc | 27,496 | 0.5323 | no | 164 | 86 | 142 | 2,740 |
| pda+hL | 27,400 | 0.57519 | no | 184 | 92 | 163 | 2,832 |
| pda+hL+fl | 27,512 | 0.47564 | no | 191 | 100 | 170 | 2,200 |
| pda+hL+hkc | 27,448 | 0.5205 | no | 193 | 89 | 172 | 2,694 |
| pda+hL+fl+hkc (full original entry) | 27,568 | 0.42646 | no | **198** | **104** | **178** | 2,111 |
| pda+fl+hkc | 27,568 | 0.42556 | no | 197 | 101 | 177 | 2,110 |

| cr1 / cr2 / cr4 / cr5 (creator `.clone()`, `new_from_array(to_bytes())`, `{&..;*c}`, a creator local) | 27,400 | 0.66507 | yes | 150 | 78 | 131 | 2,782 |
| **cr3** (creator last in the CtoState literal) | 27,408 | 0.63831 | no | 143 | 77 | 125 | **2,876** |
| fl+cr3 | 27,264 | 0.64214 | no | 149 | 79 | 131 | 2,843 |
| fl+cr5 | 27,408 | 0.64071 | no | 155 | 89 | 134 | 2,852 |

**fl partner screen.** `fl` was paired with each of the 43 `sizeknobs-cto.json` knobs that still apply to current main
(`e/knobs.json`). The best was fl itself (12 knobs tie at 0.64071 / 27,408 B). The only pair at 27,400 B is
`fl+k_cu_fee_replace`, at 0.63721 with 3,307 slots. No partner lifts fl above 0.64071.

## Findings

1. **Main's shared test is already the original spelling.** The by-value `.key()` temporary is the copy-then-memcmp
   idiom. All 4 deref/ref forms drop the copy (-80 B) and lose 0.0011-0.0014. The `&AccountInfo` binding is the same.
2. **The deferred `let holder_key; ... holder_key=hk.0;` is load-bearing.** It costs 0.105 to spell the PDA as
   `let holder_key=...0`, as the AMM sibling's `let (holder_rewards,_)=..`, or inside a block. A named seeds slice or
   array costs 0.093. All of these collapse the frame and RA tail (G rm total -110). Spellings that keep the tuple local
   and the deferred init (hkty, hkpair, hkcp, hkb) are byte-identical to main.
3. **`fl` raises G rm total by 70 (2,852 against 2,782) and entry exact by 11, but finding 5 shows most of the rm gain
   is clone-run alignment noise.**
   - The rm gain sits in orig 0x4000-0x4800 (+61). The global alignment there follows the original order instead of
     jumping, in the clone run after the sharing CPI.
   - Plain ratio drops 0.0244 through register assignment: exact matches fall in orig 0x2000-0x3000 (-47) and
     0x3800-0x4000 (-17).
   - The bools land at orig 0x290-0x2b0 exactly (a3, a5, a2).
   - w14a04/w14a41 measured this as M -145 on older mains. It is now -0.024.
4. **The full original entry (pda+hL+fl+hkc) reaches 198/246 local rm and 104 exact in 0x0-0x800 (+48 / +26).** That
   clears the angle's +20 bar by a wide margin, but the whole function collapses to 0.426 (G rm total 2,111). The entry
   forms do not compose with main's tail RA: each one moves a different long live range (holder_key tuple, curve-bool
   SSA values, the sharing pointer).
5. **The fl / cr3 rm gains in orig 0x4000-0x4800 are alignment artifacts, not skeleton wins.** That region is the
   long run of AccountInfo Rc clones: `ldxdw [r+8]`, `ldxdw [r]`, `add 1`, then `jne r,1 / ja 0x26e0` overflow traps.
   Every clone looks alike under the register mask, so any shift lets difflib re-pair blocks in order. Exact
   matches there do not rise (main 108, fl 101, cr3 92).
   The real cost is the same register cascade the PDA-first lanes found. In orig 0x2000-0x3000, fl has 121 register
   mismatches against main's 69: r8->r6 21 times (the accounts-pointer `%0` split moves to r6, as with `pda`, w14a09)
   and r5->r7 31 times.
6. `hklate` is a rm-only artifact: +9 G rm, equal plain ratio, +4 slots. The 8-instruction hk copy aligns with the
   original's second copy at orig 0x598.

## Next ideas

- Cascade census over the rm-matched instructions in orig 0x2000-0x3800 (register and frame-offset mismatches against
  the original):

  | trial | register mismatches | r8->r6 | frame mismatches |
  | --- | ---: | ---: | ---: |
  | main | 146 | 0 | 43 |
  | fl | 182 | 24 | 50 |
  | pda+hL | 307 | 24 | 134 |
  | hkc | 148 | 0 | 165 |
  | cr3 | 162 | 0 | 92 |

  `fl` and `pda` share the accounts-pointer `%0` split moving to r6 (24 sites). `hkc` and `cr3` are frame-colour
  cascades instead (registers unchanged, frame mismatches 4x / 2x), as w14a63 found for hkc.
- A lever that pins `%0` to r8 independently of the entry would unlock `fl` and `pda` together (w14a09's IR asm pin
  got within 0.007-0.009). A frame-colour fix for the holder_key copy would unlock `hkc`. Until then, entry-spelling
  lanes cannot gain.
- For rm-based screens, mask or drop the orig 0x3e00-0x4800 clone run, or use a block-anchored alignment. Otherwise
  difflib re-pairing there shows up as fake +60..+90 rm "skeleton" gains.
- `pda+hL+fl+hkc` is the original's whole entry. Any future RA fix for the tail should be rescreened on that base, not on
  `pda` alone.
