# w14a50-cto-frozenrepay: d4 + s_frozen_first with the fee unwrap_or repay

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a27-cto-hvatalit (#3337): its open lead d4 + s_frozen_first (0.65528 @ 27,392 on 6db95a7) needed +8 B.

## Landing 1 (main d371f97, 0.65638 -> 0.65698)

Three source edits:

1. **d4** (w14a27): sweep token arm `create_idempotent(..).and_then(|()| transfer_vault_tokens(..))?; return Ok(amount);`
   instead of `create_idempotent(..)?; transfer_vault_tokens(..)?; return Ok(amount);` (-24 B).
2. **s_frozen_first**: `let frozen=token_frozen(..)?;` before `let amount=token_raw_amount(..)?;` (+16 B; d4+ff = 27,392).
3. **t42 fee unwrap_or** (repay, +8 B): `curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);` instead of
   `if let Some(f)=fee{curve.creator_fee_bps=f;}`. Same value in every case (the field keeps its value on None).

| | main 28ab23a | d4+ff+t42 on 28ab23a | main d371f97 | merged (this PR) |
| --- | ---: | ---: | ---: | ---: |
| ratio | 0.65488 | 0.65548 | 0.65638 | **0.65698** |
| slots_diff | 3,280 | 3,194 | 3,280 | 3,193 |
| bytes | 27,400 | 27,400 | 27,400 | 27,400 |
| normalized / raw | 1034/1034 | 1034/1034 | 1034/1034 | 1034/1034, no gains/losses |

Differential: 363 cases, 0 mismatches. Unstripped sha256 `8bf606bf2cf7d63c98f8fe2e9497d3c0af9903399ad8ae7014a1c04b894921be`.

## Screen k1 (raw-IR capture + opt + llc oracle; tools/ under $OUT)

Base d4+ff on 28ab23a: oracle 0.65558 @ 27,392 (m0 = main's ratio 0.65488; tokens differ from main by two register swaps).
194 single knobs collected from sizeknobs-cto.json, knobs13, w14a27 newknobs, w14a31 e/ (#3307), w14a26 genes.py (#3291),
w14a32 src edits (#3299) and #3340. Best at 27,400: t42 fee unwrap_or 0.65548 (built: 0.65548). Other +8 B repays:
ev_cb_local 0.65458, cu_replace 0.65279. Most zero-size knobs are token-identical to the base.
Ledger approach `frozenrepay`, keys `0x22a10-w14-<sha7>-frozenrepay-*-v1`.
