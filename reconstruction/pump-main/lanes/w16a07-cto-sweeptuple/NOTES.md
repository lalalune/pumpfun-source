# w16a07-cto-sweeptuple: sweep decisions in the sibling tuple idiom (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9bd38c7d5 (`$BASE`, not rebuilt; admin_cto source identical to 9120883/1cc4879: 0.67376, 3,124 slots,
M 2,249, Mperm 2,292). Ledger approach `sweeptuple`, keys `0x22a10-w16-9bd38c7-sweeptuple-<variant>-v1`.

## Result

| | ratio | slots | bytes | M | normalized / raw | losses | differential |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| main 9bd38c7 | 0.67376 | 3,124 | 27,400 | 2,249 | 1034 / 1034 | - | - |
| **A6 + ev6** | **0.67436** | 3,141 | 27,400 | 2,251 | 1034 / 1034 | none | 388 cases, 0 mismatches |

measure.sh sha `a8a70a59c345af69`. Two source edits:

1. **A6, the AMM guard as a tuple match with the TCF arm first** (lines 659-661, error line 660 kept):
   `match (amm_present,amm_frozen){(_,false)=>if !a.coin_creator_vault_ata.data_is_empty(){TCF CPI?;}`
   `(true,true)=>{require!(token_raw_amount(..)?==0,CtoSharedVaultFrozen);}(false,true)=>{}}`.
   This is the shape of `sweep_fees.rs` line 152 (`(true,true)=>..,(_,false)=>..,(false,true)=>{}`), with the arms
   reordered. On its own it is 27,392 B and M 2,244, and it differs from main in exactly one place: the line-660
   `token_raw_amount(..)?` test becomes `jne r7,2,err` instead of `jeq r7,2,+1; ja err`. That is the original's form
   (orig 0x2528 `jne r7,0x2,+0x7c6`). Registers, frame and the rest of the stream are unchanged.
2. **ev6, `AdminCtoEvent{is_holder_reward:..` first** (line 767; w15a30 litfamily permutation `ev:6012345789abc`, +8 B,
   M 2,247 alone). It is the size repay. The original loads `is_holder_reward` late, so this one is a repay, not a
   faithful step; its extra instruction lands at cand 0x4e10, inside the region where A6's insertion map pays.

## Mechanism

rustc creates LLVM blocks in first-reference order, and BPF ISel decides branch polarity from the IR order: when the
`?` Ok block is the IR-next block, the condition is inverted and one `jne` is emitted; otherwise `jeq ok; ja err`. BPF
cannot re-invert after placement (`analyzeBranch` fails on conditional branches). In main's post-opt IR the 660 call
block `bb13.i118` is followed by the whole TCF clone run (`bb22.i144`..), and its Ok block `bb63.i` comes after it.
The tuple decision tree (test `amm_frozen` first, then a redundant `amm_present` test that LLVM folds) changes the
first-reference order so that `bb63.i` directly follows `bb13.i118`.

IR oracle (`tools/irmv.py`): moving `bb63.i` right after `bb13.i118` in main's post-opt IR (`opt -passes=instnamer`
first) and running llc gives A6's bytes exactly. `tools/qflip.py` does the same flip on a finished `fn.bin` (and the
sh_iflet flip, `SH`), so any captured variant can be composed with A6 without a new build. It reproduces m_A6 and
sh_iflet+A6 token-for-token.

## Price table (raw-IR capture + opt/llc oracle, `tools/scr.py`; `data/res-9bd38c7.jsonl`)

Bases: m = main, s = sh_iflet, t = tai (w15a26 `p_tai`, the faithful TCF program form). Marker = registers of the first
TCF program clone (orig lamports r7, key r9, data r0, E r5, O r6).

| variant | spelling | bytes | M | Mperm | marker |
| --- | --- | ---: | ---: | ---: | --- |
| m_0 | main | 27,400 | 2,249 | 2,292 | lam r7 key r0 data r4 E r5 O r5 (2/5) |
| m_A1 = m_A2 | `match amm_frozen as i32{1=>660,_=>if !empty{TCF}}` (A2: arms swapped, byte-identical) | 27,392 | 2,243 | 2,286 | = main |
| m_A3 | `(true,true)=>660,(true,false)=>TCF,(false,_)=>{}` (drops the second `data_is_empty` call) | 27,320 | 1,732 | 1,732 | TCF moved |
| m_A5 | `(true,true)=>660,(_,false)=>if !empty{TCF},(false,true)=>{}` (sweep_fees arm order) | 27,384 | 2,141 | 2,186 | TCF moved to 0x1f88 |
| **m_A6** | `(_,false)=>if !empty{TCF},(true,true)=>660,(false,true)=>{}` | 27,392 | 2,244 | 2,287 | = main |
| m_A6c | `match amm_frozen{false=>TCF,true=>660}` | 27,400 | = main | | |
| m_A6e | `if !amm_frozen{TCF}else{660}` | 27,400 | = main | | |
| m_A7 | `(false,_)=>{}` first, then (true,true), (true,false) | 27,320 | 1,732 | 1,732 | |
| m_N1 | `match native as i32{1=>native,_=>token}` | 27,480 | 1,583 | 1,742 | re-laid |
| m_N2 | `match native as i32{0=>token,_=>native}` | 27,456 | 1,582 | 1,742 | re-laid |
| m_T1 | token arm `match (frozen,amount>0){(true,_)=>719,(false,true)=>CPI,(false,false)=>{}}` | 27,400 | = main | | |
| m_T2 | token arm `match frozen as i32{1=>719,_=>if amount>0{CPI}}` | 27,408 | 2,246 | 2,289 | = main (flips the and_then `?` to jeq+ja) |
| m_t1 | a1 + separate `?` (w14a70 t1) | 27,408 | 2,243 | 2,286 | = main |
| m_t1A6 | t1 + A6 | 27,400 | 2,246 | 2,289 | = main |
| s_A6 | sh_iflet + A6 | 27,384 | 2,244 | 2,287 | = main |
| s_t1A6 | sh_iflet + t1 + A6 | 27,392 | 2,242 | 2,285 | = main |
| t_0 | tai | 27,416 | 2,170 | 2,248 | lam r5 key r4 data r7 E r0 O r0 (0/5) |
| t_A6 | tai + A6 | 27,408 | 2,171 | 2,249 | 0/5 |

- Every `as i32` / tuple spelling either folds to main (T1, A6c, A6e), flips exactly one `?` polarity (A1/A2, A6, T2), or
  re-lays the sweep (A3, A5, A7, N1, N2). None of them moves the TCF clone-run registers: the w15a26 marker
  (lamports Rc in r7 on tai) never appears, and the clone run keeps main's names in every variant that keeps the layout.
- The native/token split is the dangerous one: `match native as i32` creates the native arm first and MBP re-lays the
  whole sweep (-666 M).

## Polarity oracle (`tools/polscan.py`, `data/polscan_m0.jsonl`)

For every `br i1` block in main's sweep (IR blocks 120-285) whose IR-next block is neither successor, each successor was
moved to follow it (40 moves). No single move beats main. The -8 B moves at M 2,244 are A6 (`bb13.i118 -> bb63.i`) and
`wallet.exit -> bb34`. A6 is the best single flip in the sweep.

## Size repay (`data/insmap_m_A6_1.json`, `data/qcomp_*.jsonl`)

- Insertion map of A6 (one 8 B junk slot at every position, w15a03 `insmapn.py`): base 2,244; main+1 at 602 positions
  (cand 0x2220-0x2478, 0x3f08-0x4bd8, 0x4e18-0x5578), main+2 at 47, main+3 at 0x54b8. That is about four times the
  sh_iflet map's main+1 area.
- Binary composition of A6 onto every +8 B `fn.bin` of the w15/w16 lanes (214 variants, `qcomp_A6_on_27408_variants`):
  ev6 (w15a30 `ev_6012345789abc`) gives **2,251**; cu_unwrapcur, e0u, rr7O, wl_writ_eq and ev7 tie main (2,249).
- A6 + sh_iflet onto every +16 B `fn.bin` (180 variants): best real source variant 2,244 (I6n, cs5). (w16a04's
  `Lp2ra` composes to 2,265, but it is an RA-force ceiling build, not source.)

## Sweep-body spill map (`tools/spillmap.py`, `data/spillmap-*.txt`)

Every 8 B spill store in the sweep body (orig 0x1d28-0x3c68), the stored value's definition, its reloads, and the
frame-masked aligned candidate instruction. The head, where the run's register pressure starts:

| value | original | main |
| --- | --- | --- |
| skip gate | spill slot [0x8e0], reloaded at 0x1d38 (`jne r1,0`) | r9 (`jne r9,0,+1; ja`) |
| `ctx.bumps.creator_vault` | r7, spilled after the 648 test (0x1f70 [0x910]), reloaded for the seed byte (0x2060) | r9 through the TCF run, stored straight from r9 (0x2038) |
| `native` (memcmp i32) | r9, spilled after the 648 test (0x1f68 [0x918]) | r7, spilled (0x1f48 [0x918]) |
| `&a.holder_creator_vault` | spilled at its def (0x1f48 [0x8e0]); dead reloads at the token arm (0x2130) and native arm (0x3bb8) | r6 through the TCF run, spilled mid-arm (0x20b8 [0x9b8]) |
| [0x950] (validate-side value) | self-copy at the gate (0x1d48-0x1d50); reloaded into r1 before every sweep-exit tag test (0x2158, 0x24a0, 0x2608, 0x3c50) | not live in a register at the join |

In the clone run itself the original spills E/O after the payer clone (0x2830 [0x970], 0x2838 [0x978]) and the
`rent_epoch`/`is_signer`/`is_writable`/owner bytes of each clone into a descending run from [0x9c8]; main spills the
same fields in a different slot order (the table lists every store). The token-arm call order differs as well: the
original calls `token_raw_amount` before `token_frozen` (0x20c8 then 0x2110, call targets 0x6ce0 then 0x6b08); main
calls `token_frozen` first. That is w14a70's a1, -24 B / M 2,242 alone on this main.

## Landed

PR #3859, merged by land.py as `7e5ba44a7` (zero losses, closer: admin_cto, runtime 388/0). New main: 0.67436, 3,141
slots, M 2,251.

## After landing: binary polarity oracle on 7e5ba44 (`tools/flipall.py`, `tools/flippairs.py`)

`qflip` generalised: every `jCC a,b,+1; ja +X` can become `jNCC a,b,+X` (-8 B), and every lone conditional jump can
become `jNCC +1; ja` (+8 B), with jumps re-fixed and registers/frame assumed unchanged (exact for A6 and sh_iflet).
- Singles (69 minus, 74 plus, `data/flipall_main7e5ba44.json`): none above 2,251. The best minus flips reach 2,250
  (0x1000, 0x1288, 0x1800); 9 plus flips keep 2,251 at +8 B.
- All 5,106 minus x plus pairs at 27,400 B (`data/flippairs_main7e5ba44_top60.json`): the best is **2,252 (+1)**, for
  example sh_iflet's site 0x4a30 with a plus flip at 0x5520 or 0x5558. Those plus sites are Rc drop-glue `jne` tests
  (strong-count decrement), which no source spelling controls, so the +1 is alignment, not shape. The polarity
  dimension is exhausted on the new main: at most +1 M, and not source-reachable.

## Next ideas

- On 7e5ba44, main + the sh_iflet flip is 27,392 B at M 2,245. One +8 B junk slot gives 2,253 at cand 0x54b8 and 2,252
  at 0x5450-0x54a0 (`data/insmap_main7e5ba44_SH_1.json`). That is where the original has its extra `mov64 r9,r1` after
  the Rent `ProgramError::from` (orig 0x54e0; the swept-r9 copy residual of w14a06/w14a33/w14a70). A source form that
  produces that copy would let sh_iflet land on top of #3859 at about +2 M.
- A6 is a faithful -8 B step at the sweep head. Its insertion map is wide (602 main+1 slots), so any faithful +8 B
  construct in 0x3f08-0x4bd8 or 0x4e18-0x5578 pairs with it. ev6 is a repay, not faithful: replace it when a faithful
  +8 B appears.
- A6 + sh_iflet is 27,384 B at M 2,244 (no loss for the second flip). A +16 B faithful pair would make that base pay.
- `qflip.py` can compose the A6 and sh_iflet flips onto any captured `fn.bin`. Re-run `qcompl.py` over new lanes' rx
  dirs before building pairs.

## Tools (`tools/`, experiment only; absolute paths point at this lane's OUT)

`gen.py` (variant generator: A1-A7, A6b-e, N1/N2, T1-T5, V1, a1/t1, P1-P8, ev6/ev7 on bases m/s/t), `scr.py` (capture +
rx + M/Mperm/marker screen, 2 workers), `marker.py` (TCF first-clone registers), `irmv.py` (post-opt IR block move +
llc), `polscan.py` (polarity oracle), `qflip.py` / `qcomp.py` / `qcompl.py` (binary `?`-flip composition), `spillmap.py`,
`mdiff.py` (masked listing diff), `fdis.py`, `rel.py`, `fnbin.py`, `rec.py` (ledger rows). rx.py, capraw.py, relab.py,
mperm.py, bdis.py, insmapn.py and lit.py are unchanged copies from w15a26, w15a31, w15a03 and w15a30.
