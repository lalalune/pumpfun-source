# w12a09-cto-cleanroom: structural outline of the original `admin_cto::execute`

Target: window `0x22a10`, `pump_recovered::admin_cto::execute`
(`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `20a1ae9c0` (program source unchanged on `e61df0357`), admin_cto ratio 0.43919, slots_diff 3352.
Second branch (`swarm/w12a09-cto-cleanroom-2`): main `b5975fa67` (after #2749), admin_cto 0.45147, slots_diff 3308.

## Result

| base | change | admin_cto ratio | slots_diff | bytes | normalized / raw | losses |
| --- | --- | ---: | ---: | ---: | --- | --- |
| 20a1ae9c0 | - | 0.43919 | 3352 | 27,400 | 1033 / 1033 | - |
| 20a1ae9c0 | t01: validate `if let Some(f)=fee{..}` → `match fee{None=>{},Some(f)=>{..}}` | 0.46285 | 3320 | 27,400 | 1033 / 1033 | 0 / 0 |
| b5975fa67 (L1, #2749) | - | 0.45147 | 3308 | 27,400 | 1033 / 1033 | - |
| b5975fa67 | t02: same change | 0.47551 | - | 27,392 | 1033 / 347 | 686 raw (size) |
| b5975fa67 | t03: t02 + `holder` rebound per target arm in validate | 0.48487 | - | 27,384 | 1033 / 347 | 687 raw (size) |
| b5975fa67 | t14: `holder` per arm alone | 0.48381 | - | 27,368 | 1033 / 347 | size |
| 4f24fbc32 (L2, #2792) | - | 0.45177 | 3308 | 27,400 | 1034 / 1034 | - |
| 4f24fbc32 | t13: t03 + can_edit last (= L2 + fee `match` + `holder` per arm) | 0.48517 | - | 27,384 | | size |

t01 passes the 363-case `pump_admin_cto_differential.py` (0 mismatches). On L1/L2 both changes gain
ratio but shrink the function by 8–32 B, so they are not landable alone. They are handed to the size-knob
lanes with the measured deltas below. Ledger keys `0x22a10-w12-*-validate-fee-match-none-first-v1`,
`0x22a10-w12-*-holder-phi*`, `0x22a10-w12-70f2704-*`.

## Mechanism: ISel reverse post-order fixes the sret-demotion slot order

BPF returns one register. Every call whose IR return type is a two-word aggregate (`{ i64, ptr }`)
therefore gets its own 16-byte stack object for the demoted return value. That covers
`From<AnchorError>::from`, `with_pubkeys`, `prepare_bonding_curve`, every CPI `Result<()>`,
`create_idempotent` and the `ProgramError` conversions. SelectionDAG creates each object when it lowers
the call, and SelectionDAGISel walks the IR blocks in reverse post-order (DFS from the entry,
successor 0 first). So the frame order of these 33 slots is the RPO of their calls. On main the
predicted order equals the measured frame exactly. Read back from the original:

```
orig: 284 289 298 296 330 338 334 326 | prepare 410 ... (same calls, same order as main) ... | 312 307 307wp 306
main: 284 289 312 307 307wp 306 298 330 338 | prepare 410 ... | 334 326 296
t01 : 284 289 312 307 307wp 306 298 330 338 334 326 | prepare 410 ... | 296
```

The error slots are therefore not allocas: their order is CFG order. The scope reading in the next
section is superseded by this mechanism. Main finishes 334/326 last in RPO. Its DFS enters the fee-check
region before the continuation, because the fee test's successor 0 is `Some` (`icmp eq tag,1`
from `if let Some(f)=fee`). The original visits the continuation first, so its fee test has `None` as
successor 0: `icmp eq tag,0`, the original's `jeq tag,0` at 0x0af8 and 0x1508.
`match fee{None=>{},Some(f)=>{..}}` produces exactly that.
- IR oracle: swapping only that branch's successors in main's post-opt IR predicted 0.45956 at 27,400 B.
- Measured: the source change gives 0.46285.

The RPO also shows that the original's `!holder_reward` branch on `holder` visits the non-holder arm
(306/307/312) first, so those calls get the last slots. Swapping that IR branch as well reproduces
the original slot order exactly, but the IR oracle gives 27,408 B and 0.45829 on top of the fee swap
(on b5975fa67: 27,384 B, 0.47528). Slot order is not the whole story: RPO also fixes vreg numbering,
which changes register allocation and spill slots.
On t01's IR, a scan that swaps each of the 143 conditional branches alone finds only:
- `bb12.i` (the 296 `!enabled` test): +0.0012 at 27,400 B;
- `bb26.i`: +0.0020, but at 27,408 B.
The lane's IR tools (`rpo.py`, `irswap.py`, `swapscan.py`, `tratio.py`, `regions.py`) stay outside the
repo, in `~/.cache/pumpfun-reconstruction/lanes/w12a09-cto-cleanroom/tools/`.

### Which source forms set successor order (after InstCombine)

InstCombine rewrites a one-use `br (icmp ne ..)` to `br (icmp eq ..)` with the successors swapped,
and removes `br (not c)` by swapping. So for one-use tests:
- A `bool` field gives `br (b==0)`: the false case is always successor 0, whatever the spelling (`if b`, `if !b`, `if b {..} else {..}`).
- An integer test `x==0`, `x!=0`, `x<1`, `x>0` or a `match` gives `br (x==0)`: the zero case comes first.
- An `Option` gives a real choice:
  - `if let Some(..)=o` emits `icmp eq tag,1`, so `Some` comes first;
  - `match o{None=>..,Some(..)=>..}` (the fee in t01/t02) and `let Some(..)=o else` (306 on main) test `tag==0`, so `None` comes first.
  `is_some()`/`is_none()` were not checked here.

The `Option` forms are therefore the levers available in source.
On t02's IR the 306 test (`bb20.i`) swapped is 27,400 B / 0.47573, the expected effect of
`let t=if let Some(t)=new{t}else{return Err(..)};` (Some first). The 410 `require!` swapped is
27,400 B / 0.48173, but no one-use integer test can put the error first.

### `holder` as a phi of constants inside validate (t03)

The original carries `holder` out of validate as a phi of constants (`-0x950`: 1 on the holder arm,
0 on the non-holder arm), and its fee checks are duplicated per holder arm: 326/330 are threaded and
the arms join at 334/338 (S9). Rebinding `holder` per target arm,
`let (target,holder)=if holder{..(*holder_key,true)}else{..(t,false)}`, makes LLVM's JumpThreading
duplicate the fee tag test and the quote_locked test per arm. The non-holder arm keeps the cashback
test (330); the holder arm drops it. Both arms then join at the configurable/range checks:
the original's B24-B27 / B48-B51 / B52-B53 shape (t03 B26-B29 / B46-B49 / B50-B51). It costs 8 B.

### Trials on main b5975fa67 (L1, 0.45147 / 27,400 B)

| trial | change (on top of the fee `match`) | ratio | bytes | note |
| --- | --- | ---: | ---: | --- |
| t02 | fee `match` alone | 0.47551 | 27,392 | 8 B short: 686 raw losses |
| t04 | + 330 as `st.cashback&&!holder` | 0.47551 | 27,392 | byte-identical to t02 |
| t05 | + 306 as `let t=if let Some(t)=new{t}else{..}` | 0.47491 | 27,392 | the IR swap predicted 27,400 / 0.47573; the source form changes more than successor order |
| t06 | + 410 as `require!(creator_fee<1,..)` | 0.45889 | 27,408 | InstCombine turns `ult x,1` into `eq x,0`: successor order unchanged |
| t03 | + `holder` rebound per target arm: `let (target,holder)=if holder{..(*holder_key,true)}else{..(t,false)}` | **0.48487** | 27,384 | phi of constants as in the original (-0x950); validate tokens 0.369 → 0.419, wallet gate 0.526 → 0.684 |
| t07 | t03 + `let rent=Rent::get()?;let min=rent.minimum_balance(0);` | 0.48426 | 27,352 | -32 B |
| t08 | t03 + 306 `if let` | 0.48427 | 27,384 | no size change |
| t11 | t03 with `(holder,target)` tuple order | 0.48487 | 27,384 | same as t03 |
| t12 | t03 + curve store `if let Some(f)=fee{curve.creator_fee_bps=f;}` (fee_unwrap revert) | 0.48584 | 27,376 | best ratio so far, 24 B short |
| t13 | t03 + `can_edit_creator_fee=false` after the fee store (#2792) | 0.48517 | 27,384 | no size change |
| t14 | `holder` per arm alone (no fee `match`), on L1 | 0.48381 | 27,368 | +0.032 alone, 32 B short; fee `match` on top adds +16 B |


This lane re-derives the original function's structure from the deployed bytes only
(`win.py orig 0x22a10`, `coords.py window 0x22a10`, symbolized call targets), then compares it
with main statement by statement.

## Tool: `tools/outline.py`

```bash
T=reconstruction/pump-main/lanes/w12a09-cto-cleanroom/tools
python3 $T/outline.py blocks --side orig            # 378 basic blocks in layout order, with events
python3 $T/outline.py blocks --side cand [--cand X] # same for a candidate (default: current baseline)
python3 $T/outline.py align  [--cand X]             # difflib alignment of the two event streams
python3 $T/outline.py frame  --side orig            # every r10 offset, first/last use, count
python3 $T/outline.py dis --side orig --range 0x1c78-0x1d70   # annotated disassembly, relative offsets
```

Events are calls (symbolized through the candidate's symbol table: every other function sits at
the same address in both binaries, because both unmatched windows keep their size), Source
lines (`LINE n`), error-code immediates (`err n`), `.rodata` strings named by `lddw` (msg! texts,
seeds) and `.data.rel.ro` pointers. On main the event-stream ratio is 0.7883 (273 orig events, 275 ours):
the call/error skeleton is almost the same; the byte ratio is dominated by the frame.
Worker-specific IR capture and `llc` runners are omitted from this packet; the
portable read-only outline helper and the measured structural notes are retained.

## Outline of the original (offsets relative to 0x22a10)

| region | orig | main | source | content |
| --- | --- | --- | --- | --- |
| R0 entry | 0x0000-0x05e8 (B0-B7) | 0x0000-0x0560 (B0-B11) | 339 | holder PDA, `shared`, curve bools, `global_quote`, CtoState, `new` copy, key copies, mayhem test |
| R1 validate | 0x05e8-0x1990 (B8-B65) | 0x0560-0x18d0 (B12-B60) | 284-338 | ten error exits + collect_old memcmp + phi-of-constants exit |
| R2 prepare | 0x1990-0x1c78 (B66-B72) | 0x18d0-0x1b80 (B61-B66) | 339, 410 | `prepare_bonding_curve(..)?`, `require!(creator_fee==0)` |
| R3 wallet gate | 0x1c78-0x1d28 (B73-B79) | 0x1b80-0x1d00 (B67-B74) | 556 | `if collect_old`: executable / owner msgs |
| R4 sweep | 0x1d28-0x3c68 (B80-B219) | 0x1d00-0x3c48 (B75-B213) | 647-720 | sweep gate, creator-vault PDA (648), AMM part (660), transfer_creator_fees CPI, native/token paths (719) |
| R5 sharing CPI | 0x3c68-0x4aa8 (B220-B286) | 0x3c48-0x4a18 (B214-B280) | 745-751 | pool-authority seeds, `if let Some(val)=sharing_update`, AdminCtoSharingConfig CPI |
| R6 curve+pool | 0x4aa8-0x4e50 (B287-B293) | 0x4a18-0x4df0 (B281-B291) | 752-766 | curve writes, pool owner/data test, admin_cto_pool CPI or msg |
| R7 event | 0x4e50-0x5680 (B294-B309) | 0x4df0-0x5610 (B292-B306) | 767 | Clock::get, emit!, emit_cpi!, drops, Ok |
| R8 cold | 0x5680-0x5888 (B310-B316) | 0x5610-0x5818 (B307-B312) | 284, 556 | 556 name/fmt, 284 name/fmt, Display unwrap_failed, 284 tail, common Err exit, ret |
| R9 tails | 0x5888-0x6b08 (B317-B377) | 0x5818-0x6b08 (B313-B376) | 556-569, 663-720 | 556 tail, native rent path, wallet body (collect, CollectCreatorFeeEvent, collect_coin_creator_fee CPI), sweep token path |

### R0 entry (orig B0-B7)

1. `find_program_address([b"holder-rewards", mint], ID)`; result copied to `-0x6a0..-0x688` (holder_key).
2. `shared`: memcmp(curve.creator, sharing_config.key) → memcmp(sharing_config.owner, FEES `ro+0x2071`)
   → `!data_is_empty()`; result `xor 1` stored to `-0x920` (default 0 stored before the first test).
   Loads `new` pointer `[r5-0xff8]` (kept in r7) and fee value `[r5-0x1000]` (→ `-0x930`) between the tests.
3. Before `global_quote`: loads curve bytes `0xa3` (cashback → `-0x8e8`), `0xa5` (holder_reward → `-0x8e0`),
   `0xa2` (mayhem → r8, callee-saved). Main loads all three after `global_quote`.
4. `global_quote(curve.quote_mint, &global)`: memcmp vs zeros, vs native mint (`ro+0x2d8`), vs `global+0x3a8`.
5. B7: CtoState materialized at `-0x38..-0xb` (creator, max_fee `global+0x430`, mayhem, cashback, holder_reward,
   quote_locked`&1`, `global+0x43f`, `global+0x43e`); same layout as main.
6. B7: **`new: Option<Pubkey>` copied by value from the arg pointer before the mayhem test**, SROA pieces
   tag `[0]`→`-0x8f8`, `[1,8)`→`-0x658/-0x655` (two overlapping u32), `[8,16)`→`-0x900`, `[16,24)`→r9,
   `[24,32)`→`-0x668`, `[32]`→`-0x660`. Main reads `new` lazily from the arg pointer inside validate.
7. B7: sharing_config key copied to `-0x470..-0x458`, holder_key copied to `-0x518..-0x500` (validate's by-value
   key arguments), then `jne mayhem → B312` (284 name/fmt and tail are cold, at 0x5680/0x5790).

### R1 validate (orig B8-B65)

Decision tree (orig; main has the same CFG but other block order and polarity):

```
B8  if holder_reward:       B9  if holder(&1) -> B20 else B10: 289 name/fmt -> B18 289 tail
B12 else if !holder:        B14 if new.tag&1 == 0 -> B16: 306 name/fmt -> B38 306 tail
                                else -> B29 memcmp(t, 0) / B30 memcmp(t, holder_key) / B31 memcmp(t, sharing)
                                        -> B47 307 (to_string OUTLINED + with_pubkeys), B46 312 (to_string OUTLINED)
B13 else (holder, !hr):     B19 if !holder_enabled -> B39: 296 name/fmt -> B41 296 tail
B20 holder path:            if new.tag != 0 -> B21: 298 name/fmt -> B23 298 tail
B24 holder arm, fee tag (-0x928) != 0:   B25 quote_locked&1 -> B27 326 name/fmt -> B45 326 tail
                                         B26 -> B52 (330 not tested: holder is known)
B48 non-holder arm, fee tag != 0:        B49 quote_locked&1 -> B27 (same 326 block)
                                         B50 cashback -> B51 330 (to_string outlined)
B52 both arms: !fee_configurable(-0x940) -> B55 334 (outlined); B53 f-1 >= max -> B54 338 (outlined)
B56-B65 exit: phi-of-constants for holder (-0x950: 0/1), cashback (-0x958), fee_is_some (r7 -> -0x8e8),
            skip_sweep (r3 -> -0x8e0: 1 = skip), collect_old (r6, B63 memcmp(creator, 0)),
            sharing_update tag (-0x8f8: 0/1/2), target pieces (-0x538/-0x535, -0x548, -0x540, -0x580..-0x568)
```

Error-site order (layout): orig 289, 298, 306, 296, 326, 312, 307, 330, 338, 334 | 410 | 719, 648, 660 | 284, 556;
main 298, 289, 330, 296, 326, 306, 312, 307, 338 | 410, 334 | 719, 648, 660 | 284, 556.

### Error temporaries (`From<AnchorError>::from` sret slots): RPO evidence (see Mechanism)

Each `error!()` site writes the `From::from` result to its own 16-byte slot (`add64 r1,-X` before the call):

| line | 284 | 289 | 298 | 296 | 330 | 338 | 334 | 326 | 410 | 556 | 648 | 660 | 719 | 312 | 307 | 306 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 6d0 | 6e0 | 6f0 | 700 | 710 | 720 | 730 | 740 | 760 | 7b0 | 7c0 | 7e0 | 800 | 8a0 | 8b0 | 8d0 |
| main | 6b0 | 6c0 | 710 | 8b0 | 720 | 730 | 890 | 8a0 | 750 | 7a0 | 7b0 | 7d0 | 7f0 | 6d0 | 6e0 | 700 |

In the original the three `else`-arm target checks (306, 307, 312) are the **deepest** error slots, after
the sweep's 719, in reverse line order, while the other eight validate errors form one shallow run
(284, 289, 298, 296, 330, 338, 334, 326). On main the deep group is 296, 326, 334 instead and 306/307/312
sit inside the shallow run. This observed slot grouping is consistent with a distinct scope or helper for
target resolution (306/307/312). It is a reconstruction hypothesis: optimized
stack layout alone does not prove source scope or alloca order.

### R2-R9 (orig) in brief

- R2: B66 `prepare_bonding_curve(r1=-0x750 sret, bc+0x30, ..)`; B68 `creator_fee` test → B69/B72 410.
- R3: B73 `collect_old&1` → B75 executable byte `+0xd2` → B76 memcmp(owner, system `ro+0x1b8`)
  → msgs B77/B78 → B79 `sol_log`; writable byte → B105/B310/B317 (556); token_frozen → B107 msg / B328 body.
- R4: **B80 sweep gate is one test of a stack flag** (`ldxdw r1,[r10-0x8e0]; jne r1,0 → B220`, r9=0 = swept).
  Main tests `shared&&holder` with two compares (B75-B78). B81 native memcmp + creator-vault PDA + 648 (B94/B96),
  B82/B84 AMM ATA data_is_empty, B98/B101 token_frozen/token_raw_amount → 660 (B103),
  B109-B213 transfer_creator_fees_to_pump_v2 (12 inlined Rc clones, abort B112), B216 Rent::get →
  B319 minimum_balance/lamports/saturating_sub → B325 ensure_rent_exempt, B326 collect_transfer_native;
  token path B87 token_raw_amount, B89 token_frozen, B93 719, B341 create_idempotent + B342 collect_transfer_vault_tokens.
- R5: B220 pool-authority seeds `[b"pool-authority", mint, &[bump]]`, `sharing_update` tag `&0xff != 2`;
  B222-B285 AdminCtoSharingConfig clones (inline Rc increments), B286 CPI.
- R6: B287 curve writes: old creator copy, `creator=target`, old fee load, `is_holder_reward=[-0x950]`,
  `is_cashback_coin=[-0x958]&1`, `if fee_is_some([-0x8e8]!=0) creator_fee_bps=f`, `can_edit=0`
  (every store re-loads `[accounts+0x38]`, as on main). B290 pool owner memcmp (`ro+0x200f`), B291 data_is_empty,
  B293 8 outlined `AccountInfo::clone` + memcpy(0x150) + admin_cto_pool with **holder loaded from `-0x950`**
  (main: `jne r8,0 / mov 0/1` select, an extra block pair B289/B290).
- R7: Clock::get, AdminCtoEvent::data, sol_log_data, emit_cpi (clone, data, from_iter, exchange_malloc,
  new_with_bytes, memcpy, invoke_signed), Rc drops, Ok.

## Statement-level structural differences (orig vs main)

| # | statement | original structure | main structure |
| --- | --- | --- | --- |
| S1 | `new` | copied by value into SROA pieces at entry (before 284) | read lazily from the arg pointer |
| S2 | curve bools | loaded before `global_quote` | loaded after |
| S3 | `holder` | `arg&1`, then phi of constants (`-0x950`) after validate | `arg & !2` byte kept, `!=0` select at each use |
| S4 | fee tag | phi of constants `fee_is_some` (r7, `-0x8e8`), tested `!=0` | arg tag reloaded, tested `==1` |
| S5 | sweep gate | one stack flag set on validate exits | `shared&&holder` two tests |
| S6 | cashback | phi/stack value `&1` | `[-0x8d0] & !holder & 1` at the store |
| S7 | 306/307/312 | own (deep) error slots, to_string outlined at 307/312 | in the shallow run, to_string inlined |
| S8 | 334 | in validate after 338 | chained after the wallet executable check |
| S9 | fee checks | 326/330 duplicated per holder arm (threaded), arms join at 334/338 | arms join before the fee tag test; 330 tests holder dynamically (`r8&0xff`) |
| S10 | pool CPI `holder` arg | loaded from the phi slot | `jne r8,0` select: extra 2-block diamond in B289/B290 |

Ledger rows already cover S1 (x2-cto-new-option-early-by-value, y1-cto-spill: rejected), S3/S6
(`unwrap_or(false)` variants), S5 (w9r1-admincto-relocs t27-t30, w10r1-admincto-region2of6 tree/skip),
S7 (`296 inside holder arm`, #2370), S8. What is new here is the observed error-slot grouping, which suggests a separate
scope for 306/307/312 and provides a concrete hypothesis for subsequent source trials.
