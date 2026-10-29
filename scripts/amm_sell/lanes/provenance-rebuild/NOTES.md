# Lane provenance-rebuild (amm-sell swarm, wave 2)

Approach: mine every historical AMM `sell.rs` on this machine, dedupe by sha256, rebuild
through `try_sell.py`, and graft historical hunks onto the current (owner_ne) source.

- `collect.py`: 471 distinct sources (350 non-swarm) from ~/.codex worktree archives (393 tarballs),
  research packets, 10-provenance candidates/prior110, git history of both repos.
- `hunks.py` / `mkhybrid.py`: 333 distinct line-aligned historical hunks inside `fn cashback`;
  264 graftable on the owner_ne base (skipping reverts of the accepted fixes and macro-line moves).
- `sdist.py`: structural distance that masks lddw immediates and call targets, so candidates whose
  sell size is not 9024 are not penalised for the rodata/callee shift. baseline 112, owner_ne 85,
  owner_ne + `if ata.data_len() == 0 {` (best historical graft, 9016 bytes) 34.

Results (68 builds): no historical source is raw-equal. Best raw is align 99. Best graft is sdist 34
(`best_sell.rs`, key 199d758dbf380e08).

Provenance of the swarm GOAL (semantic-reconstruction, key c9f12a27649d78bb): the line-444
`owner != ... { return err! }` construct appeared in 126 historical sources and the line-467
`if ata.is_writable == false { return err!(..) }` construct appeared in 108, with 95 sources having
both. The line-468 `if ata.data_is_empty() == false {} else {` construct appeared in none of them.
History never tried that one spelling. r27 (validation-result-shape) got the JEQ borrow test from
`owner != &crate::ID {Err(error!)} else {Ok(())}?`, the same `!=` mechanism.

I stopped the lane when the swarm goal was reached. The remaining historical sources and hunks were
not built because the goal made them moot.
