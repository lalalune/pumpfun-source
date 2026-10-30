# Lane w12b12-cto-cpi (wave 12, pool b): CPI construction forms in `admin_cto::execute`

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 20a1ae9c0 (`$BASE` sha 8cd7695c…): 1033/1033 normalized/raw, admin_cto 0.43919, 3,352 slots.
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w12b12-cto-cpi/` (not in git).
Ledger approach `cpi-forms`, keys `0x22a10-w12-20a1ae9-cpi-<variant>-v1`.

## Oracle: the wallet `emit_cpi!` signer-seeds array is worth +0.050

The frame oracle (`w4-frame-oracle/frameoracle.py`, llc on main's own IR, no build slot) shows one
16-byte alloca that shifts the middle of the frame: `%_117.i74`, the `&[&[b"__event_authority",&[bump]]]`
array that anchor's `emit_cpi!` builds for `invoke_signed` inside the inlined `wallet` (the
`CollectCreatorFeeEvent` emission). In ours it is its own StackColoring slot at frame index 41
(T=0x480), in front of the wallet's `_110.i`, `_94.i`, `ix_data.i`, `inner_data.i`,
`authority_info.i` and `val.sroa.6.i` slots. Those all sit 16 bytes too deep (delta -16), and so do
the pool-authority signer seeds that share their slots (`_100`, `_93`, `pb`).

| IR what-if (`--move-alloca`, main IR) | masked-exact ratio |
| --- | ---: |
| none (main) | 0.43919 |
| `_117.i74` moved anywhere after `val.sroa.6.i` (before `_60.i`, `_184`, `_67`, `val7`, `st`, `_8`, `holder_key`, or END) | **0.48892** |
| `_117.i74` moved only one slot later (before `_110.i`) | 0.43919 |
| plus `target1`, `target.sroa.0/8`, `sharing_update2.sroa.3` moved before `_184` | 0.48892 (no further gain: still 8 B off) |

So the gain needs only that the 16 bytes leave the run fi41–fi53: either the array merges into some other
slot, or its alloca comes after `val.sroa.6.i`. With it gone, fi40–fi53 all line up with the original
(delta 0). The next frame break is +80 B between `val.sroa.6.i` and `_184`.

Where the original keeps it: at `[r10-0x680]` (`0x29108 stxdw [r10-0x680]`, `0x29150 stdw [r10-0x678],0x2`,
`0x29170 add64 r1,-0x680`). The same 24 bytes `[r10-0x680..-0x668)` hold `target[8..32)` earlier, at
`0x243b0..0x24458`, just before `prepare_bonding_curve`. So the original's StackColoring merged the
emit seeds into a 24-byte, short-lived, execute-local `target` piece placed next to `holder_key`
(T=0x6a0). Ours has no such slot. Our `target` is split 7/16/9 (`target.sroa.0` 7 B, two i64 in
registers, `target.sroa.8` 9 B). That split comes from the offset-1 Pubkey inside
`Result<Pubkey>`/`ControlFlow` (validate's `?`). The original splits every target copy 8/24: `[0..8)` in a
register (spill `[r10-0x918]`) and `[8..32)` in memory (`[r10-0x530]` → `[r10-0x680]` → `[r10-0x578]`). A
source shape that makes the execute-local `target` an 8/24 split should give StackColoring a 24-byte
partner for the emit seeds, and that should be worth about +0.05.

The original's pool-CPI `target` argument (`r3 = r10-0x580`) is a 32-byte slot early in frame order,
just ahead of the final `emit_cpi!` temporaries (`_184` at T=0x598). It is preceded by two 7/9-byte pairs at
T=0x538/0x548 and 0x550/0x560 (copies made at 0x243e0..0x24418). Ours keeps `target1` (32 B, no lifetime
markers) near `holder_key`. These objects make up the +80/-48 B breaks that remain after the fix above.

## CPI shapes compared with the original

- The call boundaries of all CPIs match the original: 4 `declare_program!` CPIs, 2 `create_idempotent`,
  `collect`, `transfer_vault_tokens`, `transfer_native`, 2 inlined `emit_cpi!`.
- CpiContext/accounts slots match: pool `_130` at T=0x2d0, accounts `_132` memcpy source at T=0x450,
  sharing `_105` at T=0x2d0. The `signer_seeds` slice is at 0x4e0 in ours and 0x4d0 in the original, which
  is the -16 shift described above.
- `holder` reaches the pool CPI as `and64 rX,0xff; jne` (an i1 rebuilt from `(holder_opt & -3) != 0`) in
  ours. The original reloads a canonical 0/1 spill `[r10-0x950]`, a phi of constants set in the validate
  arms (`0x23b38 mov64 r1,1; stxdw [r10-0x950],r1`).

## Trials (measure.sh, main 20a1ae9)

| variant | change | bytes | ratio | losses |
| --- | --- | ---: | ---: | --- |
| sws | sharing CPI `CpiContext::new(..).with_signer(seeds)` | 27,424 | 0.40844 | size |
| pws | pool CPI `.with_signer(seeds)` | 27,400 | 0.37328 | 0/0 |
| seedsinline | both signed CPIs take `&[&[b"pool-authority",mint.as_ref(),&[bump]]]` inline | 27,584 | 0.39982 | size |
| pocurveargs | pool CPI args read back from the curve account | 27,368 | 0.26589 | size |
| shclos | sharing CPI as a migrate.rs-style `move \|signer_seeds:&[&[&[u8]];1]\|` closure | 27,432 | 0.40808 | size |
