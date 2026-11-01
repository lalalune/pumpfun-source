# admin_cto::execute (0x22a10): region diff from Ghidra, original vs main 599891304

Inputs: the original `evidence/original/pump/deployed.so` and main's `unstripped.so` (599891304, 0.67436, M 2,251).
Both are decompiled by Ghidra 12.2 with the SBF fix-ups in `ghidra_scripts/SbfDecomp.java`. The files are:

- `orig_admin_cto.c` and `ours_admin_cto.c`: plain pseudo-C.
- `ghidra_out/*_admin_cto.addr.c`: the same C, each line tagged with its window-offset range.
- `regions/<id>.{orig,ours}.c`: the region excerpts.
- `REGIONS_TABLE.md`: the generated per-region numbers and salient lines. `regions.json` and `frame_map.json` hold the
  machine-readable form.

In the excerpts, Ghidra names a stack variable after its r10 offset: `uStack_4b8` is `[r10-0x4b8]`. Error sites are
named by their PumpError discriminant through the pooled constant `k_u32_<n>`, which is passed by reference to
`PumpError::name` and `Display::fmt`/`to_string`.

| discriminant | variant | source line |
|---:|---|---|
| 88 | CtoNotAllowedForMayhemCoin | 284 |
| 83 | HolderRewardCreatorImmutable | 289 |
| 84 | HolderRewardDisabled | 296 |
| 90 | CtoNewCreatorNotAllowed | 298 |
| 89 | CtoNewCreatorRequired | 306 |
| 30 | CreatorShouldNotBeZero | 307 (+ with_pubkeys) |
| 19 | InvalidCreator | 312 |
| 91 | CreatorFeeNotConfigurableForQuote | 326 |
| 80 | CreatorFeeNotAllowedForCashbackCoin | 330 |
| 77 | CreatorFeeNotConfigurable | 334 |
| 78 | CreatorFeeBpsOutOfRange | 338 |
| 95 | CreatorFeesNotSwept | 410 |
| 92 | CtoCreatorAccountNotWritable | wallet |
| 93 | CtoSharedVaultFrozen | 660 / 719 |
| 2006 | anchor ConstraintSeeds | 648 |

## Region table

Columns are orig/ours. Tokens are the w16 ceilings `decomp.py --lcs` per-chunk counts on main 599891304, attributed to
regions by byte overlap. "exact gap" is orig tokens minus exact LCS. "masked gap" is orig tokens minus the
frame+reg+jump-masked LCS, which is the structural part. "regs live at joins" is the summed live-in register count at
blocks with two or more predecessors (backward liveness over the Ghidra CFG).

| id | region | orig range | insns | blocks | calls | frame ld/st | regs live at joins | tokens | exact gap | masked gap |
|---|---|---|---|---|---|---|---|---:|---:|---:|
| E1 | entry: holder PDA + shared test | 0x0-0x280 | 77/59 | 3/3 | 4/4, **order differs** | 6+24 / 4+18 | 0/2 | 78 | 37 | 24 |
| E2 | entry: quote_locked | 0x280-0x420 | 51/85 | 4/6 | 3/3 | 0+12 / 1+21 | 3/3 | 50 | 24 | 15 |
| E3 | entry: CtoState, `new`/key copies, mayhem | 0x420-0x708 | 90/24 | 4/3 | 2/2 | 12+36 / 0+9 | 5/0 | 89 | 60 | 30 |
| V1 | validate: holder arm head, 289/298 | 0x708-0xb00 | 119/114 | 14/9 | 6/6, **order differs** | 24+45 / 25+46 | 4/3 | 120 | 51 | 21 |
| V2 | validate: non-holder arm memcmps + shared split | 0xb00-0xe60 | 105/156 | 13/14 | 5/10, **order differs** | 14+29 / 15+52 | 3/0 | 104 | 59 | 23 |
| V3 | validate: 306/296/326 errors + holder exit | 0xe60-0x1258 | 121/134 | 8/8 | 5/5, **order differs** | 27+51 / 25+52 | 3/0 | 121 | 58 | 39 |
| V4 | validate: 312/307 errors (outlined to_string) | 0x1258-0x1490 | 65/46 | 2/1 | 7/2, **order differs** | 10+20 / 10+20 | 0/0 | 66 | 23 | 20 |
| V5 | validate: fee checks 330/334/338 | 0x1490-0x1800 | 101/76 | 8/6 | 9/9 | 19+26 / 10+18 | 12/0 | 102 | 33 | 17 |
| J1 | join: arms → (collect_old, skip, sharing_update, target) | 0x1800-0x1990 | 50/84 | 10/12 | 1/1 | 7+17 / 10+28 | 11/21 | 49 | 22 | 9 |
| J2 | join: prepare_bonding_curve + 410 | 0x1990-0x1c88 | 91/86 | 8/9 | 4/4 | 22+35 / 19+32 | 4/5 | 92 | 36 | 14 |
| W1 | wallet head: executable/owner, shared msg! | 0x1c88-0x1f68 | 86/80 | 8/7 | 5/5 | 10+18 / 9+16 | 2/6 | 87 | 13 | 4 |
| S1 | sweep head + gate (native, vault PDA, seeds, AMM present/frozen, 660) | 0x1f68-0x26e8 | 228/237 | 31/34 | 18/18, **order differs** | 35+56 / 32+58 | 7/28 | 228 | 39 | 11 |
| T1 | TCF CPI: inline AccountInfo literals + call, Rent::get | 0x26e8-0x3c50 | 685/662 | 105/95 | 3/3 | 136+215 / 135+215 | 205/197 | 684 | 207 | 24 |
| C1 | sharing-config CPI clone run | 0x3c50-0x4aa8 | 458/465 | 69/74 | 1/1 | 87+143 / 79+143 | 147/151 | 457 | 226 | 57 |
| P1 | pool CPI: owner/empty gate, msg, clones, admin_cto_pool | 0x4aa8-0x4e50 | 115/120 | 7/7 | 13/13, **order differs** | 16+12 / 14+12 | 7/2 | 116 | 24 | 7 |
| EV | event: Clock::get, AdminCtoEvent emit + self-CPI | 0x4e50-0x5558 | 220/224 | 13/13 | 12/12 | 36+52 / 37+52 | 17/18 | 216 | 29 | 7 |
| TL | tails: errors 92/88, unwrap_failed, From | 0x5558-0x5a18 | 141/140 | 13/13 | 9/9 | 21+45 / 21+47 | 11/11 | 144 | 27 | 3 |
| S2 | sweep native arm | 0x5a18-0x5c18 | 63/65 | 9/11 | 4/4 | 11+9 / 11+9 | 11/12 | 63 | 13 | 2 |
| W2 | wallet body + sweep token arm + CollectCreatorFeeEvent + AMM collect | 0x5c18-0x6b08 | 473/480 | 49/48 | 46/46 | 71+64 / 70+68 | 18/25 | 450 | 98 | 12 |

Totals by group:

| group | exact gap | masked (structural) gap |
|---|---:|---:|
| entry + validate (E1–V5) | 345 | 189 |
| C1 sharing CPI clone run | 226 | 57 |
| T1 TCF | 207 | 24 |
| W2 wallet body | 98 | 12 |
| J1/J2/W1/S1 | 110 | 38 |

The tail groups (EV, TL, S2, P1) are within about 30 tokens each and are almost purely naming.

Main's instruction alignment against the original (difflib on reg/frame/jump-masked tokens) is 0.7975 (2,662
aligned). Ours regions come from block matching, so the ours columns are approximate where blocks moved. For example,
some of ours' validate error blocks match into E2/V2, which is why V2 shows 10 calls in ours.

## Whole-function facts from the decompile

- **Decode.** All 3,339 original and 3,337 ours instructions decode in Ghidra exactly as `win.py` decodes them
  (`decode_check.json`, 0 mismatches each).
- **Shape.** Both have one `exit`, 2 noreturn call sites (`abort` at orig +0x26e0, `core::result::unwrap_failed` at
  +0x5788) and 157 calls with the same callee multiset, apart from two calls: the original calls
  `<T as ToString>::to_string` at 312 and 307, where ours calls `<PumpError as Display>::fmt`. The Ghidra graph has 378
  blocks in the original and 373 in ours.
- **Frame.** Both frames reach r10-0x1000: the bottom slots are the outgoing stack-argument area that callees read
  through r5.
  - The original has 414 distinct r10 slots and ours 413. 19 offsets appear only in the original and 18 only in ours.
  - Argument spills: the original stores r2→-0x938, r4→-0x928, r3→-0x918, r1→-0x8f0. Ours stores r2→-0x938,
    r4→-0x910, r1→-0x8f0, r3→-0x8e8. So r3 and r4 sit 0x30 and 0x18 higher in ours.
- **Odd offsets show packed SROA pieces.** The original's odd offsets (-0x655, -0x651, -0x64d, -0x649, -0x641,
  -0x639, -0x4b5, -0x4b1, -0x4a9, -0x4a1, -0x54d, -0x535) are the 1/4/3/8-byte pieces of `Option<Pubkey>` values
  (`new`, `sharing_update`) stored unmerged.
  - Ours has the PDA tuple at -0x679 (odd) and the 7+1 split pieces at -0x699..-0x661.
  - The two programs place their `Option<Pubkey>`-shaped temporaries in different slots.
- **Error-site layout order (validate) is the biggest single block-order difference.** By address:
  - original: 289(83) 306(89) 298(90) 326(91) 296(84) | 312(19) 307(30) | 330(80) 338(78) 334(77);
  - ours: 298(90) 296(84) 289(83) 326(91) 312(19) 306(89) 307(30) | 330(80) 338(78) 334(77).

  From 410 onwards both orders agree: 410(95), 660(93), seeds(2006), 719(93), and the tails 92 and 88. Both place the
  284 mayhem error (88) and the wallet's 92 in the tail region TL, so 284 is not an early block in either.
- **Outlined to_string.** Only 312(19) and 307(30) differ. In the original, both error blocks call
  `<T as ToString>::to_string(&String, &k_u32_n)` and take the shared Err path. Ours expands
  `Display::fmt` + `unwrap_failed` inline. The other to_string sites (330, 338, 334, 93×2) are outlined in both.

## Per-region findings (original shape → ours)

### E1 entry: holder PDA first (orig 0x0-0x280)

Original pseudo-C (`regions/E1.orig.c`):

```c
mint copy -> [r10-0x6c0..-0x6a8];  seeds = {"holder-rewards",14},{&mint,32} at [r10-0x450]
solana_pubkey::Pubkey::find_program_address(&[r10-0x2d0], &seeds, 2, PUMP_PROGRAM_ID);   // FIRST call, +0xf8
holder_key = [r10-0x2d0..] -> [r10-0x6a0..-0x688]
sk = sharing_config.key -> [r10-0x2d0..]  (reuses the PDA out slot)
if (memcmp(curve+8 /*creator*/, &sk, 32) == 0 && memcmp(sharing_config.owner, PUMP_FEES_PROGRAM_ID, 32) == 0)
    shared = !AccountInfo::data_is_empty(sharing_config);
```

Ours (`regions/E1.ours.c`):

- does the `shared` test first: the `sk` copy, then memcmp creator, then memcmp FEES, then `data_is_empty`;
- then builds the seeds and calls `find_program_address(&[r10-0x679], ...)`: the out-param is the odd-aligned
  `(Pubkey,u8)` tuple, not the aligned scratch slot;
- then copies `holder_key` out in 7+1-byte pieces.

Source today has `let shared=...` before `let hk=find_program_address(...)`. The original evaluates the PDA first and
writes it into the same 32-byte scratch slot (-0x2d0) that `sk` and later the quote-mint zero key reuse.
w14a93-cto-pdaheadra tried "PDA before shared" composites with the raw-IR oracle and rejected them. None of those
trials controlled where the `(Pubkey,u8)` sret lands; this decompile shows the slot is the difference. See shim
lane 1.

### E2/E3 entry: CtoState packing and the `new` pieces (orig 0x280-0x708)

The original's loads, in order:

1. `curve+0xa3`, `+0xa5`, `+0xa2` (three flag bytes) before the quote mint copy (`+0x28..+0x40`);
2. quote_locked as a three-level `if`;
3. `global+0x430` (max_fee), `+0x43e` and `+0x43f`;
4. the creator copy (`curve+0x10..+0x20`);
5. all flags packed into one 8-byte word at [r10-0x10]:
   `uStack_10 = CONCAT(…, cVar4(+0x43e), +0x43f, quote_locked, cVar1, cVar2, cVar3)`;
6. at +0x4d8..+0x538, every SROA piece of the `new` stack argument (through `param_5 - 0xff8`):
   `bVar39 = new[0]` (tag), `u32 new[1..5]`, `u24 new[5..8]`, `u64 new[8..16]`, `u64 new[16..24]`,
   `u64 new[24..32]`, `u8 new[32]`;
7. the sharing key copy to -0x470 and holder_key to -0x518;
8. only then the mayhem test `if (cVar3 != 0)` and `param_3 & 1` (`hopt == Some(true)`).

These pieces stay live (spilled to -0x668/-0x660/-0x658/-0x654) and are consumed much later:

- C1 rebuilds the CPI's `Option<Pubkey>` from `bVar39`, `uVar62` and `uVar121`;
- J1 builds the target from the same pieces.

Ours loads `new` lazily inside the arms.

Ours' E2/E3 instruction counts (85 and 24) are blurred, because ours merges the entry blocks differently. Both
programs keep CtoState at the top of the frame: creator at -0x38..-0x20, max_fee at -0x18, the flag bytes at
-0x10..-0xb. The real difference is the order of the flag-byte stores:

- original: `stxb` -0xe, -0xf, -0x10 at +0x448..+0x460 (curve flags, right after quote_locked), then -0xd, -0xb, -0xc
  at +0x4b8..+0x4c8;
- ours: -0xd at +0x468, then -0xb, -0xc, -0xe, -0xf, -0x10 at +0x4c8..+0x4e8.

This is the CtoState-literal store order that w15a01 and w16a17-stitch16 work on. See shim lane 2 for the `new`
pieces.

### V1–V5 validate: block order and the 312/307 outline (orig 0x708-0x1800)

The original lays the validate error blocks in the order 289, 306, 298, 326, 296, then 312/307 as a pair (V4, two
blocks with outlined to_string plus the shared `From<AnchorError>`/`with_pubkeys` tail), then 330, 338, 334.

Ours places 298 and 296 first and 289 third, and interleaves 312 and 306 between 326 and 307. V4 in ours is a single
block with 2 calls (From + with_pubkeys) because 312/307 are inlined into V2/V3.

- The original's holder test is `param_3 & 1` (and-1).
- V5 has the same 9 calls in the same order. The original has 2 join blocks (12 live registers) and more frame traffic
  (19 loads and 26 stores against 10 and 18). Its 330/338/334 error payload builders (`name` + `to_string` + `From`)
  are laid out as separate join targets. Ours chains them without joins.

See shim lanes 3 and 4.

### J1 join (orig 0x1800-0x1990)

The original computes `(collect_old, skip, sharing_update, target)` with 4 small joins and 11 registers live in total,
then stores them.

Ours uses 12 blocks with 21 registers live at the joins and 28 frame stores against 17. Ours carries more values
through the join in registers and also stores more. The original's sharing_update tag is the `new` tag byte
(`bVar39`), not a separate local: `if (bVar39 != 2)` in C1 against `if (cVar1 != '\x02')` in ours.

### S1 sweep gate (orig 0x1f68-0x26e8)

The call sequence is equal except at the 649/660 AMM guard. The original lays out `token_raw_amount` (+0x20c8) before
`token_frozen` (+0x2110). Ours lays out `token_frozen` (+0x2098) first. The block holding the `(true,true)` arm's raw
amount is placed before the frozen test block.

Liveness: the original keeps only r8 (accounts) live across the gate joins, 7 registers in total. Ours keeps r6, r8
and r9, 28 in total, consistent with the known "1657=r9" and sticky-RA leads. S1's masked gap is only 11 tokens, so
this region is register naming on a matching skeleton.

### T1 TCF CPI (orig 0x26e8-0x3c50) and C1 sharing-config CPI (orig 0x3c50-0x4aa8)

Both are long call-free runs of inlined `AccountInfo{..}` literals. The frame already matches in T1: 228 of its 230
r10 slots are the same offsets in both programs (only -0x908 and -0xc38 are original-only). So T1's exact gap is
register naming and scheduling, not frame. Each `lamports.clone()`/`data.clone()` is an
`Rc` strong increment with `if (++n == 0) goto abort`. T1 has the same block count within 10 and the same calls; its
exact gap of 207 is almost all register and frame naming (masked gap 24).

C1 has the largest structural residual outside validate (masked gap 57). The original:

- stores the seed pointers with partial-width stores into slots that other code also uses as byte pieces:
  `uStack_4b8._0_4_ = "pool-authority"; _4_1_ = 0; _5_2_ = 0; _7_1_ = 0` and `uStack_4a8 = SUB87(&mint,0)`. This is
  stack coloring shared with the `new` pieces;
- builds the `Option<Pubkey>` CPI argument from the entry-loaded SROA pieces
  (`bStack_651 = bVar39; uStack_649 = uVar62; uStack_641 = uVar121`, plus -0x650/-0x64c/-0x639/-0x631 copies).

Ours copies a 32-byte stack value (`[r10-0x560..-0x548]`) and tests a separate tag `cVar1`.

C1's slot sets differ in exactly that object. The original keeps the 33-byte `Option<Pubkey>` CPI argument at
[-0x651, -0x630): tag at -0x651, payload 8-aligned at -0x650, stored as u32/u64 pieces at -0x650, -0x64c, -0x649,
-0x641, -0x639 and -0x631. It also uses -0x54d. Ours keeps the same object 8 bytes higher (tag at -0x649, aligned u64
stores at -0x648, -0x640 and -0x638) and uses -0x548. The other 147 C1 slots are common.

### P1 pool CPI (orig 0x4aa8-0x4e50)

The original tests `memcmp(pool.owner, PUMP_AMM_PROGRAM_ID) == 0 && !pool.data_is_empty()`. Ours tests
`!data_is_empty && owner == AMM`, matching the source line `let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM`.

The owner-first spelling ("mpo") was tried and rejected in w15a04/w15a33, because it moved the pool pointer. The
decompile shows the original also re-reads `accounts[0xe]` (`lVar50 = plVar115[0xe]`) for the memcmp, then passes the
same register to `data_is_empty`.

### EV, TL, S2, W2

- EV, TL and S2 have the same calls in the same order, with masked gaps of 7, 3 and 2: naming only.
- W2 has the same 46 calls in the same order; its masked gap is 12. Ours has more registers live at the joins (25 vs
  18) and 4 more frame stores. The original keeps r8 live where ours uses r9 (`0x5c50 [6,8]` against `[6,9]`).
