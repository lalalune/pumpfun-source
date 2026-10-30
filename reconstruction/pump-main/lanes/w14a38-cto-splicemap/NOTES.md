# w14a38-cto-splicemap: whole-window residual map for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 81d3d9abe (`$BASE/unstripped.so`): ratio 0.65069, 3,171 differing slots, 1034/1035 normalized and raw.
Ledger approach `splicemap`, keys `0x22a10-w14-81d3d9a-splicemap-*`.

## Method (tools/splice.py, tools/regions.py)

- Tokens are `score.normalize` instructions, exactly what target_metric's ratio uses (`splice.py load` reproduces
  0.65069 / 3171).
- A region [lo,hi) is spliced by replacing the candidate's tokens and bytes in that offset range with the original's
  (both boundaries must be instruction boundaries in both). `dratio` / `dslots` = the gain if that region alone matched.
- Each region's local residual is split by re-aligning the region with progressively masked tokens:
  `fm` = misses removed by masking r10 frame displacements (and negative add64 immediates), `rm` = then by masking
  registers, `jm` = then by masking jump offsets, `sk` = structure misses that remain (opcode / immediate / block order).
- `splice.py anchors` lists equal-offset runs whose fully masked tokens are equal (>= 4 instructions). There are only 18
  on 81d3d9a: 0x0-0x80, 0x1028, 0x1c38-0x1d30, 0x46b8-0x4970 (87 insns), 0x5c38-0x6b08 runs (wallet). Everywhere else
  ours is shifted by 8-0x40 bytes against the original, so large regions are spliced between call landmarks instead.
- `lst.py` names every call (orig call targets resolve through the candidate symbol table, the layout outside the window
  is identical); `o.calls`/`c.calls` side by side give the call LCS used for the source mapping.

## Ranked map (REGIONS.json; FIXED200.jsonl has the same split per 0x200 chunk)

| orig region | what | lines | owner | dratio | dslots | fm | rm | jm | sk |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0x26e8-0x3930 | TCF inline AccountInfo literals | 661 | sweep TCF w14a17/w14a23 | +0.0569 | 585 | 39 | 118 | 17 | 27 |
| 0x3c38-0x46b8 | sharing CPI inline literals | 745-751 | sharing CPI w14a30 | +0.0551 | 335 | 24 | 0 | 0 | 170 |
| 0x1068-0x1940 | validate fee errors (orig outlines to_string) | 307-338 | validate w14a15/w14a21 | +0.0356 | 277 | 22 | 14 | 4 | 111 |
| 0x5c38-0x6b08 | wallet() | 556-580 | wallet r8 w14a35 | +0.0354 | 287 | 24 | 58 | 22 | 14 |
| 0x0080-0x0400 | entry head: PDA (orig first), shared, quote_locked | 339 | unowned; PDA-first loses to RA (w14a09/w14a11) | +0.0168 | 107 | 4 | 7 | 0 | 48 |
| 0x0400-0x06a8 | CtoState/holder_key copy + validate head | 339, 283-296 | validate | +0.0162 | 84 | 6 | 18 | 3 | 45 |
| 0x0838-0x0e08 | validate 298/312 memcmps + error blocks | 296-312 | validate | +0.0159 | 181 | 20 | 0 | 18 | 43 |
| 0x4970-0x4e60 | curve update, pool gate, admin_cto_pool | 752-766 | curve tail w14a34 | +0.0108 | 156 | 6 | 14 | 1 | 27 |
| 0x1940-0x1c38 | sharing/collect_old tuple, prepare, 410 | 339-410 | (w14a29 notes) | +0.0090 | 92 | 6 | 3 | 3 | 27 |
| 0x1d30-0x2300 | sweep head (vault PDA, amm_frozen, 660) | 647-660 | unowned | +0.0081 | 185 | 3 | 10 | 11 | 9 |
| 0x46b8-0x4970 | sharing CPI tail (skeleton equal) | 749 | frame only | +0.0078 | 84 | 41 | 0 | 0 | 0 |
| 0x4e60-0x5538 | AdminCtoEvent + emit + event CPI | 767 | unowned | +0.0075 | 217 | 3 | 16 | 3 | 14 |
| 0x5570-0x5a80 | tail error blocks (unwrap, 284, 556), Rent min | 284, 556, 663 | unowned | +0.0063 | 162 | 6 | 8 | 2 | 14 |
| 0x5a80-0x5c38 | sweep native + return join | 664 | native join w14a33 | +0.0057 | 55 | 6 | 7 | 1 | 8 |
| 0x0e28-0x1068 | validate 306/296 error blocks | 296, 306 | validate | +0.0053 | 72 | 16 | 0 | 4 | 16 |
| 0x3968-0x3c38 | TCF call, Rent::get, native head | 661-663 | native join w14a33 | +0.0048 | 90 | 8 | 5 | 0 | 11 |
| 0x06a8-0x0838 | validate error blocks 289/298 | 289, 298 | validate | +0.0033 | 50 | 14 | 2 | 3 | 12 |
| 0x2498-0x26e8 | sweep 719 frozen/raw_amount | 719 | holder vault ATA w14a27 | +0.0033 | 74 | 0 | 3 | 9 | 11 |

Readings:
- Four owned regions (TCF, sharing CPI, validate fee errors, wallet) hold 0.183 of the 0.349 gap. The unowned ones are
  each worth at most +0.017 if matched exactly; the entry head is the largest and is already known to be the original's
  PDA-first form that loses to the register cascade.
- The sharing CPI region is pure structure at the masked level (sk 170, rm 0): the literal load order, not register names.
  TCF and wallet are register dominated (rm 118 and 58).
- The call sequences are equal from 0x1cc8 to the end (157 calls each). The only call-order differences are in the entry
  (orig: find_program_address first) and in validate's error-block order (orig 289, 298, 312-memcmps, 306, 296, 326, 312,
  307, 330, 338, 334, prepare, 410; ours 298, 289, memcmps, 296, 326, 306, 312, 307, 330, 338, prepare, 410, 334) and
  the two inlined to_string (orig 7 to_string + 6 name/fmt pairs, ours 5 + 8).
