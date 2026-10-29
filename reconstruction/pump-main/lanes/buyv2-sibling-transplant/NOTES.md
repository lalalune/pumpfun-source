# buyv2-sibling-transplant

Targets (programs/pump/src/buy_v2.rs):
- `0x13f630` `buy_v2::buy_exact_quote_in_handler` (line 545), original 20,184 B
- `0x13b9b8` `buy_v2::buy_handler` (line 179), original 15,480 B

## Result 1: restore the prior-swarm exact-quote handler (attempt 8ed0a8a6)

The 2026-10-29 swarm's `exactquote-reordering` lane worked from a base tree whose ELF is
`bbb925b7` (eq ratio 0.98742). That source was never merged; main's handler had regressed to
0.694. The tree survives in git as `5e49b8cd6:research/pump-swap-partial-recovery-20261029/snapshots/v2-best-exactquote/source.tar.gz`.
Its `buy_v2.rs` is line-aligned with main, so lines 545..end were transplanted onto main
(the handler body plus the `pay_from_user*` / `move_curve_tokens` wrappers at 1052-1055).

| metric | main d2cb88d | this branch |
| --- | --- | --- |
| eq handler bytes / ratio | 20,096 / 0.69433 | 20,176 / 0.97341 |
| eq masked (regs,br,call,stack) | 0.9176 | 0.9742 |
| buy_handler | 15,424 / 0.66526 | unchanged |
| official | 1019 / 188 | 1019 / 188, no gains, no losses |
| unstripped sha256 | 04fdafc0 | 8cff4778 |

Mechanism differences restored: `let (base_token_program,base_mint)` bound at entry,
`NO_EXACT_FEE` const with `if !native{...}` admission, whitelist test written
`a.global.whitelist_pda==a.user.key()`, `(quote,pf,cf,computed,bps,bps)` tuple order,
`creator!=default` fee arms, local wrappers for curve/user transfers, and TradeEvent field order.

Composition with lane `buyv2-hillclimb` (#1207, frozen-best buy_handler): the whole snapshot
buy_v2.rs on main gives buy 0.94354 / 15,464 and eq 0.97341 / 20,176, 1019/188, no losses
(sha 3fcb1c4b, attempt 40cfd39c).

Remaining gap to the snapshot's own 0.98742 (and frozen-best buy 0.96177): the snapshot tree
also used the `pump-native-payments` path crate, which main removed. Re-adding it changes
Cargo.toml/Cargo.lock, so it is out of bounds (attempt dc8d8c16, compile-failed in a main copy).
