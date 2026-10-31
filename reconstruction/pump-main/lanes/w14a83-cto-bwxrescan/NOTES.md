# w14a83-cto-bwxrescan: per-branch BPI weight re-sweep of `admin_cto::execute` (0x22a10) on 0d04cf4 and 95a64ba

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w13a26-cto-bfreq (#3047; `bwx.py`, `bwgreedy.py`): re-run its per-branch weight sweep on the current main,
restricted to weight states that source can reach. Ledger approach `bwxrescan`, keys
`0x22a10-w14-{0d04cf4,95a64ba}-bwxrescan-*`.

**Result: no landable change. On both mains, no weight state that source can reach (alone, as a pair, or applied to
every branch that shares a condition) beats main by more than +0.0003. The two +0.0003 states need code that source
cannot produce: a cold call on a path that has no call, or a bool that stays in memory. The table below gives each
branch's sensitivity.**

## Oracle

- Raw-IR capture plus `opt -O3`/`llc` oracle: w14a66's `capvar.sh`/`capraw.py`/`rx.py`/`px.py`/`eseq.py`/`dis.py`,
  repointed to this lane's `$OUT`. Both mains round-trip with `eq_main: true` (0d04cf4 at 0.66507/3,228, 95a64ba at
  0.66986/3,204).
- `tools/bwx.py`: w13a26's oracle with extra scores. `jm` is the ratio with jump offsets masked (w14a71 `jmcheck`
  semantics). `fm` masks frame offsets and `sk` masks frame offsets and registers (w14a66 `px.py` semantics). It also has
  `run_text()`. One llc run takes about 0.7 s.
- `tools/brtab.py m.ll bpi.txt`: one row per conditional br of execute. Each row gives the condition's defining
  instruction, the current BPI probability (from `opt -passes='print<branch-prob>'`) and a heuristic class: zero/libcall
  (0x30000000/0x50000000, i.e. 12:20 or 20:12), none (50:50), or cold/unreachable. The 0d04cf4 census is in
  `bpi-0d04cf4.jsonl`.
- `tools/rsweep.py m.ll out [BASESPEC]`: a sweep over the reachable weights only, on any post-opt module. Zero-class
  branches get 1:1; none-class branches get 20:12 and 12:20; both also get 16:1 and 1:16.
- `tools/and1.py`: rewrites each `icmp eq|ne i8 %v,0` bool test to the and-1 memory-bool form, with and without
  `!range` on the load.
- `tools/mvir.py in out BLK AFTER [SPEC]`: moves IR blocks only (it renumbers `%N` so llc accepts the result).
- `tools/reg.py [--jm]`: matched tokens per 0x800 region. `tools/jmiss.py`: jumps that align but have the wrong offset.
  `tools/ddiff.py`: a disassembly diff that ignores jump offsets.

## 1. BPI census (0d04cf4; 95a64ba is the same)

Execute has 146 conditional branches:
- 53 zero/libcall heuristic at 20:12.
- 40 with no heuristic (50:50): i1 phis, `tag==2` Result tests and `ult` range tests.
- 53 cold or unreachable. These are all std code: 40 `Rc::inc_strong` overflow traps (`strong==0` leads to
  `unreachable`), and the `PumpError`/`ErrorCode` name-lookup panics. Source cannot steer them.

## 2. Single sweep: 93 non-cold branches x {20:12, 12:20, 1:1, 1:2000, 2000:1, 16:1, 1:16, 2:1, 1:2}

The full table, with the best reachable state and the best state of any kind per branch, is in
`sensitivity-0d04cf4.md` / `.tsv`.

| main | best weight (any) | ratio | bytes | jm / fm | reachable? |
| --- | --- | ---: | ---: | --- | --- |
| 0d04cf4 0.66507 | `bb24.i` 16:1 or 2:1: wallet `create_idempotent ?` Ok-likely | 0.66537 | 27,400 | jm =, fm +0.0003 | no. The Err edge `bb79.i77` holds no call to mark cold; the effect is 2 tail blocks (`ldxdw r8,[-0x768]; ja`) trading places |
| 0d04cf4 | `bb6` 1:2000: `quote==default` memcmp | 0.66517 | 27,392 | jm -0.0002 | no (cold) |
| 95a64ba 0.66986 | `bb6` 1:2000 | 0.67026 | 27,392 | | no |
| 95a64ba | `bb94.i`/`bb47.i` 20:12 (`st.quote_locked` true-likely), `bb58.i` 12:20 or 1:2 (338 range test err-likely), `bb37.i`/`bb38.i` 20:12 (312 memcmp equal-likely) | 0.67016 | 27,400 | jm =, fm = | no. All give one identical binary: a swap of 2 spill colours (`r4` arg spill and `r8`, slots -0x910 and -0x908). `quote_locked` would have to stay a memory bool (`icmp ne i8 load,0`), but GVN forwards the zext store in `st` to an i1 phi. The 338 test is `(f-1) ult max`, which no heuristic covers. Memcmp-equal-likely is the reverse of the libcall heuristic |

Reachable states alone (a zero-class branch at 1:1, a none-class branch at 20:12/12:20): **no state on 0d04cf4 beats
main**. On 95a64ba the only reachable state above main is the frame-colour swap above.

## 3. Combinations

- `bwgreedy.py` (size-pinned greedy over all 362 singles within 0.002 of main, 0d04cf4) stops after `bb24.i` 16:1.
- Reachable pairs on 0d04cf4 (45 singles that change the code and stay within -0.012 of main, 983 pairs): the best is
  `bb35` 20:12 + `bb9.i` 20:12 at 0.66517 @27,392 (+0.0001 at -8 B). No pair at 27,400 beats main.
- Reachable pairs on 95a64ba: see section 6.
- The same weight on every branch that shares a condition (five shared i1s, including the holder test `%notholder` on
  `bb7.i`/`bb14.i` and `quote_locked` on `bb47.i`/`bb94.i`): at best equal to main on 0d04cf4.
- And-1 memory-bool form (14 i8 bool tests, `!range` kept or stripped): at best equal to main (holder_enabled `_31`).
  Holder and-1 gives 0.60916 @27,416 and holder_reward and-1 gives 0.59122 @27,360.

## 4. The 289/298 order is a block-placement effect (a structural lead, but a plain-ratio loss)

`bb7.i` is the line-289 copy of the shared holder test. At exactly 1:1 (50:50) its error block `bb10.i` becomes the
fallthrough, and errseq becomes **289 298 296**, the original order (main has 298 289). jm rises by +0.020 and fm/sk
by +0.007, but the plain ratio falls to 0.65479 @27,408. The +8 B is a `jeq`-to-next plus `ja`, because BPF
`analyzeBranch` cannot invert the branch. A tail RA spill at a new slot -0x968 adds to the loss. Any other weight
(1:2, 2:1, 20:12) leaves the order alone. The original tests holder with `and64 r8,1`, which is 50:50 by BPI, on both
of its copies. Here, setting both copies to 1:1 gives 0.60946.

The faithful layout comes from IR order, not from frequency:

| picture (0d04cf4) | ratio | bytes | jm | fm | sk | errseq head |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| main | 0.66507 | 27,400 | 0.67376 | 0.71061 | 0.79509 | 298 289 296 |
| IR: `bb10.i` moved right after `bb7.i` (`mvir.py`, no weight) | 0.66337 | 27,392 | 0.69004 | **0.7194** | **0.80419** | 289 298 296 |
| IR: the whole `bb10.i` chain (+ to_string blocks) moved | 0.66117 | 27,400 | 0.69473 | 0.7109 | 0.79599 | 289 298 296 |
| **source s289G**: `if st.holder_reward&&!(hopt==Some(true)){Err(error!(..))}else{Ok(())}?;` | 0.66117 | 27,400 | 0.69473 | 0.7109 | 0.79599 | 289 298 296 |
| s289A/C/D/E/F (`!a\|\|b{}else{return}`, `!(..){}else{}`, nested, `match` true/false-first) | = main | 27,400 | | | | 298 289 |
| `bb7.i` gets its own `icmp ne i8 %holder,1` (no zero heuristic) | 0.4745 | 27,472 | | | | holder arg kept live |

- The source form `s289G` (a `?` on an if-expression) is the first source spelling that gives the original 289/298 order
  without collapsing validate. Earlier attempts nested `if st.holder_reward{if !holder{..}}` (-380 B, w12/w13).
- Its plain-ratio loss is not jump distance. `jmiss.py` finds only +8 mis-offset jumps. The jm gain is an alignment
  change: the jm alignment of orig region 0x800-0x1000 goes from 63 to 120 tokens, while the plain alignment of that
  region goes from 123 to 109.
- Pricing: `shift.py` (w14a64) on the -8 B IR picture finds that the best pure +8 gives M 2,215, still below main's
  2,220. A reachable-weight re-sweep (`rsweep.py`) on the s289G base finds nothing above 0.66147 (`bb24.i` again).

So the 289/298 order is a real original feature and a large structural (fm/sk) lead, but every form measured so far
loses plain ratio. A partner change would have to recover about 13 matched tokens in orig 0x800-0x1000.

## 5. Ledger rows

`0x22a10-w14-0d04cf4-bwxrescan-{bpi-table,single-sweep,greedy-pairs,and1-sweep,bb7i-11,irorder-bb10,s289A,s289C,s289D,
s289E,s289F,s289G}-v1` and `0x22a10-w14-95a64ba-bwxrescan-{single-sweep,pairs,g95,qg284..qg338,qall}-v1`.

## 6. 95a64ba (after #3409, 0.66986 / 3,204)

`m95/` (in `$OUT`) holds the same census: 53/40/53, an 837-run single sweep and the reachable pairs. The singles are
in section 2.

Reachable pairs: 71 singles change the code (213 reachable singles in all, counting 2:1 and 1:2 as reachable on
none-class branches), giving 2,439 pairs.
- At 27,400 the best is 0.67016, the same colour swap as the single.
- At 27,392 the best is **0.67056 (+0.0007 at -8 B)**: `bb35` 20:12 (the sweep gate's `!skip` i1 phi, sweep-likely) plus
  `bb9.i` 20:12 (the wallet `token_frozen ?` test `tag==2`, Ok-likely). Neither weight has a source route:
  - The gate flag as a memory bool costs about 0.1 (w14a82 `k1`).
  - A `tag==2` test has no BPI heuristic.
  - Each weight alone loses (-0.002 and -0.0025).

s289G on 95a64ba: 0.66567 @27,400 (main 0.66986), sk 0.79688 (main 0.79599). The same Try-on-if-expression spelling at
each other validate site (284, 296, 298, 307, 312, 330, 334, 338) together with s289G gives exactly the s289G bytes. At
326 it gives 0.61919 @27,352, and at every site at once (`qall`) 0.45178. Only the 289 site responds to the spelling.

## 7. 963d1ee (after #3437, 0.67226 / 3,123)

The census is unchanged (53/40/53, `eq_main: true`).
- Reachable singles (`rsweep.py`, now also 2:1 and 1:2 on none-class branches): the best is +0.0003 @27,400. It comes
  from `bb95.i` 20:12 (`quote_locked`), `bb62.i` 12:20 or 1:2 (the 338 range test) and one Rc trap at 1:16. jm and fm do
  not change: this is the same spill-colour-swap family.
- Pairs over the top 32 changing singles (483 pairs): nothing above that single.

The weight lever is flat on three consecutive mains.

## Next ideas

- Find a partner for s289G. The 289/298 placement is original, and fm +0.009 shows that the validate head is closer
  in structure. What remains is matching the region 0x800-0x1000 alignment (the 298 holder-arm `new.is_some()` block,
  and the 296 `bb14.i` copy).
- Weight sweeps are now exhausted as a source lever on this target. Every frequency gain left is a 1-2 token frame-colour
  or tail-placement effect, and each needs a cold call or a memory bool that source cannot produce.
