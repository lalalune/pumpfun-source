# Lane w12a12-cto-ctxuse (wave 12, pool a)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: how `execute` consumes its `Context`, accounts and args, as a route to the frame difference.
Base: origin/main e61df03 (programs identical to 20a1ae9c0): 1033/1033, admin_cto 0.43919, 3,352 slots.
Ledger approach `ctx-accounts-use` / `frame-slot-map` / `frame-layout-ir-oracle`, keys `0x22a10-w12-20a1ae9-ctxuse-*`.

## 1. The original frame is not "56 B bigger"

The often-quoted 56 B (`[r10-0x928]` vs `[r10-0x8f0]` at the first instruction) is a spill-slot
assignment difference, not a uniform shift. Per region (frameoracle on main's IR, captured by w12a01):

| region (frame-index order) | ours | original | diff |
| --- | ---: | ---: | ---: |
| inlined-callee allocas, top .. `val.sroa.6.i` | T 0x540 | T 0x530 | ours +16 |
| own allocas, `val.sroa.6.i` .. `old_creator` | 176 B | 256 B | orig +80 |
| `old_creator` .. `holder_key` | 144 B | 112 B | ours +32 |
| `holder_key`, `mint` | 0x680, 0x6a0 | 0x6a0, 0x6c0 | orig +32 |

After `mint` come the 33 call-return slots (their RPO order differs) and the spills (regalloc differs).

## 2. Original slot map, T 0x530 .. 0x6c0 (read from the original's stack accesses)

Own allocas in frame-index order (low T = high MIR local number):

| orig T | size | what it holds (original code addresses) | ours |
| --- | ---: | --- | --- |
| 0x530 | 24 | validated target tail, bytes [8,32) (first qword in a register / spill 0x918); shares its slot with the wallet collect `val.sroa.6.i` | `val.sroa.6.i` alone, at 0x540 |
| 0x538 | 7 | target bytes [0,7), new-creator branch (0x23b50) | `target.sroa.0`, but at 0x660 |
| 0x548 | 9 | target bytes [23,32), new-creator branch | `target.sroa.8` (dead) / `_37.sroa.11` |
| 0x550 | 7 | copy of 0x538 at the validation join (0x243e0); becomes the sharing CPI `val` [1,8) | - |
| 0x560 | 9 | copy of 0x548 (0x24400); becomes `val` [24,33) | - |
| 0x580 | 32 | final `target`: stored to `curve.creator` (0x27518) and passed as r3 to `admin_cto_pool` (0x27820) | `target1`, 32 B no-lifetime, at 0x658 |
| 0x598 | 24 | `_184` Result<(),ProgramError> (event emit_cpi) | same object, 0x558 |
| 0x5c8 | 48 | `_169` ix_data iterator | 0x588 |
| 0x5e0 | 24 | `inner_data` | 0x5a0 |
| 0x610 | 48 | `authority_info` | 0x5d0 |
| 0x630 | 32 | `old_creator` (0x274e0) | 0x5f0 |
| 0x651 | 33 | `val`, the `admin_cto_sharing_config` Option<Pubkey> arg (0x26730, r3 at 0x27480) | `val7`, 0x611 |
| 0x658 | 7 | `new` arg bytes [1,8), copied at entry (0x22f00) | - |
| 0x668 | 9 | `new` arg bytes [24,33), copied at entry (0x22f48) | - |
| 0x680 | 24 | validated-target tail copy at the join (0x243b8, read at 0x24430); **hosts the wallet emit_cpi signer slice** (`[&[&[u8]];1]`, 0x29108/0x29150) | no such slot; ours has `sharing_update2.sroa.3` + `target1` (2 x 32 B, no lifetime) |
| 0x6a0 | 32 | `holder_key` | 0x680 |
| 0x6c0 | 32 | `mint` | 0x6a0 |

So the original keeps the final target in a high-numbered (late) local, and its validation `?` join
copies the target through a 24 B temporary that sits right after `holder_key` in MIR order.

## 3. IR oracle: the signer slice is the big frame lever (+0.05)

Tools: `tools/fo.sh` (frameoracle wrapper, prints the masked ratio, which equals target_metric on
the base), `tools/ops.py` (IR edit: resize an alloca / insert a pad), `tools/merge117.py` (merge the
signer-slice alloca into another alloca). IR: w12a01's capture of main (candidate sha equals main).

| IR what-if on main | masked ratio | r10 equal |
| --- | ---: | ---: |
| base | 0.43919 | 670 |
| pad 24 B before `holder_key` | 0.44518 | 678 |
| pad 32 B before `holder_key` (the naive "frame +32") | 0.43229 | 670 |
| **move `_117.i74` (wallet emit_cpi signer slice, 16 B) into the own region** (any position: before holder_key, _184, old_creator, val7 or END) | **0.48892** | 762 |
| merge `_117.i74` into `_37.sroa.11` (the `validate(..)?` ControlFlow piece) | 0.48862 | 762 |
| move `_117.i74` + pad 24 before `holder_key` | 0.49491 | 770 |
| move + pad 8 / 16 / 32 / 40 / 48 / 64 / 88 | 0.455 / 0.467 / 0.481 / 0.475 / 0.457 / 0.476 / 0.484 | |
| exact original own-region layout (holder_key, mint at orig T) | 0.46345 | 773 |

Reading:
- In ours `_117.i74` cannot merge: every slot of 16 B or more is live during the wallet emit_cpi, so
  it keeps its own slot inside the inlined region and pushes every wallet object 16 B deeper.
- In the original it merges into the 24 B slot at T 0x680. The merge oracle puts our `_37.sroa.11`
  (the ControlFlow<..,Pubkey> piece of `validate(..)?`) exactly there (implied orig T 0x680, 3/3 votes).
  The original's piece is 24 B (target bytes [8,32)), so it sorts before the 16 B slice and absorbs it;
  ours is 16 B (bytes [23,32) after the 7/16/9 split that the `new` offset-1 copies force), sorts after
  the slice and is absorbed elsewhere.
- Moving whole objects to their original T does not pay by itself: after `mint`, the call-return slot
  order (RPO) and the spill assignment differ, so a uniform +32 loses more than it gains.

Source goal from this: make the target flow through the `validate(..)?` temporary as [0,8) + [8,32)
(24 B piece) instead of 7/16/9, or otherwise give the slice a host slot outside the inlined region.

## 4. Source trials (full builds, measure.sh)

| trial | change | admin_cto | verdict |
| --- | --- | --- | --- |
| t3_aderef | `let a=&*ctx.accounts` | byte-identical | rejected |
| t1_vmatch | `match validate(..){Ok(t)=>t,Err(e)=>return Err(e)}` | 22,616 B, 0.254 | rejected |
