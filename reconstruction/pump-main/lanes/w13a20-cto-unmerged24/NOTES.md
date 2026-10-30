# w13a20-cto-unmerged24: admin_cto frame (unmerged 24 B lever, then sk stack-coloring order)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w13a07's next idea #1 / w13a01 recipe step 2: one extra unmerged 24 B execute slot with no lifetime markers.
Scratch, IR captures and builds: `~/.cache/pumpfun-reconstruction/lanes/w13a20-cto-unmerged24/` (not in git).
Ledger keys: `0x22a10-w13-2f268ad-unmerged24-*`, `0x22a10-w13-1043a51-unmerged24-*`.

## Result

| main | before | after | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| 2f268ad (build bdd08bcf) | 0.51857 / 3,327 | **0.53745** / 3,327 | 27,400 | 1034 / 1034 | none |
| 1043a51 (build 4b0db198) | 0.53206 / 3,324 | **0.55183** / 3,324 | 27,400 | 1034 / 1034 | none |
| 6af878b (#2989 merged; build 4b0db198, same bytes) | 0.53895 / 3,223 | **0.55183** / 3,324 | 27,400 | 1034 / 1034 | none |

#2989 (w13a22-cto-valslot) attacks the same StackColoring tie from the other side (validate's `t` written into an
execute-owned `tb` scratch, 0.53895). With both forms the function shrinks 8 B (27,392 B, 0.49738), so the merge keeps
the 33 B `sk` and drops `tb`: same bytes as on 1043a51, +0.01288 over 6af878b.

Runtime differential: 363 cases, 0 mismatches.

Source change (one line, line count unchanged):

```rust
let sk=(a.sharing_config.key(),core::mem::MaybeUninit::<u8>::uninit());
let mut target=validate(&st,hopt,fee,new,&holder_key,&sk.0)?;
```

## Step 1: the unmerged 24 B lever is dead on current main

Raw-IR capture of main 2f268ad (w13a01 `capraw.py` + `rx.py`, tokens equal to the baseline build), then the
post-opt `iredit.py` llc oracle:

| edit | ratio |
| --- | ---: |
| main | 0.51857 |
| F1 `mv:event_signers.i:_188` (features.py auto-detect) | 0.51857 (byte-identical: the Codex `event_signers` form already delivers F1) |
| best single `nolt` of any of the 133 lifetime allocas | 0.51857 (no gain; 24 B buffers 0.43-0.49) |
| `sz:X:+8..+48` on any no-lifetime execute alloca (`_188`, `_173`, `inner_data`, `authority_info`, `old_creator`, `val6`, `target1`, `sharing_update.sroa.3`) | 0.475-0.490 |
| net-zero swap `sz:st:24` + `nolt:_10.i50` | 0.52427 |

Since #2917-#2933 (entry copy of `new`) and the Codex event-signer form, the frame's total size is already right:
any extra unmerged frame space shifts the matched deep objects (the 33 sret-demotion slots) and costs 0.03-0.04.

## Step 2: the frame greedy finds a stack-coloring order lever instead

Size-pinned greedy over 299 items (`nolt` of every lifetime alloca, moves of 13 execute allocas to 13 anchors):

| round | edit | ratio |
| ---: | --- | ---: |
| 1 | `mv:sk:val.sroa.6.i` | 0.53745 (+0.01888) |
| 2 | `mv:sharing_update.sroa.3:_180` | 0.53925 |
| 3 | `mv:holder_key:_180` | 0.54494 |
| 4 | `mv:target1:END` | 0.54524 |

Mechanism of round 1 (`tools/frame2.py`, debug llc `-debug-only=prologepilog,stack-coloring`):
StackColoring sorts slots by size (descending), ties by frame index, then merges greedily. `sk` (the 32 B copy of
the sharing-config key) and validate's `t.i` (32 B) are both live across validate. With `t.i` first, `t.i` and
validate's error `to_string` buffers (`buf.i.i`, `buf.i18.i`, `buf.i25.i`, `buf.i53.i`, `buf.i281`) join the
48 B `_77.i91` group at 0x38 and `sk` goes to `_92.i` at 0x4b8. With `sk` first, the two swap: the buffers land at
0x4b8, exactly where the original builds its error-name Strings (orig 0x670-0x6a8:
`stdw [r10-0x4b8],0; [-0x4b0],1; [-0x4a8],0; add64 r1,-0x4b8`).

Every IR form that puts `sk` ahead of `t.i` in that order gives the same 0.53745: `mv:sk` to any frame index
before `t.i`, `mv:t.i` to any index after `sk`, or `sz:sk:33/40/48` (a larger `sk` sorts first).
An execute-level local can never precede an LLVM-inlined callee's alloca in frame-index order (inlined allocas are
prepended), so the source has to make `sk` larger than 32 B without adding code.

Source forms (raw-IR capture per trial, `tools/capvar.sh` from w13a01; scores equal build tokens):

| trial | form | bytes | ratio |
| --- | --- | ---: | ---: |
| s1 | `(key,0u8)`, `&sk.0` | 27,408 | 0.53737 (one extra `stb`) |
| **v1** | `(key,MaybeUninit::<u8>::uninit())`, `&sk.0` | **27,400** | **0.53745** |
| v2 / v4 | `(key,shared)` (with / without reading `sk.1` in the tree) | 27,192 | 0.5197 |
| v3 | `(key,holder)`, tree reads `sk.1` | 27,280 | 0.51464 |
| s6 | `Some(key)` and `Some(t)==*sharing` | 27,432 | 0.5018 |
| s7 | `(key,)` (32 B) | 27,400 | identical to main |
| s3 | `#[inline] fn validate` | 27,400 | identical to main |
| s2 | no `sk`: pass `a.sharing_config.key` | 27,288 | 0.35485 |
| s5 | validate takes `&AccountInfo`, `t==sharing.key()` | 27,328 | 0.34978 |

## Tools (this directory)

- `tools/frame2.py <module.ll> <iredit spec> <tag> [lo hi]`: applies an `iredit.py` spec (w12a02's, put it next to
  this file), runs the debug llc (`~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc`) and prints the named
  frame map: each StackColoring group's offset, leader and members. Diff two runs to see which objects swap groups.
- `tools/fdelta.py <m.o> [--pairs]`: aligns orig and candidate with registers, frame and jump offsets masked and
  prints the `orig_off - cand_off` histogram per 0x800 region (and per orig offset with `--pairs`).

- `tools/addslot.py <in.ll> <out.ll> NAME:SIZE:BEFORE`: inserts an extra alloca before a named one, kept alive by one
  volatile byte store (+8 B of code). Use it to emulate a source local that LLVM keeps unmerged.

## After the landing (#2998 -> main bf9a05d, 0.55872)

Raw IR of bf9a05d (`rx.py` eq_main), then the post-opt llc oracle:

| edit | ratio |
| --- | ---: |
| main bf9a05d | 0.55872 |
| size-pinned greedy (385 items: `nolt` and `sz:X:N+1` size ties on every lifetime alloca, execute moves) | 0.55902 (`sz:target.sroa.8:10` only) |
| any -8 B before holder_key (`sz:st:40`, `sz:val6:32`, `sz:holder_key:24`, `sz:old_creator:24`) | 0.5635-0.5665 |
| the original's layout: `target.i.sroa.0/9` unmerged after val6 (F7 0x658, G9 0x668), `st` as a 24 B X24 at 0x680, `_115.i` re-seated | 0.56591 |

The frame from 0x4c0 to val6 at 0x651 already equals the original. The residual sits between val6 and holder_key.
There, our CtoState `st` (48 B at 0x688) stands where the original keeps F7/G9/X24 (40 B). Matching the original's
layout exactly is worth no more than shrinking that region by 8 B in any way.

Source trials (capvar, raw-IR capture):

| trial | form | bytes | ratio |
| --- | --- | ---: | ---: |
| c1 | default check reads `a.bonding_curve.creator` | 27,408 | 0.5149 |
| c3 | c1 + shared arm `target=a.bonding_curve.creator` (st alloca gone) | 27,384 | 0.52292 |
| c3 + IR pad | + a 24/40/48 B unmerged slot before holder_key (`addslot.py`) | 27,392 | 0.53813 / 0.53513 / 0.49618 |
| m1-m3 | `max_fee` passed to validate instead of a CtoState field (st 38 B, align 1) | 27,296 | 0.52919 |
| m4 | m1 + `#[repr(align(8))]` CtoState (st 40 B) | 27,296 | 0.56971 |
| k1 | m1 on the w13a24 PR #3011 head (0.56291) | 27,296 | 0.56581 |

m4/k1 raise the skeleton ratio from 0.8532 to 0.8642 because register allocation in the sweep CPI clone region
(0x3800) gets closer to the original's. They are not faithful, though: the original stores `max_fee` into its
CtoState at `[r10-0x18]` (orig 0x22ee0, as ours does), and the 104 missing bytes are not repaid.

w13a24-cto-ctostatesroa (PR #3011) solves the top of the frame more faithfully: CtoState goes in the `_77.i` group at
-0x38 and the PDA result is kept alive. It reverts this lane's 33 B `sk`, because with `st` in `_77.i` a plain
`sk` lands at the original's 0x470. A size-pinned frame greedy over 393 items on the #3011 head finds only
`sz:target.sroa.8:10` (+0.0003, an SROA piece). **Frame-only levers are exhausted.** What remains is register
allocation (the original has 109 spill slots against our 108) and code shape.

## Next ideas

- Rounds 2-4 above (`holder_key` earlier in frame-index order: +0.0057 after the `sharing_update` move) were
  re-checked on top of v1: `mv:sharing_update.sroa.3:ix` +0.0018, `mv:holder_key:ix` +0.0057, `mv:target1:END`
  +0.0003 (0.54524 from 0.53745 on 2f268ad). #2974 (e32late) already moves `target1`/P2; re-run the greedy on 1043a51.
- The same size-tie trick (a 1-byte `MaybeUninit` tail) can reorder any other execute-level local against
  inlined allocas of the same size. On bf9a05d and on #3011 no other tie pays (`sz:X:N+1` scan).
- The regalloc residual: k1's skeleton gain shows that one fewer live u64 across validate reshapes the 0x3800
  sweep-clone region toward the original. Look for the original's extra spill slot, not for a frame object.
