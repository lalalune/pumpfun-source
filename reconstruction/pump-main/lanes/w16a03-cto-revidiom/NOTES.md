# w16a03-cto-revidiom: reverse idiom dictionary for admin_cto (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9bd38c7d5 (`$BASE` = `baseline-main-9bd38c7d5`: Pump Main 1034/1035 normalized and raw, admin_cto 0.67376,
3,124 slots at 27,400 B; admin_cto.rs is unchanged since 86e2a6b74). Ledger approach `revidiom`, keys
`0x22a10-w16-9bd38c7-revidiom-*`.

**Result: notes and tools only, no source change.** No spelling found here reproduces a class at or above main, and no
ordinary spelling replaces a `read_volatile` placeholder at no loss. The deliverable is the pattern -> window -> spelling
table below, a line-table source map of the whole original program, and two mechanism findings:
- `Some(args.0.map(|_|target))` is the first source form that reproduces the original's sharing-CPI `val` copy
  (tag + 7/8/8/8/1 from the validated target), but its spill slots and registers move (0.54993). Joined with w15a11's
  b01 and v01 (`vb01v`), it reaches main's structure (rfj true LCS 2984 vs 2985) with three more original-only shapes,
  at 0.5677. What remains is 16 B of frame and the TCF-run register colouring (section 4.4).
- The `args=&(new,)` tuple in main works because it loads `new`'s tag early, as the original does (orig 0x4d8). Every
  `Some(new)`-without-args form collapses for that reason alone.
- A map of where main makes instruction shapes that the original program never makes (`alien.py`): 416 4-grams. 100 of
  them come from the two CPI statements built from manual `AccountInfo{..}` literals.

## 1. Method and tools (`tools/`, experiment only, pure Python after one build)

- **Line-table build** (`tools/ir/caplines.py`): the identity build with `--emit=link,asm -C debuginfo=line-tables-only`
  (one build slot, about 3 min). It writes `pump_recovered.s` with `.loc` lines. `asmlines.py` parses it into per-function
  instruction lists (1,158 functions). Of the 716 matched windows whose symbol is in that crate, 668 have the same
  instruction sequence as the original window (`asmcheck.py`). The other 48 are aligned with difflib on mnemonics.
- **`srcmap.py`**: original address -> source. `loc()` gives the innermost `.loc` (often a core/alloc file).
  `userloc()` gives the nearest `programs/` `.loc` at or before it, which is the call site of inlined library code.
  Example: `srcmap.py 0x351f8` -> `distribute_fee_to_holders.rs:124:289` (`... mint:a.quote_mint.to_account_info() ...`).
- **`revidiom.py`**: shape n-gram index over every matched original window. Registers are alpha-renamed inside each
  n-gram, so dataflow is kept. r10 offsets and immediates are masked, except and/shift masks and compare constants below 4.
  Non-r10 memory offsets (field offsets) are kept. `revidiom.py range <lo> <hi>` lists, for an orig admin_cto range, the
  n-grams that appear in no matched window. It also lists the windows that share the most n-grams (rare ones first),
  each with the inner and user source location of the hit. `revidiom.py runs` does this for every orig-only run.
- **`runs.py`**: the orig-only runs. It runs a true-LCS DP (rfj mask) of orig vs main from the two llvm-objdump
  disassemblies (`odis.py`, `shape.py`).
- Query scripts:
  - `q1.py` / `q1src.py`: AccountInfo clone census.
  - `q2.py` / `q2src.py`: census of 7-byte `[1,8)` piece copies.
  - `q_owner.py`: owner-check / `data_is_empty` order.
  - `calls.py`: orig vs main callee sequence.
  - `binlcs.py`: masked true LCS of a `fn.bin`.
  - `fdelta.py`: frame-offset deltas over rfj-matched pairs.
  - `ircmp.py`: post-opt alloca and call diff of two oracle runs.
- `tools/ir/cap.sh <name> <edits.py> <slot>` is the raw-IR capture plus opt/llc oracle (w15a23's t118 tools, repointed).
  On 9bd38c7 it reproduces main exactly (`eq_main: true`, 0.67376 / 3,124).

Usage. The tools expect `$OUT=~/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom` (edit `OUT` in `shape.py`,
`srcmap.py` and `tools/ir/*` for another lane).

```bash
llvm-objdump -d --no-show-raw-insn evidence/original/pump/deployed.so > $OUT/dis/orig.dis   # and $BASE/unstripped.so > main.dis
python3 tools/ir/caplines.py <crate copy> $OUT/work1 $OUT/lines/cap    # one build slot; writes lines.s
python3 tools/asmlines.py                                              # -> $OUT/lines/asm.pkl
python3 tools/runs.py                                                  # orig-only runs vs main (true LCS, rfj)
python3 tools/revidiom.py range 0x3d20 0x3d88 --n 4 --top 5            # who else has this shape, and from which source line
python3 tools/srcmap.py 0x351f8                                        # any original address -> source
bash tools/ir/cap.sh <name> e/<name>.py <slot>; python3 tools/binlcs.py <name>; python3 tools/fdelta.py <name>
```

Data (`data/`): `classes-revidiom.txt` (the query classes below), `runs-revidiom.txt` (all 61 orig-only runs of at least
2 instructions), `q1-*.txt`, `q2-7byte-pieces.txt`, `call-sequence-orig-vs-main.txt`.

## 2. How unusual admin_cto's missing shapes are

| set | 4-grams | in no matched window |
| --- | ---: | ---: |
| whole original admin_cto | 3,336 | 636 (19.1%) |
| whole main admin_cto | 3,334 | 699 (21.0%) |
| the 61 orig-only runs (true LCS, rfj), with context | 397 | 172 (43%); another 55 occur in at most 8 windows |

275 of the original's 636 corpus-unseen 4-grams are already in main. Main also has 409 corpus-unseen shapes that the
original lacks. The orig-only runs are twice as unique as the function as a whole. Most of what admin_cto lacks is
register, spill and phi structure that occurs nowhere else in the program. For those there is no sibling spelling to port,
and the table says so.

## 3. Pattern -> window -> spelling table

| # | original pattern (orig offsets) | matched windows with the same shape | source construct there | verdict for admin_cto |
| --- | --- | --- | --- | --- |
| Q1 | accounts pointer reloaded from `[r10-0x8d8]` before every AccountInfo clone. All 8 sharing-CPI clones (0x3d88-0x44f8), 2 TCF clones (0x3228, 0x3340). 10 of 19 clones in total; main 3 of 19 | none at this density. holder_distribution::execute 5/13 (`anchor_spl::associated_token::create(CpiContext::new(..))` inside the recipient `for` loop, distribute_fee_to_holders.rs:86/124/126); create_v2::initialize_metadata 2/11 (create_v2.rs:591); extend::fund_bonding_curve_rent 2/4; trade::check_quote 2/4; 13 windows 1 each. Every other multi-clone CPI build holds the pointer in a register (migrate*::create_pool 0/13-0/19, init_pump_amm_boost 1/11, try_accounts 0/10) | loop-carried pressure (holder_distribution) or isolated RA splits | no source idiom; pure RA pressure in the sharing arm (`swept` in r9 in the original). Agrees with w15a34 |
| Q2a | Pubkey payload copied as 7/8/8/8/1 pieces: two overlapping `ldxw/stxw` at k+3 and k, then 8/8/8/1 | all 46 hits outside admin_cto map to core `result.rs:1952` (`Try::branch`, `Ok(v) => Continue(v)`) or to `Ok(..)` construction. pump_quote::read_pubkey (`Ok(Pubkey::new_from_array(bytes))`), parse_pool (`read_pubkey(header,139)?`), historical_curve::decode_v1-v8 and Global/GlobalConfig `try_deserialize` (borsh `Pubkey` fields via `?`), `__global::set_params` | the Ok payload of a `Result<Pubkey,E>` whose Err payload (anchor `Error` = `{i64,ptr}`) sits at 8..24, so SROA splits it on the 8-byte grid | the original's target and sharing payload are `Result<Pubkey>`-grid values (7 B / 9 B allocas plus two SSA pieces) |
| Q2b | `new` (an `Option<Pubkey>` argument) loaded on that grid at entry, before the mayhem test: tag, 7 B, 8, 8, 9 B (0x4d8-0x538) | none (all 16 4-grams unseen in the corpus) | - | unique to admin_cto. Note that main's early `args` tuple already loads the tag at this point (section 4.1) |
| Q2c | sharing-CPI `val` = tag from `new` + 7 B and 9 B from the final target allocas `[-0x550]/[-0x560]` + middle from `[-0x900]/[-0x948]` (0x3d20-0x3d80) | same Result-grid windows as Q2a (set_params, Global/GlobalConfig deserialize, decode_v*) | `?` on `Result<Pubkey>` | **reproduced** by `sharing_update=Some(args.0.map(\|_\|target))`, but at 0.54993 (section 4.2) |
| Q2d | non-holder arm rebuilds `t` in memory from the pieces before the three memcmps (0xc08-0xc78) | no shape match (11 of 18 4-grams unseen) | - | follows from Q2b |
| Q3-B | curve bools (0xa2/0xa3/0xa5) and the Global pointer loaded right after `shared`, before the quote_locked memcmps (0x268-0x2b8) | 29 of 49 4-grams unseen. Closest: swap_hop (`validate_buyback_fee_recipient_account(&a.global,..)`), DistributeCreatorFees try_accounts | account field reads held across calls | already priced as flaghoist (w14a41 0.64209) and the CtoState literal family (w15a30) |
| Q3-F | per-arm phi constants `mov rN,0/1` stored to `[-0x950]/[-0x958]/[-0x8f8]` (0xd78-0xe58) | 11 of 32 unseen. constant_product::output, buy_exact_quote_in_v2 (`gross_total(..)?`), sell_v2 (`if c.is_holder_reward{..}else{0}`) | value-producing `if`/`?` joins | generic; no admin_cto-specific spelling |
| Q3-H | holder `and64 r8,1` in r8, `jeq +1; ja` pairs (0x5e0-0x748) | 21 of 47 unseen. validate_pool / buy_v3 (`parse_pool(..)?`), buy_v2 (`trade_fees(..)`) share only `jeq +1; ja` layout pairs | layout artefacts: BPF `analyzeBranch` cannot reverse conditional branches | and-1 basin already priced (w15a11 v14 0.4109) |
| Q3-b01 | holder_key and sharing key copied by value at validate entry (0x548-0x5d0) | DistributeCreatorFees try_accounts, buy_v2, v3_emit_buy, creator_migration::execute (key copies into locals or events) | `Pubkey` by value | w15a11 b01 (0.54595) |
| Q4 | fee OK block (orig 0x1748-0x17a0: `stxdw [-0x918],r4; stxdw [-0x948],r3; mov64 r7,1`) | create_v2::execute:774-779, the same two checks (`require!(a.global.creator_fee_configurable,..)`, `require!(fee<=max,..)`) followed by **`fee=creator_fee_bps.0;`** in the OK path | a validated-fee local assigned in the OK path, so a fee-tag phi of constants appears | the sibling confirms w15a29's reading: the OK-block anchor is the fee-tag phi. Priced at -186..-276 M on main's shape by w15a29 (phiprobe) and w15a15 (j_all 0.30884). Not landable alone |

Call-order differences, orig vs main (`data/call-sequence-orig-vs-main.txt`). The 157 calls match except four places:
- holder-rewards PDA first (class A);
- 307/312 `to_string` outlined in the original (class D);
- in the sweep's token arm, `token_raw_amount` before `token_frozen` (orig 0x20c8/0x2110; w14a70 `a1` family, 0.665);
- the pool gate `owner==&AMM` before `data_is_empty` (orig 0x4be8/0x4c10; `mpo`, w14a91/w14a106/w15a04, 0.633).
All four are in the ledger.

## 4. Mechanism findings

### 4.1 Why `Some(new)` without the `args` tuple collapses

`e/u_none.py` (`let args=&(new,);` removed, `Some(new)` in the shared arm; the w14a113 w08 / w14a127 / w15a21 family):
0.48104 @27,376. The normalized post-opt execute IR differs from main in one place only: where `new`'s tag (`load i8`)
and the `new+1` GEP are emitted. Main's tuple copy loads the tag right after the CtoState stores. That is the original's
position: orig 0x4d8 `ldxb r2,[r7+0]` -> `[r10-0x8f8]`, the sharing-tag slot. u_none loads it inside the sharing arm.
Block count (281) and the alloca set are the same. The true LCS falls from exact 2255 / rfj 2985 to 1617 / 2414, so this
is a block-layout re-placement, not a frame effect. **Any spelling that drops the early `args` read must keep an early tag
read.** Several earlier "Some(new) collapses" results (gr_sun, gr_mun, w08, T_noargs) are this effect, not the payload.

### 4.2 The Q2 val shape is reproducible: `Some(args.0.map(|_|target))`

Reading Q2c off the original: the tag comes from `new` (w15a23's webs), and the payload comes from target's Result-grid
pieces. The shared non-holder arm then needs `Some(<tag of new, payload of target>)`. With `args` kept for the early tag
read (4.1):

| probe (raw-IR oracle on 9bd38c7) | ratio @ bytes | true LCS exact / j / rj / fj / rfj |
| --- | --- | --- |
| main | 0.67376 @27,400 | 2255 / 2367 / 2722 / 2581 / 2985 |
| `valmap`: `sharing_update=Some(args.0.map(\|_\|target));` | 0.54993 @27,352 | 1949 / 2068 / 2448 / 2457 / 2940 |
| `valand`: `Some(args.0.and(Some(target)))` | 0.37751 @27,352 | 1451 / 1571 / 1928 / 2339 / 2818 |
| `u_none` (4.1) | 0.48104 @27,376 | 1617 / 1720 / 2037 / 1909 / 2414 |

`valmap` emits the original's 12-instruction val copy (cand 0x3d28-0x3d88 vs orig 0x3d20-0x3d80) with one extra tag
reload and offsets 8 B lower:
- the `stxb` tag;
- a 7 B piece as two `ldxw/stxw`;
- the two 8 B SSA spills, in the same order (`[16..24)` first);
- an 8 B and a 1 B piece.

It is the first source form that does this. `match args.0{Some(_)=>Some(target),None=>None}` and
`if args.0.is_some(){Some(target)}else{None}` compile to the same bytes (vm_m, vm_i).

It also keeps the structure: rfj is only -45 vs main, and its frame bottom is `-0xc38`, the original's (main stops at
`-0xc30`). The loss is spill-slot placement and registers:
- The 2 x 32 B sharing-payload allocas become three 7 B / 9 B pairs: `sharing_update.sroa.6.sroa.*`, `sharing_update16.sroa.*`
  and the map temp `_63.sroa.5.sroa.*`.
- The two payload middle pieces become SSA values spilled at validate's exit (cand 0x1790/0x17a0). In the original one of
  them is `new`'s entry piece (`[-0x900]`, def at 0x510) and the other is the per-arm phi `[-0x948]` (3 defs).
- The long-lived argument spills then move: accounts pointer `-0x8d8` +8, ctx `-0x938` +16, `-0x918`..`-0x928` -24. Main
  has these exactly. In all, 360 matched frame accesses are off, against main's 121 (`fdelta.py`, per-slot table in the
  ledger row).

Bound: with the frame masked (`fj`), valmap is 2457 against main's 2581. With registers masked (`rj`), it is 2448
against 2722. So a perfect frame partner alone would still leave valmap 124 matched tokens short on registers.

Control: dropping main's `Ok::<_,Error>((target,sharing_update,cashback))?` round trip alone (`m_nt`) gives 0.55019, the
same level. That round trip is worth +0.12 on main through the frame. With valmap it does nothing (`vm_nt` 0.55022). So a
usable valmap needs its own frame-shaping partner. The table below lists the order and arity variants screened.

Frame-partner screen on valmap (raw-IR oracle, all at 27,352 B):

| variant | change on top of valmap | ratio | exact / rfj |
| --- | --- | --- | --- |
| vmr_stc, vmr_cts, vmr_cst, vmr_sct, vmr_tcs | the Ok round-trip tuple in each other field order | 0.54993 | 1949 / 2940 |
| vmr_ts | round trip of `(target,sharing_update)` only | 0.54993 | 1949 / 2939 |
| vmr_t | round trip of `target` only | 0.55172 | 1952 / 2939 |
| vm_nt | no round trip | 0.55022 | 1948 / 2939 |

rustc lays the tuple out the same way whatever the field order, and once the payload is on the Result grid the round trip
no longer moves the frame. None of these is a partner.

### 4.3 Both Q2 classes at once

The original's entry pieces (Q2b) are reproduced by "validate reads `args.0`" (w13a41 t1 found the 7/8/8/9 entry loads at
0x655/0x658/0x900/0x660/0x668). On 9bd38c7 that form alone (`mA`) is 0.43917 @27,584, which is +184 B and rfj 2413.
Joined with valmap (`vmA`) it is 0.4494 @27,824, rfj 2420. Each of the two Q2 classes can now be produced by an ordinary
spelling, but neither survives on today's skeleton. The original produces both because its validate is threaded per
arm. In the non-holder shared path the target pieces are then `new`'s entry SSA values (val[8..16) = `[-0x900]`, the
entry def at 0x510).

### 4.4 valmap joined with b01: two faithful classes, main's structure, not main's frame

b01 (w15a11: validate takes `holder_key` by value, so it reproduces the original's holder_key copy to `[-0x518]` at orig
0x598-0x5d0) is the other class that has an exact ordinary spelling. Joined with valmap:

| probe | change | ratio @ bytes | exact / j / rj / fj / rfj |
| --- | --- | --- | --- |
| mb01 | b01 alone (control) | 0.54595 @27,360 | 1987 / 2110 / 2499 / 2479 / 2950 |
| vb01 | valmap + b01 | 0.5662 @27,344 | 2027 / 2148 / 2568 / 2450 / 2982 |
| **vb01v** | valmap + b01 + v01 (312 compares `holder_key` first, the original memcmp order) | **0.5677 @27,344** | 2029 / 2150 / 2570 / 2452 / **2984** |
| vb2 | vb01v with the payload built in place (`match args.0{..=>Some(Some(target)),..=>Some(None)}`) | = vb01v (same bytes) | |
| vbq | vb01v + quote_locked through `&a.bonding_curve.quote_mint` (drops the 32 B `q` copy) | 0.55479 @27,288 | 1983 / 2097 / 2595 / 2403 / 2972 |
| vbt | vb01v + Ok round trip of `target` only | 0.55567 @27,376 | 1991 / 2112 / 2525 / 2450 / 2978 |

The two pieces work together on structure: each alone is rfj 2940 / 2950, together 2984, one below main's 2985. vb01v
reproduces three original-only shapes at once: the holder_key copy, the 312 compare order and the sharing-CPI val copy.
It is still 0.106 below main, for two reasons:
- **Frame** (`slotdelta.py vb01v`): 176 matched accesses over 59 slots (orig `-0xc28..-0x6d8`, the spill area) sit 16 B too
  deep. vb01v has 10,440 B of allocas against main's 10,424: b01's +32 B copy plus valmap's -16 B. The original evidently
  carries about 16 B less above its spill area. Fixing that whole delta is worth at most about +0.05 (to about 0.62).
- **Registers** (`chunkcmp.py 100`, frame masked): -129 vs main. Almost all of it is in orig 0x1800 (-24), the TCF clone
  run 0x2800-0x3800 (-21/-35) and 0x6000 (-22). The payload middle pieces now live as SSA values across the sweep and
  re-colour the TCF run.

So the valmap family needs one more 16 B frame change and a TCF-run RA change. No ordinary spelling found here gives either.

### 4.5 Where main makes shapes the original never makes (`tools/alien.py`, `data/alien-shapes-main.txt`)

416 of main's 3,334 4-grams occur neither in the original admin_cto nor in any matched window. They are mapped to
main's own source lines through the same line-table build. By line of `admin_cto.rs`:

| line | alien 4-grams | construct |
| ---: | ---: | --- |
| 339 | 96 | the execute head: PDA call before the stack-argument loads, CtoState literal, shared non-holder arm (`target=a.bonding_curve.creator`) |
| 749 | 59 | sharing CPI built from manual `AccountInfo{..}` literals (field-order permutations) |
| 661 | 41 | TCF CPI built from manual `AccountInfo{..}` literals |
| 307 | 24 | `with_pubkeys((t,Pubkey::default()))` with `to_string` inlined (class D) |
| 664 | 21 | sweep native/token arm (`token_frozen` before `token_raw_amount`) |
| 289 | 10 | holder test (`hopt==Some(true)` basin) |

The two CPI statements built from manual AccountInfo literals (lines 661 and 749) account for 100 of these shapes,
mostly at the literal fields. They earn main's ratio through RA, but they are the least faithful construct left after the
two placeholders. A later lane that
rewrites the clone runs as `to_account_info()` (s1, w15a34) should measure against this count as well as the ratio.

## 5. Next ideas

1. Start from vb01v (`e/vb01v.py`), not from valmap. It needs about 16 B less of allocas above the spill area (the
   original's sharing payload has no allocas of its own: val reads target's `[-0x550]/[-0x560]`) and a TCF-run RA change.
   Price each candidate with `slotdelta.py` and `chunkcmp.py 100` before building it.
2. Use `revidiom.py range` and `srcmap.py` before writing any "sibling idiom" trial. The corpus answers in seconds
   whether an instruction shape exists anywhere else and which source line made it.
3. Q1 needs the RA pressure of the original's sharing arm, so it can only come from a whole-region change (swept in r9),
   not from the clone-run source.
