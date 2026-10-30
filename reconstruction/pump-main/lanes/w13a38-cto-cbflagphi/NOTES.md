# w13a38-cto-cbflagphi: cashback/holder as phi flags out of validate's arms (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 9b9440f (0.62043, 3305 slots) and 52c0b08 (0.62103, 3306 slots).
Continues the next ideas of w13a26-cto-bfreq (#3047), w13a25-cto-mintsink (#3016) and w12a09's holder-phi-alone.
Ledger keys: `0x22a10-w13-{9b9440f,52c0b08}-cbflagphi-*`.

**Result: no zero-loss gain at 27,400 B.** The holder phi is faithful and lifts the frame-masked ratio by +0.009, but every
source form of it shrinks execute by about 240 B. The cashback phi is negative in every form tried. This PR records the
map of where the two flags live, the source form that reproduces the original holder phi, and the size evidence.

## Where the flags live

| | original | main (52c0b08) |
| --- | --- | --- |
| st.cashback byte (`[curve+0xa3]`) | loaded before global_quote, spilled to -0x8e8, re-tested raw in the fee path (0x23f68) | loaded after global_quote |
| cashback flag | phi spilled at **-0x958**: `r3 = st.cashback!=0` in the non-holder arm (0x23788), `r5 = 0` in the holder arm (0x23b20); curve store `ldxdw r4,[-0x958]; and64 r4,1` | `%cashback = and(_40.not, !holder)` in the entry block. Its select becomes `mov64 r1,1; stxdw [-0x8f8],r1` right after the first global_quote memcmp (the "early mov64 1 spill"), cleared to 0 later when `!st.cashback`, ANDed with `!holder` (-0x908) at the curve store |
| holder flag | phi of constants spilled at **-0x950**: stores of 0/1 in each validate arm (0x23850, 0x23b40, 0x23ef0, 0x24240, 0x242c0); 26 accesses in all (18 reloads, many as `ldxdw r1,[-0x950]` before sweep-exit joins); curve store `ldxdw r2,[-0x950]; stxb [r1+0xa5],r2`; admin_cto_pool reads it (`ldxdw r4,[-0x950]` at 0x27830) | `icmp ne (hopt & 0xfd), 0` re-derived from the spilled `hopt` argument at each use; curve store `ldxdw r2,[-0x8e0]; and64 r2,0xff; mov64 r1,1; jne; mov64 r1,0; stxb [+0xa5]`; the pool CPI reloads the curve |
| curve store order | 0xa5 (holder) then 0xa3 (cashback) | 0xa3 then 0xa5 |

## Oracles (`tools/`)

- `capvar.sh <name> <edits.py> <slot>`: crate copy + exact source edits, raw-IR capture (identity build, one slot), then
  `rx.py` (opt -O3 + llc, = measure.sh ratio). From w13a23/w13a35; paths point at this lane's cache.
- `llcx.py <name> <edits.py>`: llc-only oracle on edited post-opt IR (`rx/base/m.ll`), 3 s. `e/lcommon.py` has the IR
  edits (`L*` files).
- `abs.py`: abstracted ratios vs the original: `fm` masks frame offsets and jump targets, `rm` also masks registers.
- `reg.py`, `span.py`, `cdiff.py`, `errseq.py`: per-region matched counts, per-region size deltas, candidate-vs-candidate
  opcode diff, error-code order. They use w13a29's `slots.py` (copied here).
- `comp.py` composes lane edit files with size-knob catalog entries; `batch.sh` runs capvar batches.
- `padscan.py` / `padgreedy.py` (oracle only): volatile-store padding to bound what a size repay could give.

## IR oracle (post-opt llc on 9b9440f, main 0.62043, fm 0.7121, rm 0.85171)

Validate's Ok join is `bb69` (preds bb45.i: non-holder with fee None, bb44.i: holder with fee None, bb58.i: fee checks
passed; the holder arm already skips the cashback check, bb93.i -> bb54.i).

| edit | bytes | ratio | fm | rm |
| --- | ---: | ---: | ---: | ---: |
| L1 cashback phi `[_40.not, false, false]` at bb69 | 27,192 | 0.54256 | 0.71519 | 0.85594 |
| L5 = L1 with the icmp sunk into bb45.i | 27,248 | 0.55701 | 0.71774 | 0.85414 |
| L3 holder phi `[false, hA, true]` (hA = phi false/true at bb54.i) | 27,192 | 0.58496 | 0.71579 | 0.85383 |
| L4 = L1 + L3 | 27,008 | 0.53116 | 0.69715 | 0.84171 |
| SW: curve stores holder first (holder still an icmp) | 27,400 | 0.61384 | 0.70611 | 0.85201 |
| **L3sp** = L3 + holder-first stores + admin_cto_pool holder arg = phi | 27,152 | 0.61279 | **0.72144** | 0.85388 |
| L4sp / L6sp (L3sp + cashback phi) | 26,992 / 27,088 | 0.54068 / 0.5394 | 0.70883 / 0.71056 | |
| L3spe (L3sp + event holder from the phi) | 27,152 | 0.61219 | 0.72084 | |

The cashback phi does remove the early `mov64 r1,1; stxdw [-0x8f8]` spill, and the holder phi does give the original's
raw `ldxdw; stxb [+0xa5]` store. Every phi form shrinks the function by 150-370 B.

## Source trials (raw-IR capture oracle = identity build)

| trial | form | bytes | ratio | fm | rm |
| --- | --- | ---: | ---: | ---: | ---: |
| B | validate returns `Result<(Pubkey,bool,bool)>`, per-arm `(target,true,false)` / `(t,false,st.cashback)` | 27,152 | 0.36599 | 0.65643 | 0.79518 |
| C | returns `(Pubkey,bool)` cashback only | 27,240 | 0.3747 | 0.67037 | 0.80108 |
| D | returns `(Pubkey,bool)` holder only | 27,080 | 0.35895 | | |
| E | per-arm `(target,cashback)` inside validate only | 27,400 | 0.62043 | = main | |
| F | `fl:&mut (bool,bool)` out-param written per arm | 27,032 | 0.53876 | 0.69713 | 0.84495 |
| Fc | `cb:&mut bool` (cashback only) | 27,136 | 0.5359 | 0.65753 | 0.8445 |
| Fh | `ho:&mut bool`, holder arm `*ho=true` | 27,256 | 0.59087 | 0.70802 | 0.85431 |
| g1 | Fh + holder-first stores + `admin_cto_pool(..,target,holder,fee)` | 27,248 | 0.59126 | 0.70903 | 0.85534 |
| **h2** | g1, but `let holder0=hopt==Some(true);let cashback=st.cashback&&!holder0;` before validate | 27,160 | 0.6127 | **0.72134** | 0.85435 |
| h2 on 52c0b08 (n1) | | 27,160 | 0.6115 | 0.72043 (main 0.7118) | 0.85375 (main 0.85111) |

- Any return-type change of validate collapses the frame (as in w12/w13a04). The out-param keeps `Result<Pubkey>`.
- h2 is the source form of the L3sp oracle. The cashback must stay derived from the argument test: computing it from
  the holder phi (g1, Fh) loses the fm gain.
- g2-g5 (h2-family + entry copy `validate(..,args.0,..)`, `new.map(|k|k)`, plain `let (holder_key,_)=PDA`): 0.519-0.539.
- Size knobs on h2 (9b9440f, one at a time): pu_amm_keyfn +80 B -0.0004; ev_cb_pre / ev_nf_pre +24 B -0.0009;
  cu_fee_oldunwrap / ev_cb_local +8 B -0.0007..-0.001; g_old_fee_first 0 B; s_rent_local -24 B; wl_ts_clockvar /
  g_w_clock_local -0.047. Combined (52c0b08): n2 (+128 B) 0.60693, fm 0.71559; n3 (h2 + entrycopy3 m1) 0.60192;
  n4 0.59739. The knobs lower fm.

## Size bound

`padscan.py` puts one 240 B blob (28 volatile global stores) at the top of each of the 281 blocks of h2's post-opt IR.
The best placement reaches 0.61343 at 27,400 B, below main's 0.62103. Repaying h2's 240 B in one place cannot land it.
The original's missing bytes have to come from faithful code spread over the function. A greedy distributed padding
(`padgreedy.py`, one lddw plus volatile store per round) stalls at 0.61788 at 27,256 B after 6 rounds. It picks
register-allocation side effects, not size.

Partial holder phis keep more of the size but lose position. In these, only some uses read the phi and the rest keep
the argument test:

| IR edit | bytes | ratio | fm |
| --- | ---: | ---: | ---: |
| L3q: curve store + pool read the phi, shared tree keeps the arg test | 27,240 | 0.58233 | 0.70042 |
| L3r: shared tree + pool read the phi | 27,384 | 0.57327 | 0.71352 |
| L3t: only the pool CPI reads the phi | **27,400** | 0.5725 (3315 slots) | 0.713 |

L3t keeps the size exactly but loses 0.05 to register-allocation and frame churn. A size-neutral holder phi is not enough
on its own.

## Next ideas

- The holder phi is worth about +0.009 fm once ~240 B of faithful code is found elsewhere. Pair h2 with any candidate
  that adds bytes faithfully (entry copy of `new`, holder_key copy at -0x518, sharing payload pieces). Each of those lost
  alone because it overshot the size. Screen pairs, not singles.
- The original keeps holder in r1 across the sweep-exit joins (`ldxdw r1,[-0x950]` before `jne r7,2`). Ours spills the
  phi once (6 accesses vs 26). A use of holder after the sweep that is live in a register would reproduce those reloads.
- The cashback phi is negative in every form tried (out-param, return value, IR join phi). The original's per-arm
  cashback stores sit in the fee-None per-arm threaded tree (w13a05/w13a18), so it needs that threading first.
