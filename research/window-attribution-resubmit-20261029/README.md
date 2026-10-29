# Window-attribution resubmission (corrected, distilled)

Resubmission of the closed PR #1172, per the maintainer's invitation: *"a much
smaller packet would be welcome: one rebased on current main with the stale
conclusions removed, the checksums regenerated from the committed bytes, and an
English README."*

This packet is distilled. The full raw measurement packets (variant patches,
per-window analyses, measurement JSONs) remain archived on the
`research/window-gap-attribution-20261029` branch referenced by PR #1172
(`https://github.com/cerapmen7/pumpfun-source`, commits `270d0178`..`b92310253`).

## Status against current main (2026-10-29)

- **AMM `0x4c750` is raw-equal on main** via #1195 (line-444 owner-check
  respelling, fixing the borrow-test fold at sell+0xd00) and #1205; the README
  now shows 785/785 and whole meaningful ELF equality. Our snapshot-era
  framing "one block-placement decision" was **incomplete**: our own packet data
  records **two independent divergences** — the borrow-test fold (10 relocation
  rows uniformly −0x8) and the line-467 cold-queue reorder. Both are resolved
  upstream; our framing is withdrawn.
- **Pump `0x14f4e0` has a normalized match on main** via #1191 (README:
  1,020/1,035, 15 unmatched). Our conclusion "only an IR/llc-level ordering
  change can close it" applied to the pre-#1191 qualification candidate only
  and is **withdrawn for current main**.

## Corrections to the closed PR

1. `0x22a10` line tuple: the deployed line is **648**, not 2006 (field-swap
   misdecode in our analysis).
2. "Closing the helper pair could close four windows" is **overstated**: call
   immediates are masked by the window metric. The dependency is real (see
   FINDINGS.md §2) but cascade gains are not proven.
3. The ten `variants/*.patch` checksums in the closed PR **failed after the git
   round-trip** (hashed with CRLF hunk lines, committed as LF). Every checksum
   in this packet is generated and verified **from the committed bytes**
   (`verify.py` re-checks them against the working tree after a fresh checkout).
4. `analysis/ir-blocks.txt` did not contain the block-ordering excerpt cited in
   that RESULT.md; that citation is **withdrawn**.
5. Variant v8 (`if ata.is_writable == false`): our environment produced a
   byte-identical binary; the maintainer's rebuild differs (sha `6f854e88…`,
   9,032 B). Recorded as **environment-dependent**, not byte-identical.

## Validated findings kept

- `transfer_to_user`/`transfer_to_recipient` and `transfer_from_user`/
  `transfer_from_recipient` have identical normalized bytes; exchanging them is
  invisible to the window metric (verified; recorded in the maintainer ledger).
- The call graph among the target windows, with the masking caveat above.
- The measured source-shape and function-attribute experiment matrix
  (FINDINGS.md §3) as **negative methodology evidence** on the pre-#1191
  snapshot: frontend/MIR canonicalization results that save future attempts.

## Contents

- `README.md` — this file.
- `FINDINGS.md` — kept findings, corrections, experiment matrix (English).
- `data/` — distilled measured data (helper-body classification, experiment
  summary).
- `manifest.json`, `SHA256SUMS`, `verify.py` — integrity, verified from
  committed bytes.

## Limits

No window is gained by this packet and no source change is proposed. All
measurements were taken on the pre-#1191 qualification candidate
(`0f50faa8…` Pump / `86dbc2c6…` AMM) and are marked snapshot-conditional where
relevant. Nothing here is a security review or a deployable replacement.
