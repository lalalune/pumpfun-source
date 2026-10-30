# Lane w10r1-admincto-errseq (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`). Angle: error-sequence
alignment, meaning the order and form of every error exit in the original compared with ours.
Base: origin/main 917ee615f (1032/347, admin_cto 27,344 B, ratio 0.37637).
Builds: `~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-errseq/` (not in git).

## Error-site census (Source line immediates in layout order)

| | sequence |
| --- | --- |
| original | 289 298 306 296 326 312 307 330 338 334 410 719 648 660 284 556 |
| main | 298 289 330 296 326 306 312 307 338 410 334 719 648 660 284 556 |

- Every error tail has the same form apart from frame offsets: name(), Display::fmt, then the AnchorError
  stores and Error::from. The exceptions are 307 and 312. There the original calls the outlined `to_string`
  (it stores the line before the code), and main inlines it (#2370's finding).
- 284 (mayhem) and 556 sit at the end in both, so they are cold blocks.
- The mismatches in order all come from the control flow, not from the error forms.

## What the original's validate CFG shows (orig offsets)

- `holder` is used as `arg & 1` (0x618). That is `unwrap_or(false)`. Main computes `(x & 0xfd) != 0`, and LLVM's
  zero heuristic (BPI) makes that 62.5% likely. So MBP lays out the holder successor first, and with it 298 before 289.
  llc oracle on the captured IR: rewriting only that compare to `and 1` puts 289 before 298, as in the original.
- The 306 let-else tests the new tag with `and 1` (0x738), not an `icmp eq tag, 0`, so the zero heuristic
  does not apply there. Rewriting just that compare in the IR moves 306 before 296, as in the original.
- In the non-holder arm the original tests `shared` (0xd98, `[r10-0x920]`) after 312 and before the fee
  checks. It copies `st.creator` as the target there, so the target override happens inside validate's non-holder arm.
- In the original the fee code is single, with no duplicated 326/334/338 error blocks (154 calls). But the holder path enters
  its own fee-tag/326 test copy and skips 330, and the no-fee edges are split by holder and by shared. Main has one merged
  fee block that tests holder again for 330.

## Change (this PR)

`validate` takes `shared`, and its non-holder arm returns `if shared{st.creator}else{t}`. Execute's
`if shared&&!holder{target=st.creator;}` is removed. Behaviour is unchanged: the fee checks do not read the target.

| metric | main 917ee615f | this PR | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,344 | **27,400** | 27,400 |
| ratio | 0.37637 | 0.34781 | 1 |
| slots_diff (equal size) | n/a | 3,368 | 0 |
| calls | 154+3 | 154+3 | 154+3 |
| official normalized / raw | 1032 / 347 | 1032 / **1032** | |
| gains / losses | | 0 / 0 (raw +685, 0 raw losses) | |

Unstripped sha256 (fastbuild): 8c61702217808cbd63b389c6a6f3d8e8089c12df4d6f93c3007d762995f31848.

## Oracles

- `llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections` on the `--emit=llvm-ir` module
  (slimmed to execute plus declarations) reproduces main's execute exactly in under 1 s.
- `opt -O3` (SDK v1.44 rustlib opt) on the `-C no-prepopulate-passes` raw module, followed by llc, also reproduces main
  exactly (token ratio 1.0), in about 25 s. With this, raw-IR CFG edits can be tested without a cargo build.

## Attempts

See the ledger (approach `error-sequence-alignment`, keys `0x22a10-main-917ee615-*`).
