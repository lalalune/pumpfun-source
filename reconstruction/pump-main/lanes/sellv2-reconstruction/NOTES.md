# sellv2-reconstruction

Target: `0x144508` `sell_v2::execute` (original 13,976 B), programs/pump/src/sell_v2.rs:76.

## Metrics (target_metric.py; official census from score.py)

| trial | bytes | ratio | ordered callees | normalized/raw | gains/losses |
| --- | ---: | ---: | --- | --- | --- |
| baseline (d2cb88d + #1171) | 14,104 | 0.6620 | 79/80 (Clock::get before is_sol memcmp) | 1019/188 | none |
| is_sol before Clock (`issol`) | 14,128 | 0.6655 | 80/80 | 1019/188 | none |
| event snapshot reorder (`ev1B`, committed) | 14,008 | 0.7873 | 80/80 | 1019/188 | none |

## Mechanism (ev1B)

Read from the original's event prelude (0x146658..0x147620):

1. The curve snapshot (four reserves, `creator`, `quote_mint`) is loaded right after the last
   `transfer_to_recipient` and *before* the `sharing_config` clone + `sharing_config_shareholders`.
2. `is_sol` (memcmp of the snapshot quote mint against zero) follows the shareholder drop.
3. `Clock::get` follows the `user`/`base_mint` key copies, i.e. `timestamp:Clock::get()?.unix_timestamp`
   sits inside the `TradeEvent` literal, the idiom the matched legacy sell in lib.rs uses.
4. The event's `quote_mint` field re-reads `c.quote_mint` (descending 0x40..0x28 loads), not the local.

## Ledger attempt ids

- baseline control 0b87577c1dca41d9b3a00bab270af284
- is-sol-before-clock 7197c63dc78342208d17057fbc512bcc
- event-snapshot-before-shareholders (local quote_mint) 57e75cb5e6344b94b9ff11cb7296e190
- same with `quote_mint:c.quote_mint` 434effa992f04ff5a103951fa62910c8
