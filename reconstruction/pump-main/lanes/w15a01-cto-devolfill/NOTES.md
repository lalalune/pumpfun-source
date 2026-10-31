# w15a01-cto-devolfill: fill for the validate placeholders (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base main 90300f9d2 (0.67346, 3,124 slots, M 2,248).
Continues w14a138-cto-devolpair (#3618), w14a115-cto-devol338st (#3510) and w14a110-cto-devol338 (#3485).
Ledger approach `devolfill`, keys `0x22a10-w15-90300f9-devolfill-<variant>-v1`.

M is the count of matched masked tokens (raw-IR oracle `tools/scr3.py`: capraw identity capture, opt -O3, llc);
ratio = 2M/(6676+(bytes-27400)/8). Bases used below:

- **Q3** = main + w14a115 devol338st (`validate(st:&mut CtoState,..)`, `let hr=st.holder_reward;`,
  `st.fee_configurable=false;` in place of the line-338 volatile) + vol334_back (line-334 volatile removed).
  No `read_volatile` left; one constant store into the `st` alloca remains. 27,392 B, M 2,247.
- **D4** = Q3 without the 338 store (`d_none`): no placeholder, no store. 27,384 B, M 2,225.

## Landable gain: `fee_configurable` first in the CtoState literal

`let mut st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:..,max_fee:..,...}` (field init order
only; the struct declaration and every read are unchanged).

| build | bytes | M | ratio | slots | normalized / raw |
| --- | ---: | ---: | ---: | ---: | --- |
| main 90300f9 | 27,400 | 2,248 | 0.67346 | 3,124 | 1034 / 1034 |
| main + lf_fee_configurable (measure.sh) | 27,400 | 2,249 | **0.67376** | 3,124 | 1034 / 1034, 0 losses, differential 388/0 |

Mechanism: MIR evaluates the literal's fields in source order. Putting the `creator_fee_configurable` byte load first moves
the global's `+0x43e` byte load ahead of the bonding-curve creator copy at entry, which changes the entry register
assignment (r0/r6 swap for the two `st` byte stores) and swaps the `[r10-0x948]`/`[r10-0x900]` reload pair in the fee arm.
Every other literal order loses (table below).

## Placeholder table (raw-IR oracle)

| key | genes | bytes | M | dM vs main | placeholders |
| --- | --- | ---: | ---: | ---: | --- |
| main | - | 27,400 | 2,248 | 0 | 2 volatiles |
| Q3 | devol338st + vol334_back | 27,392 | 2,247 | -1 | 338 store |
| F (lf_fc on Q3) | + lf_fee_configurable | 27,392 | 2,248 | 0 | 338 store |
| **F_d_maxf** | F + `st.max_fee=f;` at 338 instead of `st.fee_configurable=false;` | **27,400** | **2,248** | **0 (tie, 3,124 slots)** | 338 store (value store, no volatile) |
| F_N6 | F + N6 shared-arm order | 27,408 | 2,249 | +1 at +8 B | 338 store |
| D4 | no placeholder, no store | 27,384 | 2,225 | -23 | none |
| F_d_none | F without the 338 store | 27,384 | 2,226 | -22 | none |

After this PR lands, main is 2,249, so F_d_maxf is one short of a tie on the new main.

## The two placeholders are different kinds of fill

- **334** (w14a138): pure fill. `insmap.py` on Q3 and on F: one junk 8-byte slot anywhere in 0x180-0x1a0, 0x6d8-0x18d0,
  0x19c0-0x1a90 (519 positions) gives +1 M. On F a junk slot there gives **2,249 at 27,400**, so any ordinary source change
  that adds exactly one validate instruction on top of F also beats main.
- **338**: a placement anchor, not fill. Removing it (D4) costs 22-23 M, not 1. With the range-OK block empty, the
  jlt edge goes straight to the validate join (bb75), and block placement moves the line-334 error block (stw 334 / 6077)
  from between the 338 error and the OK block to after the shared-arm code. In the original the OK block holds two spills
  (`stxdw [r10-0x918],r4; stxdw [r10-0x948],r3`) and the fee-tag phi constant `mov64 r7,1`. w14a110 (#3485) priced that
  phi at -276 M on main's RA; only a value-free store into an escaped alloca, or a value store (`st.max_fee=f`, this lane),
  keeps the placement.
- `insmatch.py` (new): inserting one ORIGINAL token from the facing LCS gap instead of junk. On Q3 the best of 748
  (position, token) pairs is 2,249 (+1 over main) in 726 cases, for example `mov64 r7,1` anywhere in 0x1748-0x17a0. So one
  faithful extra instruction is worth at most +1 M over a junk one.

## Screens on Q3 (all raw-IR oracle; M relative to main 2,248; Q3 itself is 27,392 / 2,247)

| family | rows | result |
| --- | ---: | --- |
| fee range spellings (`f<1`, `!(f>=1&&f<=max)`, `max<f`, split `f==0` / `f>max` checks, `match f{0=>..}`) | 7 | identical to Q3, or split checks +200 B / -389 (no tail merge of the two line-338 errors) |
| holder spellings (`unwrap_or(false)`, `unwrap_or_default`, `matches!`, `is_some_and`, `if let`) | 5 | all one form: +8 B, M 1,372 |
| line-298 / 302 spellings (`!holder`, `!=Some(true)`, `!matches!`, field order, De Morgan, `st.holder_reward`) | 9 | identical or -14 to -584 |
| `new` / `t` spellings (`!=None`, `if let Some(_)`, `match`, let-else, `ok_or_else`, `is_none`+`unwrap`, `!is_none`) | 8 | identical or -16 / -146 |
| InvalidCreator / zero check (swap, by ref, split, `contains`, `eq`, reversed operands) | 7 | identical, -3 / -4 / -8, or split -16 B / -361 |
| cashback placement (inline, swapped, in fee arm, at line 330, at top) | 5 | identical, or -216 / -707 |
| validate parameters by ref / by value / reordered | 6 | identical, -6, -343, -457 |
| fee-arm forms (`if fee.is_some()`, `as_ref`, `for f in fee`, `_=>`, `match &fee`, `?` errors, `require!`, `require_keys_neq!`) | 18 | identical or -86 to -189 |
| fee-arm return forms on D4 (`return Ok(target)` per arm, `match` expression, let-else / `match` early return) | 9 | -417 to -555 |
| validated-fee re-wrap on D4 (`Result<(Pubkey,Option<u64>)>`, `(Pubkey,bool)` flag, swapped tuple) | 3 | -909 to -1,147 (frame shift, w14a142) |
| 338 store kind on Q3 (`st.max_fee=f`, none, store before the range check) | 3 | +8 B / -1, -23, -23 |
| size knobs on Q3/D4 (N6, N6s, N0s, ev_mint_key, cu_fee_oldunwrap, ev_cb_local, cu_fee_replace, i_sep) | 12 | best QN6 27,408 / 2,248 |
| CtoState literal: one field moved first or last (14), then a second field after fee_configurable (13) | 27 | **lf_fee_configurable +1** (27,392 / 2,248 on Q3); the rest identical or -24 to -606 |
| validate call-site spellings (`&a.sharing_config.key()`, `&hk.0`, `args.0`) | 3 | -170, identical, -785 |

## Round 2 on main 86e2a6b (this lane's #3666 landed: 0.67376, M 2,249)

`devol` gene = devol338st + vol334_back on the new main (no `read_volatile` left). M relative to the new main (2,249).

| key | genes | bytes | M | dM |
| --- | --- | ---: | ---: | ---: |
| N_main | - | 27,400 | 2,249 | 0 (eq_main) |
| N_devol | devol (338 constant store) | 27,392 | 2,248 | -1 |
| V_d_maxf | devol + `st.max_fee=f;` at 338 | 27,400 | 2,248 | -1 (3,124 slots) |
| W_dm_a / dm_b / dm_h / dm_repl | `st.max_fee=f` spellings (`let mx`, `else{}`, `f.min(max)`, `mem::replace`) | 27,400 | 2,248 | -1 |
| W_dm_f / dm_g / dm_r / dm_take2 | two stores, `max-f`, `mem::take` at 334 + max store | 27,408 | 2,247 | -2 |
| W_dm_take | `mem::take(&mut st.fee_configurable)` at 334, no 338 store | 27,392 | 2,226 | -23 (no 338 anchor) |
| V_* (17) | devol / devol+d_maxf + CtoState declaration orders (13) or neutral literal moves mv_2_4..7 | 27,392 / 27,400 | 2,248 | -1 (all) |
| X_* (14) | devol+d_maxf + small main losers (mv_0_*, mv_1_0, qo_*, i_rev, z_rev, h_298ne, N6, N6s) | | <= 2,248 | additive, -1 to -12 |

V_d_maxf against main differs only in (a) `mov64 r1,r2` in place of the line-334 `ldxb` (f must survive the `add -1`
for the store) and (b) an r4/r5/r0 rotation of the `new`/target pieces in the holder/shared arm (0xa90, 0x1438, 0x1890,
0x18d8, 0x1960 regions). (b) is the -1.

Main-side order knobs on 86e2a6b (no gain): second literal moves after fee_configurable (`mv_i_j`, 33 rows: 4 eq_main, the
rest -1 to -633), quote_locked disjunct orders (5: -7 to -19), shared conjunct orders (5: -82 to -335), CtoState
declaration orders (13: all M-neutral, frame tokens move), block-result tuple element orders and the `Ok::<..>(..)?`
re-bind order (22: 11 eq_main, -1 to -5 otherwise).

**measure.sh of V_d_maxf** (`devol-dmaxf.patch`): 0.67346, 3,124 slots, 27,400 B, 1034/1034, 0 losses, differential 388/0,
sha 9a029b66641d3789. It has zero `read_volatile`/`black_box` and one value store (`st.max_fee=f;`) into the local `st`. It is
-0.0003 against the new main and equals the pre-#3666 main. This is the owner's devolatilization candidate if a one-token cost
is acceptable. It is not proposed for landing.

A further 30 Q3-identical spellings on V_d_maxf (`Y_*`) are all 2,248 or lower. The rotation does not respond to validate
spelling.

## Next ideas

1. On the new main, V_d_maxf (no volatile, one value store) is 27,400 / 2,248, one short. Its only loss is an RA rotation in
   the holder/shared arm; a zero-byte RA-neutral knob that rotates r4/r5/r0 back would tie, one matching an original token +1.
2. F_N6 is +1 at +8 B (27,408 / 2,249). Pair it with an M-neutral -8 B knob. None is known: no ledger row on 90300f9 /
   e88f9d5 / ebe5387 has 27,392 B with M >= 2,248 except the volatile removal itself.
3. Second-field literal orders after fee_configurable are now exhausted. The struct's DECLARATION order is untried (it
   changes the layout of `st`, so the bool store offsets move).

## Tools (experiment only)

- `tools/scr3.py` (w14a138's raw-IR screen with this lane's paths and `genes_f`), `tools/genes_f.py` (all genes above),
  `tools/insmap.py`, `tools/gaps.py`, `tools/rx.py`, `tools/capraw.py` (copied from w14a138).
- `tools/insmatch.py`: inserts an ORIGINAL token from the facing LCS gap at each position of each gap
  (`RANGE=lo,hi`). It gives the M ceiling for one faithful extra instruction.
