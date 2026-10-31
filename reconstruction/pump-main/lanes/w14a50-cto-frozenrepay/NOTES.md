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

## Screens (raw-IR capture + opt + llc oracle)

Oracle: w14a38 `capvar.sh` + `rx.py` (copied to `$OUT/tools`). On 28ab23a m0 gave main's ratio (0.65488) but two register
swaps off main's tokens. On 6330811, 2e1379d and 304b03a `eq_main` is true. Knob sources (`tools/collect.py`):
sizeknobs-cto.json, knobs13, w14a27 newknobs, w14a31 e/ (#3307), w14a26 genes.py (#3291), w14a32 src edits (#3299),
#3340, plus the reverse knobs rev_d4 / rev_ff / rev_t42. Ledger approach `frozenrepay`, keys
`0x22a10-w14-<sha7>-frozenrepay-<variant>-v1` (about 430 rows).

| screen | base | variants | best at 27,400 | notes |
| --- | --- | ---: | --- | --- |
| k1 single knobs on d4+ff | 28ab23a (d4+ff 0.65558 @27,392) | 194 (85 valid) | **t42 fee unwrap_or 0.65548** (landed, #3358) | ev_cb_local 0.65458, cu_replace 0.65279 |
| k2 single knobs | 6330811 (0.65698) | 182 | = main | -8: s10 0.65738, rev_t42 0.65708, sh_iflet 0.65678, tp_dlen 0.65588. +8: ev_cb_local 0.65538. +16: wl_ts_clockvar 0.65588 |
| ka token-arm shapes | 6330811 | 16 | = main | match / if-let / `!=0` / `!frozen` nesting / tuple forms are token-identical. `.map(\|()\|amount)` return 0.6193, frozen `return Ok(0)` 0.62208, account binding `let ta=..` 0.6374 |
| p1+p2 pairs/triples | 6330811 | 27 | none above main | best rt+cb 0.65608, ifl+cb 0.65578, s10+rt+wts 0.65578 |
| k5 s10 + knob | 6330811 | 62 | none (best 0.65708 @27,392) | |
| k8 single knobs | 2e1379d (0.65728) | 105 | = main | |
| k9 single knobs + t1 pairs | 304b03a (0.65788) | 119 | = main | t1 fee if-let (-8) 0.65828 @27,392; t1+wl_writ_eq 0.65758, t1+ev_cb_local 0.65698, t1+tp_dlen+wl_ts_clockvar 0.65638 |

- **jM (jump-masked match) ranking on 6330811:** no single knob or pair beats main's jM 2,226 (sh_iflet ties it at -8 B).
  The off-size ratio gains of s10 / rev_t42 / sh_iflet are size artifacts.
- **Synthetic size-shift bound (w14a31 shift.py, main 6330811):** the best pure +8 is +1 M (0x710-0x1750). The best
  pure -8 is +2 M (0x8c0-0xd40, validate). The best pair is +2 M. So repays are worth at most about +0.0006 now.
- **The frozen-first order is not the original's.** The original calls `token_raw_amount` (0x20c8) before
  `token_frozen` (0x2110), the pre-ff order. ff wins because of register allocation: with raw-first, ours spills r6
  to 0x9b8 and keeps the account pointer in r6, and the original does `add r8,72; ldxdw r6,[r10-0x2c8]`. Also, ours
  jumps from the `?` Err edges after both helpers to a nearby block (+161 insns). The original jumps to the far shared
  sweep join (+856 insns, orig 0x3c58). Once the swept-join residual (w14a06/w14a33 J2) is fixed, re-test raw-first
  (`rev_ff`).
