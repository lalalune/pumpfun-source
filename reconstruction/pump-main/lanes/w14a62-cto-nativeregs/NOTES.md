# w14a62-cto-nativeregs: register naming in the sweep's native arm

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w14a51-cto-sweepjoin's open residual (#3359). The original keeps `amount` in r6 and copies `min` to r3. Ours keeps
`min` in r6 and `amount` in r3, then adds a `mov r6,r3`.
Base: main 2e1379de9 (0.65728, 3,192 slots, M 2194). The raw-IR capture + opt/llc oracle reproduces it (`eq_main=true`).
Ledger: approach `nativeregs`, keys `0x22a10-w14-2e1379d-nativeregs-*` and `0x22a10-w14-fc628cf-nativeregs-*` (12 rows).

**Result: no source change.** Nothing beats main. This PR holds the mechanism, the IR bounds and the tools.

## 1. The swap, confirmed (orig 0x5950-0x5b30, main `sbs.py`)

| | original | main |
| --- | --- | --- |
| before `minimum_balance` | `mov r9,0; mov r2,0` | `mov r2,0` |
| min (ret of `minimum_balance`) | r6, then `mov r3,r6` before the `sub` | r6 |
| vault ptr (`accounts+0xd8`) | `ldxdw r8,[0x8d8]; add r8,0xd8` (accounts pointer reloaded) | `add r8,0xd8` (accounts pointer live in r8) |
| amount (`usub.sat` select) | r6 | r3, then `mov r6,r3` on the `amount>0` path |
| `amount>0` test | `jgt r0,r3` | `jgt r0,r6` |
| zero edge into the swept join | carries **r9 = 0** | carries amount (r3, then `mov r8,r3` in J2) |
| after `transfer_native` | `mov r9,r6` | `mov r3,r6` |

The original's zero edge carries the **constant 0**, not `amount`. `mov r9,0` is the swept-phi register. It is materialized
before `minimum_balance`, because the ISel constant 0 node is shared with the `minimum_balance(rent,0)` argument, and
the swept class holds it in r9 across both calls. `amount` is then live only on the transfer path, so it takes r6 by
evicting `min`, which splits `min` to r3. On main the zero edge carries `amount`, so `amount` joins the swept coalescing class,
and that class is region-split onto r3 (`-debug-only=regalloc`: `%1633 ... Split for $r3 in 5 bundles`, `$r9 no positive bundles`).

## 2. IR oracles (post-opt edit + llc, `tools/pe.py`; main 2e1379d, 0.65728 / M 2194)

| oracle | bytes | ratio | M | native arm |
| --- | ---: | ---: | ---: | --- |
| main | 27400 | 0.65728 | 2194 | min r6 / amount r3 + `mov r6,r3` |
| **z0**: zero edge feeds constant 0 into the swept Ok phi (the original's semantics) | 27408 | 0.65479 | 2186 | amount r8 unsplit (no `mov r6,r3`), but the 0 is rematerialized (`mov r3,0`, +8 B) instead of kept in r9; vault ptr r9 |
| z0 + w14a51 r4d (J2 removed) W 3:1 | 27384 | 0.65118 | 2173 | min r7 then `mov r4,r7` (the original's split, renamed), amount r8; z0 has no effect here |
| z0/main x weights on `amount>0` (7:5, 2:1, 4:1, 1:2, 1:4) | | best 0.65578 (main, 7:5) | 2189 | |
| weights on native test, Rent ok, ensure ok, transfer ok (`e/gw.py`) | | 0.466-0.6515, tn 1000:1 = main | | |
| icmp before usub.sat / vault gep before minimum_balance | 27400 | = main | | byte-identical |
| usub.sat -> sub + select | 27344 | 0.65467 | 2183 | drops the original's overflow sequence |

z0 is the only IR state whose native arm has the original's data flow. It costs 8 tokens and 8 B, because the swept
class still does not get r9: r9 is not free for it in the post-sweep region (the w14a06 swept-coalescing residual), and
the accounts pointer `%0` stays in r8 across the arm (the w14a01 `%0` split). The original reloads it from `[0x8d8]`.

## 3. Source forms (raw-IR capture + oracle, `s/*.py`, `tools/batch.sh`)

| form | bytes | ratio | note |
| --- | ---: | ---: | --- |
| v1 `(if amount==0{Ok(())}else{ensure?;transfer}).map(\|()\|amount)` | 27400 | = main | byte-identical |
| v4 `let n=amount;` passed to transfer, `.map(\|()\|amount)` (w14a03 use-count trick) | 27400 | = main | byte-identical |
| v3 `let l=lamports(); if l>min{..l-min..}` + `.map(\|()\|l.saturating_sub(min))` | 27432 | 0.6494 | worse |
| **z1** `if amount>0{ensure?;transfer.map(\|()\|amount)}else{Ok(0)}` | 27408 | 0.65479 | **= z0 oracle exactly** |
| z2 `.map(\|()\|if amount>0{amount}else{0})` | 27408 | 0.65479 | = z0 |
| z1 + each of 71 applicable w14a31/catalog knobs | | best at 27400: **z1+tp_dlen 0.65608** (M 2190) | most knobs are no-ops on this main |

So z0 can be reached from source (z1/z2), but at 27,400 B its best pairing is 4 tokens below main.

Re-run on main fc628cfd8 (0.65758, M 2195, `eq_main=true`): z1 is 0.65568 at 27,408 B (M 2189), z1+tp_dlen is 0.65638 at 27,400 B
(M 2191, 3,186 slots), and z1+wl_coin_dlen is 0.65528 at 27,392 B. The conclusion does not change.

## 4. What is left

The native-arm naming is not a local lever. It follows two global register-allocation decisions:
1. the swept/Err-payload coalescing class must get r9 across the sweep and post-sweep regions (w14a06, w14a33 section 5);
2. `%0` must be spilled, not held in r8, across the native arm (w14a01).
Once both hold, z1's constant-0 zero edge gives the original's `mov r9,0` hoisted before `minimum_balance`, with no extra
instruction (the constant is shared with the call argument). On its own, z1 is -8 tokens. Try it only on top of a state that already has (1) and (2).

## Tools (`tools/`, text only)

- `pe.py`, `rx.py`, `capraw.py`, `capvar.sh` (w14a51/w14a31 oracle, paths point at this lane), and `sbs.py`, `amap.py`,
  `absratio.py`, `dis.sh`, `disso.sh` (w14a25). Copy `orig.rel` from `~/.cache/pumpfun-reconstruction/lanes/w14a51-cto-sweepjoin/`.
- `segdiff.py`, `splice.py`, `fnbin.py` (w14a53).
- New: `reg.py <o|so>` counts raw-identical aligned lines in the native region. `rafinal.py <greedy.log> <slot>...` gives the final greedy
  assignments covering a slot index. `ovl.py <greedy.log> <vreg> <physreg>` lists the final intervals on a physreg that overlap a vreg.
  `batch.sh <slot> <names...>` runs source form -> capture -> rx -> `screen.jsonl`.
- Debug llc for `-debug-only=regalloc`: `~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc` (its output equals the SDK llc's).
- Oracle edits: `e/z0.py` (constant-0 zero edge), `e/zw.py` (z0 + `amount>0` weights), `e/gw.py` (z0 + named branch weights),
  `e/o1.py` (IR order / sub+select), `e/z0r4d.py` + `e/r4d.py` (z0 + J2 removal).
