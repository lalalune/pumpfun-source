# w7r1-swaphop-sibling: 0x5b3b0 multi_hop_curve::swap_hop (sibling transplant)

Base: origin/main 7e26cbf. 1027/1035 normalized, 293 raw. swap_hop ratio 0.7332, 18,544 B (orig 18,584), 107/107 calls.

## Trials
| trial | change | bytes | ratio | result |
|---|---|---:|---:|---|
| t1 | line 599 `require!(crate::trade::v3_can_cross(&a.global,c,&a.user.key()),..)` (trade::buy spelling) | 18,512 | 0.7014 | byte-identical to w7r1-swaphop-frame u2; rejected |
| xb* (diagnostic) | `core::hint::black_box(&*a as *const _)` at 13 positions, scratch copies only | 18,448-18,632 | 0.720-0.831 | evidence only, cannot be proposed |

## Finding (analysis)
The original reloads `a.fee_config` from `a` (spill [r10-0xa48], +8) at each get_fees and at
complete_fill (orig 0x1990, 0x1ad0, 0x2a08). Ours loads it once (%_615) and spills it. Before
LLVM optimisation the loads are separate (checked with -Cno-prepopulate-passes IR). LLVM merges
them because `%a` is `noalias nocapture readonly`. When `a` escapes early, the reloads come back
and the prologue and get_fees sequences line up with the original. This suggests that in the
original `a` reaches a callee that does not have nocapture. In our IR every callee that gets an
a-derived pointer (prepare_bonding_curve, transfer_input, native_buyback, uqp_transfer_native,
mhc_transfer_buyback_out, AccountInfo::clone) is nocapture. External callees that lack nocapture
(AccountInfo::data_len, invoke_signed accounts, sol_log_data, new_with_bytes data,
admit_associated_token_account `account`) only ever receive allocas or clones.

## Next ideas
- Find the ordinary-Rust construct that makes `a` escape: an a-derived pointer (e.g. `&a.event_authority`,
  `&a.user`, `&a.buyback_fee_recipient`, which are all stored inline) passed to a non-nocapture external
  such as `data_len`/`try_data_len`, or as a `&[AccountInfo]` slice into `invoke_signed`. Check each
  candidate against the original's call arguments (win.py orig).
- t1's local layout (mayhem test falls through to 599, memcmp falls into complete_fill) matches the
  original. Try it again once the escape mechanism is in place.
