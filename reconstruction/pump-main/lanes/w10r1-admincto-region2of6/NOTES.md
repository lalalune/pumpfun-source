# Lane w10r1-admincto-region2of6 (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`).
Angle: region split, region 2 of 6. The original window (27,400 B, 3,425 slots) is cut into six equal
byte ranges; region 2 is original `0x23be6..0x24dbd` (537 slots).
Base: origin/main 917ee615f (1032 / 347), admin_cto 27,344 B, ratio 0.37637.
Builds: `~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-region2of6/`.

## What region 2 holds in the original

Mapped with the error-site coordinates (`coords.py window 0x22a10`) and call targets:

| original offset | contents |
| --- | --- |
| 0x23be8 | tail of the 326 `CreatorFeeNotConfigurableForQuote` error (inlined to_string, then the error) |
| 0x23c68 | 312 `InvalidCreator` and 307 `CreatorShouldNotBeZero` (+ with_pubkeys): to_string is OUTLINED here (two calls) |
| 0x23ea0 | Ok(target) merge, fee tag test, 330 check (`[r10-0x8e8]` = !holder&&cashback) |
| 0x24048 | 334 check (`fee_configurable`), 338 range check (`f-1 < max`), then the 338 error block and the 334 error block back to back |
| 0x24210 | phi merges of sharing_update tag (2 = None), collect_old, skip-sweep flag; `creator != default` memcmp |
| 0x24460 | `prepare_bonding_curve` call, `?`, 410 `CreatorFeesNotSwept` |
| 0x24688 | wallet gate (`collect_old`), executable / owner checks, shared msg call |
| 0x24740 | sweep gate on a precomputed bool `[r10-0x8e0]`, sweep entry: bump read, native-mint memcmp, creator-vault PDA, 648 check, amm token_frozen |

Main's layout differs in region 2 mainly in: 312/307 inline to_string (known, PRs #2370/#2416); 330 is
placed in region 1; the 334 error block is chained after the wallet's executable check instead of after 338;
the sweep gate recomputes `holder & shared`.

Metric used for this region: `regm.py` (lane scratch) aligns the whole function with win.py's tokens and counts
how many of region 2's 537 original slots fall in matching blocks (`frac`).

## Trials (ledger approach `region-split-r2`)

| trial | mechanism | bytes | ratio | region-2 frac | result |
| --- | --- | ---: | ---: | ---: | --- |
| base | origin/main 917ee615f | 27,344 | 0.37637 | 0.4637 | |
| t1 | fee checks 326-338 as `require!` | 27,344 | 0.37637 | 0.4637 | byte-identical |
| t2 | sharing_update / collect_old / target override in one `if shared {..} else {..}` tree | 27,440 | 0.37599 | 0.4674 | size nearer (40), ratio lower |
| t3 | t2 + explicit `do_sweep` flag from the tree used as sweep gate | 27,632 | 0.30157 | 0.4544 | rejected |
| **t6** | tree with explicit holder arms: `if shared { if holder {(Some(None),false)} else {target=creator;(Some(new),false)} } else {(None, !hr && creator != default)}` | **27,368** | **0.37680** | 0.4674 | **kept** |
| t8 | t6 with the `!holder` arm first | 27,368 | 0.37680 | 0.4674 | byte-identical to t6 |
| t10 | t6 with tuple order swapped | 27,368 | 0.37680 | 0.4674 | same metrics |

t6 is 32 B from the original size (main: 56 B) and has a higher ratio, with 0 gains / 0 losses (1032 / 347).
