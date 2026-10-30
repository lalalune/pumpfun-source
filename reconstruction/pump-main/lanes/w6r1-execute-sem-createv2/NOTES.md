# Lane w6r1-execute-sem (create_v2 target), wave 6 round 1

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 125 direct calls).
Base: origin/main 099b0dd (1027/1035 normalized, 276 raw); target 0.80237, 15,584 B, 125 calls.

The lane name `w6r1-execute-sem` was also in use by a concurrent agent working on
`admin_cto::execute` (0x22a10) in the shared worktree/out dir, so this work lives in its own
worktree and branch `swarm/w6r1-execute-sem-cv2` and notes dir `lanes/w6r1-execute-sem-createv2/`.
Ledger rows use lane `w6r1-execute-sem`, keys `0x1e7c0-main-099b0dd-*`.

## Results

| Build | Bytes | Ratio | Calls | Official | sha256 (unstripped) |
| --- | ---: | ---: | ---: | --- | --- |
| base 099b0dd (v13 store order, free `init_curve`) | 15,584 | 0.80237 | 125 | 1027/276 | d9484de7 |
| g7 port (#1542 form) | 15,544 | 0.82553 | 125 | 1027/276, 0 losses, 0 raw losses | d8b1914d |

## Mechanism

#1878 integrated create_v2 in the v13 (legacy-create store order) form because at its base
g7's size change flipped a raw-call-span membership. On current main g7 loses nothing (normalized
or raw), so the closer #1542 form is restored: `impl CreateV2 { fn init_curve(&mut self, ..) }`
with `let sol = Pubkey::default();` before the eager ivqr load and `let mut fee = 0; if
matches!(source, Controlled|Nested(_)) && creator_fee_bps.0 > 0 { ..; fee = .. }`.
