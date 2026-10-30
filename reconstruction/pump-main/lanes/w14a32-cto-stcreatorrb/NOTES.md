# w14a32-cto-stcreatorrb: st.creator read-back and 312 fallthrough in the shared&&!holder arm (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: orig 0x0d78-0x0e58 (57 insns), the post-validate `shared&&!holder` arm, an open residual in w14a20 reloadarm and
w14a14 mf1fill. The original reads st.creator back from the CtoState stack copy (-0x38..-0x20, four aligned words), stores
words 1-3 twice (-0x4e8.. and -0x530..) with word 0 in a register (spill -0x918), and lays the line-312 success path out as
the fallthrough (`jeq r0,0 -> error at 0x1258`). Main forwards the first 7 B of st.creator from the curve (MemCpyOpt) and
makes the 312 error block the fallthrough (`jne r0,0,+0xe4` at 0xd00).
Ledger keys: `0x22a10-w14-b2e90aa-stcreatorrb-*-v1` (approaches `ir-bound`, `stcreatorrb-source`).

**Result: no gain. The read-back is not worth pursuing (IR bound -1 M once size-normalized), the 312 fallthrough weight
loses 35 M, and the only source form that blocks the forwarding (st built before the PDA call) relayouts the head.**

## New oracle: `tools/px.py` (post-opt IR + llc, 0.3 s, equals the build)

`tools/cappost.py <crate> <work> <out>` is an identity build that also writes the real post-opt module (`--emit=link,llvm-ir`
without `no-prepopulate-passes`). `px.py <name> [edits.py]` slims it to `execute`, applies exact `(old,new)` edits or
callables to the **optimized** IR, optionally runs `opt -passes=..` (`--opt`), then runs llc the way fastbuild does, and
prints ratio / slots / M / bytes / eq_main. On 5ee681d it prints `0.645, M 2153, eq_main true`. Use it for edits that must
survive the opt pipeline (MemCpyOpt / GVN / SimplifyCFG would undo them in `rx.py`), such as forwarding, branch weights
and operand swaps. `LLCARGS=` passes llc flags. Edits in `edits/ir/`.

Note: on ca03a2b the published baseline `unstripped.so` differed from a fresh `measure.sh` build by 44 tokens at equal ratio
(both 0.6432); on b2e90aa and 5ee681d they are equal.

## IR bounds (post-opt, px.py)

| edit | what | b2e90aa (M 2151) | 5ee681d (M 2153) |
| --- | --- | --- | --- |
| p1 | bb21 7 B memcpy of st.creator from `%st` instead of the forwarded curve ptr `%23` | M 2150 @ 27,344 (-56 B) | M 2152 @ 27,344 |
| w1 | `branch_weights 1:2000` on the last 312 br (error unlikely) | M 2116 @ 27,400 | M 2118 |
| w2 | weights on both 312 brs | M 2094 | M 2096 |
| q1 | 312 compares holder_key first, sk second (original operand order) | M 2144 | M 2146 |

- p1 is -1 M; its 0.64477 ratio comes only from being 56 B shorter. The 56 B come from a register-allocation shift in the head
  (orig chunks 0x400-0xa00 per 0x200 rm counts 31,25,28 -> 30,27,25), not from the arm itself.
- w1 does not even produce the original layout: MBP still makes the to_string error block the fallthrough after
  `jne r0,0`. Only the bb45.i/bb76 join chain moves (0x1428 -> 0x1108), and that costs 35 M.
  `-disable-tail-duplicate` changes nothing. The original's fallthrough comes from its per-arm (tail-duplicated) exits,
  the OV/feephi family, not from a branch weight.
- q1: main's sk already sits at -0x518, the original's first-operand slot, so the original operand order loses 7 M.

## Source forms (raw-IR capture + rx.py, on b2e90aa, main 0.6444 / M 2151)

| trial | spelling | bytes | ratio | M | forwarding |
| --- | --- | ---: | ---: | ---: | --- |
| s1 | arm `target={let c=&st.creator;*c}` | 27,400 | = main | 2151 | kept |
| s5 | arm `let c=st.creator;target=c` | 27,400 | = main | 2151 | kept |
| s6 | collect_old via `let cr=&st.creator;*cr!=Pubkey::default()` | 27,400 | = main | 2151 | kept |
| s3 | `#[derive(Clone,Copy)]` CtoState, validate by value | 27,400 | = main | 2151 | kept |
| s9 | `let mut st` only | 27,400 | = main | 2151 | kept |
| s4 | validate takes `&mut CtoState` | 27,400 | 0.6399 | 2136 | kept |
| s2 | `creator:Pubkey::default()` in the literal, `st.creator=..` after it | 27,408 | 0.48315 | 1613 | kept |
| s7 | quote_locked + CtoState literal before the holder_key PDA call | 27,424 | 0.41294 | 1379 | **blocked** (reads `%st`) |
| s8 | `let mut st`; arm `target=core::mem::take(&mut st.creator)` | 27,392 | 0.64419 | 2150 | kept (+dead memset) |
| s10 | `mem::replace(&mut st.creator,Pubkey::default())` | 27,392 | 0.64419 | 2150 | = s8 |
| c1 | s8 + ev_cb_local (+8) | 27,400 | 0.6411 | | |
| c4 | s8 + `curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps)` (+8) | 27,400 | 0.6426 | | |
| c5 | s8 + ev_mint_key (+16) | 27,408 | 0.63472 | | |

- Nothing between the CtoState literal and the arm can write curve memory on the success path (memcmp is readonly, the
  validate error calls do not dominate the arm). So MemCpyOpt may legally forward st.creator from the curve, and no
  spelling of the read (binding, reference, by-value, &mut) changes that.
- The only clobber available is the `find_program_address` call. Building st before it (s7) does block the forwarding,
  but it moves the curve/global reads ahead of the PDA, and that is the head/sweep relayout the PDA-first and st-first
  families already hit.
- s8/s10 reproduce p1's head RA shift exactly (same per-chunk counts; their disassemblies differ from p1 only in a few
  spill slots). The dead `memset(st,0,32)` survives DSE because `%st` escapes into the collect_old memcmp. The
  shift is worth -1 M at -8 B, and no +8 B tail knob pays it back.

## For other lanes

- The arm's original shape (aligned 4-word copy of st.creator, 8/24 split, two copies) needs the target value split 8/24.
  Main's target is split 7/i64/ptr/9 because `new: Option<Pubkey>` (payload at offset 1) is read as i64 words, so SROA cuts
  target at 7/15/23. Changing the arm alone cannot produce aligned words. This belongs with the `new`-copy/E32 work
  (w13a16, w13a03), not with reload spellings.
- Head RA is sensitive to anything that changes the liveness of `%23`/`%st` around bb21. p1 and s8 shorten the function by
  56 / 8 B at -1 M. That is a size lever, not a match lever.
