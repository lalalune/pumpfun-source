# w14a89-cto-jtnodup: the original does duplicate the non-shared arm; the swap is not the price (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 95a64ba (0.66986, 3,204 slots, sk 0.79599, fm 0.70911). This lane continues w14a76-cto-threehop (#3405)
and w14a66-cto-feeedge (#3386). Ledger: approach `jtnodup`, keys `0x22a10-w14-95a64ba-jtnodup-*` (about 80 rows).

**Result: no landable change.** The best zero-loss measurement is main (0.66986 @ 27,400). The angle's premise does not
hold. The original also threads the non-holder exit through the non-shared arm head, so blocking that duplication moves
away from the original. A swap-free bound for every faithful form is far below main, and the loss is register and frame
cascade, not block placement.

## 1. The original has `bb21.thread` (from `tools/preds.py` on `win.py orig`)

The original's exits, with `[r10-0x920]` = `shared`, `[r10-0x928]` = fee tag, `[r10-0x8e0]` = `holder_reward`,
`r8` = holder:

| orig | path | what it does |
| --- | --- | --- |
| 0x234c8 | holder, after E298 | target = holder_key pieces; fee tag: None -> 0x23af8, Some -> fee chain (E330 skipped) |
| 0x23af8 | holder fee-None exit | `r7=0`; own `shared` test -> 0x23b38 (holder shared arm) / **0x242c0** (non-shared arm head, holder_reward test) |
| 0x237d0 | non-holder, after E312 | **`shared` tested BEFORE the fee tag** |
| 0x237d8 | non-holder shared | target = `st.creator` ([r10-0x38..]); fee tag: None -> 0x23848 (`r7=0`) -> `ja` 0x24260 (non-holder shared arm); Some -> 0x23f20 |
| 0x23ea0 | non-holder non-shared | target = t; `r7=0`; fee tag: None -> **`jeq` 0x24308 = the creator memcmp, skipping the holder_reward test at 0x242f0**; Some -> 0x23f20 |
| 0x24210 | fee-Some exit (after E338) | `r7=1`; `shared` test -> `r8` holder test -> 0x24260 / 0x23b48; non-shared -> 0x242c0 |

- Orig 0x23f18 -> 0x24308 is exactly n_va's `bb21.thread`, the non-holder exit threaded through the non-shared arm to `bb22`.
  The original keeps a second, unthreaded entry for the holder and fee-Some exits (0x242c0 -> 0x242f0 test -> 0x24308).
- The non-holder arm chooses `target = shared ? st.creator : t` before the fee checks. This is the OV form (w4/w10/w12/w13a18/w13a52).
  It is what lets JT reach the tree from three exits.

## 2. The JT duplication-cost table (`tools/jtd.py`, n_va = t1 + `th.val` + `th.ex(arms)` on 95a64ba)

`jtd.py` dumps every JumpThreading pass, with the LLVM cost model: lifetime/dbg are free, intrinsic calls cost 2,
other calls 4, and every other instruction 1. The threshold is 6.

| JT pass | bb75 (validate join) | bb21 (non-shared head) | bb19 (holder test) | threads |
| --- | ---: | ---: | ---: | --- |
| JT1 | 0 (single pred) | 6 | 3 | none |
| JT2, n_va | 0 | **4** (two target-piece memcpys, 7+9 B) | 1 | `bb75.thread`+`bb21.thread` (non-holder, two-block), `bb19.thread` (regular), then `bb75.thread332`+`bb19.thread335` (holder, two-block) |

Order matters. JT walks blocks in function order, and bb21 comes before bb19.

1. `maybeThreadThroughTwoBasicBlocks(bb21)` threads the non-holder exit first, because holder_reward is known false on that edge.
2. That creates `bb75.thread`, so bb19 can be threaded normally for it.
3. Then the two-block threading of bb19 takes the holder exit.

`maybeThreadThroughTwoBasicBlocks` takes one PredPred per block (`ZeroCount==1` wins), and needs `BB` to have a single
predecessor. Without step 1, bb19 takes only its ZeroPred (the non-holder exit), and after that it has two preds.

| probe in bb21 (IR only) | bb21 cost | bb21.thread | holder exit threaded | ratio @ B | sk |
| --- | ---: | --- | --- | --- | --- |
| n_va | 4 | yes | yes | 0.26782 @27,520 | 0.56972 |
| +1 volatile load (`e1`) | 5 | yes | yes | 0.26774 @27,536 | 0.56955 |
| +2 volatile loads (`e2`) | 6 | yes | yes | 0.26766 @27,552 | 0.56938 |
| +3 volatile loads (`e3`) | 7 | **no** | **no** (only non-holder) | 0.35790 @27,280 | 0.74734 |
| `asm sideeffect ""` (`e4`, probe) | 8 | no | no | 0.37076 @27,288 | 0.74632 |
| w14a76 `n_vpin` (8 volatile loads of `%new`) | >6 | no | no | 0.355 (0d04cf4) | 0.711 |

**No instruction placed in the non-shared arm can block bb21's duplication and keep both exits threaded.** Once bb21 is not
duplicated, the holder exit is not threaded either. The original duplicates bb21 anyway (section 1), so this lever moves
away from the original.

## 3. The placement swap, priced (`tools/mvchain.py`, `tools/autoswap.py`, `tools/asmscore.py`)

The swap is a MachineBlockPlacement chain, not a JT effect. `bb56.i` (the sweep `?` join, `jne r7,2`) is placed after
the sweep dest-seeds `with_pubkeys` error block (line 648), and pulls the whole post-sweep chain (`bb89`/`bb90` ... `bb125`, about
900 asm lines) before the wallet region. The IR block frequencies of every `bb56.i` predecessor are identical in main
and OV (`print<block-freq>`). In both, the first MBP pass picks `bb56.i` as the error block's successor. In main's second
pass `bb56.i` is "non-cold CFG conflict"; in OV and n_va it is a "CFG break" candidate (debug llc `-debug-only=block-placement`).

- **OV shows the same swap with no tree threading at all.** So the swap is not caused by bb21's duplication.
- Placement-only fix: move that chain back after the `ProgramError` `From` block that jumps to `bb56.i`. The bytes do not change.

| form (95a64ba) | as built | swap moved back (bound) | fm | rm | sk |
| --- | --- | --- | --- | --- | --- |
| main | 0.66986 @27,400 | = | 0.70911 | 0.76633 | 0.79599 |
| n_va (three-hop IR, both exits + bb21.thread) | 0.26782 @27,520 | **0.33478** | 0.59483 | 0.43073 | 0.74100 |
| OV (source; `if shared{st.creator}else{t}` in the arm) | 0.44131 @27,360 | **0.54714** | 0.64938 | 0.63529 | 0.79238 |
| lv3a (source; w13a18 outparam, exact three-way threading) | 0.23825 @27,448 | **0.30769** | 0.52439 | 0.41365 | 0.70518 |
| OV + weights 2000:1 on the dest-seeds error branch `bb2.i` (llc only) | 0.53381 @27,344 | | 0.63488 | 0.62138 | 0.77733 |

(fm = frame offsets masked, rm = registers masked, sk = both masked.)

`amap.py` chunk map (1/32 of orig):

```
main     54 56 54 57 54 35 75 76 92 87 91 88 95 96 84 95 100 93 88  2 43 99 90 95 98 93 96 90 87 85 98 96
n_va-mv  51 53 76 33 48 31 63 74 81 78 81 84 94 91 81 95 100 89 83 21 24 98 82 89 92 89 85 77 73 79 92 81
OV-mv    52 56 80 71 54 34 74 75 86 85 89 86 94 91 82 95 100 92 83 21 24 98 89 95 98 92 90 87 82 84 98 92
lv3a-mv  51 60 80 70 56  5  0 25 82 74 81 84 95 92 75 90 100 86 83 21 24 98 80 86 84 85 87 77 71 80 87 80
```

- n_va, swap-free: chunks 0-24 sum to 1,792, against 1,897 for main. Chunk 3 is 33 against 57; chunks 8-11 are 324 against 358.
- OV, swap-free: chunks 0-24 sum to 1,904 against 1,897. It gains on chunk 2 (+26) and chunk 3 (+14), and loses on chunks 8-11 (-12).
  Its skeleton is within 0.004 of main, but rm/fm are 0.13/0.06 lower: a register-allocation cascade. w14a84 puts the
  RA-only ceiling at about +0.007, so this cannot be recovered.
- lv3a has a second loss at orig chunks 5-7 (0x23b00-0x24400, the duplicated fee tests). Local `mv.py` matches there are
  22/30/26 against main's 55/69/62, so these are different instructions, not placement.

The step-3 gate (a swap-free bound above main on chunks 0-24) is met only by OV, by +7 skeleton tokens. Its whole-function
ratio bound is 0.547. Nothing in this family is near landing.

## 4. Cheap source screens on 95a64ba (no gain)

- `t1` (the tree tests `new.is_none()`) is now -24 B and ratio-neutral: 0.66986 @27,376, sk 0.79784 (+0.0019). It was +40 B on 0d04cf4.
  t3/t4/t5 give the same; t2/t6/t7 (`args.0`) give 0.66916 @27,384.
- t1 + each of the 43 size knobs that still apply (`sizeknobs-cto.json`): none reaches 27,400 above main. The neutral
  0 B knobs keep 0.66986 @27,376. The +8/+16 knobs cost 0.001-0.008.
- t1 + knob pairs/triples at 27,400:
  - `g_w_clock_local+ev_cb_local`: 0.66627.
  - `ev_newfee_unwrap+g_w_clock_local+L_fee_unwrap_again`: 0.66637 @27,392.
  - `w_ev_creator_first+sh_prog_let+L_fee_unwrap_again`: 0.66028.
  - `ev_newfee_unwrap+ev_cb_local`: 0.66117.
  - `ev_mint_key+ev_cb_local`: 0.65878.
- OV variants (+t1, without the #3386 volatile): 0.4317-0.44131. lv3a/lv3b (outparam, Result<Pubkey>): 0.238.
  vba/vbb (outparam, Result<()>): 0.241 @27,064-27,096, errseq 284 moves.
- Three-hop IR pieces: `th.val` alone gives main's bytes (eq_main) on main and t1. `arms`, `keeplt` and `all3` give 0.436-0.559.

## 5. For other lanes

- Do not try to stop JT from duplicating the non-shared arm. The original duplicates it (orig 0x23f18 -> 0x24308), and
  blocking it also loses the holder exit's threading.
- Once the faithful three-way CFG is reached, the loss is register assignment and frame across the whole function.
  Placement only explains 0.07-0.11 of it. A lane that wants the faithful validate CFG has to bring a frame and register
  plan with it, not a placement fix.
- The MBP swap (`bb56.i` after the dest-seeds `with_pubkeys` block) also happens in source forms that do no threading,
  such as OV. It depends on MBP's second-pass chain state, not on IR frequencies. On 53abf28, w13a52 had OV without the swap.
- `t1` is -24 B and ratio-neutral on 95a64ba, so a faithful +24 B change would be free room. No catalog knob fills it.

## Tools (experiment only; never source proposals)

- `tools/jtd.py in.ll [regex]`: per-JT-pass block costs, preds and `.thread` blocks for execute.
- `tools/mvchain.py in.s out.s START END JALINE`: move an asm chain to replace a `ja START`, fixing fallthroughs.
  `tools/autoswap.py` finds the `bb56.i` swap automatically. Score with `tools/asmscore.py` (cc1as) and `tools/osk.py`
  (ratio/fm/rm/sk for .o/.bin).
- `tools/bwpost.py in.ll out.ll 'block:w1:w2'`: branch weights on post-opt IR (then `px.py`).
- `tools/preds.py dis.txt addr...`: branch predecessors in a `win.py orig` dump.
- `tools/cdiff.py a.bin b.bin [min]`: opcode-level diff of two candidates.
- `tools/th.py` adds `EXTRA` (insert lines into the A/Bn/H/N tree blocks) and is driven by `gen/q.py` (`QX`, `TH`).
- `rx.py`, `capraw.py`, `capvar.sh`, `batch.sh`, `px.py`, `amap.py`, `mv.py`, `bord.py`, `eseq.py`, `rec.py` come from w14a76,
  repointed to this lane.
