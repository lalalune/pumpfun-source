# w14a19-cto-framebasis: pure-frame knob basis and frame compensation for admin_cto::execute

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main f8dc9016f (0.63481, M 2119 at 27,400 B). Ledger: approach `framebasis`, keys `0x22a10-w14-f8dc901-framebasis-*-v1`.

**Status: notes only, no source change.** The premise of the angle (skeleton-positive forms lose because they add or remove
a stack object ahead of the spill area) does not hold for the strongest bases. Where it does hold (the V-forms), a perfect
compensation is measurable in IR but does not beat main.

## Oracle

Raw-IR capture + `opt -O3` + extracted `llc` (w14a08 `src.sh`/`xo.sh`, repointed), with `-stop-after=prologepilog` and
`mirframe.py` for the post-PEI frame-object list. It reproduces main exactly (0.63481, 3,337 insns, 27,400 B, 88 lddw).
Conventions: an object at MIR offset `-X` is addressed as `r10 - X` (spill slots start at `r10-0x8d8` on main, the 4 arg
spills land at 0x910/0x8d8/0x8f0/0x930 against the original's 0x928/0x918/0x8f0/0x938).

New tools (`tools/`, paths point at this lane's out dir):
- `fdelta.py ref var`: frame-object delta in frame-index order: inserted/removed objects and the shift of every later run.
- `objmap.py xdir [-v]`: aligns the frame-masked streams against the original and, per candidate frame object, prints the
  accesses whose offset equals the original's and the dominant (orig - cand) deltas. Also the best single-cut shift.
- `amove.py in out alloca:after ...`: IR-only experiment that moves static allocas inside execute's entry block (frame-index
  order), then llc + score + frame map. This is the "perfect compensation" bound.
- `mm.py xdir..`: matched original instructions M under four masks: none (the ratio), jumps masked (J), frame masked (F), both.
- `mk.sh name genes`, `q.sh queue`, `screen.sh base prefix knobs`: variant runners (two captures at a time).
- `fg2.py`: the w14a08 gene library re-anchored for f8dc901 (RAR, B3) plus w14a15's `p1 e3 tu8 hb0 s1` and the new
  `HKR HK1 HK2 TE*` forms. `rec.py`: ledger rows.

## 1. Frame-object deltas of the skeleton bases against main (f8dc901)

| base | bytes | M | J | F (frame-masked) | alloca delta against main |
| --- | ---: | ---: | ---: | ---: | --- |
| main | 27,400 | **2119** | 2144 | 2260 | - |
| e3+tu8 (w14a10) | 27,336 | 2045 | 2164 | 2374 | **none** (identical object list, spill start 0x8d8) |
| U2 = e3+tu8+s1 (w14a15) | 27,272 | 2032 | 2156 | 2365 | **none** |
| s1 (w14a05) | 27,368 | 2065 | 2064 | 2255 | **none** |
| p1 PDA-first (w14a09/11) | 27,360 | 1886 | 1922 | 2110 | **none** |
| f2 = RAR+hb0 (w14a07) | 26,912 | 2080 | 2138 | 2296 | **none** |
| B3 / et+B3 | 27,352 | 1950 | 2031 | 2279 | none (B3 no longer skeleton-positive on f8dc901) |
| V1 (holder_key by value) | 27,440 | 1806 | 1892 | 2269 | `+target.i.sroa.0` 7 B (align 4) after `event_signers.i`: **+8 for every later object and all spills** |
| V2N | 27,328 | 1861 | 1900 | 2285 | `+sk` 32 B before hk: +32 from hk on (both 7 B target pieces fold into sk) |
| **e3+tu8+V1** | 27,424 | 1932 | 2013 | **2407** | +8 from 0x548 (as V1) |
| U2+V1 | 27,376 | 1900 | 1976 | 2360 | +8 from 0x548 |

So the best skeleton bases (e3+tu8, U2, s1, p1, f2) lose nothing to stack objects: their frame-object lists equal main's.
Their frame loss is spill-slot order (register allocation), and their other loss is jump distances (J - M is 119 for
e3+tu8 against 25 for main). w14a18-cto-slotpin reaches the same conclusion from the other side: every base pinned to
main's frame stays below main (e3+tu8 2102, U2 2095, s1 2093).

## 2. The pure-frame knob basis (code identical, F unchanged; MIR deltas)

| knob | source form | delta (MIR, post-PEI) | net |
| --- | --- | --- | ---: |
| HK0 | `let (holder_key,_)=Pubkey::find_program_address(..)` | removes `hk` (33 B, align 1, plus its 7 B padding hole) | -40 from holder_key on |
| VS | validate takes `sharing:Pubkey` by value | adds `sk` 32 B; StackColoring folds execute's `target.sroa.0` (7 B) into it | +32 from hk on |
| VS+HK0 | both | | -8 from holder_key on |
| HK1 / HK2 | `let hk=..;let holder_key=hk.0;` (holder_key declared after hk) | swaps hk/holder_key in frame order; the 7 B hole moves from after hk to before mint | 0 at mint |
| TE* | `let mut target;` declared early, `target=validate(..)?` | validate's piece is gone, execute's `target.sroa.0` (7 B) and `target.sroa.8` (9 B, align 8, normally folded away) sit where the declaration puts them: after hk (TE, +8), after holder_key (TE0b/TE2, +16), after val6 (TE3/TE4, +16) | +8..+16 |
| TE5 / TE6 | declared inside the validate block | no change (TE5) / code change (TE6) | |
| HKR | `let holder_key=&hk.0;` | removes holder_key (-32), **changes code** (F -16 on e3+tu8) | not pure |

Layout facts that decide all of these: execute's own allocas are laid out in reverse MIR-local order after all
LLVM-inlined (`.i`) allocas; 33 B align-1 objects (`hk`, `val6`) leave 7 B holes before the next align-8 object; there are
exactly two 7 B holes in main's frame (after `_11.i264` at 0x1..0x8 and after `hk` at 0x679..0x680).

## 3. Compensation bound for the V-forms (IR)

`amove.py x/et_v1 x/et_v1_am1 target.i.sroa.0:hk` puts V1's extra 7 B object into hk's padding hole. The frame-object list
then equals main's exactly (the top hole after `_11.i284` gives the same frame):

| form | bytes | M | J | F | ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 27,400 | 2119 | 2144 | 2260 | 0.63481 |
| e3+tu8+V1 | 27,424 | 1932 | 2013 | 2407 | 0.57853 |
| **e3+tu8+V1, frame compensated (IR)** | 27,424 | 2096 | **2219** | 2407 | 0.62764 |
| e3+tu8+V1 with the piece after mint / sk / holder_key (IR) | 27,424 | 1957-1967 | | | 0.586-0.589 |

A perfect source compensation would recover +164 M on e3+tu8+V1, but it still sits 23 M below main because of the +24 B
and its jump distances (J is +75 over main, so the rest is size/jump repay, w14a15's problem, not frame).

No source form found realizes the compensation: the V1 piece belongs to the inlined validate, so it is always laid out
before execute's own objects, and every faithful knob that moves or removes an object of execute (HK0, VS, HK1, TE*) has
the wrong size (-40/+32/0/+8..+16). The arithmetic is tight: val6+target.sroa.0+hk+hole is exactly 80 B; adding V1's 7 B
piece needs 88 B in any packing, so only an object removal (HK0, -40) or a StackColoring fold (VS-style) can cancel it,
and both conflict with V1 (V1+VS = V2N, which changes code: F 2365).

## Ledger keys

`0x22a10-w14-f8dc901-framebasis-<name>-v1` for hk0 vs v1 v2n v2nhk et u2 s1 p1 f2 et_v1 et_v1_am1 and the rejected
combinations (et_v2nhk et_v1_hk0 et_vshk et_v2n et_hkr et_v1_hkr et_v2n_hkr et_v1_hk1 et_v1_hk2 et_v1_te* u2_v1 et_b3 ...).
Data: `data/framedelta_f8dc901.txt` (M/J/F + frame deltas), `data/objmap_*.txt`, `data/frame_main_f8dc901.txt`.
