# Lane w4-frame-oracle (wave 4): stack-frame oracle for 0x5b3b0, 0x22a10, 0x72810

Base: origin/main 630a074 (1023 normalized / 277 raw). Enabling lane: a tool that predicts
and explains the r10 frame layout from rustc's IR, and names the allocas the original places
differently.

## Tool: `frameoracle.py`

```
python3 frameoracle.py --ir pump_recovered.ll --sym '_ZN14pump_recovered5sweep7execute17h[0-9a-f]+E' \
    --win 0x72810 --name sweep-base [--edit edit.py] [--so unstripped.so]
```

Capture the IR with `--emit=link,llvm-ir` (any of the prior capture scripts; the
module keeps its value names). The tool runs the SDK llc exactly like fastbuild
(`-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext`) twice, about 12 s in all:

1. Normal run: dumps the frame before stack-coloring, after stack-coloring and after
   prologepilog. From these it reads every alloca's IR name, whether it has LIFETIME_START,
   which slot StackColoring merged it into, and the final `[SP-T]` of every surviving slot.
   `--so` checks that llc reproduces the fastbuild bytes (true on all three targets).
2. `-no-stack-coloring` run: every alloca keeps its own slot. Code is unchanged apart from
   offsets, and offsets are masked in the alignment. So aligning this run against the
   ORIGINAL window gives each alloca its own implied original slot. Allocas that share an
   implied T are the original's StackColoring groups, written in our names.

The output has four sections:
- the frame table in layout order: T ours, T implied for the original, delta, size,
  lifetime flag and merged members;
- delta breaks: where the delta changes between consecutive slots. This is exactly the
  number of bytes the original has more (or fewer) between those two slots;
- ORIGINAL StackColoring groups, with `!` on allocas that we put in a different group;
- ALLOCA ORDER: original slot representatives, in original order, that fall outside the
  longest increasing subsequence of our frame indices. These allocas need a different
  position, which means a different MIR local order or inlining.

IR what-ifs that need no edit script: `--move-alloca A:B` moves alloca `%A` to just before
`%B` (the frame-index order, which is the MIR-local order in source terms).
`--drop-lifetime A` deletes A's lifetime markers, so A is never merged. `--mir out.mir
--mir-fn '^fn sweep::execute\('` (and a second `--mir-fn` for a closure that is inlined once)
labels every `_N` alloca with its MIR type and debug name, so `_72` prints as
`_72{Result<Rent,..>}`.

`--edit` applies an IR edit (`edit(fn_text)`) first, so the tool doubles as an IR oracle
that also reports the frame. `--what-if 'ins:FI:SIZE,del:FI,size:FI:SIZE'` re-lays-out the
frame without llc.

## Rules (verified on all three targets; `PEI rule check: ok`)

1. **PEI is sequential.** Surviving slots are placed in frame-index order:
   `T = alignup(T_prev + size, align)`. SBF has no reordering. An object of size 1 at SP-1
   prints with no location (`SPOffset == -1`), and the first 8-aligned object follows it at
   T=8+size.
2. **Frame-index order is alloca order.** Allocas of inlined callees come first, ahead of
   the function's own allocas (the inliner hoists them to the top of the entry block).
   The function's own allocas follow in reverse MIR-local order (`_554` before `_503`), then
   ISel 16-byte temporaries, then 8-byte spills.
3. **A merged group sits at its representative's position.** StackColoring sorts slots by
   size (largest first, stable on frame index). Each slot then absorbs every later slot
   whose live range is disjoint from the whole group. The group's position is that of its
   largest, lowest-index member. An alloca with no LIFETIME_START is never merged (the `*`
   marker). An alloca whose live range overlaps every larger slot stays a separate slot at
   its own index.
4. **The unnamed 16-byte objects are call-return slots.** After the allocas come
   SelectionDAG's hidden return slots, one per call site that returns a 16-byte value
   (`{i64, ptr}`: `Result<()>`, `Result<u64>`, ...). ISel creates them while visiting IR
   blocks in reverse postorder, and they are never merged. So their order is the RPO of
   those calls, and it depends on branch successor order. The tool labels them
   `ret:<callee>`. The 8-byte objects after them are register-allocator spills.
5. **A delta break of +N between slots A and B** means the original has N more bytes at
   frame indices between A and B. That is either an alloca we merged away, one we lack, or
   one the original has at that index instead of ours.

## Findings per target (base 630a074)

### 0x5b3b0 swap_hop (reports/fo-swaphop-base.txt)
- **`completion` (CompleteEvent, 136 B) is a separate slot in the original** at orig
  T=0x498, and `_443` and `_27` merge into it. Ours merges it into the 232-byte `_503`
  slot (the post_complete_buy_event result). This is the +136 break between
  `authority_info46` (fi47) and `_433` (fi55). The original's completion therefore has
  lifetime markers but a live range that overlaps the 232/224-byte slots. That fits the
  nested form, where completion is still in scope across the post call. IR proof
  (reports/nolt_completion.py: drop completion's lifetime markers, so it is never merged):
  the +136 break vanishes, aligned r10 offsets equal 142 -> 172 of 723, and group
  mismatches drop from 12 to 10.
- Remaining top-of-frame mismatches: the original has two 32-byte slots after post_event
  (orig 0x360 and 0x380: `_493`+`ix_data` sit at 0x380). Ours folds them into `_547` (fi19)
  at the top. `user` (#86) belongs to the event group (0x6d0) in the original. Ours puts
  it in the `_503` group.
- The bottom of the frame (16-byte ISel temporaries and 8-byte spills) is offset +184 and
  follows from the deltas above.

### 0x22a10 admin_cto::execute (reports/fo-admincto-base.txt)
- `_109.i` (16 B, the wallet emit_cpi signer slice) implies orig T=0x680, between
  `old_creator` (fi122) and `holder_key` (fi145). This is the "24 B outer object at
  r10-0x680" from w3-adminCTO's next ideas: the original merges the slice into a slot whose
  representative sits between those two allocas, not among the inlined-callee allocas at
  the top.
- The original keeps `_160` (336 B) between `_121.i` and `_112.i` (orig 0x450 group),
  `dest.i` (32 B) between `inner_data.i` and `val.sroa.6.i`, and `target.sroa.8` (9 B)
  merged with `_116.i` at 0x548 (ours has it in a different group).
- The `buf.i18.i` and `buf.i39.i` 24-byte formatter buffers are swapped between the two 24 B
  groups at 0x488 and 0x4b8.

### 0x72810 sweep::execute (reports/fo-sweep-base.txt)
- The tool rediscovers w3-sweep's a37 result automatically: `quote_token_program.i` and
  `quote_mint.i` (inlined token-admit allocas, fi8/fi9 at the top) belong between
  `authority_info` (fi24) and `_37` in the original (orig 0x180/0x1a0). So the token code
  is not an inlined callee in the original.
- `_7.sroa.5.i` (24 B, no lifetime marker in ours) is in the original's 80-byte `ix` group,
  and `_6.i` is in the `_138` group (0x68), not in `ix`.

### IR alloca-move oracle (admin_cto, reports/fo-adm-mv3.txt)
`--move-alloca _109.i:holder_key --move-alloca sharing_update2.sroa.3:_213
--move-alloca target1:sharing_update2.sroa.3 --move-alloca target.sroa.0:target.i.sroa.0`
makes the whole frame from T=0 to val6 (0x651) equal to the original's. Equal r10
offsets go from 528 to 641 of 877. The original then has one more 24 B slot between val6
and a 16 B slot at T=0x680 (the slot that holds `_109.i`), and holder_key and mint follow at
+0. The votes for `_109.i` are 3/5, so treat its exact identity as tentative.

### admin_cto: what the original has between val6 and holder_key (read from the original code)
- 7 B slot at T 0x658, align 1: bytes [1,8) of the `new: Option<Pubkey>` argument, copied at
  entry by two overlapping `ldxw` (0x22f00/0x22f10).
- 9 B slot at T 0x668, align 8: bytes [0x18,0x21) of `new` (u64 + u8).
- 24 B slot at T 0x680: a copy of the 24 B `val.sroa.6.i` piece (the collect closure's
  quote_mint tail, 0x243b8-0x243d8, copied again to 0x578). This is the slot that the
  wallet signer array `_109.i` merges into. A 24 B slot sorts before a 16 B one, so the
  merge happens by itself once this slot exists.

Ours has two 32 B allocas with no lifetime markers there instead (`sharing_update2.sroa.3`,
and `target1`, which is the block-internal mutable `target`, MIR _53). It also has
`target.sroa.8` promoted and no 24 B slot. Dropping `let mut target=target;` (a1) is
byte-identical.

### buy_handler (0x13b9b8): the frame is exact except two swapped call-return slots
The two slots belong to the `ok_or_else(||error!(Overflow))` closure calls at
buy_v2.rs:498 and :500 inside `require_gte!`. Ours visits the error successor of each
`uadd.with.overflow` branch first, so in RPO the 500 slot comes before the 498 slot. The
original's order is consistent with success-first. Inverting the IR branches with `xor`
makes things worse (0.977 -> 0.93), so the fix has to come from rustc's successor order
in source.

### Frame census, all 12 unmatched windows on 630a074 (aligned r10 pairs equal)
0x147ba0 226/226, 0x14a8a8 333/333, 0x80df8 108/108, 0x83c00 181/181, 0x13f630 1060/1062,
0x13b9b8 797/806, 0x144508 730/737, 0x1e7c0 742/908, 0x1489f8 287/377, 0x22a10 528/877,
0x5b3b0 142/723, 0x72810 17/352 (the w4-sweep head is at 340/354). Frames are already exact
for the near-matches, so their residuals are code order, not frame slots.

### Other lanes' heads (analysis only)
- w4-swaphop aa9acd6 (ratio 0.5698), reports/fo-x-swaphop.txt: the frame from the top
  through `event` (T 0..0x6d0) equals the original's (446/744 equal). The residual: two
  16 B SROA pieces with no lifetime markers (`val18.sroa.10.sroa.0.sroa.3`,
  `val18.sroa.10.sroa.3.sroa.2`) sit between event and post_fill.sroa.16. Moving them
  after `bump` in the IR (reports/fo-xs-mv1.txt) makes post_fill.sroa.16 and .20 exact. The
  original then still has 48 B more before quote_token_program.
- w4-sweep 60914be (ratio 0.822), reports/fo-x-sweep.txt: 340/354 equal. The only group
  mismatch is `_72{Result<Rent>}`. In the original its 24 B tail (offset 8) is merged into
  the 80 B ix slot, which means the original SROA-splits the Result<Rent> and promotes the
  tag. Ours keeps a whole 32 B alloca in the event group.

Ledger rows: see `log_attempt.py search --lane w4-frame-oracle`.
