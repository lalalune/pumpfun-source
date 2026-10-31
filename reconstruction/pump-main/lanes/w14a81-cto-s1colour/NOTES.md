# w14a81-cto-s1colour: frequency levers that recolour s1's frame, priced on main 0d04cf4 (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 0d04cf460 (#3393): admin_cto 0.66507, 3,228 slots, 1034/1035 normalized, 1034 raw. Re-checked on
95a64ba75 (#3409, 0.66986, 3,204 slots) in sections 4c and 4d.
Continues w14a74-cto-s1tagjoin (#3395) next ideas 1-3, w14a47-cto-sharestruct (#3351) and w14a18-cto-slotpin (#3253).
Ledger: approach `s1colour`, keys `0x22a10-w14-0d04cf4-s1colour-*-v1`.

**Result: no source change. The s1 rescue by block frequency is closed.** Of 581 one- and two-weight pictures on s1, the
best is 0.64798. The 310 lattice-by-gate pictures top out at 0.66337. Even a perfect colour order for s1
(0.66887; 0.67276 with the gate weight) stays below main's own perfect colour order (0.68874). On 0d04cf4, holder's arg
spill stays at the head colour 0x8d8 in every single-weight picture on main. On 95a64ba the verdict is the same: s1
0.63969, its bound 0.66787 against main's 0.68544, and r1_program's jM is below main's. There, the whole
BPI-reachable frequency space on main is worth at most +0.0003.

## 1. s1 re-priced on 0d04cf4

s1 means plain `to_account_info()` for all 7 sharing accounts. The CpiContext program was already plain. s1 drops the
literal landings #3290-#3318, #3372, #3378 and #3393. It is regenerated from the current source by w14a74's `edits/gen.py`.
The rx oracle's m0 run reproduces main (`eq_main: true`).

| form | ratio | bytes | L0 / L1 / L2 (fmr) | cls orig 0x3c38-0x46b8 miss / fm / rm / jm / sk |
| --- | ---: | ---: | --- | --- |
| main 0d04cf4 | 0.66507 | 27,400 | 0.66507 / 0.70132 / 0.78310 | 190 / 24 / 0 / 0 / 166 |
| s1 | 0.63589 | 27,360 | 0.63589 / 0.69135 / 0.81247 | 233 / 30 / 123 / 15 / 65 |
| s1 + gate 8:1 (IR) | 0.64608 | 27,360 | 0.64608 / 0.69135 / 0.81247 | 232 / 29 / 123 / 15 / 65 |

Inside the sharing CPI, s1's deficit is **registers** (rm 123) and not the frame (fm 30 against 24). The frame loss
(plain - L1 = 0.0555 against main's 0.0363) is mostly outside the region, in spill colours that the clone run's spill
intervals share with later code. The gate weight is frame-only: L1 and L2 do not move, and the region's fm moves by 1.

## 2. Weight screen (`tools/wscan.py`)

`wscan.py <m.ll> <out> --pre i:a:b,... [--ws ...]` works on an rx `--keep` post-opt module. Each picture adds a `!prof`
to one more conditional `br`, by index in execute (the same indexing as w14a74 `bwsweep.py`). It reports the plain
ratio, fmr L0/L1/L2, cls fm/rm/jm/sk over orig 0x3c38-0x46b8, and the prologue arg-spill offsets (`pro`). The sharing
gate is br 114 (`icmp ne i8 %_433.sroa.0.0, 2`, -> bb36 the CPI arm) in both s1 and main.

### s1 + gate 8:1, plus one weight on each of the other 145 brs x {8:1, 1:8, 2000:1, 1:2000} (`data/wscan_s1_gate8.jsonl`)

| second weight | ratio | bytes | L1 | L2 | region fm/rm/sk |
| --- | ---: | ---: | ---: | ---: | --- |
| (none) | 0.64608 | 27,360 | 0.69135 | 0.81247 | 29/123/65 |
| Rc trap br 79 / 80, 1:2000 | **0.64798** | 27,352 | 0.69085 | 0.81259 | 29/123/65 |
| br 116 (first sharing clone's inc_strong) 1:8 | 0.64738 | 27,352 | 0.69175 | 0.81259 | 28/120/65 |
| Rc traps 129/130, 1:2000 | 0.64668 | 27,360 | 0.69255 | 0.81817 | 30/136/44 |
| br 31 (`bb19`, the shared-arm `if holder`) 1:8 | 0.64636 | 27,312 | **0.71568** | 0.83841 | 29/123/65 |

- No picture reaches main. The best plain is 0.64798, and the Rc trap weights cannot be written in source (w13a26).
- br 31 1:8 lifts L1 by +0.024, but `tools/l1m.py` shows that this is a jump-distance coincidence. All 91 new L1 matches
  are validate's error blocks (orig 0x9d0-0xe40). Their code is byte-identical to s1's except the long `ja` to the
  shared error tail: at -48 B, `ja +0x9ad` equals the original's. On main the same weight gives L1 0.69955.
  Do not read L1 gains at a different size as structure.
- The region's register misses (rm 120-136) do not move under any weight. Frequency changes only the frame here.

### Main, one weight on each of the 146 brs x {8:1, 1:8, 2000:1, 1:2000} (`data/wscan_main_single.jsonl`)

The best is Rc traps 79/80 at 1:2000: 0.66687 (+0.0018), frame-only and not expressible. This is w14a74's result again.
**In all 581 pictures, holder's r3 arg spill stays at 0x8d8, the head colour** (the original's is 0x918). The
prologue offsets change only for r4 (0x908 to 0x900, 79 pictures) and r2 (0x930 to 0x928, 9 pictures). The 0x8d8/0x8e0
colour order (holder against the accounts pointer, section 3) cannot be reached through block frequency. holder's
entry-block refs outweigh every reachable reweighting. That needs holder's representation changed (w14a10 e3/a1,
and1outline, autospell `unwrap_or(false)`: all screened and below main).

## 3. Colour-order bound (`tools/chill.py`, `tools/swap1.py`, `tools/slots.py`)

`slots.py` finds the 8-byte direct-access frame colours: objects accessed only by `ldxdw`/`stxdw`/`stdw` at exactly
that offset, never address-taken, with no overlapping access (127 in main, s1 and the original). Permuting their
offsets is always a legal frame for the same colouring, and a frequency change that only reorders StackSlotColoring's
weight order can do no more. `chill.py` hill-climbs that permutation on the plain rx ratio. It swaps each colour with
one of its top-3 L1-alignment vote targets. One metric takes 0.03 s, so a base takes about 30 s on an idle machine.
`swap1.py` lists every single pairwise swap.

| base | ratio | bytes | colour-order bound | M (matched orig insns) | colours moved |
| --- | ---: | ---: | ---: | --- | ---: |
| main 0d04cf4 | 0.66507 | 27,400 | **0.68874** | 2,220 -> 2,299 | 31 |
| s1 | 0.63589 | 27,360 | 0.66887 | 2,121 -> 2,231 | 37 |
| s1 + gate 8:1 | 0.64608 | 27,360 | 0.67276 | 2,155 -> 2,244 | 36 |
| s1 + gate 8:1 + trap 79 1:2000 | 0.64798 | 27,352 | 0.67316 | 2,161 -> 2,245 | 35 |

- s1's best possible colour order is 55-68 M below main's. A frequency lever on s1 would have to beat main's
  real frame and also give up main's frame potential. The lattice table (section 4) ranks the hybrids the same way.
- The best single colour swaps on main (`data/sw_m0.jsonl`; 84 of 7,875 gain) are:
  - 0x8d8 <-> 0x8e0 (holder against the accounts pointer): +0.00389;
  - 0x8e8 <-> 0x950 (the sharing-tag spill against the slot the original reloads before the sweep `?`): +0.0024;
  - 0x930 <-> 0x938: +0.0018;
  - 0x908 <-> 0x910: +0.0015.

  These match w14a18's f8dc table. No single swap is worth 0.005, and section 2 shows that none of them is reachable
  by frequency.
- This bound agrees with w14a18's hill-climbed legal frame (main f8dc 0.6865), and it needs no MIR round trip. Use it to
  rank bases by frame potential.

## 4. s1 hybrids: literal/plain lattice x gate weight (`tools/gatelat.py`, `data/gatelat.jsonl`)

There are 62 raw-IR captures: 6 singles `r1_<field>`, which revert one literal to `to_account_info()`, and 56 combinations
`lat_<fields>`. Each is priced with the gate at none, 8:1, 2:1, 20:12 (the zero-heuristic 5:3 a BPI-visible spelling would
give) and 1:8.

| form | none | 8:1 | 2:1 | 20:12 | 1:8 |
| --- | --- | --- | --- | --- | --- |
| main | **0.66507**@27400 | 0.65309 | 0.65309 | 0.65169@27392 | 0.60234 |
| r1_program | 0.66337@27392 | 0.65318 | 0.65318 | 0.65298 | 0.60333 |
| r1_authority | 0.66297@27400 | 0.65608 | 0.65608 | 0.65468 | 0.60234 |
| lat_au_pr | 0.66127@27392 | 0.65408 | 0.65408 | 0.65388 | 0.60333 |
| r1_pool_authority | 0.66007@27392 | 0.65019 | 0.65019 | 0.64999 | 0.60333 |
| lat_mi_ev_pr | 0.63410@27384 | 0.65508 | 0.65508 | 0.65518 | 0.60192 |
| lat_mi_ev | 0.63301@27400 | 0.65458 | 0.65458 | 0.65318 | 0.60234 |
| s1 | 0.63589@27360 | 0.64608 | 0.64578 | 0.64588@27352 | 0.60249 |

- All 310 pictures are below main. Main's all-literal form is still the lattice optimum, and the gate weight never
  pays when it is added.
- The gate weight helps exactly the forms where mint and event_authority are plain (+0.02 on lat_mi_ev). It costs
  0.007-0.012 wherever the authority or program literals remain. The two levers pull against each other, so no
  hybrid gets both.
- 20:12 prices like 8:1 (within 0.002), so a BPI-visible spelling would capture the whole gate lever. The gate is
  `icmp ne i8 tag, 2` on the `Option<Option<Pubkey>>` niche (None = 2), which no BPI heuristic biases. The candidate
  spellings (a compare with a non-zero constant, a switch with an explicit arm, an Option discriminant) only matter
  if the weight pays. It does not, on any base in the lattice, so they were not built. The toolchain is rustc
  1.79, which has no `cold_path`, and `likely` needs a feature gate.

### 4b. Colour-order bounds of the lattice (`data/chill_lattice.txt`)

| form | ratio | bytes | colour-order bound | M |
| --- | ---: | ---: | ---: | --- |
| r1_authority | 0.66297 | 27,400 | 0.68904 | 2,213 -> 2,300 |
| main | 0.66507 | 27,400 | 0.68874 | 2,220 -> 2,299 |
| lat_au_pr | 0.66127 | 27,392 | 0.68734 | 2,207 -> 2,294 |
| r1_program | 0.66337 | 27,392 | 0.68704 | 2,214 -> 2,293 |
| r1_pool_authority | 0.66007 | 27,392 | 0.68464 | 2,203 -> 2,285 |
| (every form with mint or event_authority plain) | | | ≤ 0.6805 | ≤ 2,270 |

Only r1_authority ties main's frame potential (+1 M), and its real ratio is 0.0021 lower. The forms the gate weight
helps (mint/event plain) have the lowest frame potential.

## 4c. Re-check on main 95a64ba (#3409, admin_cto 0.66986, 3,204 slots; `data/captures_95a64ba.jsonl`, `data/chill_95a64ba.txt`)

#3409 re-derives `holder` from the argument at the curve store and the event. holder's r3 arg spill moved off the head
colour (0x8d8 to 0x8e8). The original's prologue colours are r4 0x928, r3 0x918, r1 0x8f0, r2 0x938, against main's
0x910 / 0x8e8 / 0x8f0 / 0x938.

| form | ratio | bytes | L1 | jM (jump-masked matches, `tools/jmr.py`) | gate 8:1 | colour-order bound |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main | **0.66986** | 27,400 | 0.69982 | **2,264** | 0.65488 | **0.68544** (M 2,288) |
| r1_program | 0.66906 | 27,392 | 0.70352 | 2,259 | 0.65888 | 0.68464 |
| lat_au_pr | 0.66637 | 27,392 | 0.70442 | 2,248 | 0.65978 | |
| r1_authority | 0.66717 | 27,400 | 0.70072 | 2,253 | 0.65578 | |
| lat_mi_ev | 0.63860 | 27,384 | 0.68834 | | 0.65358 | |
| s1 | 0.63969 | 27,368 | 0.68076 | 2,168 | 0.64568 | 0.66787 (M 2,228) |

- r1_program and lat_au_pr have a higher L1 than main, but a lower jM. Their L1 lead is frame-side, so no 8 B repay
  can lift them above main. The w14a31 +8 B knobs are size-neutral on this main (`data/knobs_95a64ba.jsonl`):
  - `Rent::get()?.minimum_balance(0)` inline is token-identical to main;
  - `ensure_rent_exempt` as `if let Err` gives 0.66597 at 27,400;
  - `prepare_bonding_curve` as `if let Err` gives 0.66417 at 27,400;
  - the `let rent` split gives 0.58393 at 27,368.

  The hybrids r1_program + those knobs are 0.66337-0.66906.
- The best single colour swap on this main is 0x8e0 <-> 0x950 (+0.0018, `data/sw_main_95a64ba.jsonl`). The old
  0x8d8/0x8e0 lever is gone.
- w14a85-cto-s1reload prices the register side of s1 on this main. Its region-ideal register bound is 0.67356, and
  s1 + per-clone acc reload from clone 4 gives 0.65309. Its rows and this lane's frame and frequency rows agree:
  s1 needs the original's register naming of the whole region and its frame together. Neither alone beats main.

### 4d. The BPI-reachable frequency space on main 95a64ba (`data/wscan_main95a64ba_bpi.jsonl`)

A source spelling can only change a branch's probability by the BranchProbabilityInfo heuristics. It can add a
compare-with-zero/null/-1 (20:12 either way), or remove one (1:1). The screen puts {20:12, 12:20, 1:1} on each of the
146 conditional brs: 438 pictures, 4 of them above main, each by **+0.0003 (1 M)**. All 4 are frame-only (L1 and L2
equal main's), and all move the r4 arg spill from 0x910 to 0x908:

- br 16 / br 18 at 20:12: validate's `bcmp(..)==0` Pubkey tests with the memcmp heuristic reversed. That cannot be
  written without replacing the Pubkey compare.
- br 27 at 20:12: the `quote_locked` i1 phi test in validate. It has no heuristic today, and a `u8`/`!=0` spelling
  folds back to the i1.
- br 28 at 12:20: the `icmp ult` `or.cond` fee-range test.

Every other BPI-reachable picture is at or below main. On this main, the frequency route is worth at most +0.0003.

## 5. Why frequency cannot rescue s1 (mechanism)

- s1's region loss is register assignment (rm 123). In the original the accounts pointer is spilled at 0x8d8 and
  reloaded before each clone, the sharing tag stays in r6, and swept stays in r9. In s1 the accounts pointer is held in
  r7 for the whole run and r9 is free scratch. Block weights move spill-slot order. They never move which values are
  register-resident across the arm: rm is flat over 581 pictures.
- w14a69 showed that coalescing swept into the payload class lowers s1 to 0.58171. w14a47 showed that a per-clone
  accounts-pointer reload leaves rm at 100. The register state is not reachable from the sharing region alone.

## Tools (experiment only; run next to w14a74's `rx.py`, `cls.py`, `fmr.py`, `px.py` in the same `tools/` dir)

- `wscan.py`: the weight screen above (`--pre` fixed weights, `--only` for the base picture).
- `px_w.py`: px.py edit that applies `PXW=i:a:b,...` weights (for `px.py name m.ll px_w.py`).
- `gatelat.py`: gate-weight pricing of every `rx/lat_*`, `rx/r1_*`, `m0`, `s1` capture.
- `slots.py`, `chill.py`, `swap1.py`: the 8-byte colour set, the colour-order hill-climb and the single-swap table.
- `l1m.py a.bin b.bin lo hi [lvl]`: which original instructions match at level `lvl` in b but not in a, as runs.
