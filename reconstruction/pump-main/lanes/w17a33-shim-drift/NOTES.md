# w17a33-shim-drift: neutral-drift harvest (admin_cto 0x22a10, shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 8bee07558 (admin_cto bytes = 53ec7fb53): 0.68754, M 2,295, 3,096 slots, 1034/1034.
Ledger: approach `drift`, keys `0x22a10-w17-8bee075-drift-<item>-v1`.

Angle: use shim cells that change bytes but leave M unchanged ("neutral cells") as free base moves, and re-screen the
union of the single-edit generators on top of each one ("neutral cell A x every single edit B").

## 1. Oracle

w17a06's slim pre-opt oracle (`capraw.py` + `preslim.py` + `fx.py`, survivor list `surv-1647da0.txt`), process-pool
screener w17a24 `screenp.py` plus a signature -> M cache (`tools/screenq.py`). My capture of the worktree
(`ir/m0.s.ll`, md5 `bb4ff0763c19`) is byte-identical to w17a15 m6 / w17a22 m3 / w17a24 main3 / w17a26 m0 / w17a27 m0:
M 2,295 @27,400 B, sig `61dcfe87f489`, ratio 0.68754 = `current-baseline/cto.json`. Every edit file of those lanes
therefore applies by line index. Throughput on the loaded machine: about 180 combos per minute with 8 workers.

Union edit file (9,524 single edits on main's slim module): w17a15 `all_edits_m6` (pt/pb + call results, 1,061),
w17a24 `ann3_edits` (ai/ap/au/ax/se, 3,270), `vgen.py` (vaA/vaB/vaC, 1,464), w17a26 `eall` (assume eq/rg, 1,286),
w17a06 `gen.py` (vl/vs/bf/bw/sw/rr/na, 2,443; bp excluded from screens).

Main reference (`res/ref.json`, 6,082 cells): the w17a15 beam6, w17a24 ann3, w17a26 assume and w17a22 priced-vann
tables, plus a new screen of the w17a06 gen.py families on this main (1,792 cells: bw/sw/rr/na/vl:fld/bf/vs:fld and
the local volatile loads/stores, nothing above main at any size; neutral at 27,400 B: `vl:execute:28931/28930/28862/
28854`, `bf:execute:30752/30041`, `bf:wallet:31266`).

## 2. The neutral pool (re-verified)

All 46 neutral singles of the tables reproduce exactly (M, bytes, signature). They fall into 13 signatures; with the
gen.py ones, 19. **Every one is a tiny move**: the masked candidate differs from main in 1 to 8 tokens
(`tools/dist.py`: tokens outside the difflib matching with main), for example `pt:execute:28905` (hopt byte) only
swaps the destination registers of two loads at 0x4a40. Distances (tokens):

| neutral cell(s) | what it touches | dist |
| --- | --- | ---: |
| `pt/ai:execute:29860` | is_signer byte of a sharing-CPI AccountInfo clone | 8 |
| `pt/ai:execute:29520` | is_signer byte of a clone (accounts+... x+40) | 5 |
| `pt/ai:execute:29867` | is_writable byte of a sharing-CPI clone | 4 |
| `ai:execute:28873/28889/28892/28898` | CtoState byte stores (annotation only; the pt twins are byte-identical) | 2-4 |
| `pt/ai:execute:28905` | hopt byte (holder Option<bool>) | 2 |
| `pt/ai/au:execute:30701..30722` | `?` residual Result loads | 1 |
| `pt/ap/au:wallet:31699..31720` | wallet Result pointer loads | 2 |
| `pt/ai:sweep:33036`, `33041/33042` | sweep amount compares | 1 |
| `se:wallet:31265` = `bf:wallet:31266` | no-coin block head | 3 |
| gen.py `vl:execute:28931/28930/28862/28854`, `bf:execute:30752/30041` | volatile CtoState/accounts loads, fences | 1-3 |
| best two-cell (w17a24 npairs3) | e.g. `ai:execute:29520+ai:execute:29860` | 13 |
| best size-complementary triples (w17a24 trip3) | e.g. `ai:validate:27896 (+8) + au:execute:28908 (-8) + ai:execute:29860` | 32-39 |

Near-neutral cells (0 B, dM -1/-2) are just as small (1-13 tokens). The largest neutral moves on the plateau are the
size-complementary triples, and they are still under 40 of 3,337 tokens.

## 3. Neutral base x every single edit B

B set per base (`tools/drift.py mkb`): one representative per main signature of every code-changing cell at 0 B
(dM >= -30) or within 16 B (dM >= -6), 205 cells (family preference pt > ai/ap > gen > va > as > au/se), plus every
edit of the union within 15 IR lines of a base cell (identical-on-main ones included). 400-700 combos per base.

| base | cells | combos | best M @27,400 | new neutral sigs | best off-size | same dM as on main | differ (better) |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| A01 | `pt:execute:28905` | 340 | 2295 | 14 | 2295 @27416 | 285 | 8 (1) |
| B02 | `ai:validate:27896` + `au:execute:28908` + `ai:execute:29860` | 683 | 2295 | 19 | 2295 @27416 | 437 | 29 (15) |
| B03 | `ai:validate:27954` + `ai:validate:27965` + `ai:execute:29860` | 587 | 2295 | 19 | 2295 @27416 | 361 | 13 (5) |
| B04 | `ai:validate:28047` + `au:execute:28908` + `ai:execute:29520` | 427 | 2295 | 19 | 2295 @27416 | 342 | 26 (13) |
| B05 | `ai:execute:29520` + `ai:execute:29860` | 678 | 2295 | 19 | 2295 @27416 | 411 | 30 (10) |
| B06 | `ai:execute:28898` + `ai:execute:29860` | 588 | 2295 | 17 | 2295 @27416 | 371 | 17 (4) |
| B07 | `ai:execute:29860` + `ap:wallet:31699` | 579 | 2295 | 18 | 2295 @27416 | 370 | 9 (4) |
| B08 | `ai:execute:29860` + `ai:sweep:33041` | 635 | 2295 | 17 | 2295 @27416 | 408 | 19 (8) |
| B09 | `pt:execute:29860` | 586 | 2295 | 19 | 2295 @27416 | 382 | 8 (4) |
| B10 | `pt:execute:30701` | 291 | 2295 | 18 | 2295 @27416 | 288 | 0 (0) |
| B11 | `pt:wallet:31699` | 353 | 2295 | 18 | 2295 @27416 | 348 | 1 (0) |
| K1 | `kn:validate:284` | 433 | 2294 | 0 | 2295 @27392 | 410 | 16 (7) |
| K2 | `kn:validate:298` | 415 | 2295 | 1 | 2295 @27392 | 402 | 9 (7) |
| K3 | `kn:execute:339a` | 452 | 2294 | 0 | 2295 @27392 | 440 | 8 (5) |
| K4 | `kn:execute:339b` | 556 | 2294 | 0 | 2295 @27392 | 505 | 20 (11) |

(Interim: the queue continues; SUMMARY.json has the final list.)

**Additivity.** For B cells with a main reference, `M(A+B) - M(A)` equals B's dM on main in about 94% of the
combos. Every other combo is a collapse that collapses less (for example `eqa:execute:29857:29816`, -45 on main,
-23 on B02); no non-additive combo comes within 20 M of main at 27,400 B. The tiny neutral moves do not re-shuffle
the cells around them; the fresh cells after earlier landings came from moves of hundreds of tokens.

## 4. Free size knobs and two inert shims (leave-one-out in IR)

Reverting a landed shim in IR (`data/knob-edits-8bee075.jsonl`):

| IR knob | source shim | M | bytes |
| --- | --- | ---: | ---: |
| `kn:validate:284` (volatile -> plain load) | #4053 284 holder_key placeholder | 2,295 | 27,392 |
| `kn:validate:298` (pt1 -> value) | #4018 298 `pt1(3,new.is_some())` | 2,295 | 27,392 |
| `kn:execute:339a` (ptp 23 -> pointer) | #4026 `ptp(23,..)` shared owner test | 2,295 | 27,392 |
| `kn:execute:339b` (ptp 24 -> pointer) | #4026 `ptp(24,..)` CtoState max_fee | 2,295 | 27,392 |
| all four together | | **2,295** | **27,368** |
| `kn:execute:v29140` | #3961 line 339 `read_volatile` of the curve Box pointer (behind `ptp(1,..)`) | 2,295 | 27,400, **byte-identical** |
| `kn:execute:v29829` | #3965 line 749 `read_volatile` of the `pump_fees` pointer (`pf`) | 2,295 | 27,400, **byte-identical** |
| `kn:sweep:v32266` | #3936 sweep program-clone owner pin | 2,295 | 27,400 (4 tokens differ) |
| `kn:validate:x27956` / `kn:execute:x28785` | 312 expect_p / quote_locked expect | 2,283 / 2,294 | 27,392 / 27,408 |
| `kn:execute:v29764` / `v29782` / `v30159` | other volatile reloads | 2,289 / 2,234 / 2,153 | |

So main carries 32 B of free room (four knobs, any subset, M unchanged) and two volatile reloads that no longer do
anything: the `ptp(1,..)` passthrough (#4018) on the accounts pointer already blocks the forwarding that #3961's
volatile Box-pointer reload was added for, and the `pf` pin of #3965 became inert after later landings.

Knob bases x every +8 B cell (K1-K4, rows above): the +8 B cells stay at their main dM (best -1), so the free room
cannot be spent on any single cell. Knob composites that return to 27,400 B are neutral: four knobs +
`vs:wallet:30894` (0 M @+32 B: write_volatile of the wallet owner compare) = 2,295 @27,400 (dist 35); 339a + 339b +
`vl:validate:28118` (0 M @+16 B) = 2,295 @27,400.

## 5. Peel landed in this lane (byte-identical)

Source peel of the two inert reloads (no line added, line numbers unchanged):

```rust
// line 339, shared non-holder arm: plain read of the Box pointer (the ptp(1,..) passthrough stays, marked)
target=unsafe{*(&(*(ptp(1,&**a as *const AdminCto as *const u8) as *const AdminCto)).bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: passthrough on the accounts pointer the curve box reload derefs*/.creator;
// line 749, event_authority lamports Rc increment: ordinary Rust
pf=a.pump_fees.as_ref();
```

| build | admin_cto | slots | bytes | normalized / raw | losses | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| main 8bee07558 (baseline) | 0.68754 | 3,096 | 27,400 | 1034 / 1034 | | 54344822ddef0bd4 |
| peel p1a2a | 0.68754 | 3,096 | 27,400 | 1034 / 1034 | 0 / 0 | **54344822ddef0bd4 (identical)** |

The read_volatile count under programs/ drops by 2 (land.py forcing delta -2).

## Tools (`tools/`, experiment only; copy next to w17a06's oracle tools)

- `screenq.py`: w17a24 `screenp.py` + a signature -> M cache across result files.
- `drift.py ref | mkb <name> <ids> [--local N] | mkk <name> <ids> <dB> | ana <name> <sig>`: main reference table,
  B-set builder for neutral bases and knob bases, per-base summary.
- `runq.sh` / `runk.sh`: queue runners. `addit.py`: additivity of B on a base vs main. `summ.py`: the table above.
- `dist.py`: M, signature and distance from main for combos. `pos.py`: also jump-offset-masked M and change positions.
- `cdiff2.py`: disassembly diff of an IR combo against main. `lcsbp.py`: bit-parallel true LCS (main: LCS 2,300 vs
  difflib M 2,295, so the scorer's greedy alignment leaves only 5 tokens on the table).
- `rec.py`: one ledger row per screened base.
