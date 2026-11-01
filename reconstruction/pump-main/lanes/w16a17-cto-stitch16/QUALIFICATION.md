# Reviewed source qualification, 2026-10-31

The three ordinary-Rust edits are qualified on top of accepted #3969. An
independent fresh build of pre-PR main `7d5e14de9593411a25696e3bcfe27119b4854dde`
and the actually merged #3974 source both score 1,034 raw and normalized exact
windows of 1,035, with no losses. CTO remains 27,400 bytes, ratio 0.67735,
2,261 matching normalized tokens and calls154/3. Its differing positional
slots improve from 3,141 to 3,132, so the pinned-size/ratio/position rank
improves. This is nine better positions, zero additional matching tokens
and zero additional exact windows.

The Option<bool> Some/empty-None branch and error propagation are unchanged.
The rent_epoch reread uses the same immutable AccountInfo field across pure
Rc clones. Previously qualified #3965 Program/Rc guards and #3969 helper
assumptions are retained without new unsafe operations.

The stripped runtime images differ only in 1,247 CTO text bytes; all other
runtime sections and file size are unchanged. Unstripped local basic-block
symbol renaming adds one string-table byte, increasing total file size by
eight bytes after alignment; function/exported symbol identities remain unchanged.

Fresh original/candidate differential passes 388 cases, zero mismatches and
776 nonempty signed transaction vectors. The persistent lifecycle passes
nine cases, 20 unique transactions per image, 78 signatures and exact replay,
with state continuity/rollback and genuine signed dependency CPIs checked.
These finite synthetic comparisons do not prove exhaustive equivalence.
Stopped claim-token-incentive campaigns remain excluded.

The historical packet data and SUMMARY are preserved as recorded. Eighteen
private helpers and seven spec files were omitted after review found unsafe
shared-cache deletion, untracked import execution and stale metric/cache
protocols. Their original bytes remain in the original PR history. These
private experiments are not maintained tools or completion evidence.

Source snapshot: `698be2da084e9ab4790aee352c85d9ae40c61fbc3518f3034cdc93881505eaf5`.
Unstripped image: `c0799b625c349239646edae269f1602cc72d801be4f39608751a593df231d00a`.
Stripped image: `1bbae63d71949a8579095ce2daa3a12ffa74f358cfde0f14328a090a8775e9ab`.
