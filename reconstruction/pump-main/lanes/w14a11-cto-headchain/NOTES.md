# w14a11-cto-headchain: skip-polarity gate + entry `shared` chain

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 769f331fe (0.63241, 3,288 slots; oracle fm 0.72618, sk 0.85051).
Angle: continue w13a49-cto-colderr (#3156) next ideas 1 and 2: pair the original's skip-polarity sweep gate
(`swept=if skip{Ok(0)}else{sweep(..)}?`) with an entry-chain spelling that tips the whole-function block-frequency
tie the way an IR `start`/`bb1` 16:1 weight does.
Ledger keys: `0x22a10-w14-769f331-headchain-*` (approach `headchain-source` and `ir-oracle`).

**Result: no zero-loss gain, no source change. The gate is a dead lever on this main.** Even when the head tie is
tipped (by an IR weight, by a source spelling, or by PDA-first), the gate costs 0.0001-0.0003 against the same
head without it.

## Oracle

w13a49's raw-IR capture (`capvar.sh` -> `capraw.py`) plus `rx.py` (opt -O3 + llc), repointed to this lane's out dir,
reproduces main exactly: `m4` = 0.63241 / 27,400 B, `eq_main: true`. IR edits go through w13a49 `tools/ed.py`
(-> w13a31 `bwfm.py`: plain ratio, fm = frame-masked, sk = frame+register-masked skeleton). New here:
- `tools/edr.sh <m.ll> <edit|-> spec..`: run ed.py for many specs in parallel, prefixed by the edit name.
- `tools/chunkfm.py a.txt b.txt [n]` / `tools/chunkraw.py`: per original-instruction chunk (default 256 insns =
  0x800 B), how many original instructions each candidate matches (frame-masked / frame kept). It localises a
  gain or loss to a region in one line per chunk. They import w13a49 `absratio.py` (copy it next to them).
- `edits/g1m4.py`: the g1 gate (skip-polarity phi, `br skip, post, sweep`) on 769f331's names
  (`%_502.sroa.0.0.off0`, `bb76`/`bb81`).

## 1. IR: the gate tie on 769f331 (`head_sweep1.txt`)

| IR | bytes | ratio | fm | sk |
| --- | ---: | ---: | ---: | ---: |
| main | 27,400 | **0.63241** | 0.72618 | 0.85051 |
| g1 | 27,392 | 0.4827 | 0.51805 | 0.65019 |
| `bw:start:16:1` (= `bb1:16:1`, `2000:1`) | 27,224 | 0.62459 | 0.71806 | 0.85212 |
| g1 + `bw:start:16:1` | 27,232 | 0.62449 | 0.71826 | 0.85229 |
| `bw:start:4:1` | 27,248 | 0.62491 | 0.71954 | 0.85204 |
| g1 + `bw:start:4:1` | 27,432 | 0.62156 | 0.71287 | 0.8509 |
| `bw:bb15:16:1` | 27,336 | 0.58278 | 0.72316 | 0.85243 |
| g1 + `bw:bb15:16:1` | 27,320 | 0.58206 | 0.72307 | 0.85329 |
| g1 + any `bb6`/`bb2.i` (global_quote) weight | | 0.482-0.485 | | 0.650 |

- The collapse still exists after #3200/#3207/#3215 (0.4827).
- `start`/`bb1` 16:1 restores the layout, but the gated build is **below** the same weight without the gate.
  The gate's value, once layout is restored, is about -0.0001.
- `start` 16:1 itself is not a layout change. `chunkfm`: frame-masked structure is identical to main except
  one 6-instruction block. It is register assignment only: 22 fewer copies/spills, -176 B. The fm loss is in orig
  0x5800-0x6800 (-37) and the gain is in 0x800/0x2800 (+10).
- Ungated `bb6` (global_quote `quote==default`) 1:2000 = 0.63388 @27,352 and 16:1 = 0.63308 @27,344 are pure
  register renaming (132 changed lines, no structure). They cannot be reached from source because global_quote is
  shared with matched functions, and no heuristic gives 1:2000 on a memcmp test.

## 2. Single-weight map on main (`sw_m4.jsonl`, 147 br x {20:12,12:20,16:1,1:16}, 588 runs)

- Best at 27,400 B: `bb37.i`/`bb38.i`/`bb93.i` 20:12, `bb58.i` 12:20 and the AccountInfo-clone `exit125.i` 1:16 all
  give **one identical binary, 0.63271** (fm/sk = main). It swaps two validate-head spill slots (0x908/0x910: the fee
  arg `r4` spill and the `hopt` flag). None of them is source-reachable: an eq-likely memcmp, or the fee range check
  made unlikely.
- Best fm at 27,400 B: `bb79.i` 12:20 (to_string unreachable edge) 0.62792, fm 0.73427.
- Off-size: `bb18` 1:16 0.63358 @27,352. `bb6` 16:1 0.63308 @27,344.

## 3. Source spellings of the entry chain, each alone and with the gate (raw-IR capture + rx = identity build)

`hN` = head spelling, `hNg` = head spelling + `swept=if skip{Ok(0)}else{sweep(&ctx,&holder_key)}?;`
(`src_edits/hN.py` EDITS plus `src_edits/g.py`). These are w13a23 `capvar.sh` EDITS lists. They apply to main
769f331 and cef0574 unchanged.

| trial | `shared` spelling | bytes | ratio | fm | sk | + gate |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| main | `key()==creator && owner==&FEES && !data_is_empty()` | 27,400 | 0.63241 | 0.72618 | 0.85051 | g: 0.4827 |
| h1 | owner==FEES first | 27,384 | 0.61612 | **0.73389** | **0.85166** | 0.46576 |
| h2 | `if key!=creator{false}else if owner!=FEES{false}else{!empty}` | 27,400 | 0.63241 (= main) | | | 0.4827 |
| h3 | `match (key==creator, owner==FEES){(true,true)=>!empty,_=>false}` | 27,400 | 0.53146 | 0.66147 | 0.84242 | 0.46039 |
| h4 | non-short-circuit `&` | 27,544 | 0.45085 | | | 0.45812 |
| h5 | closure with early-return guards | 27,400 | 0.63062 | 0.72618 | 0.85051 | 0.4809 |
| h6 | `data_len()!=0` | 27,384 | 0.52023 | 0.67096 | 0.8199 | 0.5215 |
| h7 | `!(key!=creator \|\| owner!=FEES \|\| data_is_empty())` | 27,208 | 0.60072 | 0.69633 | 0.84666 | 0.60042 (no collapse) |
| h8 | `key==creator && (owner==FEES && !empty)` | 27,408 | 0.63232 | 0.72607 | 0.85038 | 0.48262 |
| p1 | holder_key PDA **before** `shared`, `creator==key()` (original call order and memcmp operands) | 27,384 | 0.56428 | 0.65987 | **0.85945** | 0.56398 (no collapse) |
| p2 | PDA before `shared`, `key()==creator` | 27,384 | 0.56338 | 0.65898 | 0.85915 | 0.56308 |
| p1b/p1c | p1 with `find_program_address(..).0` / `let (holder_key,_)=` | 27,384 | 0.53791 | | | |
| p1d/p1e | p1 with `let holder_key=hk.0` / `hk.0` assigned after `shared` | 27,384 | 0.56368 / 0.56398 | | | |

What the table shows:
- **Every spelling that keeps main's layout collapses under the gate.** Only spellings that already change the
  whole function (h7: -192 B, a start-16:1-like RA shift; p1/p2: PDA first) keep the layout with the gate, and
  there the gate is again 0.0003 below the same head without it.
- h1 (owner test first) is the only fm/sk-positive head spelling (+0.0077 fm, +0.0012 sk). `chunkfm` puts the
  whole gain in the sharing CPI clone run (orig 0x4000-0x4800, +37 frame-masked). The head itself is worse (-12).
  With frame offsets kept (`chunkraw`), that clone run loses 29, because its spill slots move by 8. It is
  register-allocation chaos from the vreg order, not a structural lever.
- **p1 (PDA first, creator on the left) is the original head.** Its first 64 instructions match the original's
  instruction for instruction except frame offsets and registers: seeds at 0x2d0 vs 0x450, PDA out at 0x679 vs
  0x2d0, holder_key copied ascending vs the original's descending, accounts r6 vs r8, r5 copy r9 vs r6. It has the
  best skeleton seen on this main (sk 0.85945, +0.009). It loses all of that in orig 0x3000-0x3800 (fm -209, raw
  -181): the AccountInfo clone run uses r6 for the accounts pointer where main and the original use r8, with
  every spill slot moved by 8. This confirms w14a02 (#3209) on the newer main: PDA-first is a skeleton win that is
  register-limited. It is the head the original has, so a lane that pins the clone-run accounts register
  (w14a01-acctlive) should rebase its experiments on p1, not on main's shared-first head.

## 4. Re-check on main cef0574cf (#3210, 0.63421, 3,178 slots)

| trial | bytes | ratio | fm | sk |
| --- | ---: | ---: | ---: | ---: |
| m5 (main capture, `eq_main: true`) | 27,400 | 0.63421 | 0.72648 | 0.85021 |
| g5 (gate) | 27,408 | 0.48225 | 0.5176 | 0.6482 |
| h15 (owner first) | 27,384 | 0.61732 | 0.73419 | 0.85136 |
| h1g5 | 27,392 | 0.46622 | | |
| p15 (PDA first, creator left) | 27,384 | 0.56548 | 0.66017 | 0.85915 |
| p1g5 | 27,384 | 0.56518 | | |

The same pattern holds: the gate collapses on main's head, and on the PDA-first head it is -0.0003.

## 5. IR single-weight map on p1 (`sw_p1.jsonl`)

The best weights on the PDA-first head are 1:16 on the `Rc::inc_strong` / `AccountInfo::clone` overflow
branches of the clone run: `inc_strong.exit.i98.i` 0.59481 @27,360 (sk 0.85534), and `clone.exit40.i` /
`inc_strong.exit.i47.i` 0.59323 @27,368 (fm 0.70653, sk 0.85941). They partly move the accounts-pointer register
back. They are library edges that source cannot reach, and none comes near main. The p1 register loss sits in
the clone-run RA (w14a09-cto-pdara, w14a01-cto-acctlive), not in the entry chain.

## 6. Conclusion

- The skip-polarity gate is worth at most -0.0001 to -0.0003 once the layout tie is restored, on every head tried
  (IR 16:1, h7, p1, p2). Drop it from the residual list as a ratio lever. It is the original's form, so revisit it
  only after the clone-run RA matches.
- No source spelling of the `shared` chain reproduces `start` 16:1. The `&&`/`||`/`if`/`match`/closure forms either
  fold back to main (h2, h5) or change instruction selection (h3, h4, h6, h7).
- The amm `require!` memory-bool idea (w13a49 idea 2) was not built: the `bb66.i`/`bb13.i103` 20:12 weight
  it targets is fm-negative on 53abf28 (w13a49 sw_m3). On 769f331 the amm `require!` branch (`bb13.i103`) at 20:12
  or 12:20 is byte-identical to main, 16:1 gives 0.62912 and 1:16 gives 0.48989. Nothing is left to reach there.
