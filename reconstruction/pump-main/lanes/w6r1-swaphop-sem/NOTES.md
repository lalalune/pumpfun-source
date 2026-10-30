# w6r1-swaphop-sem: `0x5b3b0` `multi_hop_curve::swap_hop` (assembly-first semantic reconstruction)

Base: origin/main `099b0dd` (1027 normalized / 276 raw), swap_hop ratio 0.7063, 18,328 B
(orig 18,584 B), **106/107 direct calls** (one `AccountInfo::clone` missing).

## Result (head)

| build | bytes | ratio | calls | segdist opregs / exact | official |
|---|---:|---:|---:|---:|---|
| base 099b0dd | 18,328 | 0.7063 | 106/107 | 785 / 912 | 1027 / 276 |
| F1 fee_config clone restored | 18,440 | 0.6853 | 107/107 | 820 / 965 | 1027 / 276, 0 losses |
| F2 + seeds from inline base_mint clone temp | 18,440 | 0.6953 | 107/107 | 789 / 935 | 0 losses |
| F3 + `let reserves` before the over-reserves test | 18,440 | 0.6953 | 107/107 | 786 / 934 | 0 losses |
| S1 + sell-arm tail `net - output` | 18,456 | 0.72444 | 107/107 | 540 / 700 | 0 losses |
| **U1** + block-scoped whitelist `user` | 18,480 | **0.72528** | **107/107** | **525 / 698** | 1027 / 276, 0 losses |

(segdist = call-anchored segment distance from the w4-swaphop tool `seg.py`; lower is better.)

## Mechanisms (each read off the original first)

1. **fee_config clone** (orig 0x16b8-0x1790): the original clones `[fee_config+0x88]` into
   -0x6d0, calls `data_len`, then drops the clone: `a.fee_config.to_account_info().data_len()`.
   Main's `AsRef::<AccountInfo>::as_ref(&*a.fee_config)` removed that call to buy size; the
   callee multiset is exact again (107/107). Costs ratio alone (regalloc of the prologue moves).
2. **seeds from a statement temporary** (orig 0x1590-0x16b0): the base_mint clone at 0x15a0 is
   dropped only after the seed array stores, i.e. the clone is a temporary of the seeds `let`:
   `&[&[b"bonding-curve", h.base_mint.to_account_info().key.as_ref(), &[curve_bump]]]`.
3. **reserves bound once** (orig r8 = `[c+0x58]` loaded at 0x22a0 and reused after
   complete_fill as base_amount at 0x2be8/0x2c40): `let reserves = c.real_token_reserves;`.
4. **sell-arm tail block** (orig 0x2438: `sub r8, output` + post_fill tag 0, then the accrue join
   at 0x2458; both the transfer_quote_out Ok edge and the two skip edges target 0x2438). The
   check at 692 (`jlt net, output` at 0x1cd0) stays early, but the subtraction is in a block after
   the transfer `if`. IR oracle: moving the sub into a new tail block drops segdist 786 -> 540;
   an empty tail block is folded (byte-identical). Source: line 692 keeps
   `net.checked_sub(output).ok_or_else(..)?;` as a check and the arm tuple uses `net - output`
   (overflow check folded by the dominating 692 test). The buy-arm analogue (orig 0x2d18) is
   neutral (S1B1 548/696).
5. **whitelist `user` scoped to the require** (orig: user copy shares slot -0x6d0 with the
   complete_fill result, and complete_fill's Some/None paths jump straight to the checked_add
   join at 0x2860; no inner merge). Our `let user` ended its lifetime in the over-reserves merge
   block, keeping that block (lifetime.end) alive. `{ let user = ..; require!(..); }` removes it
   (IR oracle user1 = U1 exactly).

## Rejected / neutral this lane
- O1 `if base <= reserves { within } else { over }` (InstCombine swaps back; 557/736).
- U2 inline `a.user.key()` in the require (0.7266 but user loaded after the mayhem test; orig before).
- Branch weights (IR oracle) on the mayhem, whitelist and over-reserves branches: <= 16 segdist.

## Remaining residuals (U1)
- Prologue/regalloc: orig keeps `[h+0x10]` in r9 and spills `&a.user` (a+0x18) to -0xa50 for
  reuse at 0xc68/0x2c68/0x2ea8/0x3920/0x3e88; ours spills `a` and recomputes.
- complete_fill result handling: orig tests tag 2 then tag 0 (None) and has three preds into the
  checked_add join; ours tests `== 1`.
- Mayhem test: orig falls through to the 599 error and places the whitelist memcmp after the
  buy transfer_input (0x29b0); ours places memcmp right after the test.
