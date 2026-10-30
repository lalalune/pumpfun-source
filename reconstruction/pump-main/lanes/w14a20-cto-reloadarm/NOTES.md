# w14a20-cto-reloadarm: deref-behind-short-circuit / in-arm reload spellings for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main b174038c1 (#3250): 0.63571, 3,173 slots, 27,400 B, **M = 2,122** (matched original instructions).
Angle: continue w14a14-cto-mf1fill (#3241 qlin2, #3246 notes). qlin2 showed that a source re-read becomes a real reload only
when no load of the same address dominates it. This lane looked for more source forms of that mechanism.
Ledger keys: `0x22a10-w14-b174038-reloadarm-*-v1` (approach `reloadarm-source`).

**Result: no zero-loss gain and no source change. On b174038 the mechanism has no second faithful instance.** Of the
three IR re-read leads above main, one is a stack-slot artifact with broken semantics. The other two have no source
spelling that keeps main's CFG. Every in-arm or short-circuit spelling that would make the read a real reload either
folds back to main (GVN), or it adds a branch to the head and the layout collapses (M −150 to −560).

## 1. Oracles re-run on b174038, ranked by M

w14a03's raw-IR capture (`capvar.sh` -> `capraw.py`) plus `rx.py` (opt -O3 + llc) reproduces main exactly (`eq_main`,
0.63571 / 27,400 B / M 2,122). `rx.py`, `irre.py`, `irhold.py` and `irremat.py` now also print M. Tables:
`irreM-b174038.tsv` (298 re-read variants), `irholdM-b174038.tsv` (84 hold variants), `irrematM-b174038.tsv` (38 remat variants).

| oracle | variants | above main (M > 2,122) |
| --- | ---: | --- |
| re-read (whole + per-block, `--sub`) | 298 | 3 (below) |
| hold (fold dominated reload into the first load) | 84 | none (best 2,119) |
| pure-value remat | 38 | none (best = main) |

| re-read lead | value | bytes | ratio | M | source form? |
| --- | --- | ---: | ---: | ---: | --- |
| `%_195.1.i` | collect Ok payload word quote_mint[0..8] at `_58.i+16`, re-read in the Clock::get block | 27,232 | 0.63892 | 2,126 | **Invalid.** The reload sits after `lifetime.end(_58.i)`. Stack coloring gives Clock::get's sret the same slot (r10-0x2d0), so the variant reads `[r10-0x2c0]` *after* Clock::get overwrote it (see `p195-excerpt.txt`, 0x61a8-0x61d8). The original (orig 0x61e0 `ldxdw r9,[r10-0x2c0]`) matches main here except for r9 vs r8. That is the payload-register residual that tagreg/colderr own. |
| `%33` | holder_enabled (global+1087), re-read at the line-296 test | 27,360 | 0.63709 | 2,125 | none: see section 2 |
| `%_363@bb1` | sharing_config AccountInfo pointer (accounts+144) re-read in the owner test | 27,408 | 0.63591 | 2,123 | none: no clobber between the loads, so the source re-read `a6`/`d7` is byte-identical. The original spills this pointer (`-0x8e0`, orig 0x150/0x210/0x258) because its r7 holds an entry-copy value. That is an RA consequence of the entry copy (w13a41/42), not a reload. |

The remaining re-reads at M 2,121 (max_fee `%_33`, fee_configurable `%35`, the event `nf`) are all below main.

## 2. Source spellings tried (raw-IR capture + rx oracle = build tokens)

| trial | spelling | bytes | ratio | M |
| --- | --- | ---: | ---: | ---: |
| main b174038 | | 27,400 | 0.63571 | 2,122 |
| a1 | `holder_enabled:holder==Some(true)&&a.global.is_holder_reward_enabled` (deref behind `&&`) | 27,592 | 0.47313 | 1,585 |
| a2 / a8 | `holder_enabled:holder!=Some(true)\|\|..` / `!(holder==Some(true))\|\|..` | 27,568 | 0.47275 | 1,583 |
| a3 | `holder_enabled:a.bonding_curve.is_holder_reward\|\|..` | 27,504 | 0.46255 | 1,547 |
| a10 | `holder_enabled:if holder==Some(true){..}else{false}` | 27,592 | 0.47313 | 1,585 |
| a4 | `fee_configurable:fee.is_none()\|\|a.global.creator_fee_configurable` | 27,464 | 0.47367 | 1,583 |
| a9 | `fee_configurable:fee.is_some()&&..` | 27,216 | 0.58861 | 1,958 |
| a5 | `max_fee:if fee.is_some(){a.global.max_..}else{0}` | 27,344 | 0.53231 | 1,775 |
| a6 | shared chain: owner read through a fresh `{let a=&ctx.accounts;..}` in the `&&` arm | 27,400 | = main | 2,122 |
| a7 | pool_updated: `ctx.accounts.pool.owner` in the `&&` arm | 27,400 | = main | 2,122 |
| b1 | CtoState literal with `quote_locked:` set to the qlin2 body inline (field order unchanged) | 27,312 | 0.58905 | 1,963 |
| b3 / b5 | same, with literal order creator,{mayhem,hr,cb \| cb,hr,mayhem},quote_locked,max_fee,he,fc | 27,352 | 0.61019 | 2,035 |
| b2 / b6 | same, bools first (original load order), creator last | 27,208 | 0.57336 | 1,907 |
| b7 | cb,hr,mayhem,quote_locked,creator,max_fee,he,fc | 27,368 | 0.57914 | 1,932 |
| c1 / c2 | validate takes `holder_key:Pubkey, sharing:Pubkey` by value; 312 holder-first / sharing-first | 27,328 | 0.56097 / 0.55887 | 1,870 / 1,863 |
| c4 | holder_key by value only, `t==holder_key\|\|t==*sharing` | 27,440 | 0.54752 | 1,829 |
| c5 | sharing by value only | 27,400 | 0.56171 | 1,875 |
| c3, c6, d1, d2, d5, d7 | see SUMMARY.json | | | |

Notes on the table:
- **Short-circuit or in-arm global reads in the CtoState literal (a1-a5, a8-a10) all add a conditional block to the entry
  chain** between the quote tests and validate. That changes the head's block frequencies and layout (the same ~0.47
  collapse w14a11 mapped for the sweep gate). The reload itself is never the issue. The source has no way to put the
  deref "in the arm" without making a new arm.
- In-arm re-reads that do not add an arm (a6, a7, d-series) are byte-identical. `ctx` is noalias, and nothing between
  the loads clobbers memory (memcmp is readonly), so GVN folds them. qlin2 worked only because writing out
  `global_quote` moved the first deref into an arm that already existed (the `contains` operand of an existing `||`).
- No other existing `||`/`&&`/if arm in execute holds the first deref of a value that is read again later. The other
  helpers take `&Account`/`&AccountInfo`, so no coercion happens at a call site. The account reads after
  `find_program_address`, `data_is_empty`, `prepare_bonding_curve` and the CPIs are already reloads (calls clobber).
- token_frozen / token_raw_amount inlined by hand would replace one internal call with that body's own calls
  (data_is_empty, try_deserialize), so the original's 154 internal call count could not hold. Not tried.

## 3. Direction check: the original reloads less from account memory, not more

Non-stack load multiset (`ldx* [rX+off]`, rX != r10), main vs original: main has **15 more**
(+0x8 51/47, +0x10 41/38, +0x18 49/46, +0x38 12/10, +0x20, +0x70, +0xa5 3/2). The original keeps 30 more stack reloads
(w13a50). So the general direction from main toward the original is *hold and spill*, not *re-read*. qlin2's gain came
from the register choice it caused (accounts pointer in r8), not from having an extra reload. One example is the extra
`ldxb r8,[r1+0xa5]` at main 0x4c18: the pool CPI's `a.bonding_curve.is_holder_reward`, which the original does not
reload. Its source forms (`pool_hr_local`, h2pair) are already in the ledger as losses.

## 4. Structural residuals seen while reading (for other lanes)

- Orig 0x0d78-0x0e58 (57 instructions, the biggest single unmatched hunk after the 0x420 head) is the post-validate
  `shared&&!holder` arm with `target=st.creator`, laid out as fallthrough after the line-312 memcmps. In main, the 312 success
  edge jumps far ahead (`jne r0,0,+0xe4` at 0xd00) and the error block is the fallthrough. In the IR, MemCpyOpt
  forwards the first 7 bytes of st.creator from the curve (`%23`) and reads the rest from `%st`. The original reads all
  four words back from st (-0x38..-0x20). This is block placement plus memcpy forwarding, not RA.
- Line 312 in the original compares t against a **copy** of holder_key (-0x518) first and a copy of the sharing key
  (-0x470) second. Main compares against sk (-0x518) first and holder_key (-0x6a0) second. All by-value spellings
  (c1-c5) lose 250-300 M. The copy must come from somewhere other than a by-value parameter.
- `tools/gaps.py <cand.o|.so> [n]` lists the largest unmatched orig/cand hunks (score tokens) with offsets. On main:
  M 2,122, 1,217 unmatched original instructions, top hunks at orig 0x420 (+60), 0xd70 (+57), 0x1728/0x1798, 0x4538.

## Tools (experiment only)

| file | what |
| --- | --- |
| `tools/gaps.py` | largest unmatched hunks between the original and a candidate, by score tokens (imports w14a03 `irre_lib.py`) |
| `tools/rng.py <dis> lo hi` | print a hex offset range of a `sodis.py`/`dis.sh` listing |
| `tools/rec.py` | records a `res.jsonl` trial in the ledger |
| `edits/*.py` | the capvar EDITS lists above (b*/c* load `blib.py`/`clib.py` from this lane's out dir; copy them alongside) |
