# w14a04-cto-hkclone: repairing the hk-first sweep clone run (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w13a32-cto-hkfirst2 (#3093, next idea 1) and w13a48-cto-vaultspill (#3193, hk-first trials).
Bases: main 23322b07c (0.62882) for the screens, re-measured on main cef0574cf (0.63421).
Ledger keys: `0x22a10-w14-23322b0-hkclone-*-v1`.

**Result: notes only, no programs/ change.** Under hk1 (the holder-rewards PDA moved in front of `shared`),
no source form found here repairs the sweep clone run. The hk-first local optimum is about 0.606 on 23322b0
and 0.603 on cef0574, which is 0.023 to 0.031 below main.

Every number is the raw-IR capture + `opt -O3` + `llc` oracle (w13a50 `capvar.sh` -> `rx.py`). The base capture
reproduces main exactly (`eq_main: true`, 0.62882 and 0.63421). fm and rm come from `abs.py` (fm masks frame
offsets and jump targets, rm also masks registers). The per-bin counts are fm-matched original instructions per 0x800
(`reg.py`).

## Main measurements

| trial | main | bytes | ratio | fm | rm |
| --- | --- | ---: | ---: | ---: | ---: |
| main | 23322b0 | 27,400 | 0.62882 | 0.72049 | 0.84781 |
| hk1 | 23322b0 | 27,384 | 0.56758 | 0.66197 | 0.85706 |
| hk1 + bumparr_top (hk1ba) | 23322b0 | 27,384 | 0.60563 | 0.70962 | 0.85496 |
| main | cef0574 | 27,400 | 0.63421 | 0.72289 | 0.84661 |
| hk1 | cef0574 | 27,384 | 0.56458 | 0.65838 | 0.85526 |
| hk1ba | cef0574 | 27,384 | 0.60264 | 0.70602 | 0.85316 |
| bumparr_top alone | cef0574 | 27,408 | 0.60147 | 0.70361 | 0.84229 |

fm-matched original instructions per 0x800 bin (23322b0):

| bin | 0 | 800 | 1000 | 1800 | 2000 | 2800 | 3000 | 3800 | 4000 | 4800 | 5000 | 5800 | 6000 | 6800 | sum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main fm | 98 | 130 | 148 | 200 | 209 | 180 | 193 | 205 | 112 | 214 | 216 | 199 | 212 | 89 | 2405 |
| hk1 fm | 123 | 130 | 148 | 196 | 204 | 172 | **51** | 140 | 112 | 223 | 218 | 195 | 208 | 89 | 2209 |
| hk1ba fm | 123 | 130 | 148 | 196 | 196 | 175 | 153 | 202 | 112 | 223 | 218 | 195 | 208 | 89 | 2368 |
| main rm | 131 | 138 | 163 | 211 | 233 | 250 | 248 | 236 | 163 | 244 | 236 | 239 | 241 | 97 | 2830 |
| hk1 rm | 166 | 138 | 163 | 211 | 233 | 250 | 246 | 235 | 163 | 245 | 235 | 239 | 239 | 97 | 2860 |

The 0x3000 bin's rm under hk1 is already at main's level (246 vs 248). **The clone-run collapse is all register
naming.** Structurally hk1 is ahead of main (rm +30), and the instruction-class histogram is the same as main's.

## Mechanism map: why hk1 loses the sweep

1. **hk1 is the original's entry structure.** With the PDA first, GVN load-PRE turns the bonding_curve pointer into
   `phi [_249, start], [_249, bb2], [reload, bb3]`: the pointer is reloaded only in the `data_is_empty` block. This is
   exactly orig 0x258-0x278 (`call data_is_empty; ldxdw r9,[r8+0x38]` inside that block, `shared=false` stored at entry).
   On main the PDA call sits between the memcmps and the join, so the load stays a plain load in the join block.
2. **The sweep runs on the accounts pointer's register.** At the sweep gate the original reloads `holder` (-0x8f8)
   into r6 at 0x1d30 (it is dead on the sweep path; this is a greedy split artifact), keeps bump in r7 and `native` in r9,
   and reloads the accounts pointer from -0x8d8 into **r8**. Every account-field load of the sweep and the clone run is
   `[r8+X]`:

   | | sweep accounts ptr | bump | native | r6 |
   | --- | --- | --- | --- | --- |
   | orig | r8 (from -0x8d8) | r7 (spilled -0x910) | r9 (spilled -0x918) | holder (reload) |
   | main | r8 (from -0x8d8/-0x8e0) | r9 | r7 | `&holder_creator_vault` gep |
   | hk1 | **r6** (from -0x8e0) | r9 | | free |
   | hk1ba | **r6** (from -0x8e0) | memory (-0x4d0) | r9 | |

   In hk1 r6 is free across the sweep, so the sweep piece of the accounts pointer takes its entry hint r6. In the
   entry the accounts pointer is r6 in every build of ours, while the original has it in r8 (with the stack-args pointer
   in r6, `&new` in r7 and the curve in r9). `tools/fmloss.py main.o hk1ba.o 1800 3000` lists the losses: almost all
   are `[r8+X]` -> `[r6+X]` and the native/bump reload pairs.
3. Base-vs-hk1ba fm losses per bin (`fmloss.py`) are in 0x1800-0x3800. hk1's gains are bin 0 (+25) and 0x4800 (+9).
   The account-field access order of the clone run is identical in orig, main and hk1ba
   (`58 0 18 20 28 b0 a8 b8 80 c8 c0 88 e0 d8 e8 48 ...`), so the clone order itself is right.

## Clone-run and entry forms screened on the hk1 base

| form | base | bytes | ratio | note |
| --- | --- | ---: | ---: | --- |
| w13a30 segscan, 228 AccountInfo clone field-segment moves | hk1 | 27,384 | 0.56788 best | +0.0003 (c0:w0) |
| same | hk1ba | 27,384 | 0.60593 best | +0.0003 (c0:e0) |
| 144 single catalog genes (genes30 + knobs34 + genes47) | hk1ba | | 0.60609 best | `pre_sk_first` @27,344; 83 change codegen, all in -0.01..+0.0005 |
| 44 random pairs of the 39 best codegen-changing genes | hk1ba | 27,344 | 0.60579 best | |
| hk6: FPA first, `holder_key` decl+copy after `shared` | 23322b0 | 27,384 | 0.56698 | +ba 0.60503 |
| hk7: decl + FPA first, copy after `shared` | 23322b0 | 27,384 | 0.56728 | +ba 0.60533 |
| hk9: hk1 + `let sk=sharing_config.key()` bound in `shared` and reused by validate | 23322b0 | 27,232 | 0.53253 | +ba 0.54846; sk9 (main + sk) 0.5518 |
| CtoState curve bools read into locals before `global_quote` (any order, tuple or lets) | main | 27,352 | 0.58231 | loads land exactly at orig 0x280 (a3,a5,a2); 0x2800 bin 180 -> 94 |
| same | hk1ba | 27,472 | 0.5439 | bin 0 123 -> 139, the rest collapses |
| w13a38 h2 holder phi (H2b / phi only) | main | 27,200 / 27,240 | 0.60051 / 0.59105 | |
| hk1 + h2 (H2b / phi only) | 23322b0 | 27,512 / 27,528 | 0.45561 / 0.46115 | hk-first and the holder phi are strongly antagonistic |
| hk1ba + h2 | 23322b0 | 27,528 / 27,544 | 0.45457 / 0.45981 | |
| `&new` kept live (cef0574): nw1 `Some(new)` in the sharing arm, nw3 `args=&(new,)` after `sk` | hk1ba | 27,344 | 0.59949 / **0.60399** | nw3 +0.0013 over hk1ba (0x4000 bin 112 -> 134); `&new` is still spilled at entry and accounts stay r6. nw2 (validate reads `args.0`) 0.43737 |
| IR probe: inline-asm r6 clobber at every sweep block (hk1ba) | | 27,464 | 0.47247 | too invasive: the barriers change the block layout |

The flag-hoist trial is the first source form that puts the original's early curve-flag loads at orig 0x280. It also makes
the r4 arg spill land at the original's -0x928 on main and, under hk1ba, reloads `skip` from a spill slot at the sweep
gate as the original does. But it costs RA everywhere else (+88 B on hk1ba), so it is a lever only together with
something that brings the sweep back.

## Conclusion

hk-first is the original's entry, both structurally (rm +30) and through the PRE phi. It loses only through register
*naming* in the sweep, because the sweep accounts pointer inherits r6 instead of r8. None of the source forms tried here
change that naming without a larger loss elsewhere: clone field order, catalog genes and pairs, hk spellings, the
holder phi, or entry flag order. hk1ba's best is 0.606 against main's 0.629 / 0.634, so size knobs cannot close it.
The hk-clone angle is exhausted on 23322b0 / cef0574.

## Next ideas (untried)

- Find what makes the original's entry put the stack-args pointer in r6, `&new` in r7 and the accounts pointer in r8.
  Ours always gives accounts r6 first. The original keeps `&new` in a register until the entry copy, and ours spills it.
  An entry form that keeps `&new` live in a register through the CtoState build would raise entry pressure the way
  the original's does, and might move accounts to r8 for the whole function. hk1 would then inherit r8 in the sweep.
- A form where `holder` is live (reloaded) at the sweep gate without the h2 phi: the original reloads holder into r6
  right before the skip test. A post-sweep use of a `holder` local reached through the gate might occupy r6.
  `ev_hold` / `pa_hold` alone did not do this under hk1ba.

## Tools (`tools/`, text only; run from the lane's `$OUT` with the w13a50 oracle tools next to them)

- `rmap.py <m.o> lo hi [v]`: orig->candidate register pairs over rm-aligned instructions in an orig range, and fm mismatches.
- `fmloss.py A.o B.o lo hi`: original instructions fm-matched in A but not in B (and vice versa), with the other side's text.
- `side.py <m.o> <orig_addr> [before after]`: orig vs candidate side by side around an orig address (rm alignment).
- `ir_clobber_probe.py`: ctoracle `--edit` that inserts an inline-asm register clobber at every sweep block (`CLOB=r6+r9`).
- `rec.py`: ledger record helper. `e/common.py`: the source edits (HK1, BA, FL, HK6/7/9, H2b/H2n) for main 23322b0.
  For cef0574, SH reads `a.sharing_config.key()==a.bonding_curve.creator` (left/right swapped by #3215).
