# w14a54-cto-feetag: the fee-tag phi never creates the fee-Some edge block; BPF codegen cannot split that edge

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a49-cto-sink76ra (#3347) and w14a36-cto-blockplace (#3325). Bases: main 0fbf8da (0.65578 / 3,279 slots),
then c3e5b51 (0.65698 / 3,182). Ledger approach `feetag`, keys `0x22a10-w14-{0fbf8da,c3e5b51}-feetag-*` (45 rows).
Result: **notes only, no landable source change.** Best zero-loss measurement = main (0.65698 / 3,182 @ 27,400).

## 1. Source forms of the original fee-tag data flow (raw-IR capture + rx opt/llc oracle)

The angle: validate yields a fee-present constant per exit (the original's `mov r7,1` on the Some exit, `r7=0` on the
None exits), and line 757 plus the `admin_cto_pool` tag read it instead of re-testing the fee argument's tag.
`gen/g1.py`, `gen/g2.py` hold the exact edits; `results.jsonl` has every row.

| form | 0fbf8da (main 0.65578) | c3e5b51 (main 0.65698) |
| --- | ---: | ---: |
| validate returns `(Pubkey,Option<u64>)`, 757+CPI read it (`opt_both`) | 0.34012 @27,056 | |
| validate returns `(Pubkey,Option<u64>)`, 757 only / CPI only | 0.40403 @27,256 | |
| validate returns `(Pubkey,bool)`, `match fee{Some=>{..;true}None=>false}` (757 / nested / both / `fs.then`) | 0.388-0.391 @27,448-27,576 | 0.39204 @27,456 |
| validate returns `(Pubkey,fee.is_some())` captured at the exit | 0.37897 @27,400 | 0.37903 @27,392 |
| `let mut fs=false; if let Some(f)=fee{..;fs=true}` returned in the tuple | 0.38815 @27,456 | 0.39048 @27,464 |
| out-param `fo:&mut bool` / `&mut u64` / `&mut u8` set after the checks, 757 reads it | 0.57408 @27,448 | 0.57669 @27,456 |
| out-param `fo:&mut Option<u64>` (`*fo=Some(f)`), 757 only = CPI only | 0.57605 @27,432 | 0.57647 @27,448 |
| out-param `Option<u64>`, 757 and CPI (fee argument tag dies in validate, as in the original) | 0.58816 @27,256 | 0.59517 @27,328 |
| out-param `Option<u64>`, 757 as `if let`/`match` | 0.57434 @27,424 | 0.57746 @27,440 |

Every form keeps main's error order `330 338 410 334`: none of them puts a block on the fee-Some edge.
Changing validate's return type costs 0.25-0.32 (the whole frame moves). The out-param forms reproduce w14a49's
ftag/ftag2 IR probes exactly (`oo_both` == `ftagn.py b`, token-identical). Their loss is a frame-slot shift:
`tools/offmap.py` shows the fee-tag spill slot inserted at about `[r10-0x918]` and every deeper slot moved 8 B
(320 remapped tokens, `oo_757`). When the argument tag dies (`oo_both`) the frame shrinks 8 B instead, and RA puts
`bb26` and wallet's `bb53.i82` elsewhere (-144 B).

## 2. Why the fee-tag phi cannot give the edge block (tools/px.py, tools/ftagn.py, tools/bw58.py)

The phi constant is materialised at the top of `bb58.i` (`mov64 r2,1` before the range test), not on the edge.

- Branch weights on `bb58.i` (1:1, 2:3, 1:2, 1:4) do not change it.
- With diagnostic llc flags `-machine-sink-split-probability-threshold=100` and `-phi-elim-split-all-critical-edges=1`,
  ftag and main stay byte-identical.
- A non-cheap (load) phi input defined in `bb58.i` does not split either. Two distinct-type tag phis (`ftagn.py b`)
  become one register.

The reason: BPF `analyzeBranch` cannot analyse conditional branches. MachineSink, PHIElimination and TailDuplicator
therefore never split or duplicate across an edge out of a block that ends in a conditional jump.

**So the original's +0x1800 block must be an IR basic block**, not a codegen artefact. It is a copy of the join `bb76`
(the shared test, plus the phi copies and spills RA put there). In the original, JumpThreading or tail duplication sent
the fee-None exits to their own copies and left the join as the fee-Some exit's private successor. That matches
w13a05's per-arm threading finding.

## 3. IR bounds on c3e5b51 (post-opt IR; the join block is now `bb74`)

| probe | ratio | bytes | fm | sk | errseq |
| --- | ---: | ---: | ---: | ---: | --- |
| main | 0.65698 | 27,400 | 0.70401 | 0.78850 | 330 338 410 334 |
| empty-asm block on `bb58.i -> join` (bound) | 0.66447 | 27,400 | 0.71061 | 0.79569 | 330 338 334 410 |
| real 8 B instruction (volatile load) on that edge (diagnostic) | 0.66467 | 27,408 | 0.7108 | 0.79587 | 330 338 334 410 |
| **h7**: 7-byte target piece written into `target.sroa.0` in the validate arms (`hoist.py ... seven`) | **0.65827** | 27,368 | **0.71583** | **0.80066** | 330 338 410 334 |
| h7 + edge block | 0.66577 | 27,368 | 0.72242 | 0.80785 | 330 338 334 410 |
| h7 + fee-tag phi + edge block | 0.58718 | 27,400 | 0.70551 | 0.79539 | 330 338 334 410 |

Any surviving instruction on the edge reaches the bound. That instruction costs 8 B, which a -8 B knob would repay.
The h7 hoist is a new lead: +0.0013 ratio with +0.012 fm and +0.012 sk, but 32 B short. Its source analogues all
collapse the frame (section 4). Adding the fee-tag phi costs about 0.08 even on top of h7 and the edge block, so the
phi is net negative on any skeleton measured here.

## 4. Other source routes tried (all rejected)

- Holder-first sharing tree, so JumpThreading could thread the fee-None exits off the join (`gen/g3.py`).
  Spellings: `holder&&shared`, holder-nested, `match (holder,shared)`, `!holder&&shared`, `shared&&holder`.
  Results: 0.6298-0.6407 at 27,224-27,456. The nested form gives the original order `330 338 334 410` (0.64073,
  fm 0.67066), but nothing is threaded, because the join's target memcpys exceed the JT threshold.
  Hand-threading that IR (`tools/thr.py`) gives 0.638-0.639 at +128..240 B.
- `-jump-threading-threshold=24` (diagnostic): it threads the join, but also all of execute (0.41-0.43).
- Target written through `out:&mut Pubkey` in the arms (`Result<()>`, or `Result<Pubkey>` ignored): 0.155-0.228.
- validate returns `Result<&Pubkey>` (`new:&Option<Pubkey>`): 0.28398 @26,784.

## 5. Remaining gap and next ideas

- The bound is +0.0075 (0.66447 on c3e5b51). It needs an IR block with a real instruction on validate's fee-Some exit,
  plus a -8 B repay. The only faithful producer is the original's per-exit join copies. That is IR threading of the
  join for the fee-None exits, with the shared test known per arm (w13a05) or holder-first. It needs the join to be
  cheap at JT time, i.e. without the target-piece memcpys (h1/h7).
- h7 (+0.0013, fm/sk +0.012 at -32 B) is worth a lane: find a source form that stores the 7-byte target piece in
  validate's arms without changing validate's return type, then repay 32 B with `$SWARM/w11/sizeknobs-cto.json`.

## Tools (experiment only; never source proposals)

`tools/capvar.sh` + `tools/rx.py` (raw-IR capture, `opt -O3` with `OPTARGS`, llc, score); `tools/batch.sh` (2 workers).
`tools/px.py` (post-opt llc oracle with fm/sk/errseq); `tools/eseq.py` (error-line sequence); `tools/offmap.py`
(frame-offset remap between two builds); `tools/hoist.py` (h1/h7); `tools/ftagn.py`, `tools/bw58.py`, `tools/thr.py`,
`tools/split1.py`. Edit sets are in `gen/`.
